import pandas as pd
from dataclasses import dataclass, field
from enum  import StrEnum

class DisplayState(StrEnum):
    VISIBLE = 'visible'
    HIDDEN = 'hidden'
    HIGHLIGHTED = 'highlighted'

@dataclass
class QuotesText:
    original: str = ''
    formatted: str = ''
    quotes: list = field(default_factory=list)


@dataclass
class TimelineSegment:
    start_ts: float
    end_ts: float
    title: str
    summary: str
    marked: bool = False
    has_card: bool = True
    labels: list = field(default_factory=list)
    quotes_text: QuotesText = field(default_factory=QuotesText)
    quotes_note: str = ''


def from_dataframe(segments: pd.DataFrame) -> list[TimelineSegment]:
    return [
        TimelineSegment(seg['start timestamp [sec]'].item(),
                        seg['end timestamp [sec]'].item(),
                        seg['title'],
                        seg['summary'])
        for seg in segments.to_records()
    ]
