import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
from pathlib import Path
from scipy.stats import entropy

def compute_transition_entropy(df, window_size=15):
    # Convert timestamps to numeric (seconds)
    df = df.sort_values(by='start timestamp [sec]')
    
    # Get unique speakers
    unique_speakers = df['speaker'].unique()
    print(unique_speakers)
    speaker_to_idx = {spk: i for i, spk in enumerate(unique_speakers)}
    num_speakers = len(unique_speakers)

    # Initialize results list
    results = []
    
    # Iterate over the dataset with a sliding window
    start_idx = 0

    start_time = df.iloc[0]['start timestamp [sec]']
    end_time = df.iloc[-1]['end timestamp [sec]']

    #for window_start in np.arange(start_time, end_time, window_size):
    for t in np.arange(start_time, end_time, .5):

        window_start = t - window_size / 2
        window_end = t + window_size / 2
        window_data = df[(df['start timestamp [sec]'] >= window_start) & (df['end timestamp [sec]'] <= window_end)]
        
        # Compute transition matrix
        transition_matrix = np.zeros((num_speakers, num_speakers))
        for j in range(len(window_data) - 1):
            s1 = speaker_to_idx[window_data.iloc[j]['speaker']]
            s2 = speaker_to_idx[window_data.iloc[j+1]['speaker']]
            transition_matrix[s1, s2] += 1
        
        # Normalize transition matrix to get probabilities
        row_sums = transition_matrix.sum(axis=1, keepdims=True)
        transition_probs = np.divide(transition_matrix, row_sums, where=row_sums != 0)
        turn_entropy = entropy(transition_probs.flatten(), base=2) if transition_probs.size > 0 else 0
        
        results.append({'time': t, 'entropy': turn_entropy})
    
    return pd.DataFrame(results)

def plot_entropy(entropy_df):
    plt.figure(figsize=(10, 5))
    plt.plot(entropy_df['time'], entropy_df['entropy'], linestyle='-')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Transition Entropy')
    plt.title('Speaker Transition Entropy Over Time')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    args = parser.parse_args()

    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    transcript = pd.read_csv(args.meta.parent / meta['utterances'], encoding='utf-8-sig')
    entropy_df = compute_transition_entropy(transcript)
    plot_entropy(entropy_df)
