---
name: terraria-plr-decrypt
description: Decrypt and analyze Terraria player save files (.plr), including AES-128 decryption, full field parsing for version 319 (1.4.5.x) and best-effort support for older versions, Chinese item/buff/prefix name lookup, and read-only reports. Use when the user asks to decrypt, parse, inspect, explain, translate, or analyze a Terraria .plr character save, or to explain any field inside one.
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

## Rules (red lines)

- Read-only analysis. Never write back, patch, or re-export the `.plr` file itself.
- Keep the decrypted plaintext in memory only; do not save decrypted copies to disk.
- Report unknown IDs as `[未知ID=<n>]`; do not guess names.
- Report unread trailing bytes as raw hex and note that 1.4.5.6 ignores them.

## Field knowledge

- For the exact v319 field order and version gates, read `references/format.md`.
- For Chinese item/buff/prefix names, use `references/names.md` (parsed automatically by the script via `--names`).
- The old reference terms `extra_v315`, `qd/fb/Ie/pe/qe/cb`, `na 字节`, `中间段` are obsolete; use the real names in `references/format.md`.

## Notes

- The script is self-contained (pure-Python AES with FIPS-197 self-test) and works offline.
- Version 319 is fully supported; versions 279/194 are parsed best-effort with version gates.
- Buff time is in ticks (60 ticks = 1 second); play time is in .NET TimeSpan ticks (10,000,000/s).
- If the user wants a full inventory dump or a specific section, rerun with `--json` and format the relevant part.
