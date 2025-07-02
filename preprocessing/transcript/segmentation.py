import time
import os
import argparse
import pandas as pd
import json

from super_dialseg import CSMSegmenter
from pathlib import Path
from openai import OpenAI

# https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api/172683

def generate_prompt_summary(text, language):
    return {
      'messages': [
          {
              "role": "system",
              "content": f"You are a linguist who provides concise and accurate summaries from {language} dialogues and utterances."
          },
          {
              "role": "user", 
              "content": f'Summarize the following {language} dialogue in one sentence, focusing only on the content and omitting speaker details: """{text}"""'
          }
       ], 
      'verify_predicate': lambda x: len(x.split('.')) == 1,
      'temperature': 0.0, 
      'max_tokens': 250
    }

def generate_prompt_keywords(text, language):
    return {
      'messages': [
          {
              "role": "system",
              "content": f"You are a linguist who extracts topics from {language} dialogue transcripts."
          },
          {
              "role": "user", 
              "content": f'Provide a maximum of comma-separated topics in {language} that best describe the following text: """{text}"""'
          }
       ], 
      'verify_predicate': lambda x: len(x.split(',')) <= 5,
      'temperature': 0.0, 
      'max_tokens': 100
    }

def generate_prompt_title(text, language):
    return {
      'messages': [
          {
              "role": "system",
              "content": f"You are a linguist who creates {language} titles for dialogue transcripts."
          },
          {
              "role": "user", 
              "content": f'Give the following text a concise and short title in {language}. Output only the title without any prefix or parentheses. : """{text}"""'
          }
       ], 
      'verify_predicate': lambda x: '"' not in x and len(x) < 200,
      'temperature': 0.0, 
      'max_tokens': 50
    }

def execute_prompt(client, prompt_def, model):
    completion = client.chat.completions.create(
        model = model,
        #temperature = prompt_def['temperature'], 
        #max_tokens = prompt_def['max_tokens'],
        messages=prompt_def['messages']
    )

    response = completion.choices[0].message.content
    passed_check = prompt_def['verify_predicate'](response)
    return response, passed_check



def utterances_from_transcript(transcript):
    lengths = transcript['text'].apply(lambda t: len(t.split(' ')))
    transcript = transcript[lengths > 10]
    utterances = transcript.apply(lambda row: row['speaker'] + ": " + row['text'], axis=1)
    utterances = utterances.values.tolist()
    return utterances



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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--gpt_model', default='gpt-4o-mini', required=False)
    args = parser.parse_args()

    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    if meta['language'] == 'german':
        backbone = 'google-bert/bert-base-german-cased'
    elif meta['language'] == 'english':
        backbone = 'bert-base-uncased'
    else:
        backbone = 'bert-base-uncased'

    openai_api_key = os.environ.get('OPENAI_KEY_PRIVATE')
    client = OpenAI(
        api_key=openai_api_key,
    )

    print(backbone)
    segmenter = CSMSegmenter(backbone=backbone, cut_rate=1.25)

    transcript = pd.read_csv(args.meta.parent / meta['utterances'], encoding='utf-8-sig')
    transcript['text'] = transcript['text'].astype(str)
    transcript['speaker'] = transcript['speaker'].astype(str)

    word_count = transcript['text'].apply(lambda t: len(str(t).split(' ')))
    transcript_trunc = transcript[word_count > 5]

    utterances = transcript_trunc.apply(lambda row: row['speaker'] + ": " + row['text'], axis=1)
    utterances = utterances.values.tolist()
    print(utterances)

    _, segmented_dialogue = segmenter(utterances)
    print(segmented_dialogue)
    out_table = []
    index = 0
    
    for s in segmented_dialogue.split(20*'-'):
        snippets = [sn for sn in s.split('\n') if len(sn) > 0]
        utterance_count = len(snippets)

        indices = transcript_trunc.iloc[index: index+utterance_count].index
        index += utterance_count

        transcript_segment = transcript_trunc.loc[indices]

        start_ts = transcript_segment.iloc[0]['start timestamp [sec]']
        end_ts = transcript_segment.iloc[-1]['end timestamp [sec]']

        transcript_segment_full = transcript[(transcript['start timestamp [sec]'] >= start_ts) & (transcript['end timestamp [sec]'] <= end_ts)]
        prompt_title = generate_prompt_title(s, meta['language'])
        prompt_summary = generate_prompt_summary(s, meta['language'])

        response_title, passed_title = execute_prompt(client, prompt_title, model=args.gpt_model)
        response_summary, passed_summary = execute_prompt(client, prompt_summary, model=args.gpt_model)

        overlapping_speech_sec = speech_overlap(transcript_segment_full)
        num_turns = count_turns(transcript_segment_full)

        print(80*'*')
        print(response_title)
        print(80*'*')

        if not passed_title:
            print(f'WARNING: OpenAI generated title "{response_title}" does not conform with requested format!')

        if not passed_summary:
            print(f'WARNING: OpenAI generated summary "{response_summary}" does not conform with requested format!')

        if start_ts < end_ts:
            out_table.append([start_ts, end_ts, end_ts-start_ts, overlapping_speech_sec, num_turns, response_title, response_summary])
        else:
            print(f'Error - Segment {" ".join(snippets)} has invalid bounds!')

        #time.sleep(1)

    out_table = pd.DataFrame(out_table, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]', 'speech overlap [sec]', 'turn count', 'title', 'summary'])
    out_table.to_csv((args.out_dir / 'topic_segments.csv'), index=None, encoding='utf-8-sig')