"""Resume section splitting and header manipulation."""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple


def _heading_normalize(title: str) -> str:
    title = title.strip().lstrip("#").strip()
    title = unicodedata.normalize("NFKD", title)
    title = "".join(ch for ch in title if not unicodedata.combining(ch))
    title = title.lower()
    title = re.sub(r"[\W_]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def _make_alias_map(section_aliases: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {key: [_heading_normalize(a) for a in aliases] for key, aliases in section_aliases.items()}


def split_resume_sections(md_text: str, alias_map: Dict[str, List[str]]) -> Tuple[str, List[Tuple[str, str]]]:
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    header_lines: List[str] = []
    sections: List[Tuple[str, str]] = []
    current_title: Optional[str] = None
    current_lines: List[str] = []

    for line in lines:
        if line.startswith("## "):
            raw_title = line[3:].strip()
            norm_title = _heading_normalize(raw_title)
            matched = any(norm_title in alist for alist in alias_map.values())
            if matched:
                if current_title is not None:
                    sections.append((current_title, "\n".join(current_lines).rstrip()))
                current_title = raw_title
                current_lines = [line]
            else:
                if current_title is None:
                    header_lines.append(line)
                else:
                    current_lines.append(line)
        else:
            if current_title is None:
                header_lines.append(line)
            else:
                current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines).rstrip()))
    return "\n".join(header_lines).rstrip(), sections


def is_static_section(title: str, static_keys: List[str], alias_map: Dict[str, List[str]]) -> bool:
    norm = _heading_normalize(title)
    return any(norm in alias_map.get(key, []) for key in static_keys)


def build_mutable_bundle(sections: List[Tuple[str, str]], static_keys: List[str], alias_map: Dict[str, List[str]]) -> str:
    parts = [content.strip() for title, content in sections if not is_static_section(title, static_keys, alias_map)]
    return "\n\n".join(parts).strip() + "\n"


def build_static_bundle(sections: List[Tuple[str, str]], static_keys: List[str], alias_map: Dict[str, List[str]]) -> str:
    parts = [content.strip() for title, content in sections if is_static_section(title, static_keys, alias_map)]
    return "\n\n".join(parts).strip() + "\n"


def replace_subtitle(header: str, new_subtitle: str) -> str:
    lines = header.splitlines()
    heading_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# "):
            heading_idx = i
            break
    if heading_idx == -1:
        return f"**{new_subtitle}**\n\n{header}"
    inserted = False
    for j in range(heading_idx + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped:
            lines[j] = f"**{new_subtitle}**"
            inserted = True
            break
    if not inserted:
        lines.insert(heading_idx + 1, f"**{new_subtitle}**")
    return "\n".join(lines).rstrip()
