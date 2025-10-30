#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt automatisch die Rezepte-Indizes für DE/EN (i18n Suffix-Variante).

- Sucht unter docs/<recipes_dir> nach *.md
- Erwartete Lokalisierung: <name>.<lang>.md (z.B. ananas-fried-rice.de.md)
- Ignoriert: index.*.md
- Liest YAML-Frontmatter (zwischen '---' ... '---')
- Verwendet Meta-Felder (optional):
    title, cover, portions, time.prep, time.cook, difficulty, tags, date
- Sortiert absteigend nach 'date' (YYYY-MM-DD oder YYYY-MM oder YYYY)
  Fallback: Dateiname/mtime.
- Schreibt:
    docs/<recipes_dir>/index.de.md
    docs/<recipes_dir>/index.en.md
- Links zeigen auf die Basestem-Datei (ohne Sprachsuffix), damit mkdocs-static-i18n korrekt auflöst.

Aufruf:
  python scripts/make_recipes_index.py --root docs --recipes-dir rezepte --verbose
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from datetime import datetime
import yaml
from typing import Dict, Any, Optional, List, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

LANGS = ["de", "en"]  # welche Sprachen erzeugt werden sollen

# UI-Texte je Sprache
UI = {
    "de": {
        "title": "Rezepte",
        "subtitle": "Wähle ein Gericht aus oder nutze die Suche.",
        "open": ":arrow_right: Zum Rezept",
        "chips": {
            "servings": "Portionen",
            "prep": "Vorbereitung",
            "cook": "Kochen",
            "level": "Level",
        },
        "no_cover": "Kein Bild",
    },
    "en": {
        "title": "Recipes",
        "subtitle": "Pick a dish or use search.",
        "open": ":arrow_right: Open recipe",
        "chips": {
            "servings": "Servings",
            "prep": "Prep",
            "cook": "Cook",
            "level": "Level",
        },
        "no_cover": "No image",
    },
}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="docs", help="Root der MkDocs-Dokumente (default: docs)")
    p.add_argument("--recipes-dir", default="rezepte", help="Unterordner mit Rezepten (default: rezepte)")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()

def read_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Gibt (meta, body) zurück. meta={} falls keine Frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = m.group(1)
    meta = yaml.safe_load(fm) or {}
    body = text[m.end():]
    return meta, body

def parse_date(val: Any) -> Optional[datetime]:
    """Parst flexible Datumsangaben (YYYY-MM-DD | YYYY-MM | YYYY)."""
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
    """Extrahiert Sprachsuffix aus Dateiname: foo.de.md -> de."""
    parts = path.name.split(".")
    if len(parts) < 3:
        return None
    lang = parts[-2].lower()
    return lang if lang in LANGS else None

def base_stem(path: Path) -> str:
    """foo.de.md -> foo.md (ohne Sprachsuffix), damit i18n korrekt auflöst."""
    parts = path.name.split(".")
    if len(parts) >= 3 and parts[-2] in LANGS and parts[-1] == "md":
        return ".".join(parts[:-2]) + ".md"
    return path.name

def collect_recipes(recipes_dir: Path, verbose=False):
    """Liest alle Rezepte und liefert je Sprache eine Liste von Dicts."""
    per_lang: Dict[str, List[Dict[str, Any]]] = {lang: [] for lang in LANGS}
    for md in sorted(recipes_dir.glob("*.md")):
        if md.name.startswith("index."):
            continue
        lang = lang_of_file(md)
        if not lang:
            # nicht-lokalisierte Datei: optional ignorieren oder DE zuordnen
            lang = "de"
        text = md.read_text(encoding="utf-8")
        meta, _ = read_frontmatter(text)
        title = meta.get("title") or md.stem
        cover = meta.get("cover")
        portions = meta.get("portions")
        time_prep = (meta.get("time") or {}).get("prep")
        time_cook = (meta.get("time") or {}).get("cook")
        difficulty = meta.get("difficulty")
        date_obj = parse_date(meta.get("date"))
        if not date_obj:
            # Fallback: mtime
            date_obj = datetime.fromtimestamp(md.stat().st_mtime)
        item = {
            "title": str(title),
            "cover": str(cover) if cover else None,
            "portions": portions,
            "time_prep": time_prep,
            "time_cook": time_cook,
            "difficulty": difficulty,
            "date": date_obj,
            "link": base_stem(md),  # sprachneutraler Link
            "path": md,
        }
        per_lang.setdefault(lang, []).append(item)
        if verbose:
            print(f"[{lang}] + {md.name} -> {item['title']}")
    # sortiere je Sprache nach Datum absteigend
    for lang, items in per_lang.items():
        items.sort(key=lambda x: (x["date"], x["title"].lower()), reverse=True)
    return per_lang

def render_index(lang: str, items: List[Dict[str, Any]]) -> str:
    ui = UI[lang]
    chips = ui["chips"]
    lines = []
    lines.append(f"# {ui['title']}\n")
    lines.append(ui["subtitle"] + "\n")
    lines.append('<div class="grid cards" markdown>\n')
    for it in items:
        cover = it["cover"]
        title = it["title"]
        link = it["link"]
        meta_bits = []
        if it["portions"]:
            meta_bits.append(f"**{chips['servings']}:** {it['portions']}")
        if it["time_prep"]:
            meta_bits.append(f"**{chips['prep']}:** {it['time_prep']}")
        if it["time_cook"]:
            meta_bits.append(f"**{chips['cook']}:** {it['time_cook']}")
        if it["difficulty"]:
            meta_bits.append(f"**{chips['level']}:** {it['difficulty']}")
        meta_line = " · ".join(meta_bits) if meta_bits else ""
        # Karte
        lines.append(f"- {'![](' + cover + ')' if cover else ui['no_cover']}  \n"
                     f"  **{title}**  \n"
                     f"  {meta_line}  \n"
                     f"  [{UI[lang]['open']}]({link})")
        lines.append("")  # Leerzeile zwischen Karten
    lines.append("</div>\n")
    return "\n".join(lines)

def main():
    args = parse_args()
    root = Path(args.root).resolve()
    recipes_dir = (root / args.recipes_dir).resolve()
    assert recipes_dir.exists(), f"{recipes_dir} existiert nicht."
    per_lang = collect_recipes(recipes_dir, verbose=args.verbose)

    # Schreibe index pro Sprache
    for lang in LANGS:
        out_path = recipes_dir / f"index.{lang}.md"
        content = render_index(lang, per_lang.get(lang, []))
        out_path.write_text(content, encoding="utf-8")
        if args.verbose:
            print(f"Geschrieben: {out_path}")

if __name__ == "__main__":
    main()
