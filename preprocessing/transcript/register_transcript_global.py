import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import argparse
import pandas as pd
import logging

from tqdm import tqdm
from pathlib import Path
from manifest_manager import ManifestManager
from collections.abc import Callable
from faster_whisper import WhisperModel
#from pyannote.audio import Pipeline
#from pyannote.audio.pipelines.utils.hook import ProgressHook
import gc

LANGUAGES = {
    "en": "english",
    "zh": "chinese",
    "de": 'german',
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "he": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
    "yue": "cantonese",
}

"""
def diarization(audio_path:Path, hf_token:str) -> None:
    # Community-1 open-source speaker diarization pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        token=hf_token)

    # send pipeline to GPU (when available)
    pipeline.to(torch.device("cuda"))

    # apply pretrained pipeline (with optional progress hook)
    with ProgressHook() as hook:
        output = pipeline(audio_path, hook=hook)  # runs locally

    # print the result
    for turn, speaker in output.speaker_diarization:
        print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")



"""

def stt(audio_path: Path, language: str,
        max_speech_pause: float,
        consumer_callback: Callable[[str, float, float], None],
        model_size: str ='large-v3') -> None:

    model = WhisperModel(model_size, device='cuda', compute_type='float16')

    segments, info = model.transcribe(audio_path, beam_size=5,
                                      language=language if language in LANGUAGES else None,
                                      word_timestamps=True, vad_filter=True)
    last_segment = None

    for curr_segment in segments:
        for curr_word in curr_segment.words:
            if last_segment is not None:
                last_text, last_start, last_end = last_segment
                if curr_word.start - last_end <= max_speech_pause:
                    last_segment = (last_text + curr_word.word, last_start, curr_word.end)
                else:
                    print(last_segment)
                    consumer_callback(last_segment)
                    last_segment = (curr_word.word, curr_word.start, curr_word.end)
            else:
                last_segment = (curr_word.word, curr_word.start, curr_word.end)

    if last_segment is not None:
        consumer_callback(last_segment)
    return model


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--max_speech_pause', type=float, default=0.5)
    parser.add_argument('--root_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with ManifestManager(args.manifest, args.root_dir) as man:
        out_path = args.root_dir / 'transcript.csv'
        audio_path = man.get_source('audio')['path']
        rec_root = args.root_dir

        transcript_segments = []
        model = stt(audio_path, man.get_language(), args.max_speech_pause, transcript_segments.append)
        transcript = pd.DataFrame.from_records(transcript_segments,
                                               columns=('text',
                                                        'start timestamp [sec]',
                                                        'end timestamp [sec]'))

        transcript['speaker'] = ''
        transcript.to_csv(out_path, index=False, encoding='utf-8-sig')
        man.register_artifact('transcript', {'path': str(out_path), 'offset_sec': 0.0})
        logging.info('Registered "transcript" as an global artifact')

    """
    # Cleanup model after everything is done
    if 'model' in locals():
        del model
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        del model
        """
    print('-------------------DONE-------------------')
    gc.collect()
    sys.exit(0)