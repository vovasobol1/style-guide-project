#!/usr/bin/env python3
"""Проверка Markdown-файлов на правила руководства, которые можно проверить автоматически.

Ошибки (код возврата 1):
  ORF-01  буква «ё» вне списка разрешенных слов;
  ORF-02  прямые кавычки в тексте;
  ORF-03  дефис или двойной дефис вместо тире;
  ORF-04  склонение иноязычного названия через апостроф;
  TON-01  обращение «Вы» с прописной буквы в середине предложения;
  слова из scripts/stop_words.txt (TON-05, TRM-03).

Предупреждения (код возврата 0):
  TON-04  предложение длиннее MAX_SENTENCE_WORDS слов.

Код, ссылки, HTML-комментарии и участки между маркерами
<!-- stylecheck: off --> и <!-- stylecheck: on --> не проверяются.

Запуск: python3 scripts/stylecheck.py [файлы или каталоги]
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP_WORDS_FILE = ROOT / "scripts" / "stop_words.txt"
DEFAULT_TARGETS = ["docs", "README.md", "CONTRIBUTING.md"]
MAX_SENTENCE_WORDS = 30
YO_ALLOWED = {"всё"}

OFF_MARKER = "<!-- stylecheck: off -->"
ON_MARKER = "<!-- stylecheck: on -->"

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
SKIP_LINE_RE = re.compile(r"^\s*(\|?\s*:?-{3,}|---\s*$|!!!|\?\?\?)")
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
HEADING_RE = re.compile(r"^\s*#{1,6}\s")

STRIP_PATTERNS = [
    re.compile(r"<!--.*?-->"),
    re.compile(r"(`+).+?\1"),
    re.compile(r"\]\([^)]*\)"),
    re.compile(r"<https?://[^>]+>"),
    re.compile(r"https?://\S+"),
    re.compile(r"\{[#.][^}]*\}"),
]

YO_WORD_RE = re.compile(r"\w*[ёЁ]\w*")
STRAIGHT_QUOTE_RE = re.compile(r'"')
HYPHEN_AS_DASH_RE = re.compile(r"(?<=\S)\s-\s(?=\S)")
DOUBLE_HYPHEN_RE = re.compile(r"(?<!-)--(?!-)")
APOSTROPHE_RE = re.compile(r"[A-Za-z]+['’][а-яё]+")
CAPITAL_YOU_RE = re.compile(r"(?<=[а-яёa-z0-9,;:] )(Вы|Вас|Вам|Вами|Ваш\w*)\b")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+(?=[«(\"A-ZА-ЯЁ0-9])")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)*")


def load_stop_words():
    """Читает шаблоны вида «регулярное выражение | правило | что писать вместо»."""
    rules = []
    for number, raw in enumerate(STOP_WORDS_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(" | ")]
        if len(parts) != 3:
            sys.exit(f"{STOP_WORDS_FILE.name}:{number}: ожидается «шаблон | правило | замена»")
        pattern, rule, hint = parts
        rules.append((re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.IGNORECASE), rule, hint))
    return rules


def clean(line):
    """Убирает из строки части, которые не являются текстом документа."""
    for pattern in STRIP_PATTERNS:
        line = pattern.sub(" ", line)
    return line


def check_line(text, stop_words):
    errors = []
    for match in YO_WORD_RE.finditer(text):
        if match.group().lower() not in YO_ALLOWED:
            errors.append(("ORF-01", f"«{match.group()}»: пишите «е» вместо «ё»"))
    if STRAIGHT_QUOTE_RE.search(text):
        errors.append(("ORF-02", "прямые кавычки: используйте «елочки»"))
    if HYPHEN_AS_DASH_RE.search(text) or DOUBLE_HYPHEN_RE.search(text):
        errors.append(("ORF-03", "дефис вместо тире: используйте « — »"))
    for match in APOSTROPHE_RE.finditer(text):
        errors.append(("ORF-04", f"«{match.group()}»: не склоняйте название через апостроф"))
    for match in CAPITAL_YOU_RE.finditer(text):
        errors.append(("TON-01", f"«{match.group()}»: обращение пишем со строчной буквы"))
    for pattern, rule, hint in stop_words:
        for match in pattern.finditer(text):
            errors.append((rule, f"«{match.group()}»: {hint}"))
    return errors


def long_sentences(text):
    for sentence in SENTENCE_SPLIT_RE.split(text.strip()):
        words = WORD_RE.findall(sentence)
        if len(words) > MAX_SENTENCE_WORDS:
            yield len(words), " ".join(words[:6])


def check_file(path, stop_words):
    errors, warnings = [], []
    in_fence = None
    enabled = True
    in_front_matter = False
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if number == 1 and raw.strip() == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            in_front_matter = raw.strip() != "---"
            continue

        fence = FENCE_RE.match(raw)
        if fence:
            marker = fence.group(1)
            if in_fence is None:
                in_fence = marker
            elif marker[0] == in_fence[0] and len(marker) >= len(in_fence):
                in_fence = None
            continue
        if in_fence:
            continue

        if OFF_MARKER in raw:
            enabled = False
            continue
        if ON_MARKER in raw:
            enabled = True
            continue
        if not enabled or SKIP_LINE_RE.match(raw):
            continue

        text = clean(LIST_MARKER_RE.sub("", raw))
        for rule, message in check_line(text, stop_words):
            errors.append(f"{path}:{number}: {rule} {message}")

        if raw.lstrip().startswith("|") or HEADING_RE.match(raw):
            continue
        for count, start in long_sentences(text):
            warnings.append(f"{path}:{number}: TON-04 предложение из {count} слов: «{start}…»")
    return errors, warnings


def collect(targets):
    files = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.suffix == ".md" and path.exists():
            files.append(path)
    return files


def main():
    stop_words = load_stop_words()
    files = collect(sys.argv[1:] or DEFAULT_TARGETS)
    all_errors, all_warnings = [], []
    for path in files:
        errors, warnings = check_file(path, stop_words)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for line in all_warnings:
        print(f"предупреждение: {line}")
    for line in all_errors:
        print(f"ошибка: {line}")
    print(f"Проверено файлов: {len(files)}, ошибок: {len(all_errors)}, предупреждений: {len(all_warnings)}")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
