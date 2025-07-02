import pandas as pd
import openai
import tiktoken
import os
import re

from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN
from nltk.tokenize import sent_tokenize
from tqdm import tqdm
from itertools import chain
import argparse

from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, OpenAI
from bertopic.dimensionality import BaseDimensionalityReduction
from bertopic.vectorizers import ClassTfidfTransformer
from docx2python import docx2python
from umap import UMAP

openai_api_key = os.environ.get('OPENAI_KEY_PRIVATE')


def get_representation_model(rm='KeyBERT', gpt_model='gpt-3.5-turbo'):
    if rm == 'KeyBERT':
        representation_model = KeyBERTInspired()
    elif rm == 'NMR':
        representation_model = MaximalMarginalRelevance(diversity=0.5)
    elif rm == 'OpenAI':
        representation_model = OpenAI(
            openai.OpenAI(api_key=openai_api_key), 
            model=gpt_model, 
            delay_in_seconds=2, 
            chat=True,
            nr_docs=4,
            doc_length=100,
            tokenizer= tiktoken.encoding_for_model(gpt_model))
    else:
        raise ValueError(f'No valid representation model "{rm}"!')

    return representation_model

def get_topic_model(representation_model, language):
    """
    embedding_model = "all-MiniLM-L6-v2"
    embedding_model = "all-mpnet-base-v2"
    zeroshot_topic_list = ["Konflikte", "Grünflächen", "Soziale Interaktion", "Infrakstruktur", "Politik"]

    umap_model = UMAP(n_neighbors=10, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    vectorizer_model = CountVectorizer(stop_words="english", min_df=2, max_df=0.75, ngram_range=(1, 2))
    ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True, bm25_weighting=True)
    cluster_model = HDBSCAN(min_cluster_size=4, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
    """

    return BERTopic(representation_model=representation_model, 
                    language=language,
                    min_topic_size=3,
                    #zeroshot_topic_list=zeroshot_topic_list,
                    #zeroshot_min_similarity=.85,
                    #hdbscan_model=cluster_model,  
                    #ctfidf_model=ctfidf_model, 
                    #vectorizer_model=vectorizer_model, 
                    #umap_model=umap_model, 
                    #embedding_model=embedding_model,
                    calculate_probabilities=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--gpt_model', default='gpt-3.5-turbo', choices=['gpt-3.5-turbo', 'gpt-4'], required=False)
    parser.add_argument('--representation_model', default='KeyBERT', choices=('KeyBERT', 'NMR', 'OpenAI'), required=False)
    parser.add_argument('--language', choices=('german', 'english'), default='english')
    args = parser.parse_args()

    root_dir = args.meta.parent
    segments = pd.read_csv(root_dir / 'data' / 'topic_segments.csv')
    docs = segments['Text'].tolist()

    #p = re.compile('[a-zA-Z0-9]+:')
    #docs = [re.sub(p, '', s).replace('\n', ' ').strip() for s in segments['Text'].tolist()]
    #segments = pd.read_csv('D:\\Recordings\\Workshop-BandVIS\\public\\topic_segments.csv')
    #segments = pd.read_csv('D:\\Recordings\\Gigamapping Codesign Workshop - 13.11.23\\tables\\topic_segments.csv')

    rm = get_representation_model(args.representation_model, gpt_model=args.gpt_model)
    tm = get_topic_model(rm, args.language)

    topics, _ = tm.fit_transform(docs)

    topic_assignment = tm.get_document_info(docs)
    print(topic_assignment)

    segments['Topic ID']  = topic_assignment['Topic']
    segments['Topic Name']  = [re.sub('.+_', '', n) for n in topic_assignment['Name'].values]
    segments.to_csv(root_dir / 'data' / 'topic_segments.csv', index=False, encoding='utf-8-sig')

    fig = tm.visualize_heatmap()
    fig.show()