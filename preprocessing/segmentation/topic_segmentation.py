import argparse
import pandas as pd
import json
import matplotlib.pyplot as plt
import ruptures as rpt
import scipy
import numpy as np
import scipy.signal
import openai
import os
import logging

from pathlib import Path
from sentence_transformers import SentenceTransformer


def chunk_transcript(df, gap_threshold=2.0):
    df = df.sort_values(by='start timestamp [sec]').reset_index(drop=True)
    chunks = []
    current_chunk = []
    chunk_start = df.loc[0, 'start timestamp [sec]']
    chunk_end = df.loc[0, 'end timestamp [sec]']
    
    for i, row in df.iterrows():
        if current_chunk and row['start timestamp [sec]'] - chunk_end > gap_threshold:
            # Save the completed chunk
            chunks.append({
                'start timestamp [sec]': chunk_start,
                'end timestamp [sec]': chunk_end,
                'text': ' '.join([r['text'] for r in current_chunk if len(r['text'].split(' ')) > 0] ),
                'speakers': list(set(r['speaker'] for r in current_chunk))
            })
            # Start a new chunk
            current_chunk = []
            chunk_start = row['start timestamp [sec]']
        
        current_chunk.append(row)
        chunk_end = row['end timestamp [sec]']
    
    # Append the last chunk
    if current_chunk:
        chunks.append({
            'start timestamp [sec]': chunk_start,
            'end timestamp [sec]': chunk_end,
            'text': ' '.join([r['text'] for r in current_chunk]),
            'speakers': list(set(r['speaker'] for r in current_chunk))
        })
    
    return chunks



def generate_prompt_summary(text, language):
    return [
          {
              "role": "system",
              "content": f"You are a linguist who provides concise and accurate summaries from {language} dialogues and utterances."
          },
          {
              "role": "user", 
              "content": f'Summarize the following {language} dialogue in one sentence, focusing only on the content and omitting speaker details: """{text}"""'
          }
    ]

def generate_prompt_keywords(text, language):
    return [
          {
              "role": "system",
              "content": f"You are a linguist who extracts topics from {language} dialogue transcripts."
          },
          {
              "role": "user", 
              "content": f'Provide a maximum of comma-separated topics in {language} that best describe the following text: """{text}"""'
          }
    ]

def generate_prompt_title(text, language):
    return [
          {
              "role": "system",
              "content": f"You are a linguist who creates {language} titles for dialogue transcripts."
          },
          {
              "role": "user", 
              "content": f'Give the following text a concise and short title in {language}. Output only the title without any prefix or parentheses. : """{text}"""'
          }
    ]

def execute_prompt(client, prompt_def, model):
    completion = client.chat.completions.create(
        model = model,
        messages=prompt_def
    )
    return completion.choices[0].message.content


def count_turns(transcript):
    last = -1
    count = 0
    
    for _, row in transcript.iterrows():
        if row['speaker'] != last:
            last = row['speaker']
            count += 1
    return count


def speech_overlap(transcript):
    rows = [r for _, r in transcript.iterrows()]
    overlap_sec = 0

    for i in range(len(rows)):
        start_sec = rows[i]['start timestamp [sec]']
        j = i - 1

        while j >= 0 and rows[j]['end timestamp [sec]'] > start_sec:
            overlap_sec += rows[j]['end timestamp [sec]'] - start_sec
            j -= 1
    return overlap_sec


def segment_attributes(transcript_segment):
    overlapping_speech_sec = speech_overlap(transcript_segment)
    num_turns = count_turns(transcript_segment)

    joined_text = '.'.join(transcript_segment['text'].tolist())

    title = "Title not generated"
    summary = "Summary not generated"

    title = execute_prompt(client, generate_prompt_title(joined_text, meta['language']), args.gpt_model)
    summary = execute_prompt(client, generate_prompt_summary(joined_text, meta['language']), args.gpt_model)

    return {'summary': summary, 'title': title, 'overlap': overlapping_speech_sec, 'num_turns': num_turns}


def mvt_segmentation(mvt, downsampling_factor=5, min_dur_sec=30, show_plot=True):

    if 'timestamp [sec]' not in mvt.columns:
        print("Adding timestamp column")
        mvt['timestamp [sec]'] = np.linspace(0, meta['duration_s'], mvt.shape[0])
    
    preprocessed = pd.DataFrame.copy(mvt)

    if 'timestamp [sec]' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['timestamp [sec]'])

    if 'frame' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['frame'])

    if 'full' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['full'])

    if downsampling_factor > 1:
        preprocessed = scipy.signal.decimate(preprocessed.values, downsampling_factor, axis=0)
    else:
        preprocessed = preprocessed.values

    print(f'Original signal shape: {mvt.shape}, downsampled signal shape: {preprocessed.shape}')

    #min_size = (meta['duration_s'] / mtv.shape[0]) * min_dur_sec / downsampling_factor
    min_size = int(preprocessed.shape[0] * min_dur_sec / meta['duration_s'])

    print(f"Minimum segment size: {min_size}")

    algo = rpt.Pelt(model="rbf", min_size=min_size, jump=5).fit(preprocessed)
    #algo = rpt.Pelt(model="rbf", min_size=1, jump=1).fit(preprocessed)
    result = algo.predict(pen=20)
    #result = algo.predict(pen=1)

    if show_plot:
        rpt.display(preprocessed, result)
        plt.show()

    return result

    
def transcript_segmentation_single(transcript, model):
    start_ts = transcript.iloc[0]['start timestamp [sec]']
    end_ts = transcript.iloc[-1]['end timestamp [sec]']

    chunks = chunk_transcript(transcript, gap_threshold=1.0)
    print(chunks)
    print(80*'-')
    embeddings = model.encode([c['text'] for c in chunks], normalize_embeddings=True)

    scores = model.similarity(embeddings[:1], embeddings[1:])
    scores = scores.numpy().flatten()

    if scores.shape[0] < 2:
        return [(start_ts, end_ts)]

    thresholded = np.argwhere(scores < 0.5).flatten()

    if thresholded.shape[0] == 0 or thresholded[0] == 0:
        return [(start_ts, end_ts)]

    split_idx = thresholded[np.argmin(scores[thresholded])]
    mid_ts = chunks[split_idx]['end timestamp [sec]']

    print(f"Splitting at {mid_ts} with score {scores[split_idx]}")
    return [(start_ts, mid_ts), (mid_ts, end_ts)]


def transcript_segmentation_multi(transcript, model, gap_threshold=0.75, similarity_threshold=0.5, min_dur_sec=10.0):
    start_ts = transcript.iloc[0]['start timestamp [sec]']
    end_ts = transcript.iloc[-1]['end timestamp [sec]']

    # Chunk the transcript based on pauses
    chunks = chunk_transcript(transcript, gap_threshold=gap_threshold)
    print(chunks)
    print(80*'-')

    # Encode chunk texts into embeddings
    embeddings = model.encode([c['text'] for c in chunks], normalize_embeddings=True)

    # Compute similarity scores between consecutive chunks
    scores = model.similarity(embeddings[:-1], embeddings[1:]).numpy().flatten()

    # If there aren't enough chunks to split meaningfully, return the full range
    if len(scores) < 2:
        return [(start_ts, end_ts)]

    print(scores)

    # Adaptive thresholding (optional)
    mean_sim = np.mean(scores)
    std_sim = np.std(scores)
    adaptive_threshold = min(similarity_threshold, mean_sim - 0.5 * std_sim)  # Adjust threshold dynamically
    print(f"Adaptive threshold: {adaptive_threshold}")

    # Identify potential split points where similarity drops below threshold
    split_indices = np.argwhere(scores < adaptive_threshold).flatten()
    split_indices = split_indices[split_indices < len(chunks) - 1] 

    # Filter out too-close splits and ensure min segment length
    split_times = []
    last_split = start_ts

    for idx in split_indices:
        split_ts = chunks[idx]['end timestamp [sec]']
        if split_ts - last_split >= min_dur_sec:  # Enforce a minimum segment length
            print(f"Splitting at {split_ts} with score {scores[idx]}")
            split_times.append(split_ts)
            last_split = split_ts

    # If no valid split points, return the full segment
    if not split_times:
        return [(start_ts, end_ts)]

    # Generate segment boundaries
    segments = [(start_ts, split_times[0])] + [(split_times[i], split_times[i + 1]) for i in range(len(split_times) - 1)]
    segments.append((split_times[-1], end_ts))  # Add last segment

    return segments



if __name__ == '__main__':
    #openai_api_key = os.environ.get('OPENAI_KEY_PRIVATE')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        logging.error("OpenAI API key not found in environment variables.")
        exit(1)

    client = openai.OpenAI(api_key=openai_api_key)

    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--gpt_model', default='gpt-4o-mini', required=False)
    parser.add_argument('--input_signal', default='movement', required=False)
    parser.add_argument('--downsampling_factor', default=5, required=False, type=int)
    parser.add_argument('--similarity_threshold', default=.5, required=False, type=float)
    parser.add_argument('--gap_threshold', default=1, required=False, type=float)
    parser.add_argument('--min_dur_sec', default=15, required=False, type=float)
    args = parser.parse_args()

    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    transcript = pd.read_csv(args.meta.parent / meta['utterances'], encoding='utf-8-sig')
    transcript['text'] = transcript['text'].astype(str)
    transcript['speaker'] = transcript['speaker'].astype(str)

    model_name_or_path="Alibaba-NLP/gte-multilingual-base"
    model = SentenceTransformer(model_name_or_path, trust_remote_code=True)

    if args.input_signal not in meta:
        logging.error(f"Signal {args.input_signal} not found in meta file.")
        exit(1)

    mtv = pd.read_csv(args.meta.parent / meta[args.input_signal], encoding='utf-8-sig')
    result = mvt_segmentation(mtv, downsampling_factor=args.downsampling_factor, min_dur_sec=2*args.min_dur_sec, show_plot=True)

    out_table = []

    for segment_start, segment_end in zip(result[:-1], result[1:]):
        mtv_segment = mtv.iloc[segment_start*args.downsampling_factor:segment_end*args.downsampling_factor]

        start_ts = mtv_segment.iloc[0]['timestamp [sec]']
        end_ts = mtv_segment.iloc[-1]['timestamp [sec]']

        if end_ts - start_ts < 5:
            print("Skipping short segment")
            continue

        transcript_segment = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]

        if transcript_segment.empty:
            print("Empty segment")
            continue

        #for start_ts, end_ts in transcript_segmentation_single(transcript_segment, model):
        for start_ts, end_ts in transcript_segmentation_multi(transcript_segment, model, args.gap_threshold, args.similarity_threshold, args.min_dur_sec):
            transcript_sub_segment = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]
            seg_attr = segment_attributes(transcript_sub_segment)
            out_table.append([start_ts, end_ts, end_ts-start_ts, seg_attr['overlap'], seg_attr['num_turns'], seg_attr['title'], seg_attr['summary']])

    out_table = pd.DataFrame(out_table, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]', 'speech overlap [sec]', 'turn count', 'title', 'summary'])
    out_table.to_csv((args.out_dir / 'topic_segments.csv'), index=None, encoding='utf-8-sig')
