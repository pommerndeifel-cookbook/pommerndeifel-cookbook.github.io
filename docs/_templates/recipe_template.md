---
title: "[REZEPTTITEL]"
date: 2025-10-30
tags: [rezepte, kueche]
cover: "rezepte/bilder/[bilddatei].jpg"   # relativ zu /docs
portions: 2
time:
  prep: "15 Min"
  cook: "20 Min"
difficulty: "einfach"
nutrients:
  kcal: 520
  protein_g: 14
  carbs_g: 78
  fat_g: 15
---

# {{ page.meta.title }}

![{{ page.meta.title }}]({{ page.meta.cover }}){ loading=lazy }

<div class="recipe-meta">
  <span class="chip">Portionen: {{ page.meta.portions }}</span>
  <span class="chip">Vorbereitung: {{ page.meta.time.prep }}</span>
  <span class="chip">Kochen: {{ page.meta.time.cook }}</span>
  <span class="chip">Level: {{ page.meta.difficulty }}</span>
</div>

??? tip "Kurzbeschreibung"
    Kurzer Einleitungstext: Geschmack, Kontext, saisonale Hinweise, Varianten.

## Zutaten
- [ ] Zutat 1
- [ ] Zutat 2
- [ ] Zutat 3

## Zubereitung
1. Schritt 1 …
2. Schritt 2 …
3. Schritt 3 …

## Hinweise & Variationen
- Tipp 1
- Tipp 2

## Nährwerte (pro Portion)
| kcal | Protein (g) | Carbs (g) | Fett (g) |
|-----:|------------:|----------:|---------:|
| {{ page.meta.nutrients.kcal }} | {{ page.meta.nutrients.protein_g }} | {{ page.meta.nutrients.carbs_g }} | {{ page.meta.nutrients.fat_g }} |
