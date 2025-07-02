import openai
import json
import os
import argparse
import logging
import pandas as pd

import tiktoken

from pathlib import Path
from typing import List, Dict


def chunk_dialogue(dialogue: List[Dict], chunk_size: int = 100, overlap: int = 10) -> List[List[Dict]]:
    """Splits a dialogue into overlapping chunks to fit within the model's context size."""
    chunks = []
    for i in range(0, len(dialogue), chunk_size - overlap):
        chunk = dialogue[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


def call_openai_api(dialogue_chunk: List[Dict], client, model, language) -> List[Dict]:
    """Calls OpenAI's structured API to segment a dialogue chunk."""
    messages = [
        #{"role": "system", "content": f"Divide the {language} dialogue into coherent segments by providing start and end indices and assign fitting titles. Segments should be roughly between 15 to 90 seconds in duration. Further, summarize each segment in a single sentence, focusing solely on the content while omitting speaker details. Return the result in {language} and in valid JSON format."},  # <-- Fix: Explicitly mention "JSON"
        #{"role": "system", "content": f"Divide the {language} dialogue into segments. Segments should be roughly between 15 to 90 seconds in duration and can be topic-based or based on the speaker dynamics. Assign fitting titles to each segment. Further, summarize each segment in a single sentence, focusing solely on the content while omitting speaker details. Return the result in {language} and in valid JSON format."},  # <-- Fix: Explicitly mention "JSON"
        #{"role": "system", "content": f"Segment the {language} dialogue into fine-grained parts. Assign a concise and relevant title to each segment. Additionally, provide a one-sentence summary of each segment, focusing on content while omitting speaker details. Return the output strictly in valid JSON format and in {language}."},
        {"role": "system", "content": f"Segment the {language} dialogue into parts based on the discussed topics, each with a minimum duration of roughly 15 seconds. Return the output strictly in valid JSON format and in {language}."},
        {"role": "user", "content": json.dumps(dialogue_chunk)}
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        functions=[{
            "name": "segment_dialogue",
            "description": f"Segments of the {language} dialogue based on the discussed topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_id": {
                                    "type": "integer",
                                    "description": "The id of the first utterance in the segment."
                                },
                                "end_id": {
                                    "type": "integer",
                                    "description": "The id of the last utterance in the segment."
                                }
                            },
                            "required": ["start_id", "end_id"],
                            "additionalProperties": False
                        }
                    }
                }
            }
        }]
    )

    segment_response = response.choices[0].message.function_call.arguments

    """
    if segment_response.refusal:
        print(segment_response.refusal)
    """

    
    return json.loads(segment_response)['segments']


def merge_segments(segments: List[Dict]) -> List[Dict]:
    """Merges consecutive segments with the same title."""
    merged = []
    for seg in segments:
        if merged and merged[-1]["title"] == seg["title"]:
            merged[-1]["end_index"] = seg["end_index"]
        else:
            merged.append(seg)
    return merged


def segment_large_dialogue(dialogue: List[Dict], client, model, language) -> List[Dict]:
    """Handles long dialogues by chunking, processing, and merging results."""
    all_segments = []
    for chunk in chunk_dialogue(dialogue):
        segments = call_openai_api(chunk, client, model, language)
        print(segments)
        all_segments.extend(segments)
    return merge_segments(all_segments)


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
                'text': ' '.join([r['text'] for r in current_chunk]),
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


if __name__ == '__main__':
    openai_api_key = os.environ.get('OPENAI_KEY_PRIVATE')
    if not openai_api_key:
        logging.error("OpenAI API key not found in environment variables.")
        exit(1)

    client = openai.OpenAI(api_key=openai_api_key)

    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--gpt_model', default='gpt-4o-mini', required=False)
    args = parser.parse_args()

    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    transcript = pd.read_csv(args.meta.parent / meta['utterances'], encoding='utf-8-sig')
    transcript['text'] = transcript['text'].astype(str)
    transcript['speaker'] = transcript['speaker'].astype(str)

    word_count = transcript['text'].apply(lambda t: len(str(t).split(' ')))
    transcript_trunc = transcript[word_count > 0]

    utterances = transcript_trunc.apply(lambda row: {'speaker': row['speaker'], 'utterance': row['text'], 'id': row.name, 'duration [sec]': row['end timestamp [sec]'] - row['start timestamp [sec]']}, axis=1)
    utterances = utterances.values.tolist()
    print(utterances)

    enc = tiktoken.encoding_for_model(args.gpt_model)
    encoded_lengths = [len(enc.encode(utterance['utterance'])) for utterance in utterances]
    print(f'Number of tokens of utterances: {sum(encoded_lengths)}')

    segmented_dialogue = call_openai_api(utterances, client=client, model=args.gpt_model, language=meta['language'])

    out_table = []

    for s in segmented_dialogue:
        min_idx = s['start_id']
        max_idx = s['end_id']

        transcript_segment = transcript.iloc[min_idx: max_idx+1]

        overlapping_speech_sec = speech_overlap(transcript_segment)
        num_turns = count_turns(transcript_segment)

        if transcript_segment.empty:
            print("Empty segment")
            continue

        start_ts = transcript_segment['start timestamp [sec]'].iloc[0]
        end_ts = transcript_segment['end timestamp [sec]'].iloc[-1]

        joined_text = '.'.join(transcript_segment['text'].tolist())
        print(s['topic'])

        title = execute_prompt(client, generate_prompt_title(joined_text, meta['language']), args.gpt_model)
        summary = execute_prompt(client, generate_prompt_summary(joined_text, meta['language']), args.gpt_model)

        out_table.append([start_ts, end_ts, end_ts-start_ts, overlapping_speech_sec, num_turns, title, summary, s['topic']])

    out_table = pd.DataFrame(out_table, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]', 'speech overlap [sec]', 'turn count', 'title', 'summary', 'topic'])
    out_table.to_csv((args.out_dir / 'topic_segments.csv'), index=None, encoding='utf-8-sig')