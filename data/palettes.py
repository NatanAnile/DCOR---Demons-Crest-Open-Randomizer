"""Paletas de sprite por área (quem ocupa cada slot antes e depois do meio de fase).

O 2º byte de cada entrada da lista de sprites da área é o slot de paleta (valor/2). Paletas por slot: lista da área
($81:8479, do slot 1 em diante, 80:A504) e, por cima, os pares [id, destino] do meio de fase (80:A6A0). Paleta de item
= a que o jogo original usa num slot de item em 2+ áreas (tabela $99:9100). Usado por insanity_gfx.py.
"""
from collections import Counter

import rom_tables as v

TBL_AREA_PAL = 0x818479
ITEMS = (0x4D, 0x4E, 0x4F, 0x50)


def area_palettes(rom, area):
    p, slots = 0x810000 | rom.u16(TBL_AREA_PAL + area * 2), {}
    while rom.u16(p):
        slots[len(slots) + 1] = rom.u16(p) // 32
        p += 2
    return slots


def mid_palettes(rom, area):
    base_tbl = 0xBD0000 | rom.u16(v.MID_OPERAND)
    p = 0xBD0000 | rom.u16(base_tbl + area * 2)
    if rom.u8(p) == 0:
        return {}
    y = 3
    while rom.u8(p + y) >= 0x10:
        y += 2
    if rom.u8(p + y) != 0:
        y += 1
        while rom.u16(p + y) != 0:
            y += 2
        y += 2
    else:
        y += 1
    return {rom.u8(p + y + 2 + 2 * k) // 0x20: rom.u8(p + y + 1 + 2 * k) for k in range(rom.u8(p + y))}


def states(rom, area):
    """(slots before the mid-stage, slots after)"""
    before = area_palettes(rom, area)
    after = dict(before)
    after.update(mid_palettes(rom, area))
    return before, after


def item_palettes(van):
    """palette vanilla puts on each item sprite's slot: {sid: Counter(id)} and the overall set."""
    per_sprite, overall = {}, Counter()
    for area in range(116):
        before, after = states(van, area)
        n_main = len(van.tile_list(area))
        for k, (sid, pal) in enumerate(van.sprite_list(area)):
            if sid not in ITEMS:
                continue
            slot = pal // 2
            pid = (before if k < n_main else after).get(slot)
            if pid is not None:
                per_sprite.setdefault(sid, Counter())[pid] += 1
                overall[pid] += 1
    return per_sprite, {pid for pid, n in overall.items() if n >= 2}
