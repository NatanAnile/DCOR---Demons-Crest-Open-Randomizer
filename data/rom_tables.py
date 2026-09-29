"""Leitura da ROM do Demon's Crest (USA): endereço SNES -> arquivo e tabelas gráficas por área.

Listas por área: tile sets ($BD:9953), sprites ($81:AE11), meio de fase (tabela no operando de 80:BFB5) e segmentos
(operando de 80:C11B). Allocator = o empacotamento da VRAM de sprites do jogo (80:C2AF). Usado pelo planejamento de
gráfico dos itens (item_gfx.py, insanity_gfx.py).
"""
DIR_SETS = 0x98D000          # tile set: ptr24 + number of 16x16 units (4th byte)
TBL_TILES = 0xBD9953         # main tile set list per area (u16 until $FFFF)
TBL_SPR = 0x81AE11           # sprite list per area (id/palette pairs until 0)
TBL_FLAG = 0x81AD9D          # per-area flags
MID_OPERAND = 0x80BFB5       # LDA $xxxx,Y of the mid-stage loader (points at the mid-stage table)
SEG_OPERAND = 0x80C11B       # LDX $xxxx,Y of the segment loader (points at the segment table)
FIXED_SETS = ((0x08, 0xBD8480), (0x02, 0xBD8484), (0x04, 0xBD8488))   # order from 80:BF3D-BF61


def ea(a):
    return ((a >> 16) & 0x7F) * 0x8000 + ((a - 0x8000) & 0xFFFF)


class Rom:
    def __init__(self, path):
        self.b = bytes(path) if isinstance(path, (bytes, bytearray)) else open(path, 'rb').read()

    def u8(self, a): return self.b[ea(a)]
    def u16(self, a): o = ea(a); return self.b[o] | self.b[o + 1] << 8

    def units(self, tset): return self.u8(DIR_SETS + tset + 3)

    def tile_list(self, area):
        p, t = 0xBD0000 | self.u16(TBL_TILES + area * 2), []
        while self.u16(p) != 0xFFFF:
            t.append(self.u16(p)); p += 2
        return t

    def u16_list_until_zero(self, p):
        out = []
        while self.u16(p):
            out.append(self.u16(p)); p += 2
        return out

    def sprite_list(self, area):
        p, s = 0x810000 | self.u16(TBL_SPR + area * 2), []
        while self.u8(p):
            s.append((self.u8(p), self.u8(p + 1))); p += 2
        return s

    def mid(self, area):
        """(fixed bases, tile sets) of the mid-stage entry (format from 80:BFB9-C0ED)."""
        base_tbl = 0xBD0000 | self.u16(MID_OPERAND)
        p = 0xBD0000 | self.u16(base_tbl + area * 2)
        if self.u8(p) == 0:
            return [], []
        y, fixed, sets = 3, [], []
        while self.u8(p + y) >= 0x10:
            fixed.append(self.u8(p + y) * 16); y += 2
        if self.u8(p + y) != 0:
            y += 1
            sets = self.u16_list_until_zero(p + y)
        return fixed, sets

    def segments(self, area):
        """tile sets per pass of the segment loader (80:C112, table at the operand of 80:C11B): list of lists."""
        p = 0xBD0000 | self.u16((0xBD0000 | self.u16(SEG_OPERAND)) + area * 2)
        c = self.u8(p)
        if c == 0:
            return []
        n = self.u8(p + 1)
        q = p + 2 + 9 * c
        passes = []
        for _ in range(c + 1):
            passes.append([self.u16(q + 4 * k) for k in range(n)])
            q += 4 * n
        return passes


class Allocator:
    """Packing from 80:C2AF: every 16x16 unit advances $40 bytes, skipping the bottom tile row."""
    def __init__(self, rom, flag):
        self.rom, self.s = rom, 0x8000
        self.a0 = 0x60 if flag & 1 else 0
        for bit, list_ptr in FIXED_SETS:
            if flag & bit:
                self.load(rom.u16(list_ptr))

    def base(self): return ((self.s & 0x3FFF) >> 5) + self.a0

    def load(self, tset):
        for _ in range(self.rom.units(tset)):
            self.s += 0x40
            if self.s & 0x200:
                self.s += 0x200
