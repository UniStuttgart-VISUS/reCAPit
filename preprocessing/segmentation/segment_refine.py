import argparse
import pandas as pd
import json
import numpy as np
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--similarity_threshold', default=.5, required=False, type=float)
    parser.add_argument('--gap_threshold', default=1, required=False, type=float)
    parser.add_argument('--min_dur_sec', default=15, required=False, type=float)
    args = parser.parse_args()

    root_dir = args.meta.parent
    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        transcript = pd.read_csv(meta['artifacts']['transcript'], encoding='utf-8-sig')
        transcript['text'] = transcript['text'].astype(str)
        transcript['speaker'] = transcript['speaker'].astype(str)

        model_name_or_path="Alibaba-NLP/gte-multilingual-base"
        model = SentenceTransformer(model_name_or_path, trust_remote_code=True)

        out_path = args.out_dir / 'refined.csv'
        initial_segments = pd.read_csv(meta['artifacts']['segments']['initial'])
        out_table = []

        for _, row in initial_segments.iterrows():
            start_ts = row['start timestamp [sec]']
            end_ts = row['end timestamp [sec]']

            if row['duration [sec]'] < 5:
                print("Skipping short segment")
                continue

            transcript_segment = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]
            if transcript_segment.empty:
                print("Empty segment")
                continue

            for start_ts, end_ts in transcript_segmentation_multi(transcript_segment, model, args.gap_threshold, args.similarity_threshold, args.min_dur_sec):
                transcript_sub_segment = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]
                out_table.append([start_ts, end_ts, end_ts-start_ts])

        out_table = pd.DataFrame(out_table, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]'])
        out_table.to_csv(out_path, index=None, encoding='utf-8-sig')
        meta['artifacts']['segments']['refined'] = str(out_path)

        f.seek(0)
        json.dump(meta, f, indent=4)
