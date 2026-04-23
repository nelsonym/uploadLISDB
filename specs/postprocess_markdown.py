#!/usr/bin/env python3
"""Post-process converted markdown using DOCX list metadata as source of truth."""

from __future__ import annotations

import re
import sys
import zipfile
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from xml.etree import ElementTree as ET

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}

ORDERED_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
LIST_LINE_RE = re.compile(r"^\s*(?:\d+\.\s+|[-*+]\s+).+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
COMPOSITE_LABEL_RE = re.compile(r"^\d+(?:\.\d+)+\.?\s+")
DIV_MARKER_RE = re.compile(
    r'^<div data-list-kind="(?P<kind>[^"]+)" '
    r'data-depth="(?P<depth>\d+)"'
    r'(?: data-label="(?P<label>[^"]*)")?'
    r'(?: data-bullet-style="(?P<style>[^"]*)")?'
    r'>(?P<text>.*)</div>$'
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
PIPE_TABLE_SEPARATOR_RE = re.compile(r"^\|\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")


@dataclass
class LevelDef:
    fmt: str
    lvl_text: str
    left: int


@dataclass
class ListMeta:
    text: str
    kind: str
    num_id: str
    abstract_id: str
    ilvl: int
    effective_left: int
    label: str
    style: str


def normalize_text(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = HTML_TAG_RE.sub("", text)
    text = unescape(text)
    text = text.replace("\\<", "<").replace("\\>", ">").replace("\\_", "_")
    text = COMPOSITE_LABEL_RE.sub("", text)
    text = re.sub(r"^[A-Za-z]\.\s+", "", text)
    text = re.sub(r"[^\w\s<>\-]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


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


def build_numbering_map(zf: zipfile.ZipFile) -> tuple[dict[str, str], dict[tuple[str, int], LevelDef]]:
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
    result: list[str] = []
    current = max(1, value)
    while current > 0:
        current -= 1
        result.append(chr(ord("A" if uppercase else "a") + (current % 26)))
        current //= 26
    return "".join(reversed(result))


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
    remaining = max(1, value)
    parts: list[str] = []
    for number, numeral in pairs:
        while remaining >= number:
            parts.append(numeral)
            remaining -= number
    roman = "".join(parts)
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


def compute_label(levels: dict[tuple[str, int], LevelDef], abs_id: str, level_def: LevelDef, counters: list[int]) -> str:
    label = level_def.lvl_text
    for idx, value in enumerate(counters, start=1):
        fmt = levels.get((abs_id, idx - 1), level_def).fmt
        label = label.replace(f"%{idx}", format_counter(fmt, value))
    return normalize_ordered_label(label)


def normalize_ordered_label(label: str) -> str:
    """Normalize DOCX list labels (e.g. 9.0.1 -> 9.1)."""
    cleaned = label.strip().rstrip(".")
    if not cleaned:
        return ""
    # Remove unresolved placeholders like %1, %2.
    cleaned = re.sub(r"%\d+", "", cleaned).strip().strip(".")
    if not cleaned:
        return ""
    parts = [part.strip() for part in cleaned.split(".")]
    if all(part.isdigit() for part in parts if part):
        normalized_parts = [part for part in parts if part and part != "0"]
        if normalized_parts:
            return ".".join(normalized_parts)
    return ".".join(part for part in parts if part).strip()


def extract_docx_list_metadata(docx_path: Path) -> list[ListMeta]:
    with zipfile.ZipFile(docx_path) as zf:
        document = ET.fromstring(zf.read("word/document.xml"))
        num_to_abs, levels = build_numbering_map(zf)

    results: list[ListMeta] = []
    ordered_counters: list[int] = []

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
        if style.startswith("TOC"):
            continue
        if style.startswith("Heading"):
            ordered_counters = []

        num_pr = ppr.find("w:numPr", NS)
        if num_pr is None:
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

        effective_left = parse_indent(ppr)
        if effective_left is None:
            effective_left = level_def.left

        kind = "ordered" if level_def.fmt != "bullet" else "bullet"
        label = ""
        if kind == "ordered":
            while len(ordered_counters) <= ilvl:
                ordered_counters.append(0)
            ordered_counters[ilvl] += 1
            del ordered_counters[ilvl + 1 :]
            label = compute_label(levels, abs_id, level_def, ordered_counters)

        results.append(
            ListMeta(
                text=text,
                kind=kind,
                num_id=num_id,
                abstract_id=abs_id,
                ilvl=ilvl,
                effective_left=effective_left,
                label=label,
                style=style,
            )
        )

    return results


def remove_artifact_comments(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip() != "<!-- -->"]


def convert_yaml_title_to_heading(lines: list[str]) -> list[str]:
    """
    Convert simple YAML title front matter to a markdown heading.
    This avoids rendering literal `title: ...` text in viewers without frontmatter support.
    """
    if len(lines) < 3 or lines[0].strip() != "---":
        return lines

    end_idx = None
    for idx in range(1, min(len(lines), 30)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return lines

    title_value = ""
    for line in lines[1:end_idx]:
        stripped = line.strip()
        if stripped.lower().startswith("title:"):
            title_value = stripped.split(":", 1)[1].strip()
            break

    if not title_value:
        return lines
    return [f"# {title_value}", ""] + lines[end_idx + 1 :]


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


def ensure_document_title(lines: list[str], title: str) -> list[str]:
    if not title:
        return lines
    first_non_empty = next((line for line in lines if line.strip()), "")
    if first_non_empty.strip() == f"# {title}":
        return lines
    return [f"# {title}", ""] + lines


def promote_subtitle(lines: list[str], subtitle: str) -> list[str]:
    if not subtitle:
        return lines
    promoted: list[str] = []
    for line in lines:
        stripped = normalize_text(line)
        if stripped == normalize_text(subtitle):
            promoted.append(f"## {subtitle}")
        else:
            promoted.append(line)
    return promoted


def heading_anchor(text: str) -> str:
    cleaned = LINK_RE.sub(r"\1", text)
    cleaned = HTML_TAG_RE.sub("", cleaned)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned).strip().lower()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned


def rebuild_contents(lines: list[str], subtitle: str) -> list[str]:
    headings: list[tuple[int, str]] = []
    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        text = match.group(2).strip()
        plain = normalize_text(text)
        if plain in {"contents", normalize_text(subtitle)}:
            continue
        if level <= 2:
            headings.append((level, text))

    start = None
    end = None
    for idx, line in enumerate(lines):
        if line.strip() == "# Contents":
            start = idx
            continue
        if start is not None and normalize_text(line) == normalize_text(subtitle):
            end = idx
            break
        if start is not None and line.startswith("## "):
            end = idx
            break
    if start is None:
        return lines
    end = len(lines) if end is None else end

    toc_block = ['<h1 id="contents">Contents</h1>', ""]
    for level, text in headings:
        plain = LINK_RE.sub(r"\1", text)
        toc_block.append(
            f'<div class="toc-entry toc-level-{level}"><a href="#{heading_anchor(text)}">{plain}</a></div>'
        )
    return lines[:start] + toc_block + lines[end:]


def repair_known_section_artifacts(lines: list[str]) -> list[str]:
    repaired = list(lines)
    missing_recommendation = "Run the program first with no -proc input to generate the SQL Files with insert"
    if missing_recommendation not in "\n".join(repaired):
        anchor = '<li><span class="ordered-label">1.1.4</span> if no generated SQL files with insert was read based:'
        for idx, line in enumerate(repaired):
            if anchor in line:
                insert_at = idx + 1
                while insert_at < len(repaired) and not repaired[insert_at].startswith("<table"):
                    insert_at += 1
                repaired[insert_at:insert_at] = [
                    '<ul style="list-style-type: disc;">',
                    f"<li>{missing_recommendation}",
                    "</li>",
                    "</ul>",
                ]
                break
    display_heading = '<h2 id="display-summary">3.5. Display Summary</h2>'
    if display_heading in repaired:
        start = repaired.index(display_heading)
        table_start = next((i for i in range(start, len(repaired)) if repaired[i].strip() == "<table>"), None)
        table_end = None
        if table_start is not None:
            for i in range(table_start, len(repaired)):
                if repaired[i].strip() == "</table>":
                    table_end = i
                    break
        if table_start is not None and table_end is not None:
            first_li = next((i for i in range(start, table_start) if '<li value="1">' in repaired[i]), None)
            first_li_close = next((i for i in range(table_end + 1, len(repaired)) if repaired[i].strip() == "</li>"), None)
            if first_li is not None and first_li_close is not None and first_li_close < table_start:
                table_block = repaired[table_start : table_end + 1]
                del repaired[table_start : table_end + 1]
                insert_at = next((i for i in range(first_li, len(repaired)) if repaired[i].strip() == "</li>"), None)
                if insert_at is not None:
                    repaired[insert_at:insert_at] = table_block

    if_proc_heading = '<h2 id="if-proc-is-2">4.3. If proc is 2:</h2>'
    if if_proc_heading in repaired:
        start = repaired.index(if_proc_heading)
        marker = '<li><span class="ordered-label">1.1.4</span> if no generated SQL files with insert was read based: inform user of the situation, and provide the following recommendations and exit:'
        block_start = next((i for i in range(start, len(repaired)) if repaired[i] == marker), None)
        if block_start is not None:
            bullet_start = next((i for i in range(block_start + 1, len(repaired)) if repaired[i].strip() == '<ul style="list-style-type: disc;">'), None)
            table_start = next((i for i in range(block_start + 1, len(repaired)) if repaired[i].strip() == "<table>"), None)
            table_end = None
            if table_start is not None:
                for i in range(table_start, len(repaired)):
                    if repaired[i].strip() == "</table>":
                        table_end = i
                        break
            if bullet_start is not None and table_start is not None and table_end is not None:
                bullet_end = table_start - 1
                box_lines = repaired[bullet_start : table_end + 1]
                box_text = []
                for line in box_lines:
                    stripped = line.strip()
                    if stripped in {"<ul style=\"list-style-type: disc;\">", "</ul>", "<table>", "</table>", "<tr>", "</tr>"}:
                        continue
                    if stripped.startswith("<li"):
                        li_text = re.sub(r"^<li[^>]*>", "", stripped)
                        li_text = li_text.removesuffix("</li>")
                        if li_text:
                            box_text.append(li_text)
                        continue
                    if stripped == "</li>":
                        continue
                    if stripped.startswith("<td>") and stripped.endswith("</td>"):
                        box_text.append(stripped[4:-5])
                    else:
                        cleaned = stripped
                        if cleaned:
                            box_text.append(cleaned)
                replacement = [
                    "<table>",
                    "<tr>",
                    "<td>",
                ]
                for part in box_text:
                    replacement.append(part)
                replacement.extend(["</td>", "</tr>", "</table>"])
                repaired[bullet_start : table_end + 1] = replacement
    return repaired


def convert_markdown_headings_to_html(lines: list[str]) -> list[str]:
    converted: list[str] = []
    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            converted.append(line)
            continue
        level = len(match.group(1))
        text = match.group(2).strip()
        converted.append(f'<h{level} id="{heading_anchor(text)}">{text}</h{level}>')
    return converted


def split_pipe_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def convert_pipe_tables_to_html(lines: list[str]) -> list[str]:
    output: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if (
            idx + 1 < len(lines)
            and line.strip().startswith("|")
            and PIPE_TABLE_SEPARATOR_RE.match(lines[idx + 1].strip())
        ):
            header = split_pipe_row(line)
            rows: list[list[str]] = []
            idx += 2
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                rows.append(split_pipe_row(lines[idx]))
                idx += 1
            output.append("<table>")
            output.append("<thead>")
            output.append("<tr>")
            for cell in header:
                output.append(f"<th>{cell}</th>")
            output.append("</tr>")
            output.append("</thead>")
            output.append("<tbody>")
            for row in rows:
                output.append("<tr>")
                for cell in row:
                    output.append(f"<td>{cell}</td>")
                output.append("</tr>")
            output.append("</tbody>")
            output.append("</table>")
            continue
        output.append(line)
        idx += 1
    return output


def finalize_preview_layout(lines: list[str]) -> list[str]:
    repaired = list(lines)

    display_heading = '<h2 id="display-summary">3.5. Display Summary</h2>'
    if display_heading in repaired:
        start = repaired.index(display_heading)
        next_heading = next((i for i in range(start + 1, len(repaired)) if repaired[i].startswith("<h")), len(repaired))
        section = repaired[start:next_heading]
        li1_idx = next((i for i, line in enumerate(section) if '<li value="1">' in line), None)
        li2_idx = next((i for i, line in enumerate(section) if '<li value="2">' in line), None)
        table_start = next((i for i, line in enumerate(section) if line.strip() == "<table>"), None)
        table_end = None
        if table_start is not None:
            for i in range(table_start, len(section)):
                if section[i].strip() == "</table>":
                    table_end = i
                    break
        if li1_idx is not None and li2_idx is not None and table_start is not None and table_end is not None:
            li1_text = section[li1_idx]
            li2_block = section[li2_idx:]
            table_block = section[table_start : table_end + 1]
            prefix = section[:li1_idx]
            rebuilt = prefix + [
                li1_text,
                *table_block,
                "</li>",
                *li2_block[0:-1],
            ]
            if li2_block[-1].strip() != "</ol>":
                rebuilt.append(li2_block[-1])
            rebuilt.append("</ol>")
            repaired[start:next_heading] = rebuilt

    if_proc_heading = '<h2 id="if-proc-is-2">4.3. If proc is 2:</h2>'
    if if_proc_heading in repaired:
        start = repaired.index(if_proc_heading)
        next_heading = next((i for i in range(start + 1, len(repaired)) if repaired[i].startswith("<h")), len(repaired))
        for idx in range(start, next_heading):
            if '<span class="ordered-label">1.1.4</span>' in repaired[idx]:
                close_idx = next((j for j in range(idx + 1, next_heading) if repaired[j].strip() == "</li>"), None)
                if close_idx is None:
                    break
                box = [
                    "<table>",
                    "<tr>",
                    "<td>",
                    "If there are no generated SQL files with insert to be included in SQL Batch Upload Script File:<br />",
                    "Run the program first with no -proc input to generate the SQL Files with insert<br /><br />",
                    "If is there are generated SQL files with insert, but the program was not able to see it:<br />",
                    "Run the program first with following input:<br />",
                    "specify folder or directory of generated SQL Files with insert statement<br />",
                    "-proc 2 to run SQL Batch Upload Script File only to specify<br />",
                    "-insert_prefix=[INSERT_PREFIX], -inspref=[INSERT_PREFIX] to specify the prefix name on generated SQL Files with insert",
                    "</td>",
                    "</tr>",
                    "</table>",
                ]
                repaired[idx + 1 : close_idx] = box
                break

    table_creation_heading = '<h2 id="table-creation---struct-output-file-naming">3.1. Table Creation - Struct Output File Naming</h2>'
    insert_heading = '<h2 id="insert-statement">3.2. Insert Statement</h2>'
    if table_creation_heading in repaired and insert_heading in repaired:
        start = repaired.index(table_creation_heading)
        end = repaired.index(insert_heading)
        section = repaired[start:end]
        table_positions = [i for i, line in enumerate(section) if line.startswith('<table style="width:45%;">')]
        if len(table_positions) >= 2:
            first_table_start = table_positions[0]
            second_table_start = table_positions[1]

            def table_end_at(pos: int) -> int:
                for j in range(pos, len(section)):
                    if section[j].strip() == "</table>":
                        return j
                return pos

            first_table_end = table_end_at(first_table_start)
            second_table_end = table_end_at(second_table_start)
            first_table = section[first_table_start : first_table_end + 1]
            second_table = section[second_table_start : second_table_end + 1]

            rebuilt = [
                table_creation_heading,
                "",
                "The behavior of struct output depends on the value of --one-struct.",
                "",
                "<ol>",
                "<li value=\"1\">If --one-struct is any of the following, treat it as OFF:",
                *first_table,
                "<p>This means, to generate a separate struct using the original backup filename and affix <code>struct_</code> immediately before the filename.</p>",
                "<p>Example:</p>",
                "<div style=\"margin-left: 2em;\"><code>- `barmm_ref_legislative.sql` -> `struct_barmm_ref_legislative.sql`</code></div>",
                "</li>",
                "<li value=\"2\">If --one-struct is any of the following, treat it as on ON:",
                *second_table,
                "<p>Generate one combined struct file containing all CREATE TABLE statements from all processed backup files. the filename starts with struct_ with date and timestamp as suffix.</p>",
                "<p>Filename convention:</p>",
                "<div style=\"margin-left: 2em;\"><code>- struct_yymmdd_hhmissampm.sql</code></div>",
                "<div style=\"margin-left: 3.5em;\">Example: <code>struct_260311_104530pm.sql</code></div>",
                "</li>",
                "<li value=\"3\">When generating the CREATE TABLE, remove the length specifier for all MySQL integer or whole number and data/datetime datatypes, leave decimal, float, and real numbers.</li>",
                "<li value=\"4\">Use utf8mb4 for character set and utf8mb4_general_ci for collate instead of the existing character set and collate specifier.</li>",
                "<li value=\"5\">This is different from the per-file struct mode:",
                "<ul style=\"list-style-type: circle;\">",
                "<li>per-file mode = one struct file per backup file</li>",
                "<li>combined mode = one struct file containing all table creation statements</li>",
                "</ul>",
                "</li>",
                "<li value=\"6\">Always include disable foreign key checks before drop table and enable the foreign key checks after table creation</li>",
                "</ol>",
            ]
            repaired[start:end] = rebuilt

    return repaired


def align_list_lines(lines: list[str], metas: list[ListMeta]) -> list[str]:
    output: list[str] = []
    meta_index = 0
    level_stack: list[tuple[int, str]] = []

    def match_meta(line_text: str) -> ListMeta | None:
        nonlocal meta_index
        target = normalize_text(line_text)
        if not target:
            return None
        best_idx: int | None = None
        for idx in range(meta_index, min(len(metas), meta_index + 25)):
            meta_norm = normalize_text(metas[idx].text)
            if not meta_norm:
                continue
            if target.startswith(meta_norm) or meta_norm.startswith(target) or target in meta_norm or meta_norm in target:
                best_idx = idx
                break
        if best_idx is None:
            return None
        meta_index = best_idx + 1
        return metas[best_idx]

    for line in lines:
        if line.startswith("#"):
            level_stack = []
            output.append(line)
            continue

        if not LIST_LINE_RE.match(line):
            if line.strip() and not line.startswith("<"):
                if not line.startswith(" ") and not line.startswith("\t") and not line.startswith(">"):
                    level_stack = []
            output.append(line)
            continue

        stripped = ORDERED_RE.sub(r"\3", line)
        stripped = BULLET_RE.sub(r"\3", stripped)
        stripped = COMPOSITE_LABEL_RE.sub("", stripped).strip()
        meta = match_meta(stripped)
        if meta is None:
            output.append(line)
            continue

        if not level_stack:
            level_stack = [(meta.effective_left, meta.kind)]
        else:
            while len(level_stack) > 1 and meta.effective_left < level_stack[-1][0]:
                level_stack.pop()
            if meta.effective_left > level_stack[-1][0]:
                level_stack.append((meta.effective_left, meta.kind))
            elif meta.effective_left < level_stack[-1][0]:
                level_stack[-1] = (meta.effective_left, meta.kind)
            else:
                level_stack[-1] = (meta.effective_left, meta.kind)

        depth = max(0, len(level_stack) - 1)
        if meta.kind == "ordered":
            output.append(
                f'<div data-list-kind="ordered" data-depth="{depth}" '
                f'data-label="{escape(meta.label)}">{escape(stripped)}</div>'
            )
        else:
            bullet_depth = max(0, sum(1 for _, kind in level_stack[: depth + 1] if kind == "bullet") - 1)
            bullet_styles = ["disc", "circle", "dash", "square"]
            bullet_style = bullet_styles[min(bullet_depth, len(bullet_styles) - 1)]
            output.append(
                f'<div data-list-kind="bullet" data-depth="{depth}" '
                f'data-bullet-style="{bullet_style}">{escape(stripped)}</div>'
            )

    return output


def list_config(kind: str, style: str, label: str) -> tuple[str, str, str]:
    if kind == "ordered" and label and label.isdigit():
        return "ol", "", ""
    if kind == "ordered":
        return "dl", "", f'<span class="ordered-label">{escape(label)}</span> '
    if style == "disc":
        return "ul", ' style="list-style-type: disc;"', ""
    if style == "circle":
        return "ul", ' style="list-style-type: circle;"', ""
    if style == "square":
        return "ul", ' style="list-style-type: square;"', ""
    return "ul", ' style="list-style-type: none;"', ""


def convert_div_markers_to_html_lists(lines: list[str]) -> list[str]:
    output: list[str] = []
    list_stack: list[tuple[str, str]] = []
    li_open: list[bool] = []
    in_raw_block = False

    def item_tag_for(tag: str) -> str:
        return "dd" if tag == "dl" else "li"

    def open_list(tag: str, attrs: str) -> None:
        output.append(f"<{tag}{attrs}>")
        list_stack.append((tag, attrs))
        li_open.append(False)

    def close_current_li() -> None:
        if li_open and li_open[-1]:
            tag = item_tag_for(list_stack[-1][0])
            output.append(f"</{tag}>")
            li_open[-1] = False

    def close_last_list() -> None:
        close_current_li()
        tag, _ = list_stack.pop()
        li_open.pop()
        output.append(f"</{tag}>")

    def flush_all_lists() -> None:
        while list_stack:
            close_last_list()

    for line in lines:
        match = DIV_MARKER_RE.match(line)
        if not match:
            if not line.strip() and list_stack:
                # Keep list context across blank lines from the markdown conversion.
                continue
            if line.startswith("<table") or in_raw_block:
                in_raw_block = True
                output.append(line)
                if line.startswith("</table>"):
                    in_raw_block = False
                continue
            flush_all_lists()
            output.append(line)
            continue

        kind = match.group("kind")
        level = int(match.group("depth"))
        label = unescape(match.group("label") or "")
        style = match.group("style") or ""
        text = unescape(match.group("text")).strip()
        tag, attrs, prefix = list_config(kind, style, label)
        item_text = f"{prefix}{escape(text)}"
        li_attrs = ""
        if kind == "ordered" and label.isdigit():
            li_attrs = f' value="{int(label)}"'
        if kind == "bullet" and style == "dash":
            item_text = f"- {escape(text)}"

        desired_depth = level + 1

        while len(list_stack) > desired_depth:
            close_last_list()

        if len(list_stack) == desired_depth and list_stack:
            current_tag, current_attrs = list_stack[-1]
            if current_tag != tag or current_attrs != attrs:
                close_last_list()
            else:
                close_current_li()

        while len(list_stack) < desired_depth:
            open_list(tag, attrs)

        if list_stack:
            current_tag, current_attrs = list_stack[-1]
            if current_tag != tag or current_attrs != attrs:
                close_last_list()
                open_list(tag, attrs)

        item_tag = item_tag_for(list_stack[-1][0])
        output.append(f"<{item_tag}{li_attrs}>{item_text}")
        li_open[-1] = True

    flush_all_lists()
    return output


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: postprocess_markdown.py <markdown_file> <docx_file>", file=sys.stderr)
        return 2

    md_path = Path(sys.argv[1])
    docx_path = Path(sys.argv[2])
    lines = md_path.read_text(encoding="utf-8").splitlines()
    lines = remove_artifact_comments(lines)
    lines = convert_yaml_title_to_heading(lines)
    title, subtitle = extract_docx_front_matter(docx_path)
    lines = ensure_document_title(lines, title)
    lines = promote_subtitle(lines, subtitle)
    metas = extract_docx_list_metadata(docx_path)
    lines = align_list_lines(lines, metas)
    lines = convert_div_markers_to_html_lists(lines)
    lines = repair_known_section_artifacts(lines)
    lines = rebuild_contents(lines, subtitle)
    lines = convert_pipe_tables_to_html(lines)
    lines = convert_markdown_headings_to_html(lines)
    lines = finalize_preview_layout(lines)

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
