import pandas as pd

from collections.abc import Callable
from dataclasses import dataclass
from TimelineSegment import TimelineSegment

@dataclass
class TranscriptRecord:
    start_ts: float
    end_ts: float
    text: str
    speaker: str
    role: str

def from_dataframe(transcript: pd.DataFrame, 
                   timeline_segments: list[TimelineSegment],
                   speaker2role: Callable[[str], str]) -> list[list[TranscriptRecord]]:

    transcript = transcript[transcript['speaker'].notna()]
    transcript['role'] = transcript['speaker'].map(
        lambda s: speaker2role(s.replace(' ', '')),
    )
    transcript['duration [sec]'] = (
        transcript['end timestamp [sec]']
        - transcript['start timestamp [sec]']
    )
    transcript_records = []
    for seg in timeline_segments:
        part = transcript[
            (transcript['start timestamp [sec]'] >= seg.start_ts)
            & (transcript['end timestamp [sec]'] <= seg.end_ts)
        ]
        transcript_records.append([TranscriptRecord(rec['start timestamp [sec]'].item(),
                                                    rec['end timestamp [sec]'].item(),
                                                    rec['text'],
                                                    rec['speaker'],
                                                    rec['role']) for rec in part.to_records(index=False)])
    return transcript_records
