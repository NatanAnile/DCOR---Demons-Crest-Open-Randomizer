# Cópia de DemonsCrest Editor/chefes.py (28/09): o DCOR usa pra aplicar os patches de mapa do anti-softlock.
# A fonte é a do editor; se ela mudar, copiar de novo.
"""Chefes e eventos de área do Demon's Crest (US): vida, drop, portão do chefe e saída da área. Só biblioteca padrão.

Tudo aqui foi conferido na ROM US (27/09):
- Vida = byte $36 do objeto (82:8901 faz vida -= dano; FF = não apanha). Onde cada chefe grava: sonda que roda a
  rotina de início + 300 quadros de cada chefe na área dele (SpawnSim, DB = $81) e anota a escrita em $36 — e o
  código desmontado em volta confere (operando de LDA/LDX #n, ou tabela lida com o subtipo). O Crawler não grava
  nesse intervalo (a mapear).
- Trio the Pago (96) NÃO é chefe: é minigame (MINIGAMES). Entra aqui só pelo prêmio (HP 0C, BC:A13E).
- Drop = operando de LDA #id antes de JSL 82:877B (cria) / 82:87E9 (o chefe vira o item); Arma 1/2 lê a tabela
  $81:F0A2; Crawler e Grewon montam o id com LDA #sub / XBA / LDA #tipo.
- Quem encerra a área é o ITEM, não o chefe: toda crest (82:EA93) e HP de subtipo 0-4, 6 ou 1F (82:EB20: CMP #5 / CMP #7 /
  CMP #$1F; o bit $40 "parado" já foi limpo em 82:EA88)
  vão pro estado 2 (82:EB7C: fanfarra, mensagem) → 80:BB58 → próxima área = $81:97DA[área] (1 byte, áreas 0-63;
  < $F0 = área*2; $F0-$FF = mapa-múndi, $0EA6 = valor & $0F).
- Portão do chefe (80:A45F, ao chegar no chefe): $81:80A1[área] → ponteiro no banco $81 pra [índice][máscara]; se
  $1E51+índice tem a máscara, o chefe é pulado. $FFFF = sem portão. Tabela das áreas 0-63.
"""
import struct

# ---------------------------------------------------------------- itens (id = tipo | subtipo << 8)
ITEMS = {}
for k, n in enumerate(('Buster', 'Tornado', 'Claw', 'Demon Fire', 'Earth Crest', 'Air Crest', 'Water Crest',
                       'Time Crest')):
    ITEMS[k * 2 << 8 | 0x48] = n
for k in range(1, 17):
    ITEMS[k << 8 | 0x49] = 'HP %02X' % k
ITEMS[0x1F49] = 'HP sem flag (recarga)'
for k in range(5):
    ITEMS[k * 2 << 8 | 0x2D] = 'Vellum %02X' % (k * 2)
    ITEMS[(0x0A + k * 2) << 8 | 0x2D] = 'Potion %02X' % (0x0A + k * 2)
for k, n in enumerate(('Crown', 'Skull', 'Armor', 'Fang', 'Hand')):
    ITEMS[k * 2 << 8 | 0x2E] = 'talismã ' + n
for sub, n in ((0, '20G'), (2, '5G'), (4, '1G'), (6, 'recarga total'), (8, '+2 HP'), (0x0A, '+1 HP')):
    ITEMS[sub << 8 | 0x23] = n


def item_name(i):
    """nome do item; bit $40 do subtipo = parado (não quica: 82:EA82 limpa o bit e põe o estado 4)."""
    base = i & 0xBFFF
    return ITEMS.get(base, 'id %04X' % base) + (' (parado)' if i & 0x4000 else '')


def ends_area(i):
    """o item encerra a área ao ser pego: crest, ou HP de subtipo 0-4/6 — o teste (82:EB20) vê o subtipo já sem o
    bit $40 (82:EA88 TRB $03)."""
    t, s = i & 0xFF, i >> 8 & 0x3F
    return t == 0x48 or (t == 0x49 and (s < 7 and s != 5 or s == 0x1F))   # 1F = HP sem flag (82:EB2A; Flier 2)


# ---------------------------------------------------------------- chefes: (tipo, variante) → onde fica cada valor
# variante = subtipo & $7F (o bit 7 é do spawner). vida: [(endereço, bytes esperados antes, depois)] — o valor é o
# byte no endereço; o contexto confere que a ROM tem o código original ali.
BOSS_NAMES = {0x09: 'Hippogriff', 0x13: 'Grewon', 0x1A: 'Crawler', 0x28: 'Flame Lord', 0x33: 'Somulo',
              0x52: 'Somulo (cabeça)', 0x6B: 'Ovnunu', 0x6F: 'Holothurion', 0x74: 'Belth', 0x7B: 'Skulla',
              0x82: 'Flier', 0xA5: 'Arma'}
MINIGAMES = {0x96: 'Trio the Pago'}      # não é chefe
VARIANT_NAMES = {(0x09, 0): 'Hippogriff 1', (0x09, 2): 'Hippogriff 2', (0x09, 4): 'Hippogriff 3',
                 (0xA5, 0): 'Arma 1', (0xA5, 2): 'Arma 2', (0xA5, 4): 'Arma 3',
                 (0x82, 0): 'Flier 1', (0x82, 1): 'Flier 2', (0x13, 0): 'Grewon 1', (0x13, 2): 'Grewon 2'}


def imm(addr, op, after=None):           # operando de LDA/LDX #n (8 bits) seguido de STA/STX $36 (ou BRA pro STA)
    return (addr, op, after or (0x85 if op == 0xA9 else 0x86))


SITES = {
    (0x09, 0): {'vida': [imm(0x829967, 0xA9, 0x80)], 'drop': ('word', [0x829999])},     # BRA → 82:9985 STA $36
    (0x09, 2): {'vida': [imm(0x82997C, 0xA9, 0x80)], 'drop': ('word', [0x8299A7])},
    (0x09, 4): {'vida': [imm(0x829984, 0xA9)], 'drop': ('word', [0x8299A7])},
    (0xA5, 0): {'vida': [(0x81F066, None, None)], 'drop': ('tab', [0x81F0A2])},
    (0xA5, 2): {'vida': [(0x81F067, None, None)], 'drop': ('tab', [0x81F0A4])},
    (0xA5, 4): {'vida': [(0x81F068, None, None)], 'drop': ('word', [0x82F009])},
    (0x82, 0): {'vida': [(0x81EDF5, None, None)], 'drop': ('word', [0x85DBA0, 0x85EF1F])},
    (0x82, 1): {'vida': [(0x81EDF6, None, None)], 'drop': ('word', [0x85DBA7, 0x85EF26])},
    (0x6B, 0): {'vida': [imm(0x83BFAA, 0xA9)], 'drop': ('word', [0x83C6D4])},
    (0x74, 0): {'vida': [imm(0x83E735, 0xA2)], 'drop': ('word', [0x83E8D8])},
    (0x7B, 0): {'vida': [imm(0xBD8522, 0xA2)], 'drop': ('word', [0xBD85AD, 0xBD8B99])},
    (0x28, 0): {'vida': [imm(0x82CBFB, 0xA9), imm(0x82CC73, 0xA9)], 'drop': ('word', [0x82CCFD])},
    (0x6F, 0): {'vida': [imm(0x83D37D, 0xA9)], 'drop': ('word', [0x83D7B7])},
    (0x13, 0): {'vida': [imm(0xBE980C, 0xA9)], 'drop': ('xba', 0xBE9E23, 0xBE9E26)},
    (0x13, 2): {'vida': [imm(0xBE980C, 0xA9)], 'drop': ('xba', 0xBE9E23, 0xBE9E34)},
    (0x1A, 0): {'vida': [], 'drop': ('xba', 0x82BA12, 0x82BA15)},
    (0x33, 0): {'vida': [imm(0x838A3D, 0xA9)], 'drop': None},
    (0x52, 0): {'vida': [imm(0x8397BE, 0xA9)], 'drop': ('word', [0x8396D3])},
    (0x96, 0): {'vida': [], 'drop': ('word', [0xBCA13E])},
}
VIDA_LABELS = {(0x28, 0): ('1ª fase', '2ª fase')}
NOTES = {
    (0x09, 2): 'o drop é o mesmo código do Hippogriff 3 (82:99A7): vale pros dois',
    (0x09, 4): 'o drop é o mesmo código do Hippogriff 2 (82:99A7): vale pros dois',
    (0x13, 0): 'a vida e o subtipo do drop são os mesmos do Grewon 2 (BE:980C / BE:9E23)',
    (0x13, 2): 'a vida e o subtipo do drop são os mesmos do Grewon 1; o tipo é o 2º LDA (BE:9E34)',
    (0xA5, 4): 'o drop do Arma 3 é o objeto 4F que vira a crest (82:F009)',
    (0x1A, 0): 'vida ainda não mapeada (não grava $36 nos primeiros 300 quadros)',
    (0x33, 0): 'a luta da área 0 não solta item (o HP 01 sai da cabeça, área 17)',
}


def key_of(i):
    """(tipo, variante) de um id de objeto com dados (chefe ou minigame); partes/variantes que dividem o código
    (Crawler, Trio etc.) = variante 0."""
    t, v = i & 0xFF, i >> 8 & 0x7F
    if t in (0x1A, 0x96, 0x33, 0x52, 0x6B, 0x6F, 0x74, 0x7B, 0x28):
        v = 0
    return (t, v) if (t, v) in SITES else None


def boss_label(key):
    return VARIANT_NAMES.get(key) or BOSS_NAMES.get(key[0]) or MINIGAMES.get(key[0], '%02X' % key[0])


def kind(key):
    return 'minigame' if key[0] in MINIGAMES else 'chefe'


def _o(a):
    return (a >> 16 & 0x7F) * 0x8000 + (a & 0x7FFF)


def site_ok(d, key):
    """[problemas] se o código em volta não é o original (ROM modificada, ex. rando com desvio)."""
    bad = []
    for a, op, st in SITES[key]['vida']:
        if op is not None and (d[_o(a) - 1] != op or d[_o(a) + 1] != st or (st != 0x80 and d[_o(a) + 2] != 0x36)):
            bad.append('vida em %06X' % a)
    spec = SITES[key]['drop']
    if spec and spec[0] == 'word':
        for a in spec[1]:
            if d[_o(a) - 1] != 0xA9:
                bad.append('drop em %06X' % a)
    elif spec and spec[0] == 'xba':
        if d[_o(spec[1]) - 1] != 0xA9 or d[_o(spec[1]) + 1] != 0xEB or d[_o(spec[2]) - 1] != 0xA9:
            bad.append('drop em %06X' % spec[1])
    return bad


def read(d, key):
    """{'vida': [valores], 'drop': id ou None}."""
    s = SITES[key]
    out = {'vida': [d[_o(a)] for a, _, _ in s['vida']], 'drop': None}
    spec = s['drop']
    if spec and spec[0] in ('word', 'tab'):
        out['drop'] = struct.unpack_from('<H', d, _o(spec[1][0]))[0]
    elif spec:
        out['drop'] = d[_o(spec[1])] << 8 | d[_o(spec[2])]
    return out


def write(d, key, vals):
    """grava vida (lista) e drop no bytearray d."""
    s = SITES[key]
    for (a, _, _), v in zip(s['vida'], vals.get('vida', [])):
        if not 1 <= v <= 0xFE:
            raise ValueError('vida %d fora de 1-254 (FF = não apanha)' % v)
        d[_o(a)] = v
    spec, i = s['drop'], vals.get('drop')
    if spec and i is not None:
        if spec[0] in ('word', 'tab'):
            for a in spec[1]:
                struct.pack_into('<H', d, _o(a), i)
        else:
            d[_o(spec[1])], d[_o(spec[2])] = i >> 8, i & 0xFF


def shared(key):
    """outras chaves que dividem algum endereço com esta (mudar uma muda a outra)."""
    def addrs(k):
        s = SITES[k]
        a = {x for x, _, _ in s['vida']}
        if s['drop']:
            a |= set(s['drop'][1]) if s['drop'][0] in ('word', 'tab') else {s['drop'][1], s['drop'][2]}
        return a
    mine = addrs(key)
    return [k for k in SITES if k != key and addrs(k) & mine]


# ---------------------------------------------------------------- área: saída e portão do chefe
N_EVENT_AREAS = 64
GATE_TAB, GATE_NONE, EXIT_TAB = 0x8180A1, 0x818121, 0x8197DA
GATE_IDX = {0: 'crest', 2: 'talismã', 3: 'HP 01-08', 4: 'HP 09-10'}


def gate_name(g):
    if g is None:
        return 'nenhum'
    idx, mask = g
    if idx == 0:
        names = [n for k, n in enumerate(('Buster', 'Tornado', 'Claw', 'Demon Fire', 'Earth Crest', 'Air Crest',
                                          'Water Crest', 'Time Crest')) if mask >> k & 1]
        return 'tem ' + ' ou '.join(names)
    if idx in (3, 4):
        return 'tem ' + ' ou '.join('HP %02X' % ((idx - 3) * 8 + k + 1) for k in range(8) if mask >> k & 1)
    return '$1E%02X & %02X' % (0x51 + idx, mask)


GATE_CHOICES = [None] + [(0, 1 << k) for k in range(8)] + [(3, 1 << k) for k in range(8)] + \
               [(4, 1 << k) for k in range(8)]


def gate_read(d, a):
    p = struct.unpack_from('<H', d, _o(GATE_TAB + a * 2))[0]
    v = struct.unpack_from('<H', d, _o(0x810000 | p))[0]
    return None if v == 0xFFFF else (v & 0xFF, v >> 8)


def gate_write(d, a, g):
    """aponta o portão da área pra 2 bytes [índice][máscara] que já existam no banco $81 (o jogo só lê; o banco
    não tem espaço livre) — primeiro os registros de portão do jogo ($8123-$8138), depois o banco todo."""
    if g is None:
        target = GATE_NONE
    else:
        pat = bytes(g)
        b0 = _o(0x818000)
        k = d.find(pat, _o(0x818123), _o(0x818139))
        if k < 0:
            k = d.find(pat, b0, b0 + 0x8000)
        if k < 0:
            raise ValueError('portão %s: não achei os bytes %s no banco $81' % (gate_name(g), pat.hex()))
        target = 0x810000 | 0x8000 + k - b0
    struct.pack_into('<H', d, _o(GATE_TAB + a * 2), target & 0xFFFF)


def gate_users(d, a):
    """áreas que apontam pro mesmo registro de portão (o original é compartilhado, ex. 14/50/51)."""
    p = struct.unpack_from('<H', d, _o(GATE_TAB + a * 2))[0]
    return [b for b in range(N_EVENT_AREAS) if struct.unpack_from('<H', d, _o(GATE_TAB + b * 2))[0] == p]


def exit_read(d, a):
    return d[_o(EXIT_TAB + a)]


def exit_write(d, a, v):
    d[_o(EXIT_TAB + a)] = v


def exit_name(v):
    if v >= 0xF0:
        return 'mapa-múndi ($0EA6 = %d)' % (v & 0x0F)
    return 'área %d' % (v // 2)


EXIT_CHOICES = [a * 2 for a in range(113)] + list(range(0xF0, 0xF6))
