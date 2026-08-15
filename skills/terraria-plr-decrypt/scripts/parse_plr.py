#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decrypt and parse a Terraria .plr player save (read-only).

Primary target: version 319 (1.4.5.x). Older versions (194/279) are parsed
with version gates from the game's Player.Deserialize implementation.

Usage:
  parse_plr.py <file.plr> [--names <all_id.md>] [--json <out.json>] [--text <out.txt>]

The decrypted plaintext is kept in memory only and never written to disk.
"""

import argparse
import json
import struct
import sys

# ---------------------------------------------------------------------------
# Pure Python AES-128 (FIPS-197 self-tested; no external dependency)
# ---------------------------------------------------------------------------

SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
]

INV_SBOX = [
    0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
    0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
    0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
    0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
    0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
    0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
    0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
    0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
    0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
    0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
    0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
    0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
    0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
    0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
    0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
    0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
]

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def xtime(a):
    a <<= 1
    if a & 0x100:
        a ^= 0x11B
    return a & 0xFF


def gf_mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = xtime(a)
        b >>= 1
    return r


def key_expansion(key):
    nk, nr = 4, 10
    w = [list(key[i * 4:(i + 1) * 4]) for i in range(nk)]
    for i in range(nk, 4 * (nr + 1)):
        temp = w[i - 1][:]
        if i % nk == 0:
            temp = temp[1:] + temp[:1]
            temp = [SBOX[b] for b in temp]
            temp[0] ^= RCON[i // nk]
        w.append([w[i - nk][j] ^ temp[j] for j in range(4)])
    return [bytes(sum(w[4 * r:4 * r + 4], [])) for r in range(nr + 1)]


def aes_decrypt_block(key, block):
    rk = key_expansion(key)
    state = list(block)
    add = lambda i: [state[j] ^ rk[i][j] for j in range(16)]

    def inv_shift_rows(s):
        tmp = s[:]
        for r in range(1, 4):
            for c in range(4):
                s[r + 4 * c] = tmp[r + 4 * ((c - r) % 4)]

    def inv_sub_bytes(s):
        for i in range(16):
            s[i] = INV_SBOX[s[i]]

    def inv_mix_columns(s):
        for c in range(4):
            x = [s[r + 4 * c] for r in range(4)]
            s[0 + 4 * c] = gf_mul(x[0], 14) ^ gf_mul(x[1], 11) ^ gf_mul(x[2], 13) ^ gf_mul(x[3], 9)
            s[1 + 4 * c] = gf_mul(x[0], 9) ^ gf_mul(x[1], 14) ^ gf_mul(x[2], 11) ^ gf_mul(x[3], 13)
            s[2 + 4 * c] = gf_mul(x[0], 13) ^ gf_mul(x[1], 9) ^ gf_mul(x[2], 14) ^ gf_mul(x[3], 11)
            s[3 + 4 * c] = gf_mul(x[0], 11) ^ gf_mul(x[1], 13) ^ gf_mul(x[2], 9) ^ gf_mul(x[3], 14)

    state = add(10)
    for rnd in range(9, 0, -1):
        inv_shift_rows(state)
        inv_sub_bytes(state)
        state = add(rnd)
        inv_mix_columns(state)
    inv_shift_rows(state)
    inv_sub_bytes(state)
    state = add(0)
    return bytes(state)


def fips197_self_test():
    key = bytes(range(16))
    pt = bytes.fromhex("00112233445566778899aabbccddeeff")
    ct = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
    assert aes_decrypt_block(key, ct) == pt, "AES self-test failed"


def cbc_decrypt(data, key, iv):
    out = bytearray()
    prev = iv
    for i in range(0, len(data), 16):
        blk = data[i:i + 16]
        out += bytes(a ^ b for a, b in zip(aes_decrypt_block(key, blk), prev))
        prev = blk
    return bytes(out)


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

class Reader:
    def __init__(self, data):
        self.data = data
        self.off = 0

    def read(self, n):
        b = self.data[self.off:self.off + n]
        if len(b) != n:
            raise ValueError(f"unexpected EOF at offset {self.off} (want {n}, got {len(b)})")
        self.off += n
        return b

    def u8(self):
        return self.read(1)[0]

    def u16(self):
        return struct.unpack("<H", self.read(2))[0]

    def i32(self):
        return struct.unpack("<i", self.read(4))[0]

    def u32(self):
        return struct.unpack("<I", self.read(4))[0]

    def i64(self):
        return struct.unpack("<q", self.read(8))[0]

    def u64(self):
        return struct.unpack("<Q", self.read(8))[0]

    def f32(self):
        return struct.unpack("<f", self.read(4))[0]

    def bool_(self):
        return self.u8() != 0

    def rgb(self):
        return tuple(self.read(3))

    def string(self):
        n = self.read_7bit()
        return self.read(n).decode("utf-8", errors="replace")

    def read_7bit(self):
        shift = 0
        val = 0
        while True:
            b = self.u8()
            val |= (b & 0x7F) << shift
            shift += 7
            if not (b & 0x80):
                return val


def item5(r):
    return {"id": r.i32(), "prefix": r.u8()}


def item10(r):
    return {"id": r.i32(), "count": r.i32(), "prefix": r.u8(), "favorite": r.bool_()}


def item9(r):
    return {"id": r.i32(), "count": r.i32(), "prefix": r.u8()}


def compact(items):
    return [i for i in items if i["id"] != 0]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_plr(data):
    r = Reader(data)
    version = r.i32()
    relogic = r.read(7)
    if relogic != b"relogic":
        raise ValueError(f"header check failed: {relogic!r}")
    file_type = r.u8()
    if file_type != 3:
        raise ValueError(f"unexpected file type: {file_type}")

    out = {"version": version, "file_type": file_type}
    out["revision"] = r.u32()
    out["favorite"] = r.u64()
    out["name"] = r.string()

    # difficulty: v10+ (v17+: byte; v10-16: bool hardcore)
    if version >= 10:
        out["difficulty"] = r.u8() if version >= 17 else (2 if r.bool_() else 0)
    else:
        out["difficulty"] = 0
    if version >= 138:
        out["play_time_ticks"] = r.i64()
    else:
        out["play_time_ticks"] = 0

    out["hair"] = r.i32()
    if version >= 82:
        out["hair_dye"] = r.u8()
    else:
        out["hair_dye"] = 0
    if version >= 283:
        out["team"] = r.u8()
    else:
        out["team"] = 0

    # hideVisibleAccessory: 2 bits bytes (v124+), 1 byte (v83-123)
    if version >= 124:
        out["hide_visible_accessory"] = [r.u8(), r.u8()]
    elif version >= 83:
        out["hide_visible_accessory"] = [r.u8()]
    else:
        out["hide_visible_accessory"] = []
    if version >= 119:
        out["hide_misc"] = r.u8()
    else:
        out["hide_misc"] = 0
    if version >= 107:
        out["skin_variant"] = r.u8()
    else:
        out["male"] = r.bool_()
        out["skin_variant"] = None

    out["health"] = r.i32()
    out["health_max"] = r.i32()
    out["mana"] = r.i32()
    out["mana_max"] = r.i32()
    if version >= 125:
        out["extra_accessory"] = r.bool_()
    else:
        out["extra_accessory"] = False
    if version >= 229:
        out["unlocked_biome_torches"] = r.bool_()
        out["using_biome_torches"] = r.bool_()
    else:
        out["unlocked_biome_torches"] = False
        out["using_biome_torches"] = False

    perms = ["ate_artisan_bread"]
    if version >= 256:
        out["ate_artisan_bread"] = r.bool_()
    else:
        out["ate_artisan_bread"] = False
    if version >= 260:
        for k in ["used_aegis_crystal", "used_aegis_fruit", "used_arcane_crystal",
                  "used_galaxy_pearl", "used_gummy_worm", "used_ambrosia"]:
            out[k] = r.bool_()
    else:
        for k in ["used_aegis_crystal", "used_aegis_fruit", "used_arcane_crystal",
                  "used_galaxy_pearl", "used_gummy_worm", "used_ambrosia"]:
            out[k] = False

    if version >= 182:
        out["downed_dd2_any_difficulty"] = r.bool_()
    else:
        out["downed_dd2_any_difficulty"] = False
    if version >= 128:
        out["tax_money"] = r.i32()
    else:
        out["tax_money"] = 0
    if version >= 254:
        out["deaths_pve"] = r.i32()
        out["deaths_pvp"] = r.i32()
    else:
        out["deaths_pve"] = 0
        out["deaths_pvp"] = 0

    out["colors"] = {
        "hair": r.rgb(),
        "skin": r.rgb(),
        "eye": r.rgb(),
        "shirt": r.rgb(),
        "undershirt": r.rgb(),
        "pants": r.rgb(),
        "shoes": r.rgb(),
    }

    out["equipment"] = [item5(r) for _ in range(20)]
    out["dye"] = [item5(r) for _ in range(10)]
    out["inventory"] = [item10(r) for _ in range(50)]
    out["coins"] = [item10(r) for _ in range(4)]
    out["ammo"] = [item10(r) for _ in range(4)]
    out["misc"] = [{"equip": item5(r), "dye": item5(r)} for _ in range(5)]
    out["piggy_bank"] = [item9(r) for _ in range(40)]
    out["safe"] = [item9(r) for _ in range(40)]
    if version >= 182:
        out["defenders_forge"] = [item9(r) for _ in range(40)]
    else:
        out["defenders_forge"] = []
    if version >= 198:
        out["void_bag"] = [item10(r) if version >= 269 else item9(r) for _ in range(40)]
    else:
        out["void_bag"] = []
    if version >= 200:
        out["downed_deerclops"] = r.bool_()
    else:
        out["downed_deerclops"] = False

    buff_count = 44 if version >= 269 else 22
    out["buffs"] = [{"id": r.i32(), "time_ticks": r.i32()} for _ in range(buff_count)]

    out["spawn_points"] = []
    while True:
        x = r.i32()
        if x == -1:
            break
        out["spawn_points"].append({
            "x": x, "y": r.i32(), "world_id": r.i32(), "world_name": r.string(),
        })

    out["hotbar_locked"] = r.bool_()
    if version >= 145:
        out["hide_info"] = [r.bool_() for _ in range(13)]
    else:
        out["hide_info"] = []
    out["angler_quests_finished"] = r.i32()
    if version >= 255:
        out["gamepad_binds"] = [r.i32() for _ in range(4)]
    else:
        out["gamepad_binds"] = []

    if version >= 230:
        toggle_count = 12
    elif version >= 200:
        toggle_count = 11
    else:
        toggle_count = 10
    out["building_toggles"] = [r.i32() for _ in range(toggle_count)]

    if version >= 181:
        out["bartender_quest_log"] = r.i32()
    else:
        out["bartender_quest_log"] = 0
    if version >= 200:
        out["dead"] = r.bool_()
        out["respawn_timer"] = r.i32() if out["dead"] else 0
    else:
        out["dead"] = False
        out["respawn_timer"] = 0
    if version >= 202:
        out["last_time_player_was_saved"] = r.i64()
    else:
        out["last_time_player_was_saved"] = 0
    if version >= 206:
        out["golfer_score_accumulated"] = r.i32()
    else:
        out["golfer_score_accumulated"] = 0

    # Journey research (ItemsSacrificedUnlocksTracker): v282+ starts with one bool (ignored)
    if version >= 218:
        if version >= 282:
            r.u8()
        research_count = r.i32()
        out["research"] = [{"item": r.string(), "count": r.i32()} for _ in range(research_count)]
    else:
        out["research"] = []

    # Temporary item slots (4 building accessory slots): bits byte + 9B item per set bit
    if version >= 214:
        bits = r.u8()
        temp = []
        for i in range(4):
            if bits & (1 << i):
                temp.append(item9(r))
        out["temporary_slots"] = {"bits": bits, "items": temp}
    else:
        out["temporary_slots"] = {"bits": 0, "items": []}

    # Creative powers: loop of (bool has, u16 id, payload); ends with bool false
    powers = []
    if version >= 220:
        while True:
            has = r.u8()
            if not has:
                break
            pid = r.u16()
            if pid == 5:      # GodmodePower
                powers.append({"id": pid, "name": "godmode", "enabled": r.bool_()})
            elif pid == 11:   # FarPlacementRangePower
                powers.append({"id": pid, "name": "far_placement_range", "enabled": r.bool_()})
            elif pid == 14:   # SpawnRateSliderPerPlayerPower
                powers.append({"id": pid, "name": "spawn_rate_slider", "value": r.f32()})
            else:
                raise ValueError(f"unknown creative power id {pid} at offset {r.off}")
    out["creative_powers"] = powers

    if version >= 253:
        sc = r.u8()
        out["super_cart"] = {"unlocked": bool(sc & 1), "enabled": bool(sc & 2), "raw": sc}
    else:
        out["super_cart"] = {"unlocked": False, "enabled": False, "raw": 0}

    if version >= 262:
        out["current_loadout_index"] = r.i32()
        out["loadouts"] = []
        for _ in range(3):
            slots = [item9(r) for _ in range(20)]
            dyes = [item9(r) for _ in range(10)]
            hide = [r.bool_() for _ in range(10)]
            out["loadouts"].append({"slots": compact(slots), "dyes": compact(dyes), "hide": hide})
    else:
        out["current_loadout_index"] = 0
        out["loadouts"] = []

    if version >= 280:
        out["voice_variant"] = r.u8()
    else:
        out["voice_variant"] = 1 if out.get("male", True) else 2
    if version >= 281:
        out["voice_pitch_offset"] = r.f32()
    else:
        out["voice_pitch_offset"] = 0.0

    if version >= 300:
        n = r.i32()
        out["pending_refunds"] = [item9(r) for _ in range(n)]
    else:
        out["pending_refunds"] = []
    if version >= 310:
        n = r.i32()
        out["one_time_dialogues"] = [r.string() for _ in range(n)]
    else:
        out["one_time_dialogues"] = []

    out["parsed_offset"] = r.off
    out["plaintext_length"] = len(data)
    out["trailing_hex"] = data[r.off:].hex(" ") if r.off < len(data) else ""
    return out


def decrypt(path):
    fips197_self_test()
    key = "h3y_gUyZ".encode("utf-16-le")
    with open(path, "rb") as f:
        enc = f.read()
    if len(enc) % 16 != 0:
        raise ValueError(f"encrypted file length {len(enc)} is not a multiple of 16")
    return cbc_decrypt(enc, key, key)


# ---------------------------------------------------------------------------
# Names (all_id.md style: ### [ITEMS]/[BUFFS]/[PREFIXES] + `ID<TAB>name` lines)
# ---------------------------------------------------------------------------

def load_names(path):
    names = {"items": {}, "buffs": {}, "prefixes": {}}
    section = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("### ["):
                tag = line[5:-1].strip()
                if tag == "ITEMS":
                    section = "items"
                elif tag == "BUFFS":
                    section = "buffs"
                elif tag == "PREFIXES":
                    section = "prefixes"
                else:
                    section = None
                continue
            if section and "\t" in line and not line.lstrip().startswith("#"):
                try:
                    iid, name = line.split("\t", 1)
                    names[section][int(iid)] = name
                except ValueError:
                    pass
    return names


def fmt_name(names, section, iid):
    if iid == 0:
        return "空"
    if names and iid in names[section] and names[section][iid]:
        return names[section][iid]
    return f"[未知ID={iid}]"


# ---------------------------------------------------------------------------
# Human-readable Chinese summary
# ---------------------------------------------------------------------------

DIFF = {0: "经典", 1: "中核", 2: "硬核", 3: "旅途"}


def item_line(names, item, kind="inv"):
    if item["id"] == 0:
        return None
    name = fmt_name(names, "items", item["id"])
    prefix = item.get("prefix", 0)
    pfx = ""
    if prefix:
        pfx = "（" + fmt_name(names, "prefixes", prefix) + "）"
    if kind == "inv":
        fav = " [收藏]" if item.get("favorite") else ""
        return f"{name}{pfx} ×{item['count']}{fav}"
    return f"{name}{pfx}"


def build_text(out, names):
    lines = []
    lines.append(f"# {out['name']} 存档分析")
    lines.append("")
    lines.append(f"- 存档版本：{out['version']}（1.4.5.x）" if out["version"] >= 315 else f"- 存档版本：{out['version']}")
    lines.append(f"- 难度：{DIFF.get(out['difficulty'], out['difficulty'])}")
    secs = out["play_time_ticks"] / 10_000_000
    lines.append(f"- 游玩时长：{secs / 3600:.1f} 小时（{out['play_time_ticks']} ticks）")
    lines.append(f"- 生命/魔力：{out['health']}/{out['health_max']}，{out['mana']}/{out['mana_max']}")
    if "team" in out:
        lines.append(f"- PvP 队伍：{out['team']}")
    if out.get("skin_variant") is not None:
        gender = "男" if out["skin_variant"] <= 3 else "女"
        lines.append(f"- 皮肤变体：{out['skin_variant']}（{gender}）")
    lines.append(f"- 发型：{out['hair']}；发色：{out['colors']['hair']}")
    lines.append("")

    lines.append("## 永久强化")
    perms = ["ate_artisan_bread", "used_aegis_crystal", "used_aegis_fruit", "used_arcane_crystal",
             "used_galaxy_pearl", "used_gummy_worm", "used_ambrosia"]
    labels = ["工匠面包", "埃癸斯水晶", "埃癸斯果实", "奥术水晶", "银河珍珠", "软糖虫", "龙涎香"]
    on = [lab for lab, k in zip(labels, perms) if out.get(k)]
    lines.append("，".join(on) if on else "无")
    lines.append("")

    def section(title, items, kind="inv"):
        nonempty = [item_line(names, i, kind) for i in items]
        nonempty = [x for x in nonempty if x]
        lines.append(f"## {title}")
        lines.extend(nonempty if nonempty else ["（空）"])
        lines.append("")

    equip = out["equipment"]
    armor_labels = ["头盔", "胸甲", "护腿"] + [f"饰品{i}" for i in range(7)] + \
                   ["时装头", "时装身", "时装腿"] + [f"时装饰品{i}" for i in range(7)]
    eq_nonempty = []
    for i, item in enumerate(equip):
        if item["id"]:
            line = item_line(names, item, "equip")
            if line:
                eq_nonempty.append(f"{armor_labels[i] if i < len(armor_labels) else i}：{line}")
    lines.append("## 当前装备")
    lines.extend(eq_nonempty if eq_nonempty else ["（空）"])
    lines.append("")

    section("染料", out["dye"], "equip")
    section("主背包", out["inventory"])
    section("钱币", out["coins"])
    section("弹药", out["ammo"])
    misc_labels = ["宠物", "照明宠物", "矿车", "坐骑", "钩爪"]
    misc_nonempty = []
    for i, m in enumerate(out["misc"]):
        if m["equip"]["id"]:
            misc_nonempty.append(f"{misc_labels[i]}：{item_line(names, m['equip'], 'equip')}")
    lines.append("## 杂项装备")
    lines.extend(misc_nonempty if misc_nonempty else ["（空）"])
    lines.append("")
    section("猪猪存钱罐", out["piggy_bank"])
    section("保险箱", out["safe"])
    section("护卫熔炉", out["defenders_forge"])
    section("虚空袋", out["void_bag"])

    if out["loadouts"]:
        for idx, lo in enumerate(out["loadouts"], 1):
            lo_items = [item_line(names, i, "equip") for i in lo["slots"]]
            lo_items += [item_line(names, i, "equip") for i in lo.get("dyes", [])]
            lo_items = [x for x in lo_items if x]
            lines.append(f"## 配装 {idx}")
            lines.extend(lo_items if lo_items else ["（空）"])
            lines.append("")

    buff_nonempty = []
    for b in out["buffs"]:
        if b["id"]:
            name = fmt_name(names, "buffs", b["id"])
            buff_nonempty.append(f"{name}（剩余 {b['time_ticks'] / 60:.0f} 秒）")
    lines.append("## 当前增益")
    lines.extend(buff_nonempty if buff_nonempty else ["（无）"])
    lines.append("")

    lines.append("## 统计与状态")
    lines.append(f"- 钓鱼任务完成：{out['angler_quests_finished']}")
    lines.append(f"- 酒馆老板任务：{out['bartender_quest_log']}")
    lines.append(f"- 高尔夫得分：{out['golfer_score_accumulated']}")
    lines.append(f"- 死亡（PvE/PvP）：{out['deaths_pve']}/{out['deaths_pvp']}")
    lines.append(f"- 税钱：{out['tax_money']}")
    if out.get("super_cart", {}).get("raw"):
        sc = out["super_cart"]
        lines.append(f"- 超级矿车：已解锁={sc['unlocked']}，已启用={sc['enabled']}（原始 0x{sc['raw']:02x}）")
    if out["research"]:
        lines.append(f"- 旅途研究：{len(out['research'])} 项")
    if out["creative_powers"]:
        lines.append(f"- 创造模式权限：{len(out['creative_powers'])} 项")
    if out["one_time_dialogues"]:
        lines.append(f"- 一次性对话记录：{len(out['one_time_dialogues'])} 条")
    if out["trailing_hex"]:
        lines.append(f"- 尾部多余字节（1.4.5.6 读取时忽略）：{out['trailing_hex']}")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Decrypt and parse a Terraria .plr save (read-only)")
    ap.add_argument("input", help="path to .plr file")
    ap.add_argument("--names", help="path to all_id.md name library")
    ap.add_argument("--json", help="write parsed JSON to this file")
    ap.add_argument("--text", help="write Chinese summary to this file")
    args = ap.parse_args()

    pt = decrypt(args.input)
    out = parse_plr(pt)
    names = load_names(args.names) if args.names else None

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    text = build_text(out, names) if names else json.dumps(out, ensure_ascii=False, indent=2)
    if args.text:
        with open(args.text, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
