#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt automatisch die Rezepte-Indizes für DE/EN als Glossar A–Z.

- i18n-Suffix-Variante: <slug>.<lang>.md (z.B. ananas-fried-rice.de.md)
- schreibt:
    docs/<recipes_dir>/index.de.md
    docs/<recipes_dir>/index.en.md
- Gruppiert nach Anfangsbuchstaben (A–Z, sonst '#'), ignoriert führende Artikel.

Aufruf:
  python scripts/make_recipes_index.py --root docs --recipes-dir rezepte --verbose
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
LANGS = ["de", "en"]

UI = {
    "de": {
        "title": "Rezepte (Glossar)",
        "subtitle": "Alphabetische Übersicht. Wähle ein Rezept oder nutze die Suche.",
        "no_entries": "_Keine Rezepte gefunden._",
        "articles": ["der", "die", "das", "ein", "eine", "einen", "einem", "einer", "the", "a", "an"],
        "letters": [chr(c) for c in range(ord("A"), ord("Z")+1)] + ["#"],
    },
    "en": {
        "title": "Recipes (Glossary)",
        "subtitle": "Alphabetical index. Pick a recipe or use search.",
        "no_entries": "_No recipes found._",
        "articles": ["the", "a", "an", "der", "die", "das"],
        "letters": [chr(c) for c in range(ord("A"), ord("Z")+1)] + ["#"],
    },
}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="docs", help="MkDocs root (default: docs)")
    p.add_argument("--recipes-dir", default="rezepte", help="Recipes subdir (default: rezepte)")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()

def read_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return meta, body

def parse_date(val: Any) -> Optional[datetime]:
    if not val:
        return None
    s = str(val)
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def lang_of_file(path: Path) -> Optional[str]:
    parts = path.name.split(".")
    if len(parts) < 3:
        return None
    lang = parts[-2].lower()
    return lang if lang in LANGS else None

def base_stem(path: Path) -> str:
    parts = path.name.split(".")
    if len(parts) >= 3 and parts[-2] in LANGS and parts[-1] == "md":
        return ".".join(parts[:-2]) + ".md"
    return path.name

# --- Glossar-Helfer ---

def normalize_first_char(s: str) -> str:
    if not s:
        return "#"
    ch = s[0]
    # deutsche Umlaute / ß / Akzente grob normalisieren
    mapping = {
        "Ä":"A","Ö":"O","Ü":"U","ä":"A","ö":"O","ü":"U",
        "ẞ":"S","ß":"S",
        "À":"A","Á":"A","Â":"A","Ã":"A","Å":"A","à":"A","á":"A","â":"A","ã":"A","å":"A",
        "È":"E","É":"E","Ê":"E","Ë":"E","è":"E","é":"E","ê":"E","ë":"E",
        "Ì":"I","Í":"I","Î":"I","Ï":"I","ì":"I","í":"I","î":"I","ï":"I",
        "Ò":"O","Ó":"O","Ô":"O","Õ":"O","ò":"O","ó":"O","ô":"O","õ":"O",
        "Ù":"U","Ú":"U","Û":"U","ù":"U","ú":"U","û":"U",
        "Ç":"C","ç":"C",
        "Ñ":"N","ñ":"N",
    }
    ch = mapping.get(ch, ch)
    ch = ch.upper()
    return ch if "A" <= ch <= "Z" else "#"

def strip_leading_article(title: str, lang: str) -> str:
    arts = UI[lang]["articles"]
    t = title.strip()
    tl = t.lower()
    for a in arts:
        if tl.startswith(a + " "):
            return t[len(a)+1:].strip()
    return t

def sort_key(title: str, lang: str) -> str:
    # Für Sortierung: führenden Artikel entfernen, grob ASCII-ähnlich machen
    t = strip_leading_article(title, lang)
    repl = str.maketrans({
        "Ä":"Ae","Ö":"Oe","Ü":"Ue","ä":"ae","ö":"oe","ü":"ue","ẞ":"Ss","ß":"ss",
        "À":"A","Á":"A","Â":"A","Ã":"A","Å":"A",
        "È":"E","É":"E","Ê":"E","Ë":"E",
        "Ì":"I","Í":"I","Î":"I","Ï":"I",
        "Ò":"O","Ó":"O","Ô":"O","Õ":"O",
        "Ù":"U","Ú":"U","Û":"U",
        "Ç":"C","Ñ":"N",
    })
    return t.translate(repl).lower()

def collect_recipes(recipes_dir: Path, verbose=False):
    per_lang: Dict[str, List[Dict[str, Any]]] = {lang: [] for lang in LANGS}
    for md in sorted(recipes_dir.glob("*.md")):
        if md.name.startswith("index."):
            continue
        lang = lang_of_file(md) or "de"
        text = md.read_text(encoding="utf-8")
        meta, _ = read_frontmatter(text)
        title = str(meta.get("title") or md.stem)
        cover = meta.get("cover")
        date_obj = parse_date(meta.get("date")) or datetime.fromtimestamp(md.stat().st_mtime)
        item = {
            "title": title,
            "cover": str(cover) if cover else None,
            "date": date_obj,
            "link": base_stem(md),
            "path": md,
            "sort_key": sort_key(title, lang),
            "group": normalize_first_char(strip_leading_article(title, lang)),
        }
        per_lang.setdefault(lang, []).append(item)
        if verbose:
            print(f"[{lang}] + {md.name} -> {title} (group {item['group']})")
    # innerhalb der Sprache sortieren nach sort_key, dann Titel
    for lang, items in per_lang.items():
        items.sort(key=lambda x: (x["group"], x["sort_key"], x["title"].lower()))
    return per_lang

def render_glossary(lang: str, items: List[Dict[str, Any]]) -> str:
    ui = UI[lang]
    if not items:
        return f"# {ui['title']}\n\n{ui['no_entries']}\n"

    # Map Letter -> Liste
    groups: Dict[str, List[Dict[str, Any]]] = {L: [] for L in ui["letters"]}
    for it in items:
        groups.setdefault(it["group"], []).append(it)

    out: List[str] = []
    out.append(f"# {ui['title']}\n")
    out.append(ui["subtitle"] + "\n")

    for letter in ui["letters"]:
        lst = groups.get(letter, [])
        if not lst:
            continue
        out.append(f"## {letter}\n")
        for it in lst:
            # reine Glossar-Liste: nur Linktitel (keine Bilder/Chips)
            out.append(f"- [{it['title']}]({it['link']})")
        out.append("")  # Leerzeile nach Gruppe
    out.append("")  # EOF newline
    return "\n".join(out)

def main():
    args = parse_args()
    root = Path(args.root).resolve()
    recipes_dir = (root / args.recipes_dir).resolve()
    assert recipes_dir.exists(), f"{recipes_dir} existiert nicht."
    per_lang = collect_recipes(recipes_dir, verbose=args.verbose)
    for lang in LANGS:
        out_path = recipes_dir / f"index.{lang}.md"
        content = render_glossary(lang, per_lang.get(lang, []))
        out_path.write_text(content, encoding="utf-8")
        if args.verbose:
            print(f"Geschrieben: {out_path}")

if __name__ == "__main__":
    main()
