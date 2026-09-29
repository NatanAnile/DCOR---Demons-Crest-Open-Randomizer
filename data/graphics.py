"""Decoder for Demon's Crest sprite tile sets (port of 80:C2AF + 80:C300).

Tile set directory $98:D000 + id: 24-bit pointer + number of 16x16 units (4th byte).
Each C300 call: 2 mask bytes + 1 fill byte -> 16 bytes; every mask nibble (bits 3..0 = bytes 0..3 of the
group) says whether the byte comes from the stream or is the fill byte.
A 16x16 unit = 4 calls for the top row (tiles t, t+1) + 4 for the bottom row (t+16, t+17): 128 bytes.
"""
import rom_tables as v


class Stream:
    def __init__(self, rom, ptr):
        self.rom, self.bank, self.y = rom, ptr >> 16, ptr & 0xFFFF

    def byte(self):
        b = self.rom.u8((self.bank << 16) | self.y)
        self.y = (self.y + 1) & 0xFFFF
        if self.y == 0:                                  # 80:C345: next bank, back to $8000
            self.bank += 1
            self.y = 0x8000
        return b


def c300_call(f):
    m0, m1, fill = f.byte(), f.byte(), f.byte()
    out = bytearray()
    for mask_byte in (m0, m1):
        for nib in (mask_byte >> 4, mask_byte & 0xF):
            for bit in (8, 4, 2, 1):
                out.append(f.byte() if nib & bit else fill)
    return out


def units(rom, tset):
    """list of 16x16 units; each one = (tile t, t+1, t+16, t+17), 32 bytes per tile."""
    ptr = rom.u16(v.DIR_SETS + tset) | rom.u8(v.DIR_SETS + tset + 2) << 16
    n = rom.u8(v.DIR_SETS + tset + 3)
    f = Stream(rom, ptr)
    out = []
    for _ in range(n):
        top = b''.join(c300_call(f) for _ in range(4))
        bottom = b''.join(c300_call(f) for _ in range(4))
        out.append((top[:32], top[32:], bottom[:32], bottom[32:]))
    return out
