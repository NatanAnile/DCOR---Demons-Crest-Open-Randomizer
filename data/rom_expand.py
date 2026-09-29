"""Expand a Demon's Crest (USA) ROM from 2 MB to 4 MB without triggering the anti-piracy checks.

Why a plain expansion breaks the game: two anti-piracy checks compare a header byte read through the normal
bank with the same byte read through the mirror bank $40:
    82:9B33  LDA $80FFC0 / CMP $40FFC0 / BEQ +  / LDA #$FF / STA $0EED   -> pause disabled (read at 84:8A3B)
    BE:E356  LDA $80FFC1 / CMP $40FFC1 / BEQ +  / LDA #$FF / STA $0EEE   -> enemies take no damage (82:88FB)
On a 2 MB LoROM, $40:FFC0 mirrors the header, so they match. On 4 MB, bank $40 maps to the new half and
they don't. Fix: change the CMP bank from $40 to $80 (the header is compared with itself). 2 bytes.
The two SRAM checks (80:875A, 80:E561) don't depend on the ROM size and are left alone.

Usage: python rom_expand.py INPUT.sfc [OUTPUT.sfc]      (default output: "<input> - 4MB.sfc")
Works on the vanilla ROM and on randomizer output; running it on an already expanded ROM changes nothing.
"""
import re
import sys

SIZE_2MB, SIZE_4MB = 0x200000, 0x400000
HEADER = 0x7FC0                      # LoROM internal header
ROM_SIZE_BYTE = HEADER + 0x17        # $0B = 2 MB, $0C = 4 MB
CHECKSUM = HEADER + 0x1C             # complement (2 B) + checksum (2 B)

# LDA $80:FFxx / CMP $40:FFxx (same xx) / BEQ +6 / LDA #$FF
CHECK = re.compile(rb'\xAF(.)\xFF\x80\xCF\1\xFF([\x40\x80])\xF0\x06\xA9\xFF', re.S)


def fix_checksum(rom):
    rom[CHECKSUM:CHECKSUM + 4] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    c = s ^ 0xFFFF
    rom[CHECKSUM:CHECKSUM + 4] = bytes([c & 0xFF, c >> 8, s & 0xFF, s >> 8])


def expand(rom, fill=0x00):
    """Returns the 4 MB ROM and a list of report lines. Raises ValueError if the ROM doesn't look right."""
    rom = bytearray(rom)
    if len(rom) % 0x8000 == 512:
        rom = rom[512:]              # strip copier header
    if len(rom) not in (SIZE_2MB, SIZE_4MB):
        raise ValueError('unexpected ROM size: %d bytes' % len(rom))

    matches = list(CHECK.finditer(rom[:SIZE_2MB]))
    if len(matches) != 2:
        raise ValueError('expected 2 anti-piracy checks, found %d (not a Demon\'s Crest USA ROM?)' % len(matches))
    report = []
    for m in matches:
        pos = m.start() + 7          # bank byte of the CMP operand
        snes = '%02X:%04X' % (0x80 | (m.start() >> 15), 0x8000 | (m.start() & 0x7FFF))
        if rom[pos] == 0x40:
            rom[pos] = 0x80
            report.append('patched check at %s (file 0x%06X): CMP bank $40 -> $80' % (snes, pos))
        else:
            report.append('check at %s already patched' % snes)

    if len(rom) == SIZE_2MB:
        rom += bytes([fill]) * (SIZE_4MB - SIZE_2MB)
        report.append('expanded 2 MB -> 4 MB (new half filled with $%02X, free from $C0:8000 / file 0x200000)' % fill)
    rom[ROM_SIZE_BYTE] = 0x0C
    fix_checksum(rom)
    report.append('header ROM size = $0C, checksum = $%04X' % (rom[CHECKSUM + 2] | rom[CHECKSUM + 3] << 8))
    return rom, report


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else re.sub(r'\.(sfc|smc)$', '', src, flags=re.I) + ' - 4MB.sfc'
    with open(src, 'rb') as f:
        rom, report = expand(f.read())
    with open(dst, 'wb') as f:
        f.write(rom)
    for line in report:
        print(line)
    print('written:', dst)


if __name__ == '__main__':
    main()
