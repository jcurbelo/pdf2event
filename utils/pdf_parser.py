from typing import List, IO, Tuple
from pdfminer.high_level import extract_text
import re
import datefinder

EVENT_TITLES = [
    'ADDITION OF ANY NEW PARTIES',
    'FACT WITNESS LIST',
    'EXHIBIT LIST',
    'EXPERT WITNESSES',
    'FACT AND EXPERT DISCOVERY',
    'MOTIONS FOR SUMMARY JUDGMENT and DAUBERT MOTIONS',
    'OBJECTIONS TO PLEADINGS AND ALL OTHER PRETRIAL',
    'MEDIATION',
    'TRIAL',
    'JOINT PRETRIAL STIPULATION',
    'DONE and ORDERED'
]

# number of dates per title
DATES_COUNT = [
    1,
    1,
    1,
    1,
    2,
    2,
    2,
    1,
    1,
    1,
]


def extract_case_number(text: str) -> str:
    m = re.search(r"Case No: ([^\n]+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1)
    return ''


def clean_text(text: str) -> str:
    # remove unwanted content
    text = re.sub(r"Page \d+ of \d+", '', text)
    text = re.sub(r"Case No: [^\n]+", '', text)
    # remove extra empty lines
    lines = text.split('\n')
    lines = [line for line in lines if line.strip()]
    text = '\n'.join(lines)
    return text


def extract_chunks(text: str) -> dict:
    chunks = {}
    lines = text.split('\n')
    current_idx = 0
    current_chunk = ''
    current_title = None
    next_title = EVENT_TITLES[current_idx]
    for l in lines:
        if next_title in l:
            if current_title is not None:
                chunks[current_title] = current_chunk
            current_chunk = ''
            # set up for next title
            if current_idx == len(EVENT_TITLES) - 1:
                break
            current_idx += 1
            current_title = next_title
            next_title = EVENT_TITLES[current_idx]
        if current_title is not None:
            current_chunk += '\n' + l
    return chunks


def parse_files(files: List[Tuple[IO, str]]) -> List[dict]:
    return [{**parse_file(f), 'filename': name} for f, name in files]


def parse_file(file: IO) -> dict:
    try:
        text = extract_text(file)
        case_number = extract_case_number(text)
        text = clean_text(text)
        chunks = extract_chunks(text)
        dates = {}
        for title, content in chunks.items():
            dates[title] = [d.date().isoformat()
                            for d in datefinder.find_dates(content)][0:DATES_COUNT[EVENT_TITLES.index(title)]]
        return {"dates": dates, "case": case_number}
    except Exception as e:
        pass
    return {"dates": [], "case": "INVALID FILE"}
