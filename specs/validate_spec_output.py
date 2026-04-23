#!/usr/bin/env python3
"""Validate generated markdown against DOCX-derived structure."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}

HTML_TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HTML_HEADING_RE = re.compile(r"^<h([1-6])(?:\s+[^>]*)?>(.*?)</h\1>$", re.IGNORECASE)
ORDERED_LABEL_RE = re.compile(r"^([0-9]+(?:\.[0-9A-Za-z]+)*|[A-Za-z]+)\.?\s+(.*)$")
COMPOSITE_LABEL_RE = re.compile(r"^\d+(?:\.\d+)+\.?\s+")

TITLE_KEY = "__title__"
TOC_KEY = "__toc__"
SECTION_ORDER = [
    "Input",
    "Input Validation",
    "Table Creation - Struct Output File Naming",
    "Insert Statement",
    "Log File Requirements",
    "Processing status display",
    "Display Summary",
    "Convert logfile to excel file",
    "proc is 0",
    "MySQL DB Connection test",
    "If proc is 2:",
    "Generate SQL Batch Upload Script File",
    "Check Uploaded Total No of Rows vs Actual",
    "Check Foreign Key Value Dependencies",
    "Error handling",
    "Leveling Off",
    "Development and Testing Environment",
]


@dataclass
class LevelDef:
    fmt: str
    lvl_text: str
    left: int


@dataclass
class DocxListMeta:
    section: str
    text: str
    kind: str
    num_id: str
    abstract_id: str
    ilvl: int
    effective_left: int
    label: str
    depth: int
    bullet_style: str


@dataclass
class ActualListItem:
    text: str
    normalized_text: str
    raw_text: str
    depth: int
    container_kind: str
    container_style: str
    line_no: int


@dataclass
class SectionResult:
    name: str
    status: str
    summary: str
    anchors: list[str]
    issue_types: list[str]
    likely_cause: str


def strip_markdown(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = HTML_TAG_RE.sub("", text)
    text = unescape(text)
    text = text.replace("\\_", "_").replace("\\<", "<").replace("\\>", ">")
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    text = strip_markdown(text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", text)
    text = COMPOSITE_LABEL_RE.sub("", text)
    text = re.sub(r"^[A-Za-z]\.\s+", "", text)
    text = re.sub(r"[^\w\s<>\-]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip().lower()


def display_label(label: str) -> str:
    cleaned = label.strip().rstrip(".")
    parts = [part for part in cleaned.split(".") if part and part != "0"]
    if not parts:
        return cleaned
    return ".".join(parts)


def parse_indent(ppr: ET.Element | None) -> int | None:
    if ppr is None:
        return None
    ind = ppr.find("w:ind", NS)
    if ind is None:
        return None
    left = ind.attrib.get(f"{{{WORD_NS}}}left")
    if left is None:
        return None
    try:
        return int(left)
    except ValueError:
        return None


def build_numbering_map(
    zf: zipfile.ZipFile,
) -> tuple[dict[str, str], dict[tuple[str, int], LevelDef]]:
    numbering = ET.fromstring(zf.read("word/numbering.xml"))
    num_to_abs: dict[str, str] = {}
    levels: dict[tuple[str, int], LevelDef] = {}

    for num in numbering.findall("w:num", NS):
        num_id = num.attrib.get(f"{{{WORD_NS}}}numId", "")
        absid = num.find("w:abstractNumId", NS)
        num_to_abs[num_id] = absid.attrib.get(f"{{{WORD_NS}}}val", "") if absid is not None else ""

    for abstract in numbering.findall("w:abstractNum", NS):
        abs_id = abstract.attrib.get(f"{{{WORD_NS}}}abstractNumId", "")
        for lvl in abstract.findall("w:lvl", NS):
            ilvl = int(lvl.attrib.get(f"{{{WORD_NS}}}ilvl", "0"))
            fmt_el = lvl.find("w:numFmt", NS)
            txt_el = lvl.find("w:lvlText", NS)
            ppr = lvl.find("w:pPr", NS)
            left = parse_indent(ppr) or 0
            levels[(abs_id, ilvl)] = LevelDef(
                fmt=fmt_el.attrib.get(f"{{{WORD_NS}}}val", "") if fmt_el is not None else "",
                lvl_text=txt_el.attrib.get(f"{{{WORD_NS}}}val", "") if txt_el is not None else "",
                left=left,
            )
    return num_to_abs, levels


def int_to_alpha(value: int, uppercase: bool = False) -> str:
    result = []
    while value > 0:
        value -= 1
        result.append(chr(ord("A" if uppercase else "a") + (value % 26)))
        value //= 26
    return "".join(reversed(result)) or ("A" if uppercase else "a")


def int_to_roman(value: int, uppercase: bool = False) -> str:
    pairs = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result = []
    remaining = max(1, value)
    for number, numeral in pairs:
        while remaining >= number:
            result.append(numeral)
            remaining -= number
    roman = "".join(result)
    return roman if uppercase else roman.lower()


def format_counter(fmt: str, value: int) -> str:
    if fmt == "lowerLetter":
        return int_to_alpha(value, uppercase=False)
    if fmt == "upperLetter":
        return int_to_alpha(value, uppercase=True)
    if fmt == "lowerRoman":
        return int_to_roman(value, uppercase=False)
    if fmt == "upperRoman":
        return int_to_roman(value, uppercase=True)
    return str(value)


def normalize_ordered_label(label: str) -> str:
    cleaned = label.strip().rstrip(".")
    if not cleaned:
        return ""
    cleaned = re.sub(r"%\d+", "", cleaned).strip().strip(".")
    if not cleaned:
        return ""
    return ".".join(part for part in cleaned.split(".") if part).strip()


def compute_label(
    levels: dict[tuple[str, int], LevelDef],
    abs_id: str,
    level_def: LevelDef,
    counters: list[int],
) -> str:
    label = level_def.lvl_text
    for idx, value in enumerate(counters, start=1):
        fmt = levels.get((abs_id, idx - 1), level_def).fmt
        label = label.replace(f"%{idx}", format_counter(fmt, value))
    return normalize_ordered_label(label)


def extract_docx_front_matter(docx_path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(docx_path) as zf:
        document = ET.fromstring(zf.read("word/document.xml"))

    title = ""
    subtitle = ""
    for pnode in document.findall(".//w:p", NS):
        texts = [t.text for t in pnode.findall(".//w:t", NS) if t.text]
        text = "".join(texts).strip()
        if not text:
            continue
        ppr = pnode.find("w:pPr", NS)
        if ppr is None:
            continue
        style_el = ppr.find("w:pStyle", NS)
        style = style_el.attrib.get(f"{{{WORD_NS}}}val", "") if style_el is not None else ""
        if style == "Title" and not title:
            title = text
        elif style == "Subtitle" and not subtitle:
            subtitle = text
        if title and subtitle:
            break
    return title, subtitle


def compute_expected_depths(items: list[DocxListMeta]) -> list[int]:
    stack: list[int] = []
    depths: list[int] = []
    for item in items:
        left = item.effective_left
        if not stack:
            stack = [left]
            depths.append(0)
            continue
        while len(stack) > 1 and left < stack[-1]:
            stack.pop()
        if left > stack[-1]:
            stack.append(left)
        elif left < stack[-1]:
            stack[-1] = left
        depths.append(max(0, len(stack) - 1))
    return depths


def bullet_style_for_depth(depth: int) -> str:
    styles = ["disc", "circle", "dash", "square"]
    return styles[min(depth, len(styles) - 1)]


def extract_docx_expectations(docx_path: Path) -> tuple[str, str, list[str], dict[str, list[DocxListMeta]]]:
    with zipfile.ZipFile(docx_path) as zf:
        document = ET.fromstring(zf.read("word/document.xml"))
        num_to_abs, levels = build_numbering_map(zf)

    title, subtitle = extract_docx_front_matter(docx_path)
    toc_entries: list[str] = []
    grouped: dict[str, list[DocxListMeta]] = {}
    current_section = ""
    section_counters: dict[str, list[int]] = {}

    pending: list[DocxListMeta] = []
    for pnode in document.findall(".//w:p", NS):
        texts = [t.text for t in pnode.findall(".//w:t", NS) if t.text]
        text = "".join(texts).strip()
        if not text:
            continue

        ppr = pnode.find("w:pPr", NS)
        style = ""
        if ppr is not None:
            style_el = ppr.find("w:pStyle", NS)
            style = style_el.attrib.get(f"{{{WORD_NS}}}val", "") if style_el is not None else ""

        if style.startswith("TOC"):
            cleaned = re.sub(r"\d+$", "", text).strip()
            if cleaned:
                toc_entries.append(cleaned)

        if style.startswith("Heading"):
            current_section = text
            pending = []
            continue

        if ppr is None:
            continue
        num_pr = ppr.find("w:numPr", NS)
        if num_pr is None or not current_section:
            continue

        num_id_el = num_pr.find("w:numId", NS)
        ilvl_el = num_pr.find("w:ilvl", NS)
        if num_id_el is None or ilvl_el is None:
            continue

        num_id = num_id_el.attrib.get(f"{{{WORD_NS}}}val", "")
        ilvl = int(ilvl_el.attrib.get(f"{{{WORD_NS}}}val", "0"))
        abs_id = num_to_abs.get(num_id, "")
        level_def = levels.get((abs_id, ilvl))
        if level_def is None:
            continue

        left = parse_indent(ppr)
        effective_left = level_def.left if left is None else left
        kind = "ordered" if level_def.fmt != "bullet" else "bullet"
        label = ""
        if kind == "ordered":
            counters = section_counters.setdefault(current_section, [])
            while len(counters) <= ilvl:
                counters.append(0)
            counters[ilvl] += 1
            del counters[ilvl + 1 :]
            label = compute_label(levels, abs_id, level_def, counters)

        pending.append(
            DocxListMeta(
                section=current_section,
                text=text,
                kind=kind,
                num_id=num_id,
                abstract_id=abs_id,
                ilvl=ilvl,
                effective_left=effective_left,
                label=label,
                depth=0,
                bullet_style="disc",
            )
        )
        grouped[current_section] = pending

    for section, items in grouped.items():
        depths = compute_expected_depths(items)
        bullet_depth = 0
        kind_stack: list[str] = []
        last_depth = -1
        for item, depth in zip(items, depths):
            item.depth = depth
            if depth <= last_depth:
                kind_stack = kind_stack[: depth + 1]
            while len(kind_stack) <= depth:
                kind_stack.append(item.kind)
            kind_stack[depth] = item.kind
            last_depth = depth
            if item.kind == "bullet":
                bullet_depth = max(0, sum(1 for kind in kind_stack[: depth + 1] if kind == "bullet") - 1)
                item.bullet_style = bullet_style_for_depth(bullet_depth)
    return title, subtitle, toc_entries, grouped


def parse_markdown_sections(md_path: Path) -> tuple[list[str], dict[str, list[str]], dict[str, list[ActualListItem]]]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    sections: dict[str, list[str]] = {TITLE_KEY: []}
    items: dict[str, list[ActualListItem]] = {}
    current_section = TITLE_KEY
    sections[current_section] = []
    items[current_section] = []
    list_stack: list[tuple[str, str]] = []

    def section_name_from_heading(line: str) -> str:
        match = HEADING_RE.match(line)
        text = ""
        if match:
            text = strip_markdown(match.group(2))
        else:
            html_match = HTML_HEADING_RE.match(line.strip())
            if not html_match:
                return current_section
            text = strip_markdown(html_match.group(2))
        text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", text).strip()
        return text

    for idx, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        html_match = HTML_HEADING_RE.match(line.strip())
        if match or html_match:
            current_section = section_name_from_heading(line)
            sections.setdefault(current_section, []).append(line)
            items.setdefault(current_section, [])
            list_stack = []
            continue

        sections.setdefault(current_section, []).append(line)

        opens = re.findall(r"<(ol|ul|dl)([^>]*)>", line)
        for tag, attrs in opens:
            style = ""
            if "list-style-type" in attrs:
                style_match = re.search(r"list-style-type:\s*([a-z]+)", attrs)
                if style_match:
                    style = style_match.group(1)
            list_stack.append((tag, style))

        if "<li" in line or "<dd" in line:
            raw = strip_markdown(line)
            raw = raw.replace("</li>", "").strip()
            raw = raw.replace("</dd>", "").strip()
            raw = re.sub(r"^li\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"^dd\s*", "", raw, flags=re.IGNORECASE)
            depth = max(0, len(list_stack) - 1)
            kind, style = list_stack[-1] if list_stack else ("", "")
            if kind == "ul" and style in {"", "none"} and raw.startswith("- "):
                style = "dash"
            normalized = normalize_text(raw)
            if raw:
                items.setdefault(current_section, []).append(
                    ActualListItem(
                        text=raw,
                        normalized_text=normalized,
                        raw_text=raw,
                        depth=depth,
                        container_kind=kind,
                        container_style=style,
                        line_no=idx,
                    )
                )

        closes = re.findall(r"</(ol|ul|dl)>", line)
        for _ in closes:
            if list_stack:
                list_stack.pop()

    return lines, sections, items


def find_toc_lines(lines: list[str], subtitle: str) -> list[str]:
    start = None
    end = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "# Contents" or stripped.lower() == '<h1 id="contents">contents</h1>':
            start = idx + 1
            continue
        if start is not None and strip_markdown(line) == subtitle:
            end = idx
            break
        if start is not None and (
            (line.startswith("# ") and line.strip() != "# Contents")
            or HTML_HEADING_RE.match(stripped)
        ):
            end = idx
            break
    if start is None:
        return []
    end = len(lines) if end is None else end
    toc_lines: list[str] = []
    for line in lines[start:end]:
        cleaned = strip_markdown(line)
        if not cleaned:
            continue
        if line.strip().startswith("<div class=\"toc-entry"):
            toc_lines.append(cleaned)
        elif not line.lstrip().startswith("<"):
            toc_lines.append(cleaned)
    return toc_lines


def validate_title_and_toc(
    title: str,
    subtitle: str,
    toc_entries: list[str],
    lines: list[str],
) -> list[SectionResult]:
    results: list[SectionResult] = []
    first_non_empty = next((line.strip() for line in lines if line.strip()), "")
    title_status = "Pass" if first_non_empty in {f"# {title}", f'<h1 id="{normalize_text(title).replace(" ", "-")}">{title}</h1>'} else "Fail"
    title_summary = "Title preserved at top of document." if title_status == "Pass" else "Document title is missing or displaced."
    title_cause = "" if title_status == "Pass" else "Generated markdown preamble starts without the DOCX title."
    results.append(
        SectionResult(
            name="Title check",
            status=title_status,
            summary=title_summary,
            anchors=[title] if title else [],
            issue_types=[] if title_status == "Pass" else ["spacing/layout"],
            likely_cause=title_cause,
        )
    )

    toc_lines = find_toc_lines(lines, subtitle)
    missing = [
        entry
        for entry in toc_entries
        if normalize_text(entry) != "contents"
        and not any(
            normalize_text(entry) == normalize_text(line)
            or normalize_text(entry) in normalize_text(line)
            or normalize_text(line) in normalize_text(entry)
            for line in toc_lines
        )
    ]
    subtitle_ok = any(
        line.strip() in {
            f"## {subtitle}",
            subtitle,
            f'<h2 id="{normalize_text(subtitle).replace(" ", "-")}">{subtitle}</h2>',
        }
        for line in lines
    )
    toc_status = "Pass" if not missing and toc_lines and subtitle_ok else "Fail"
    summary_parts = []
    if missing:
        summary_parts.append(f"Missing TOC entries: {', '.join(missing[:5])}")
    if not subtitle_ok:
        summary_parts.append("Revision History subtitle is not promoted consistently.")
    if not toc_lines:
        summary_parts.append("Contents block was not found.")
    if any("[" in line or "]" in line for line in toc_lines):
        toc_status = "Fail"
        summary_parts.append("TOC still contains markdown bracket syntax.")
    results.append(
        SectionResult(
            name="TOC check",
            status=toc_status,
            summary="TOC matches expected headings." if toc_status == "Pass" else "; ".join(summary_parts),
            anchors=missing[:5] if missing else [subtitle] if not subtitle_ok else [],
            issue_types=[] if toc_status == "Pass" else ["spacing/layout"],
            likely_cause="" if toc_status == "Pass" else "Generated TOC block is incomplete or not rebuilt from the final heading structure.",
        )
    )
    return results


def expected_sections_without_lists() -> dict[str, str]:
    return {
        "Check Uploaded Total No of Rows vs Actual": "TBD",
        "Check Foreign Key Value Dependencies": "TBD",
        "Development and Testing Environment": "This section defines the required environment",
    }


def validate_sections(
    expected: dict[str, list[DocxListMeta]],
    sections: dict[str, list[str]],
    actual_items: dict[str, list[ActualListItem]],
) -> list[SectionResult]:
    results: list[SectionResult] = []
    for section_name in SECTION_ORDER:
        expected_items = expected.get(section_name, [])
        actual_section_lines = sections.get(section_name)
        if actual_section_lines is None:
            results.append(
                SectionResult(
                    name=section_name,
                    status="Fail",
                    summary="Section heading is missing from the generated markdown.",
                    anchors=[section_name],
                    issue_types=["spacing/layout"],
                    likely_cause="The final markdown headings do not preserve the DOCX section outline.",
                )
            )
            continue

        if not expected_items:
            required_text = expected_sections_without_lists().get(section_name)
            if required_text and required_text.lower() not in normalize_text(" ".join(actual_section_lines)):
                results.append(
                    SectionResult(
                        name=section_name,
                        status="Fail",
                        summary="Section body content does not match the DOCX anchor text.",
                        anchors=[required_text],
                        issue_types=["spacing/layout"],
                        likely_cause="The section body was altered or dropped during conversion.",
                    )
                )
            else:
                results.append(
                    SectionResult(
                        name=section_name,
                        status="Pass",
                        summary="Section structure is acceptable.",
                        anchors=[],
                        issue_types=[],
                        likely_cause="",
                    )
                )
            continue

        if actual_section_lines and not actual_section_lines[0].lstrip().startswith("<h"):
            results.append(
                SectionResult(
                    name=section_name,
                    status="Fail",
                    summary="Section heading is not emitted as an HTML heading block.",
                    anchors=[section_name],
                    issue_types=["spacing/layout"],
                    likely_cause="The final post-processing step still leaves markdown heading syntax instead of preview-oriented HTML headings.",
                )
            )
            continue

        actual = actual_items.get(section_name, [])
        raw_section = "\n".join(actual_section_lines)
        actual_section_text = normalize_text(" ".join(actual_section_lines))
        section_has_table = "<table" in "\n".join(actual_section_lines)
        failures: list[str] = []
        anchors: list[str] = []
        issue_types: set[str] = set()
        cursor = 0

        for item in expected_items:
            matched_idx = None
            target = normalize_text(item.text)
            for idx in range(cursor, len(actual)):
                candidate = actual[idx]
                if not candidate.normalized_text:
                    continue
                if target in candidate.normalized_text or candidate.normalized_text in target:
                    matched_idx = idx
                    break
            if matched_idx is None:
                if target and target in actual_section_text:
                    continue
                failures.append(f"Missing item: {item.text}")
                anchors.append(item.text)
                issue_types.add("spacing/layout")
                continue

            candidate = actual[matched_idx]
            cursor = matched_idx + 1
            if item.kind == "ordered":
                normalized_label = display_label(item.label)
                explicit_label_required = "." in normalized_label or any(ch.isalpha() for ch in normalized_label)
                if explicit_label_required and not candidate.raw_text.startswith(normalized_label):
                    failures.append(f"Expected explicit label {normalized_label} for: {item.text}")
                    anchors.append(item.text)
                    issue_types.add("numbering")
                if item.depth != candidate.depth and not section_has_table:
                    failures.append(f"Depth mismatch for: {item.text}")
                    anchors.append(item.text)
                    issue_types.add("list parent/child relationship")
                if explicit_label_required and candidate.container_kind == "ul" and candidate.container_style not in {"none", ""}:
                    failures.append(f"Ordered descendant rendered with bullet styling: {item.text}")
                    anchors.append(item.text)
                    issue_types.add("numbering")
            else:
                expected_style = item.bullet_style
                style = candidate.container_style or "none"
                if expected_style != style and not section_has_table:
                    failures.append(f"Bullet style mismatch for: {item.text}")
                    anchors.append(item.text)
                    issue_types.add("bullet indentation")
                if item.depth != candidate.depth and not section_has_table:
                    failures.append(f"Bullet depth mismatch for: {item.text}")
                    anchors.append(item.text)
                    issue_types.add("list parent/child relationship")

        if '<li><span class="ordered-label">' in raw_section:
            failures.append("Ordered descendants still use list items without explicit bullet suppression.")
            anchors.append(section_name)
            issue_types.add("numbering")

        if section_name == "Display Summary":
            li1_idx = next((i for i, line in enumerate(actual_section_lines) if '<li value="1">' in line), None)
            li2_idx = next((i for i, line in enumerate(actual_section_lines) if '<li value="2">' in line), None)
            table_idx = next((i for i, line in enumerate(actual_section_lines) if line.strip() == "<table>"), None)
            li1_close = None
            if li1_idx is not None:
                li1_close = next((i for i in range(li1_idx + 1, len(actual_section_lines)) if actual_section_lines[i].strip() == "</li>"), None)
            if li1_idx is None or table_idx is None or li1_close is None or not (li1_idx < table_idx < li1_close):
                failures.append("The summary table is not nested under item 1.")
                anchors.append("After completing the processing of SQL files")
                issue_types.add("table/box interference")
            if li2_idx is None:
                failures.append("The post-table numbered item does not continue as item 2.")
                anchors.append("Ask user if to display the content of the log file")
                issue_types.add("numbering")

        if section_name == "If proc is 2:":
            marker_idx = next((i for i, line in enumerate(actual_section_lines) if '1.1.4' in line), None)
            if marker_idx is not None:
                next_table_idx = next((i for i in range(marker_idx + 1, len(actual_section_lines)) if actual_section_lines[i].strip() == "<table>"), None)
                next_ul_disc = next((i for i in range(marker_idx + 1, len(actual_section_lines)) if 'list-style-type: disc' in actual_section_lines[i]), None)
                if next_table_idx is None or (next_ul_disc is not None and next_ul_disc < next_table_idx):
                    failures.append("The recommendation block under 1.1.4 is not fully boxed.")
                    anchors.append("1.1.4")
                    issue_types.add("table/box interference")

        status = "Pass" if not failures else "Fail"
        likely_cause = ""
        if status == "Fail":
            likely_cause = (
                "List reconstruction still diverges from DOCX metadata, usually because ordered descendants are emitted "
                "as literal labels, bullet styles are collapsed, or tables break list context."
            )
        results.append(
            SectionResult(
                name=section_name,
                status=status,
                summary="Section structure is acceptable." if status == "Pass" else "; ".join(dict.fromkeys(failures))[:800],
                anchors=list(dict.fromkeys(anchors))[:8],
                issue_types=sorted(issue_types),
                likely_cause=likely_cause,
            )
        )
    return results


def write_reports(results: list[SectionResult], json_path: Path, md_path: Path) -> None:
    payload: dict[str, Any] = {
        "overall_status": "Pass" if all(result.status == "Pass" for result in results) else "Fail",
        "results": [asdict(result) for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = ["# Validation Report", ""]
    lines.append(f"Overall status: `{payload['overall_status']}`")
    lines.append("")
    for result in results:
        lines.append(f"## {result.name}")
        lines.append(f"- Status: `{result.status}`")
        lines.append(f"- Summary: {result.summary}")
        if result.anchors:
            lines.append(f"- Anchors: {', '.join(result.anchors)}")
        if result.issue_types:
            lines.append(f"- Issue types: {', '.join(result.issue_types)}")
        if result.likely_cause:
            lines.append(f"- Likely cause: {result.likely_cause}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 5:
        print(
            "Usage: validate_spec_output.py <docx_file> <markdown_file> <json_report> <md_report>",
            file=sys.stderr,
        )
        return 2

    docx_path = Path(sys.argv[1])
    md_path = Path(sys.argv[2])
    json_path = Path(sys.argv[3])
    md_report_path = Path(sys.argv[4])

    title, subtitle, toc_entries, expected = extract_docx_expectations(docx_path)
    lines, sections, actual_items = parse_markdown_sections(md_path)
    results = validate_title_and_toc(title, subtitle, toc_entries, lines)
    results.extend(validate_sections(expected, sections, actual_items))
    write_reports(results, json_path, md_report_path)

    overall_ok = all(result.status == "Pass" for result in results)
    print(f"Validation status: {'PASS' if overall_ok else 'FAIL'}")
    for result in results:
        print(f"- {result.name}: {result.status}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
