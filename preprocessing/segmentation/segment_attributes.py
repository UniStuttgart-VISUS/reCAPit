import argparse
import pandas as pd
import json
import openai
import os
import logging

from pathlib import Path

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


def segment_attributes(transcript_segment, language):
    overlapping_speech_sec = speech_overlap(transcript_segment)
    num_turns = count_turns(transcript_segment)

    joined_text = '.'.join(transcript_segment['text'].tolist())

    title = "Title not generated"
    summary = "Summary not generated"

    title = execute_prompt(client, generate_prompt_title(joined_text, language), args.gpt_model)
    summary = execute_prompt(client, generate_prompt_summary(joined_text, language), args.gpt_model)

    logging.info(f'GPT response - {title}: {summary}')

    return {'summary': summary, 'title': title, 'overlap': overlapping_speech_sec, 'num_turns': num_turns}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--gpt_model', default='gpt-4o-mini', required=False)
    parser.add_argument('--target_segments', default='refined', choices=('initial', 'refined'), required=False)
    parser.add_argument('--openai_api_key', required=False, type=str)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    root_dir = args.manifest.parent
    manifest = json.load(open(args.manifest, 'r'))

    if 'transcript' not in manifest['artifacts']:
        logging.error("Transcript is not specified in artifacts!")
        exit(1)

    if 'segments' not in manifest['artifacts']:
        logging.error("Segments are not specified in artifacts!")
        exit(1)

    if args.target_segments not in manifest['artifacts']['segments']:
        logging.error(f'There are no "{args.target_segments}" segments found')
        exit(1)

    if args.openai_api_key is None:
        openai_api_key = args.openai_api_key

    if openai_api_key is None:
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logging.error('Either pass your OpenAI API key as an argument or store it in the environment variable "OPENAI_API_KEY".')
            exit(1)

    client = openai.OpenAI(api_key=openai_api_key)

    transcript = pd.read_csv(manifest['artifacts']['transcript']['path'], encoding='utf-8-sig')
    transcript['text'] = transcript['text'].astype(str)
    transcript['speaker'] = transcript['speaker'].astype(str)

    out_table = []
    segments = pd.read_csv(manifest['artifacts']['segments'][args.target_segments]['path'])

    for _, row in segments.iterrows():
        start_ts = row['start timestamp [sec]']
        end_ts = row['end timestamp [sec]']

        transcript_segment = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]

        if transcript_segment.empty:
            logging.warning(f"Time span {start_ts:.2f}s - {end_ts:.2f}s has no speech")
            continue

        seg_attr = segment_attributes(transcript_segment, manifest['language'])
        out_table.append([start_ts, end_ts, end_ts-start_ts, seg_attr['overlap'], seg_attr['num_turns'], seg_attr['title'], seg_attr['summary']])

    out_table = pd.DataFrame(out_table, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]', 'speech overlap [sec]', 'turn count', 'title', 'summary'])
    out_table.to_csv(manifest['artifacts']['segments'][args.target_segments]['path'], index=None, encoding='utf-8-sig')
    logging.info(f'Successfully modified "{args.target_segments}" segments')