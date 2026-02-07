import os
from typing import Any
os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = '1'

import sys
import argparse
import whisperx
import gc
import torch
import pandas as pd
import queue

from pathlib import Path
from helper.manifest_manager import ManifestManager
from whisperx.diarize import DiarizationPipeline
from whisperx.utils import TO_LANGUAGE_CODE
from threading import Thread
from typing_extensions import Self

def delete_model(model: Any) -> None:
    gc.collect()
    torch.cuda.empty_cache()
    del model


class DebugOutputWindow:
    """A tkinter window for visual debugging that displays stdout output."""
    
    def __init__(self, title: str = "Debug Output") -> None:
        import tkinter as tk
        from tkinter import scrolledtext
        
        self._tk = tk
        self._text_queue: queue.Queue[str] = queue.Queue()
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x300")
        self.root.resizable(True, True)
        
        self.text_widget = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        self._original_stdout = sys.stdout
        
    def write(self, text: str) -> None:
        """Write text to the queue (thread-safe) and original stdout."""
        self._original_stdout.write(text)
        self._text_queue.put(text)
        
    def flush(self) -> None:
        """Flush the original stdout."""
        self._original_stdout.flush()
        
    def _process_queue(self) -> None:
        """Process all pending text from the queue (called from main thread)."""
        while True:
            try:
                text = self._text_queue.get_nowait()
                self.text_widget.insert(self._tk.END, text)
                self.text_widget.see(self._tk.END)
            except queue.Empty:
                break
        
    def update(self) -> None:
        """Update the tkinter window and process queued text."""
        self._process_queue()
        self.root.update()
        
    def close(self) -> None:
        """Close the debug window."""
        self.root.destroy()
        
    def __enter__(self) -> Self:
        sys.stdout = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        sys.stdout = self._original_stdout

class SpeechToTextPipeline(Thread):
    def __init__(self, audio_path: Path,
                 language: str,
                 model_name: str,
                 num_speakers: int,
                 hf_token: str,
                 device: str) -> None:
        super().__init__()

        self.audio = whisperx.load_audio(audio_path)
        self.model_name = model_name
        self.num_speakers = num_speakers
        self.hf_token = hf_token
        self.language = TO_LANGUAGE_CODE[language]
        self.device = device
        self.compute_type = 'float16' if device == 'cuda' else 'int8'
        self.result = None

    def run(self) -> None:
        print('******************************* START TRANSCRIBE *******************************')
        self.transcribe()
        print('******************************** END TRANSCRIBE ********************************')
        print('******************************* START ALIGNMENT ********************************')
        self.align()
        print('********************************* END ALIGNMENT ********************************')
        if self.hf_token != '' and self.num_speakers > 0:
            print('**************************** START DIARIZATION *****************************')
            self.diarize()
            print('***************************** END DIARIZATION ******************************')

    def transcribe(self) -> None:
        model = whisperx.load_model(self.model_name, device=self.device, language=self.language, compute_type=self.compute_type)
        self.result = model.transcribe(self.audio, batch_size=8, verbose=True)
        delete_model(model)

    def align(self) -> None:
        model_a, metadata = whisperx.load_align_model(language_code=self.result['language'], device=self.device)
        self.result = whisperx.align(self.result['segments'], model_a, metadata, self.audio, self.device, return_char_alignments=False)
        delete_model(model_a)

    def diarize(self) -> None:
        diarize_model = DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)
        diarize_segments = diarize_model(self.audio, num_speakers=self.num_speakers)
        self.result = whisperx.assign_word_speakers(diarize_segments, self.result)


def segments_to_dataframe(segments: list[dict]) -> pd.DataFrame:
    out = []
    for seg in segments:
        """
        speakers = [w['speaker'] if w['score'] >= min_score else '' for w in seg['words']]
        res = np.unique_counts(speakers)
        assigned_speaker = res.values[res.counts.argmax()]  # noqa: PD011
        """
        formatted_text = seg['text'].strip('"').strip()
        #formatted_text = f'"{formatted_text}"'

        out.append((seg['start'], seg['end'], formatted_text, seg.get('speaker', '')))

    return pd.DataFrame.from_records(out, columns=['start timestamp [sec]',
                                                'end timestamp [sec]',
                                                'text', 'speaker'])

def run_pipeline_with_debug(stt_pipeline: SpeechToTextPipeline) -> None:
    """Run the pipeline with a debug output window."""
    with DebugOutputWindow('Transcript Pipeline Debug') as debug_window:
        stt_pipeline.start()

        # Keep the window responsive while the pipeline is running
        while stt_pipeline.is_alive():
            debug_window.update()
            stt_pipeline.join(timeout=0.1)


def run_pipeline_standard(stt_pipeline: SpeechToTextPipeline) -> None:
    """Run the pipeline without debug output."""
    stt_pipeline.start()
    stt_pipeline.join()

def remove_time_offset(transcript: pd.DataFrame, offset_sec: float) -> None:
    transcript['start timestamp [sec]'] = transcript['start timestamp [sec]'] - offset_sec
    transcript['end timestamp [sec]'] = transcript['end timestamp [sec]'] - offset_sec


def trim(transcript: pd.DataFrame, duration_sec: float) -> pd.DataFrame:
    mask = (transcript['start timestamp [sec]'] >= 0) & (transcript['end timestamp [sec]'] <= duration_sec)
    return transcript[mask]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--num_speakers', type=int, default=0)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--hf_token', type=str, default='')
    parser.add_argument('--show_output', action='store_true', help='Enable visual debug display')
    args = parser.parse_args()

    with ManifestManager(args.manifest, args.root_dir) as man:
        out_path = args.root_dir / 'transcript.csv'
        audio_src = man.get_source('audio')
        rec_root = args.root_dir
        duration_sec = man.get_duration_sec()

        stt_pipeline = SpeechToTextPipeline(audio_src['path'],
                                            man.get_language(),
                                            'large-v2',
                                            args.num_speakers,
                                            args.hf_token,
                                            args.device)

        if args.show_output:
            run_pipeline_with_debug(stt_pipeline)
        else:
            run_pipeline_standard(stt_pipeline)

        transcript = segments_to_dataframe(stt_pipeline.result['segments'])
        remove_time_offset(transcript, audio_src['offset_sec'])
        transcript = trim(transcript, duration_sec)

        transcript.to_csv(out_path, index=False, encoding='utf-8-sig',
                          float_format='%.2f')

        man.register_artifact('transcript', {'path': str(out_path), 'offset_sec': 0.0})

    gc.collect()
    sys.exit(0)
