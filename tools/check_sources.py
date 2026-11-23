#!/usr/bin/env python3
"""Prüft das Quellenregister und alle lokalen Quellenverweise.

Der Prüfer ist absichtlich konservativ: Er bestätigt keine historische
Richtigkeit, sondern verhindert kaputte IDs, fehlende lokale Dateiverweise und
nicht registrierte Literatur-/Fußnotenverweise. Außerdem muss jede Datei unter
data/ und img/ über local_files einem Registereintrag zugeordnet sein, damit das
Verzeichnis der Datensätze aktuell bleibt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REGISTRY_PATH = DATA / "sources.json"
IMG = ROOT / "img"

# Dateien, die keine Datengrundlage sind und deshalb nicht im Register stehen müssen.
NICHT_REGISTRIERT = {
    "data/sources.json",            # das Register selbst
    "data/vignetten.json",          # eigene Schriftrollen-Texte (Format: docs/VIGNETTEN.md)
    "data/vignetten_demo.json",     # Beispielinhalte für die Vignetten-Vorschau
    "img/icons/favicon.png",        # Projektlogo
}


def registrierungspflichtig() -> list[str]:
    """Alle Daten- und Bilddateien relativ zum Projektordner (Kachelordner als Ganzes)."""
    pfade: list[str] = []
    for path in sorted(DATA.rglob("*.json")):
        pfade.append(path.relative_to(ROOT).as_posix())
    for path in sorted(IMG.iterdir()):
        if path.is_dir() and path.name != "icons":
            pfade.append(path.relative_to(ROOT).as_posix() + "/")
        elif path.is_file():
            pfade.append(path.relative_to(ROOT).as_posix())
    icons = IMG / "icons"
    if icons.is_dir():
        pfade.extend(p.relative_to(ROOT).as_posix() for p in sorted(icons.iterdir()) if p.is_file())
    return [p for p in pfade if p not in NICHT_REGISTRIERT]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def values(value: Any) -> Iterable[str]:
    """Normalisiert source_id und source_ids zu einzelnen Zeichenketten."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item


def walk_source_references(value: Any, location: str) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in {"source_id", "source_ids"}:
                if not isinstance(child, (str, list)):
                    yield child_location, "<ungültiger Typ>"
                elif isinstance(child, list) and any(not isinstance(item, str) for item in child):
                    yield child_location, "<ungültiger Listeneintrag>"
                else:
                    for source_id in values(child):
                        yield child_location, source_id
            yield from walk_source_references(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_source_references(child, f"{location}[{index}]")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        registry = read_json(REGISTRY_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FEHLER: {REGISTRY_PATH.relative_to(ROOT)} kann nicht gelesen werden: {exc}")
        return 1

    sources = registry.get("sources")
    categories = registry.get("categories")
    statuses = registry.get("status_labels")
    if not isinstance(sources, list):
        errors.append("sources.json: Feld 'sources' muss eine Liste sein.")
        sources = []
    if not isinstance(categories, list):
        errors.append("sources.json: Feld 'categories' muss eine Liste sein.")
        categories = []
    if not isinstance(statuses, dict):
        errors.append("sources.json: Feld 'status_labels' muss ein Objekt sein.")
        statuses = {}

    if not isinstance(registry.get("stand"), str):
        warnings.append("sources.json: Feld 'stand' (Datum der letzten Pflege, JJJJ-MM-TT) fehlt.")

    category_ids = {item.get("id") for item in categories if isinstance(item, dict)}
    known_ids: set[str] = set()
    registrierte_pfade: set[str] = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label}: Eintrag muss ein Objekt sein.")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{label}: fehlende oder ungültige id.")
            continue
        if source_id in known_ids:
            errors.append(f"{label}: doppelte Quellen-ID '{source_id}'.")
        known_ids.add(source_id)

        status = source.get("usage_status")
        if status not in statuses:
            errors.append(f"{source_id}: unbekannter usage_status '{status}'.")

        primary = source.get("primary_category")
        listed_categories = source.get("categories", [])
        if primary not in category_ids:
            errors.append(f"{source_id}: unbekannte primary_category '{primary}'.")
        if not isinstance(listed_categories, list) or not listed_categories:
            errors.append(f"{source_id}: categories muss eine nichtleere Liste sein.")
        else:
            for category in listed_categories:
                if category not in category_ids:
                    errors.append(f"{source_id}: unbekannte Kategorie '{category}'.")
            if primary not in listed_categories:
                errors.append(f"{source_id}: primary_category fehlt in categories.")

        local_files = source.get("local_files", [])
        if status in {"used", "partially_used"} and not local_files:
            errors.append(f"{source_id}: verwendete Quelle ohne local_files.")
        if local_files and not isinstance(local_files, list):
            errors.append(f"{source_id}: local_files muss eine Liste sein.")
        elif isinstance(local_files, list):
            for file_ref in local_files:
                path_value = file_ref.get("path") if isinstance(file_ref, dict) else None
                if not isinstance(path_value, str) or not path_value:
                    errors.append(f"{source_id}: local_files enthält keinen gültigen Pfad.")
                elif not (ROOT / path_value).exists():
                    errors.append(f"{source_id}: lokaler Pfad fehlt: {path_value}")
                else:
                    registrierte_pfade.add(path_value)

    for pfad in registrierungspflichtig():
        abgedeckt = any(
            pfad == eintrag or (eintrag.endswith("/") and pfad.startswith(eintrag))
            for eintrag in registrierte_pfade
        )
        if not abgedeckt:
            warnings.append(f"{pfad}: Datei steht in keinem Registereintrag (local_files).")

    all_data: dict[str, Any] = {}
    for path in sorted(DATA.glob("*.json")):
        if path == REGISTRY_PATH:
            continue
        try:
            content = read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: ungültiges JSON: {exc}")
            continue
        all_data[path.name] = content
        for location, source_id in walk_source_references(content, path.relative_to(ROOT).as_posix()):
            if source_id not in known_ids:
                errors.append(f"{location}: nicht registrierte source_id '{source_id}'.")

    literature = all_data.get("literatur.json", {})
    if isinstance(literature, dict) and isinstance(literature.get("titel"), list):
        for entry in literature["titel"]:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                if entry["id"] not in known_ids:
                    errors.append(
                        f"data/literatur.json: Literatur-ID '{entry['id']}' fehlt im Quellenregister."
                    )

    texts = all_data.get("texte.json", {})
    if isinstance(texts, dict) and isinstance(texts.get("texte"), list):
        for text in texts["texte"]:
            if not isinstance(text, dict):
                continue
            for footnote in text.get("fussnoten", []):
                source_id = footnote.get("q") if isinstance(footnote, dict) else None
                if isinstance(source_id, str) and source_id not in known_ids:
                    errors.append(
                        f"data/texte.json: Fußnoten-ID '{source_id}' fehlt im Quellenregister."
                    )

    for warning in warnings:
        print(f"WARNUNG: {warning}")
    for error in errors:
        print(f"FEHLER: {error}")

    if errors:
        print(f"Quellenprüfung fehlgeschlagen: {len(errors)} Fehler, {len(warnings)} Warnungen.")
        return 1
    print(
        f"Quellenprüfung erfolgreich: {len(known_ids)} Registereinträge, "
        f"{len(all_data)} Datendateien, {len(warnings)} Warnungen."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
