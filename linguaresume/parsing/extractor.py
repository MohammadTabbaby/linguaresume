"""Text extraction helpers for resumes."""
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Set

try:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
except ImportError:
    ENGLISH_STOP_WORDS = set()


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_companies(markdown_text: str) -> Set[str]:
    companies = set()
    for line in re.findall(r"^### (.+)", markdown_text, re.MULTILINE):
        en_match = re.search(r"\[EN:\s*([^\]]+?)\]", line)
        if en_match:
            companies.add(en_match.group(1).strip())
        else:
            companies.add(line.split(",")[0].strip())
    return companies


def extract_dates(markdown_text: str) -> Set[str]:
    return set(re.findall(r"\(([^)]+\d{4}[^)]*)\)", markdown_text))


def company_matches(master: str, output: str) -> bool:
    output = output.strip()
    en_match = re.search(r"\[EN:\s*([^\]]+)\]", output)
    if en_match:
        output = en_match.group(1).strip()
    master_norm = normalize_text(master)
    output_norm = normalize_text(output)
    if output_norm == master_norm:
        return True
    master_tokens = set(master_norm.split())
    output_tokens = set(output_norm.split())
    if not master_tokens or not output_tokens:
        return False
    common = master_tokens & output_tokens
    if len(common) / max(len(output_tokens), 1) >= 0.5:
        return True
    if len(common) >= 2 and {"tahar", "sfar"} <= common:
        return True
    acronym_match = re.search(r"\(([^)]+)\)", output)
    if acronym_match and acronym_match.group(1).lower() in master_norm:
        return True
    return False


def extract_total_months(md: str) -> float:
    patterns = [
        r'\((\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{4}|Present|Current|Aujourd\'hui|aujourd\'hui)\)',
        r'\((\d{2}\.\d{4})\s*[-–]\s*(\d{2}\.\d{4}|Present|Current|Aujourd\'hui|aujourd\'hui)\)',
    ]
    matches = []
    for pat in patterns:
        matches.extend(re.findall(pat, md, re.IGNORECASE))

    total = 0
    now = datetime.now()

    for start, end in matches:
        try:
            if '/' in start:
                start_date = datetime.strptime(start, "%m/%Y")
            elif '.' in start:
                start_date = datetime.strptime(start, "%m.%Y")
            else:
                continue

            if end.lower() in ("present", "current", "aujourd'hui"):
                end_date = now
            elif '/' in end:
                end_date = datetime.strptime(end, "%m/%Y")
            elif '.' in end:
                end_date = datetime.strptime(end, "%m.%Y")
            else:
                continue

            total += (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        except ValueError:
            continue
    return total


def extract_keywords(text: str, stopwords: Set[str]) -> Set[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = text.split()
    if ENGLISH_STOP_WORDS:
        stopwords = stopwords | set(ENGLISH_STOP_WORDS)
    return {w for w in words if len(w) > 3 and w not in stopwords}


def _bullet_sections(md: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = None
    for line in md.splitlines():
        if line.startswith("## "):
            current = None
        elif line.startswith("### "):
            header = re.sub(r",?\s*\(\d{2}/\d{4}.*?\).*?$", "", line)
            header = re.sub(r"\[EN:.*?\]", "", header)
            header = re.sub(r",?\s*\w+\s+\d{4}\s*[-–]\s*(?:\w+\s+\d{4}|Present).*?$", "", header)
            current = header.replace("### ", "").strip()
            sections[current] = []
        elif line.startswith(("- ", "* ", "+ ")) and current:
            sections[current].append(line[2:].strip())
    return sections


def _sig_tokens(text: str) -> Set[str]:
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    words = re.findall(r"[\w]+", norm)
    tokens = set()
    for w in words:
        if re.match(r"[A-Z]{2,}", w):
            tokens.add(w.upper())
        elif len(w) >= 5:
            tokens.add(w.lower())
    return tokens
