#!/usr/bin/env python3
"""Prueft das Plugin-Paket gegen die Verzeichnisvorgaben, die `claude plugin validate` nicht prueft.

Quelle jeder Regel: claude.com/docs/plugins/pre-submission-checklist und
code.claude.com/docs/en/plugins/manifest-reference (abgerufen 03.11.2026). Gemessen am
03.11.2026: `claude plugin validate` (v2.1.284) laesst einen fehlenden Icon-Pfad, einen
reservierten Namen (`claude-...`) und eine Nicht-URL in den Verzeichnisfeldern durch - darum
dieser Waechter.

Aufruf: python3 -I werkzeuge/pruefe_paket.py [plugin-ordner]
Exit 0 = keine BLOCKIERT-Befunde; OFFEN-Befunde werden gemeldet, brechen aber nicht ab,
ausser mit --streng.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
STANDARD_ORDNER = WURZEL / "calcing-engineering"

# Betreiberfreigabe: die einzige E-Mail-Adresse, die im Paket stehen darf (Impressum, Support).
ERLAUBTE_EMAILS = {"info@calcing.de"}
ERWARTETE_LIZENZ = "MIT"  # Betreiberentscheidung 03.11.2026
LIZENZ_INHABER = "Copyright (c) 2026 CalcIng - Müller Engineering Solutions GmbH"
RESERVIERT_GANZ = {"claude", "anthropic", "anthropics", "claude-code", "claude-mods",
                   "official", "plugin", "mcp", "test"}
RESERVIERT_PRAEFIX = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
SYSTEMDATEIEN = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
BILD_ENDUNGEN = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
SCHRIFT_ENDUNGEN = {".ttf", ".otf", ".woff", ".woff2"}
# Portal 13.11.2026 (Version 846e61b, "Directory policy"): nennt eine Textdatei des Pakets eine
# Bild- oder Schriftdatei, haelt das Verzeichnis die Version als "Image or font file that the
# plugin's code could run" fest (gemeldet fuer README.md, das `assets/icon.png` nannte). Nur
# plugin.json darf das Icon nennen - dort ist es das Verzeichnisfeld `icon`.
DARF_ASSETS_NENNEN = {Path(".claude-plugin") / "plugin.json"}
GEHEIMNIS_MUSTER = [
    re.compile(r"(?i)bearer\s+[a-z0-9._-]{20,}"),
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),  # JWT
    re.compile(r"(?i)(api[_-]?key|secret|password|passwort)\s*[:=]\s*\S{6,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def woerter_ausserhalb_code(text: str) -> int:
    ohne = re.sub(r"```.*?```", " ", text, flags=re.S)
    ohne = re.sub(r"`[^`]*`", " ", ohne)
    return len(re.findall(r"\w+", ohne))


def frontmatter(text: str) -> dict[str, str] | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return None
    felder: dict[str, str] = {}
    for zeile in m.group(1).splitlines():
        if ":" in zeile and not zeile.startswith(" "):
            k, v = zeile.split(":", 1)
            felder[k.strip()] = v.strip()
    return felder


def pruefe(ordner: Path) -> tuple[list[str], list[str], list[str]]:
    blockiert: list[str] = []
    offen: list[str] = []
    ok: list[str] = []

    manifest_pfad = ordner / ".claude-plugin" / "plugin.json"
    if not manifest_pfad.is_file():
        return [f"{manifest_pfad} fehlt"], offen, ok
    m = json.loads(manifest_pfad.read_text(encoding="utf-8"))

    name = m.get("name", "")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", name):
        blockiert.append(f"name {name!r}: nicht [a-z0-9-], 1-64 Zeichen, Anfang/Ende alphanumerisch")
    elif name in RESERVIERT_GANZ or name.startswith(RESERVIERT_PRAEFIX):
        blockiert.append(f"name {name!r}: reserviert")
    else:
        ok.append(f"name {name!r}: Muster und nicht reserviert")
    for feld in ("description", "author", "version"):
        (ok if m.get(feld) else blockiert).append(f"plugin.json {feld}: {'gesetzt' if m.get(feld) else 'fehlt'}")
    for feld in ("displayName",):
        wert = m.get(feld, "") + (m.get("author") or {}).get("name", "")
        if any(ord(c) in (0x200b, 0x200c, 0x200d, 0xfeff) for c in wert):
            blockiert.append(f"{feld}/author.name: unsichtbare Zeichen")
    for feld in ("homepage", "documentationUrl", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"):
        wert = m.get(feld)
        if wert is None:
            offen.append(f"plugin.json {feld}: nicht gesetzt")
        elif not str(wert).startswith("https://"):
            blockiert.append(f"plugin.json {feld}: keine https-URL ({wert!r})")
        else:
            ok.append(f"plugin.json {feld}: https")
    icon = m.get("icon")
    if icon:
        p = (ordner / icon).resolve()
        if not str(icon).startswith("./") or ordner.resolve() not in p.parents or not p.is_file():
            blockiert.append(f"icon {icon!r}: Pfad nicht ./..., ausserhalb oder fehlt")
        elif p.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n" and p.suffix.lower() == ".png":
            blockiert.append(f"icon {icon!r}: kein vollstaendiges PNG")
        else:
            ok.append(f"icon {icon!r}: vorhanden, PNG")

    # Lizenz: Portal "License missing" = Blocks. Betreiberentscheidung 03.11.2026: MIT, beides
    # gesetzt (LICENSE-Datei und plugin.json "license"); beide muessen zueinander passen.
    lizenz_feld = m.get("license")
    lizenz_datei = ordner / "LICENSE"
    if not lizenz_feld and not lizenz_datei.is_file():
        blockiert.append("Lizenz: weder LICENSE noch plugin.json license (Portal: 'License missing')")
    elif lizenz_feld != ERWARTETE_LIZENZ:
        blockiert.append(f"plugin.json license {lizenz_feld!r} != Betreiberentscheidung {ERWARTETE_LIZENZ!r}")
    elif not lizenz_datei.is_file():
        blockiert.append("LICENSE fehlt (Betreiberentscheidung: Datei und Feld)")
    else:
        text = lizenz_datei.read_text(encoding="utf-8")
        if not text.startswith("MIT License") or LIZENZ_INHABER not in text:
            blockiert.append("LICENSE: nicht 'MIT License' oder Copyright-Inhaber fehlt")
        else:
            ok.append(f"Lizenz: plugin.json {lizenz_feld!r} und LICENSE (MIT, {LIZENZ_INHABER})")

    readme = ordner / "README.md"
    if not readme.is_file():
        blockiert.append("README.md fehlt")
    else:
        n = woerter_ausserhalb_code(readme.read_text(encoding="utf-8"))
        (ok if n >= 40 else blockiert).append(f"README: {n} Woerter ausserhalb von Code (>= 40)")

    mcp = ordner / ".mcp.json"
    if mcp.is_file():
        server = json.loads(mcp.read_text(encoding="utf-8")).get("mcpServers")
        if not isinstance(server, dict) or not server:
            blockiert.append(".mcp.json: kein mcpServers-Objekt")
        else:
            for key, cfg in server.items():
                if cfg.get("type") not in ("http", "sse", "ws") or not str(cfg.get("url", "")).startswith(("https://", "wss://")):
                    blockiert.append(f".mcp.json {key}: type/url nicht http(s)")
                elif "headers" in cfg:
                    blockiert.append(f".mcp.json {key}: headers gesetzt (keine Geheimnisse ins Paket)")
                else:
                    ok.append(f".mcp.json {key}: {cfg['type']} {cfg['url']}, ohne headers")

    skills = sorted((ordner / "skills").glob("*/SKILL.md"))
    if not skills:
        blockiert.append("keine skills/<name>/SKILL.md")
    for s in skills:
        fm = frontmatter(s.read_text(encoding="utf-8"))
        if fm is None:
            blockiert.append(f"{s.relative_to(ordner)}: keine Frontmatter")
            continue
        sname, desc = fm.get("name", ""), fm.get("description", "")
        if sname != s.parent.name or not re.fullmatch(r"[a-z0-9-]{1,64}", sname):
            blockiert.append(f"{s.relative_to(ordner)}: name {sname!r} != Ordner oder Muster")
        elif not desc or desc.startswith("[") or len(desc) > 1024:
            blockiert.append(f"{s.relative_to(ordner)}: description leer, Liste oder > 1024 ({len(desc)})")
        else:
            ok.append(f"{s.relative_to(ordner)}: name = Ordner, description {len(desc)} Zeichen")
        zeilen = s.read_text(encoding="utf-8").count("\n")
        if zeilen >= 500:
            blockiert.append(f"{s.relative_to(ordner)}: {zeilen} Zeilen (< 500 empfohlen)")

    dateien = [p for p in ordner.rglob("*")]
    if len(dateien) > 512:
        blockiert.append(f"{len(dateien)} Eintraege > 512")
    assets = {p.relative_to(ordner) for p in dateien
              if p.is_file() and p.suffix.lower() in BILD_ENDUNGEN | SCHRIFT_ENDUNGEN}
    asset_namen = {a.as_posix() for a in assets} | {a.name for a in assets}
    namen_klein: dict[str, Path] = {}
    for p in dateien:
        rel = p.relative_to(ordner)
        if p.name in SYSTEMDATEIEN:
            blockiert.append(f"Systemdatei {rel}")
        if p.is_symlink():
            blockiert.append(f"symbolischer Link {rel}")
        if re.search(r'[:<>"|?*]|[ .]$', p.name):
            blockiert.append(f"Dateiname nicht Windows-tauglich: {rel}")
        k = str(rel).lower()
        if k in namen_klein:
            blockiert.append(f"Namen unterscheiden sich nur in Gross/Klein: {rel}")
        namen_klein[k] = rel
        if rel.parts[0] == "bin":
            blockiert.append("bin/ auf oberster Ebene: claude.ai/Cowork installieren nicht")
        if not p.is_file():
            continue
        groesse = p.stat().st_size
        if p.suffix.lower() in BILD_ENDUNGEN:
            if groesse >= 5 * 1024 * 1024:
                blockiert.append(f"{rel}: {groesse} Byte >= 5 MiB")
            continue
        if groesse >= 256 * 1024:
            blockiert.append(f"{rel}: {groesse} Byte >= 256 KiB")
            continue  # nicht weiter durchsuchen (Regex-Laufzeit), ist ohnehin blockiert
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            blockiert.append(f"{rel}: Binaerdatei, kein Bild")
            continue
        genannt = sorted(n for n in asset_namen if n in text)
        if genannt and rel not in DARF_ASSETS_NENNEN:
            blockiert.append(f"{rel}: nennt Bild-/Schriftdatei {genannt} (Portal: Version bleibt angehalten)")
        for muster in GEHEIMNIS_MUSTER:
            if muster.search(text):
                blockiert.append(f"{rel}: moegliches Geheimnis ({muster.pattern})")
        # wortweise statt ueber den ganzen Text: der Regex backtrackt sonst quadratisch
        fremde = {m.group(0) for w in text.split() if "@" in w for m in [EMAIL.search(w)] if m} - ERLAUBTE_EMAILS
        if fremde:
            blockiert.append(f"{rel}: E-Mail-Adressen ausserhalb der Freigabe: {sorted(fremde)}")
    ok.append(f"{len(dateien)} Eintraege, Groessen, Namen, Geheimnisse, E-Mails geprueft")
    return blockiert, offen, ok


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ordner = Path(args[0]) if args else STANDARD_ORDNER
    blockiert, offen, ok = pruefe(ordner)
    for z in ok:
        print(f"OK         {z}")
    for z in offen:
        print(f"OFFEN      {z}")
    for z in blockiert:
        print(f"BLOCKIERT  {z}")
    if blockiert or ("--streng" in sys.argv and offen):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
