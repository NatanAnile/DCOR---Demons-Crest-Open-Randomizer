"""Minimal 65816 assembler for the item patch (only what the patch uses).

Usage: a = Asm(origin); a.op('LDA', 'imm16', 0x1234); a.label('x'); a.br('BNE', 'x'); a.resolve() ...
Immediate size is explicit (imm8/imm16): the assembler does not track REP/SEP.
"""

OPC = {
    ('PHP', 'imp'): 0x08, ('PLP', 'imp'): 0x28, ('PHA', 'imp'): 0x48, ('PLA', 'imp'): 0x68,
    ('PHB', 'imp'): 0x8B, ('PLB', 'imp'): 0xAB, ('PHX', 'imp'): 0xDA, ('PLX', 'imp'): 0xFA,
    ('PHY', 'imp'): 0x5A, ('PLY', 'imp'): 0x7A, ('CLC', 'imp'): 0x18, ('SEC', 'imp'): 0x38,
    ('ASL', 'acc'): 0x0A, ('DEC', 'acc'): 0x3A, ('XBA', 'imp'): 0xEB, ('TAX', 'imp'): 0xAA,
    ('TAY', 'imp'): 0xA8, ('TXA', 'imp'): 0x8A, ('TYA', 'imp'): 0x98, ('INX', 'imp'): 0xE8,
    ('RTL', 'imp'): 0x6B, ('RTS', 'imp'): 0x60, ('INC', 'acc'): 0x1A, ('INY', 'imp'): 0xC8,
    ('JSR', 'abs'): 0x20, ('LDY', 'imm16'): 0xA0, ('LDX', 'imm16'): 0xA2, ('LSR', 'acc'): 0x4A, ('ADC', 'long'): 0x6F, ('STA', 'longx'): 0x9F,
    ('CMP', 'imm8'): 0xC9,
    ('REP', 'imm8'): 0xC2, ('SEP', 'imm8'): 0xE2,
    ('LDA', 'imm8'): 0xA9, ('LDA', 'imm16'): 0xA9, ('LDA', 'dp'): 0xA5, ('LDA', 'abs'): 0xAD,
    ('LDA', 'absy'): 0xB9, ('LDA', 'long'): 0xAF, ('LDA', 'longx'): 0xBF,
    ('STA', 'dp'): 0x85, ('STA', 'abs'): 0x8D, ('STA', 'absy'): 0x99, ('STA', 'long'): 0x8F,
    ('STA', 'sr'): 0x83,
    ('AND', 'imm8'): 0x29, ('AND', 'imm16'): 0x29, ('ORA', 'imm8'): 0x09, ('ORA', 'imm16'): 0x09,
    ('TSB', 'abs'): 0x0C, ('CMP', 'imm16'): 0xC9, ('CMP', 'long'): 0xCF,
    ('ADC', 'imm16'): 0x69, ('ADC', 'longx'): 0x7F, ('SBC', 'imm16'): 0xE9, ('EOR', 'imm16'): 0x49,
    ('TYX', 'imp'): 0xBB,
    ('CPX', 'imm8'): 0xE0, ('CPX', 'imm16'): 0xE0, ('CPY', 'imm16'): 0xC0, ('LDA', 'absx'): 0xBD,
    ('STA', 'absx'): 0x9D, ('AND', 'long'): 0x2F, ('ORA', 'long'): 0x0F,
    ('STZ', 'abs'): 0x9C, ('PHD', 'imp'): 0x0B, ('PLD', 'imp'): 0x2B, ('TCD', 'imp'): 0x5B,
    ('JML', 'long'): 0x5C, ('JSL', 'long'): 0x22,
    ('BEQ', 'rel'): 0xF0, ('BNE', 'rel'): 0xD0, ('BCC', 'rel'): 0x90, ('BCS', 'rel'): 0xB0,
    ('BRA', 'rel'): 0x80, ('BRL', 'rell'): 0x82,
}
SIZE = {'imp': 0, 'acc': 0, 'imm8': 1, 'imm16': 2, 'dp': 1, 'abs': 2, 'absy': 2, 'absx': 2, 'long': 3, 'longx': 3,
       'sr': 1, 'rel': 1, 'rell': 2}


class Asm:
    def __init__(self, origin):
        self.origin, self.b, self.labels, self.fix = origin, bytearray(), {}, []

    def pc(self): return self.origin + len(self.b)

    def label(self, name): self.labels[name] = self.pc()

    def op(self, mn, mode='imp', arg=0):
        self.b.append(OPC[(mn, mode)])
        n = SIZE[mode]
        if isinstance(arg, str) and mn == 'JSR':
            self.fix.append((len(self.b), 2, arg, 'abs16'))
            self.b += bytes(2)
        elif isinstance(arg, str):
            self.fix.append((len(self.b), n, arg, mode))
            self.b += bytes(n)
        else:
            self.b += (arg & ((1 << (8 * n)) - 1)).to_bytes(n, 'little') if n else b''

    def br(self, mn, target): self.op(mn, 'rel', target)

    def mvn(self, dest, src): self.b += bytes([0x54, dest, src])

    def resolve(self):
        for pos, n, name, mode in self.fix:
            target = self.labels[name]
            if mode == 'rel':
                d = target - (self.origin + pos + 1)
                if not -128 <= d <= 127:
                    raise ValueError('branch out of range: ' + name)
                self.b[pos] = d & 0xFF
            elif mode == 'rell':
                d = target - (self.origin + pos + 2)
                self.b[pos:pos + 2] = (d & 0xFFFF).to_bytes(2, 'little')
            else:                                  # abs16 (JSR) and long: low bytes of the address
                self.b[pos:pos + n] = (target & ((1 << (8 * n)) - 1)).to_bytes(n, 'little')
        return bytes(self.b)
