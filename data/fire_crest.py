"""DCOR - crest inicial sorteada e Fire Crest como item (29/09, handoff do Neitan).

Com a opção "Randomizar Crest inicial":
  - o Firebrand começa SEM o tiro Fire: a arma 0 (Fire, tiro tipo 40) só atira com a Fire Crest;
  - começa com uma crest sorteada pelo gerador (nunca a Tornado). Buster, Claw e Demon Fire já saem escolhidas como
    arma; as de transformação (Earth/Air/Water/Time) ficam só ligadas: o jogador escolhe no menu para se transformar;
  - a Fire Crest vira item da pool: crest (objeto 48) de subtipo 10, com o desenho sem uso do sprite 4F (animação +00,
    quadro 1). Pegar liga FLAGS bit 0 (RAM livre, não o $1E51/$1E52: o $1E52 = FE é o final secreto e o bit 0100
    transforma toda crest em HP em 82:E9EE).
Ganchos (código no banco $C2):
  80:F222  entrada da criação do tiro (único chamador 80:EFDE): tipo 40 sem a Fire Crest -> sai por 80:F23C, o
           caminho "sem vaga livre" do próprio jogo (PLP / CLC / RTS), e nenhum tiro nasce
  82:EA08  LDA $D744,X (sprite do item)   82:EA17 LDA $D745,X (animação): subtipo 10 -> sprite 4F, animação 00
  82:EAA2  LDA $D730,X / TSB $1E51 (bit da crest pega): subtipo 10 -> FLAGS bit 0
  82:EAC2  LDA $D754,Y / STA $3B,X (texto da mensagem, banco $BE): subtipo 10 -> texto novo no banco $C2
  84:88E8  STZ $1E51 / STZ $1E52 do jogo novo: grava a crest inicial, zera FLAGS e escolhe a arma (como o menu, 84:8DBE)
"""
from asm65816 import Asm

BASE = 0xC28000
FLAGS = 0x7E1F92            # bit 0 = Fire Crest (DCOR); o resto livre (Head Butt vai aqui)
FIRE_SUB = 0x10
FIRE_ID = FIRE_SUB << 8 | 0x48
FIRE_TEXT = ['YOU GOT "FIRE CREST".', None, 'NOW YOU CAN', 'LIGHT TORCHES', 'AND DEAL BASIC DAMAGE']
# crest inicial -> (bits em $1E51, arma $1054, forma $1002). Arma None: fica a 0 (Fire) e sem transformar.
START = {'Buster': (0x01, 0x02, 0x00), 'Claw': (0x04, 0x06, 0x00), 'Demon Fire': (0x08, 0x08, 0x00),
         'Earth Crest': (0x10, None, None), 'Air Crest': (0x20, None, None), 'Water Crest': (0x40, None, None),
         'Time Crest': (0x80, None, None)}


def encode(lines):
    """Texto de mensagem do jogo: 02 = nova linha, 6A = espera botão e nova página (None), '.' é ']', 00 = fim."""
    out = bytearray()
    for i, ln in enumerate(lines):
        if ln is None:
            out.append(0x6A)
            continue
        if i and lines[i - 1] is not None:
            out.append(0x02)
        out += ln.replace('.', ']').encode('ascii')
    return bytes(out) + b'\x00'


def apply(rom, start):
    """rom: insanity_rom.Rom (4 MB, antes dos gráficos dos itens); start = nome da crest inicial."""
    bits, weapon, form = START[start]
    a = Asm(BASE)
    # --- tiro: A = [força][tipo] (80:EFD8-EFDB), 16 bits a partir daqui
    a.label('shot')
    a.op('PHP'); a.op('REP', 'imm8', 0x30); a.op('TAY')                      # o que 80:F222 fazia
    a.op('AND', 'imm16', 0x00FF); a.op('CMP', 'imm16', 0x0040); a.br('BNE', 'shot_ok')
    a.op('LDA', 'long', FLAGS); a.op('AND', 'imm16', 0x0001); a.br('BNE', 'shot_ok')
    a.op('JML', 'long', 0x80F23C)                                            # sem Fire Crest: nenhum tiro
    a.label('shot_ok')
    a.op('JML', 'long', 0x80F226)
    # --- sprite e animação do item (X = subtipo; largura de X/M do chamador preservada)
    for name, table, fire in (('d744', 0x81D744, 0x4F), ('d745', 0x81D745, 0x00)):
        a.label(name)
        a.op('PHP'); a.op('REP', 'imm8', 0x30)
        a.op('CPX', 'imm16', FIRE_SUB); a.br('BNE', name + '_n')
        a.op('LDA', 'imm16', fire); a.op('PLP'); a.op('RTL')
        a.label(name + '_n')
        a.op('LDA', 'longx', table); a.op('AND', 'imm16', 0x00FF); a.op('PLP'); a.op('RTL')
    # --- coleta: X 8 bits (SEP #$10 em 82:EA9E)
    a.label('bit')
    a.op('CPX', 'imm8', FIRE_SUB); a.br('BNE', 'bit_n')
    a.op('PHP'); a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'long', FLAGS); a.op('ORA', 'imm16', 0x0001); a.op('STA', 'long', FLAGS)
    a.op('PLP'); a.op('RTL')
    a.label('bit_n')
    a.op('LDA', 'absx', 0xD730); a.op('TSB', 'abs', 0x1E51); a.op('RTL')      # o original, na largura de M do jogo
    # --- mensagem: A/X/Y 16 bits (REP #$30 em 82:EAA8), X = objeto da caixa, Y = subtipo
    a.label('msg')
    a.op('CPY', 'imm16', FIRE_SUB); a.br('BNE', 'msg_n')
    a.op('LDA', 'imm16', 'text'); a.op('STA', 'absx', 0x003B)
    a.op('SEP', 'imm8', 0x20); a.op('LDA', 'imm8', BASE >> 16); a.op('STA', 'absx', 0x003D); a.op('REP', 'imm8', 0x20)
    a.op('RTL')
    a.label('msg_n')
    a.op('LDA', 'absy', 0xD754); a.op('STA', 'absx', 0x003B); a.op('RTL')
    # --- jogo novo: A/X 8 bits (84:8938 acabou de rodar SEP #$30 e zerar forma/arma)
    a.label('start')
    a.op('PHP'); a.op('SEP', 'imm8', 0x30)
    a.op('LDA', 'imm8', bits); a.op('STA', 'abs', 0x1E51); a.op('LDA', 'imm8', 0x00); a.op('STA', 'abs', 0x1E52)
    a.op('STA', 'long', FLAGS); a.op('STA', 'long', FLAGS + 1)
    if weapon is not None:                                                   # como o menu (84:8DBE)
        a.op('LDA', 'imm8', form); a.op('STA', 'abs', 0x1002)
        a.op('LDA', 'imm8', weapon); a.op('STA', 'abs', 0x1054)
        a.op('LSR', 'acc'); a.op('STA', 'abs', 0x1038)
        a.op('JSL', 'long', 0x80DF94)
    a.op('PLP'); a.op('RTL')
    a.label('text')
    a.b += encode(FIRE_TEXT)
    code = a.resolve()
    L = a.labels

    o = rom.off(BASE)
    assert not any(rom.b[o:o + len(code)]), 'banco $C2 não está vazio'
    rom.put(BASE, code)
    jsl = lambda t, n: bytes((0x22,) + t.to_bytes(3, 'little')) + b'\xEA' * (n - 4)
    for addr, want, lab, n, kind in ((0x80F222, '08c230a8', 'shot', 4, 'jml'),
                                     (0x82EA08, 'bd44d729ff00', 'd744', 6, 'jsl'),
                                     (0x82EA17, 'bd45d729ff00', 'd745', 6, 'jsl'),
                                     (0x82EAA2, 'bd30d70c511e', 'bit', 6, 'jsl'),
                                     (0x82EAC2, 'b954d79d3b00', 'msg', 6, 'jsl'),
                                     (0x8488E8, '9c511e9c521e', 'start', 6, 'jsl')):
        rom.expect(addr, bytes.fromhex(want))
        rom.put(addr, bytes((0x5C,) + L[lab].to_bytes(3, 'little')) if kind == 'jml' else jsl(L[lab], n))
    return [f'crest inicial: {start}; Fire Crest = item {FIRE_ID:04X}; código {BASE >> 16:02X}:{BASE & 0xFFFF:04X}-'
            f'{(BASE + len(code) - 1) & 0xFFFF:04X}']
