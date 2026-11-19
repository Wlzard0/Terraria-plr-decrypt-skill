---
name: terraria-plr-decrypt
description: Decrypt and analyze Terraria player save files (.plr), including AES-128 decryption, full field parsing for v319 (1.4.5.6), source-verified v322/v324/v326 (1.4.5.8) format deltas, best-effort support for older versions, Chinese item/buff/prefix name lookup, and read-only reports. Use when the user asks to decrypt, parse, inspect, explain, translate, or analyze a Terraria .plr character save, or to explain any field inside one.
---

# Terraria .plr 存档解密与分析

## Workflow

1. Locate the `.plr` file (user-provided path or Terraria Players folder). Ask only if ambiguous.
2. Decrypt and parse with `scripts/parse_plr.py` (run from this skill folder, or use absolute paths):

```bash
python scripts/parse_plr.py "<file.plr>" \
  --names references/names.md \
  --json "<output>.json" \
  --text "<output>.txt"
```

3. Read the generated text report and summarize in Chinese, following the user's requested level of detail (overview vs full inventory listing).
4. If parsing fails, report the exact failure offset/reason; never fill gaps with invented values.

### v322–v326 support (implemented in `scripts/parse_plr.py`)

The bundled parser implements v319 plus the verified v322/v324/v326 deltas (see `references/format.md`):

- v322+: a `bool favorited` after every main armor/dye item (`item5f`) and every item in all three loadouts (10 bytes each, `item10`);
- v324+: one reserved `bool` immediately after `ateArtisanBread`, exposed as `reserved_v324`;
- v326: accepted header version; no additional `Player.Deserialize` field is gated specifically at v326.

Without these gates a v326 file desynchronizes (31 bytes before the spawn-point section, a further 90 bytes in the loadouts) and the script dies with `unexpected EOF`. If you see that error on a v322+ file, the gates have regressed.

A parse counts as complete only when: no exception, `trailing_hex` is empty, and the remaining bytes are exactly valid PKCS#7 padding (reported as `pkcs7_padding_hex`; its length is `plaintext_length - parsed_offset`, anywhere in 1..16 — e.g. `04 04 04 04` or `09`×9 depending on payload length).

### Quick field lookup

- Difficulty / mode: JSON key `difficulty` — 0 classic (softcore), 1 mediumcore, 2 hardcore, 3 journey.
- Journey research list: `research`; creative powers: `creative_powers` (the game writes the three persistent powers for every character, journey or not, so they do not indicate journey mode).

### Verification record

- v326 (1.4.5.8): four non-journey/journey sample characters (3840 B plaintext, payload 3831 B + 9 B padding) parse to completion, read-only; difficulty values and header fields were cross-checked against an independent parser. A v326 regression sample with payload 3836 B + `04 04 04 04` padding also passes. Source files' SHA-256 unchanged before/after.
- v319 regression: a journey-mode character (18352 B plaintext, payload 18337 B + 15 B padding, 847 research entries) parses to completion with `trailing_hex` empty. The research section averages ≈ 17 B/entry (1 B length + internal name + int32 count); each researched item adds roughly 17–25 bytes.
- Not re-verified after the v322–v326 changes: versions older than v319 (279/194).

## Rules (red lines)

- Read-only analysis. Never write back, patch, or re-export the `.plr` file itself.
- Keep the decrypted plaintext in memory only; do not save decrypted copies to disk.
- Report unknown IDs as `[未知ID=<n>]`; do not guess names.
- Report unread trailing bytes as raw hex. First distinguish valid PKCS#7 AES padding (for example `04 04 04 04`) from genuine unread game data; only the latter should be reported as an unknown trailing field.

## Field knowledge

- For the exact v319–v326 field order and version gates, read `references/format.md`.
- For Chinese item/buff/prefix names, use `references/names.md` (parsed automatically by the script via `--names`).
- The old reference terms `extra_v315`, `qd/fb/Ie/pe/qe/cb`, `na 字节`, `中间段` are obsolete; use the real names in `references/format.md`.

## Notes

- The script is self-contained (pure-Python AES with FIPS-197 self-test) and works offline.
- Versions 319 and 322/324/326 are supported by the script. Versions 279/194 are parsed best-effort with version gates.
- When running under Windows PowerShell 5.1, set `$env:PYTHONIOENCODING='utf-8'` and write `--text`/`--json` to a temp folder (not next to the `.plr`); delete the reports afterwards if the user does not need them.
- Buff time is in ticks (60 ticks = 1 second); play time is in .NET TimeSpan ticks (10,000,000/s).
- If the user wants a full inventory dump or a specific section, rerun with `--json` and format the relevant part.
