"""Insanity Randomizer - grava a distribuição de itens na ROM (código nosso, do zero).

Usado por insanity_rando.py (--rom). A ROM sai com 4 MB (conserto da antipirataria, rom_expand.py, cópia da
ferramenta validada em DemonsCrest Editor/ferramentas/rom_expand): a metade nova ($C0:8000+) guarda a tabela nova de potes e os desvios.
Toda escrita confere o valor original antes de trocar (AssertionError = ROM diferente da esperada).
Endereços e formatos: DOCUMENTACAO - Randomizer.md §3.
"""
import os

from rom_expand import expand, fix_checksum
import fire_crest
import insanity_gfx

ITEM_TYPES = (0x2D, 0x2E, 0x48, 0x49)
POT_TABLE = 0xC08000        # conteúdo do pote por subtipo (cópia da $81:D85C + entradas novas)
POT_OLD = 0x81D85C
POT_OLD_LEN = 0x14          # subtipos 00-12 do original, mantidos (potes fora da pool continuam iguais)
CODE = 0xC08100

# Onde cada check é gravado. Tipos:
#   obj  (x, y, id original)            registro na lista de objetos ($81:C874 e $81:C9D0), em qualquer área
#   pot  (áreas, x, y, id original)     pote: ganha subtipo próprio na tabela nova
#   word (endereços, id original)       id de 16 bits (operando LDA #, tabela) - todos recebem o mesmo item
#   xba  (end. subtipo, end. tipo, id)  LDA #sub / XBA / LDA #tipo
#   bell (endereço, id original)        LDX #pote do sino: grava um pote com subtipo próprio
#   hippo / grewon                      desvio (o mesmo código atende outras áreas, que continuam iguais)
SLOTS = {
    'Trio the Pago': ('word', [0xBCA13E], 0x4C49),
    'Somulo (cabeça)': ('word', [0x8396D3], 0x0149),
    'Pote 20G área 1': ('pot', [1], 392, 376, 0x0257),
    'Estátua Vellum 00': ('word', [0x81B4FD], 0x002D),
    'Hippogriff 1': ('word', [0x829999], 0x0249),
    'Potion 0A': ('obj', 1624, 392, 0x4A2D),
    'HP 07 chão': ('obj', 432, 440, 0x4749),
    'Pote recarga fase 1': ('pot', [1], 1640, 408, 0x0457),
    'Arma 1': ('word', [0x81F0A2], 0x0848),
    'Potion 0C': ('obj', 1304, 424, 0x4C2D),
    'Hand': ('obj', 1960, 424, 0x482E),
    'Pote Vellum 02': ('pot', [6], 456, 328, 0x0657),
    'Pote HP 08': ('pot', [7], 56, 424, 0x0857),
    'HP 0A pós-Flame Lord': ('obj', 560, 240, 0x4A49),
    'Pote recarga área 7': ('pot', [7], 912, 424, 0x0457),
    'Pote 20G área 6': ('pot', [6], 472, 536, 0x0257),
    'Ovnunu': ('word', [0x83C6D4], 0x4048),
    'Ossos HP 09': ('word', [0x81B509], 0x0949),
    'Belth': ('word', [0x83E8D8], 0x0349),
    'Pote 20G área 10 a': ('pot', [10], 472, 104, 0x0257),
    'Pote 20G área 10 b': ('pot', [10], 784, 360, 0x0257),
    'Pote 20G área 10 c': ('pot', [10], 840, 104, 0x0257),
    'Potion 0E': ('obj', 1133, 200, 0x4E2D),
    'Pote recarga área 11': ('pot', [11], 560, 426, 0x0457),
    'Pote Vellum 04': ('pot', [11], 1480, 88, 0x0A57),
    'Skulla': ('word', [0xBD85AD, 0xBD8B99], 0x0449),
    'Pote 20G área 13 a': ('pot', [13], 472, 216, 0x0257),
    'Pote 20G área 13 b': ('pot', [13], 536, 280, 0x0257),
    'Pote 20G área 13 c': ('pot', [13], 632, 328, 0x0257),
    'Pote 20G área 13 d': ('pot', [13], 712, 232, 0x0257),
    'Pote 20G área 13 e': ('pot', [13], 808, 264, 0x0257),
    'Pote recarga área 14': ('pot', [14, 50, 51], 1528, 216, 0x0457),
    'Flame Lord': ('word', [0x82CCFD], 0x4248),
    'Pote HP 0B': ('pot', [15], 256, 170, 0x0C57),
    'Skull': ('obj', 208, 170, 0x422E),
    'Potion 10': ('obj', 536, 408, 0x502D),
    'Pote 20G área 18': ('pot', [18], 40, 296, 0x0257),
    'Pote recarga área 19': ('pot', [19], 1656, 120, 0x0457),
    'Flier 1': ('word', [0x85DBA0, 0x85EF1F], 0x0448),
    'Hippogriff 2': ('hippo',),
    'Crown': ('word', [0x81B505], 0x002E),
    'Vellum 06': ('obj', 440, 264, 0x462D),
    'Arma 2': ('word', [0x81F0A4], 0x0A48),
    'Pote HP 0D': ('pot', [25], 56, 472, 0x0E57),
    'Holothurion': ('word', [0x83D7B7], 0x4649),
    'Crawler': ('xba', 0x82BA12, 0x82BA15, 0x0C48),
    'Estátua HP 0E': ('word', [0x81B50D], 0x0E49),
    'Estátua HP 05': ('word', [0x81B50B], 0x0549),
    'Potion 12': ('obj', 152, 56, 0x522D),
    'Ossos Vellum 08': ('word', [0x81B50F], 0x082D),
    'Pote recarga área 30': ('pot', [30], 1144, 408, 0x0457),
    'Grewon': ('grewon',),
    'Pote HP 0F': ('pot', [32], 456, 184, 0x1057),
    'Flier 2': ('word', [0x85DBA7, 0x85EF26], 0x1F49),
    'Armor': ('word', [0x81B511], 0x042E),
    'Arma 3': ('word', [0x82F009], 0x4E48),
    'Sino HP 10': ('bell', 0xBEFA01, 0x1257),
    'Fang': ('obj', 1960, 440, 0x462E),
}

# id de cada item do jogo original (o gerador trabalha por categoria; aqui cada categoria vira ids concretos)
VANILLA_IDS = {
    'HP': [0x0149, 0x0249, 0x0349, 0x0449, 0x0549, 0x0649, 0x0749, 0x0849, 0x0949, 0x0A49, 0x0B49, 0x0C49,
           0x0D49, 0x0E49, 0x0F49, 0x1049],
    'Vellum': [0x002D, 0x022D, 0x042D, 0x062D, 0x082D],
    'Potion': [0x0A2D, 0x0C2D, 0x0E2D, 0x102D, 0x122D],
    'Crown': [0x002E], 'Skull': [0x022E], 'Armor': [0x042E], 'Fang': [0x062E], 'Hand': [0x082E],
    'Buster': [0x0048], 'Tornado': [0x0248], 'Claw': [0x0448], 'Demon Fire': [0x0648],
    'Earth Crest': [0x0848], 'Air Crest': [0x0A48], 'Water Crest': [0x0C48], 'Time Crest': [0x0E48],
    'Fire Crest': [0x1048],                     # item novo do DCOR (fire_crest.py), só com a crest inicial sorteada
}
FILLER_IDS = {'20G': 0x0023, 'Recarga': 0x0623}


class Rom:
    def __init__(self, data):
        self.b = bytearray(data)

    @staticmethod
    def off(a):
        return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)

    def u8(self, a):
        return self.b[self.off(a)]

    def u16(self, a):
        o = self.off(a)
        return self.b[o] | self.b[o + 1] << 8

    def put(self, a, data):
        o = self.off(a)
        self.b[o:o + len(data)] = bytes(data)

    def put16(self, a, v, expect=None):
        if expect is not None:
            assert self.u16(a) == expect, f'{a:06X}: esperado {expect:04X}, achei {self.u16(a):04X}'
        self.put(a, (v & 0xFF, v >> 8))

    def expect(self, a, data):
        o = self.off(a)
        assert self.b[o:o + len(data)] == bytes(data), f'{a:06X}: bytes inesperados {self.b[o:o + len(data)].hex()}'


def object_records(rom):
    """(área, endereço do registro, id, x, y) das duas listas de objetos."""
    for tbl, n in ((0x81C874, 116), (0x81C9D0, 64)):
        seen = set()
        for area in range(n):
            e = tbl + area * 3
            p = rom.u16(e) | rom.u8(e + 2) << 16
            if p in seen:          # listas compartilhadas entre áreas: grava uma vez só
                continue
            seen.add(p)
            for i in range(rom.u8(p)):
                r = p + 1 + 6 * i
                yield area, r, rom.u16(r), rom.u16(r + 2), rom.u16(r + 4)


def with_bounce(new, orig):
    """Mantém o bit $40 (não quica) do lugar quando o item novo é do tipo que o usa."""
    if new & 0xFF in ITEM_TYPES and orig & 0xFF in ITEM_TYPES:
        return (new & ~0x4000) | (orig & 0x4000)
    return new


def concrete(placement, rng):
    """Categoria -> id concreto (HPs, vellums e potions são intercambiáveis dentro da categoria)."""
    stock = {k: list(v) for k, v in VANILLA_IDS.items()}
    for v in stock.values():
        rng.shuffle(v)
    return {loc: FILLER_IDS[it] if it in FILLER_IDS else stock[it].pop() for loc, it in placement.items()}


SOMULO_HEAD_HP = 4      # vida da cabeça do Somulo na 1ª luta (original 7); tiros para vencer = vida - 1
CASTLE_LOCS = ('Sino HP 10', 'Fang')
BOSS_LOC = 0xDFFF      # All Bosses: os 15 bits de LOC dos chefes (tudo menos 2000 = Trio, que é minigame)


def castle_req(go, ids):
    """Go Mode na ROM: lista de (endereço longo, máscara 16 bits) que precisam estar TODOS ligados para o castelo
    aparecer no mapa; None = 5 vellums pelo código original validado. Flags do jogo: crest $81:D730 -> $1E51
    (Earth 10, Air 20, Water 40, Time 80), HP flag n -> $1E54 bit n-1 (só os HPs fora do castelo)."""
    if go == 'bosses':
        return [(LOC, BOSS_LOC)]
    if go == 'crests':
        return [(0x7E1E51, 0x00F0)]
    if go == 'hp':
        m = 0
        for loc, i in ids.items():
            if loc not in CASTLE_LOCS and i & 0xFF == 0x49 and 1 <= (i >> 8 & 0x1F) <= 0x10:
                m |= 1 << ((i >> 8 & 0x1F) - 1)
        return [(0x7E1E54, m)]
    return None

PATCH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'patch')
PATCH_FILES = {27: 'area_027.dcmapa.json', 29: 'area_029.dcmapa.json', 38: 'area_038.dcmapa.json',
               59: 'area_059.dcmapa.json'}   # 59 = a 27 depois que o Crawler aparece ($7FE002, 29/09)


def apply_map_patches(data, areas):
    """Patches de mapa do Neitan (editor de fases, DCOR/patch) na ROM ainda sem o rando. Cada arquivo traz também as
    outras áreas que estavam abertas no editor: só a área pedida entra, e só o desenho (telas e blocos novos) —
    objetos, eventos, gráficos, colisão e animação do arquivo ficam de fora (o rando mexe em objetos/drops depois)."""
    if not areas:
        return []
    import json
    import mapa
    docs = []
    for a in areas:
        j = json.load(open(os.path.join(PATCH_DIR, PATCH_FILES[a]), encoding='utf-8'))
        d = next(x for x in j['areas'] if x['area'] == a)
        keep = {k: d[k] for k in ('area', 'conjunto', 'largura', 'altura', 'grade', 'telas', 'blocos_novos') if k in d}
        docs.append(keep)
    parsed = mapa.parse({'formato': mapa.FORMATO, 'versao': mapa.VERSAO, 'areas': docs})
    merge_shared_screens(data, parsed)
    return mapa.apply(data, parsed)


def merge_shared_screens(data, parsed):
    """Áreas que usam a mesma tela (27 e 59 dividem a 135, 29/09): a tela é uma só na ROM, então as edições de cada
    patch são juntadas bloco a bloco (o que cada um mudou em relação ao original). Só é erro se dois patches mudam o
    MESMO bloco para valores diferentes. Os docs saem com a tela juntada nos dois."""
    import mapa
    r = mapa.R(bytearray(data))
    shared = {}
    for doc in parsed:
        for s in doc['telas'].values():
            shared.setdefault((doc['conjunto'], s['tela']), []).append((doc, s))
    for (n, t), uses in shared.items():
        if len(uses) < 2:
            continue
        orig = mapa.rom_screen(r, n, t)
        merged = [list(row) for row in orig]
        for doc, s in uses:
            for y, row in enumerate(s['grade']):
                for x, b in enumerate(row):
                    if b == orig[y][x]:
                        continue
                    if merged[y][x] != orig[y][x] and merged[y][x] != b:
                        raise mapa.MapaErro('tela %d do conjunto %d: patches das áreas %s mudam o bloco (%d,%d) de jeitos '
                                            'diferentes' % (t, n, ', '.join(str(d['area']) for d, _ in uses), x, y))
                    if b >= 0x1000 and any(b not in d['novos'] for d, _ in uses):
                        raise mapa.MapaErro('tela %d: bloco novo %X usado por outra área que não o define' % (t, b))
                    merged[y][x] = b
        for doc, s in uses:
            s['grade'] = [list(row) for row in merged]


def write(vanilla, placement, rng, go='vellum', patches=(), start=None):
    """Devolve (ROM 4 MB, ids por check). start = crest inicial sorteada (None = jogo original: Fire desde o início)."""
    data, _ = expand(vanilla)
    data = bytearray(data)
    write.map_report = apply_map_patches(data, patches)
    rom = Rom(data)
    ids = concrete(placement, rng)
    records = list(object_records(rom))

    # tabela nova de potes: original + 1 subtipo por pote da pool (o sino também)
    table = bytearray(rom.b[rom.off(POT_OLD):rom.off(POT_OLD) + POT_OLD_LEN])
    def new_pot_sub(item):
        sub = len(table)
        assert sub < 0x80, 'tabela de potes cheia (o bit 7 do subtipo é flag do spawner)'
        table.extend((item & 0xFF, item >> 8))
        return sub

    for loc, spec in SLOTS.items():
        new, kind = ids[loc], spec[0]
        if kind == 'obj':
            _, x, y, orig = spec
            hit = [r for a, r, i, rx, ry in records if (i, rx, ry) == (orig, x, y)]
            assert hit, f'{loc}: registro não achado'
            for r in hit:
                rom.put16(r, with_bounce(new, orig), orig)
        elif kind == 'pot':
            _, areas, x, y, orig = spec
            hit = [r for a, r, i, rx, ry in records if (i, rx, ry) == (orig, x, y) and a in areas]
            assert hit, f'{loc}: pote não achado'
            sub = new_pot_sub(new)
            for r in hit:
                rom.put16(r, sub << 8 | 0x57, orig)
        elif kind == 'word':
            _, addrs, orig = spec
            for a in addrs:
                rom.put16(a, with_bounce(new, orig), orig)
        elif kind == 'xba':
            _, a_sub, a_type, orig = spec
            assert (rom.u8(a_sub), rom.u8(a_type)) == (orig >> 8, orig & 0xFF), f'{loc}: bytes inesperados'
            new = with_bounce(new, orig)
            rom.put(a_sub, (new >> 8,))
            rom.put(a_type, (new & 0xFF,))
        elif kind == 'bell':
            _, a, orig = spec
            rom.put16(a, new_pot_sub(new) << 8 | 0x57, orig)
        elif kind == 'hippo':
            hippo = new
        elif kind == 'grewon':
            grewon = with_bounce(new, 0x0648)

    rom.put(POT_TABLE, table)
    code = bytearray()

    # pote: 84:C4E2 LDA $D85C,X / JSL 82:87E9  ->  JSL pot (A 16 bits, X = subtipo)
    pot = CODE + len(code)
    code += bytes((0xBF, 0x00, 0x80, 0xC0, 0x22, 0xE9, 0x87, 0x82, 0x6B))   # LDA $C08000,X / JSL 87E9 / RTL
    rom.expect(0x84C4E2, (0xBD, 0x5C, 0xD8, 0x22, 0xE9, 0x87, 0x82))
    rom.put(0x84C4E2, (0x22, pot & 0xFF, pot >> 8 & 0xFF, pot >> 16) + (0xEA,) * 3)

    # Hippogriff: 82:99A0 (ramo $1DD8 != 0: áreas 20 e 37) -> subtipo 2 (área 20) solta o item, os outros a recarga
    h = CODE + len(code)
    code += bytes((0xA9, 0x00, 0x7F, 0x8D, 0xED, 0x09,          # LDA #$7F00 / STA $09ED   (como o original)
                   0xAD, 0xD8, 0x1D, 0x29, 0xFF, 0x00,          # LDA $1DD8 / AND #$00FF   (subtipo do Hippogriff)
                   0xC9, 0x02, 0x00, 0xD0, 0x10,                # CMP #2 / BNE recarga
                   0xAF) + long3(LOC) + (0x09, 0x00, 0x80, 0x8F) + long3(LOC) +   # LOC |= 8000 (Hippogriff 2
                  (                                             #   vencido: All Bosses; a área não encerra)
                   0xA9, hippo & 0xFF, hippo >> 8, 0x80, 0x03,  # LDA #item / BRA
                   0xA9, 0x23, 0x06,                            # recarga: LDA #$0623
                   0x22, 0xE9, 0x87, 0x82, 0x6B))               # JSL 82:87E9 / RTL
    rom.expect(0x8299A0, (0xA9, 0x00, 0x7F, 0x8D, 0xED, 0x09, 0xA9, 0x23, 0x06, 0x22, 0xE9, 0x87, 0x82))
    rom.put(0x8299A0, (0x22, h & 0xFF, h >> 8 & 0xFF, h >> 16) + (0xEA,) * 9)

    # Grewon: BE:9E22 (A 8 bits) subtipo 0 (área 30) solta o item; os outros (área 41) seguem com recarga
    g = CODE + len(code)
    code += bytes((0xA6, 0x03, 0xD0, 0x07,                                # LDX $03 / BNE outro
                   0xA9, grewon >> 8, 0xEB, 0xA9, grewon & 0xFF,          # LDA #sub / XBA / LDA #tipo
                   0x80, 0x0D,                                            # BRA chama
                   0xA9, 0x80, 0x8D, 0xEE, 0x09, 0x9C, 0xED, 0x09,        # outro: LDA #$80 / STA $09EE / STZ $09ED
                   0xA9, 0x06, 0xEB, 0xA9, 0x23,                          # LDA #$06 / XBA / LDA #$23
                   0x22, 0xE9, 0x87, 0x82, 0x6B))                         # chama: JSL 82:87E9 / RTL
    rom.expect(0xBE9E22, (0xA9, 0x06, 0xEB, 0xA9, 0x48, 0xA6, 0x03, 0xF0, 0x0A, 0xA9, 0x80, 0x8D, 0xEE, 0x09,
                          0x9C, 0xED, 0x09, 0xA9, 0x23, 0x22, 0xE9, 0x87, 0x82))
    rom.put(0xBE9E22, (0x22, g & 0xFF, g >> 8 & 0xFF, g >> 16) + (0xEA,) * 19)

    # Somulo, 1ª luta (área 0, objeto 33): a cabeça entra na fase vulnerável (estado 1A, 83:8A3C LDA #$07 / STA $36)
    # com vida 7 e a luta acaba quando chega a 1 -> 6 tiros. Neitan (27/09): 3 tiros -> vida 4. Medido no emulador
    # (lua/somulo_test.lua, jogo novo sem crest): 1 de dano por tiro (tabela $81:D959).
    rom.expect(0x838A3C, (0xA9, 0x07, 0x85, 0x36))
    rom.put(0x838A3D, (SOMULO_HEAD_HP,))
    write.fire_report = fire_crest.apply(rom, start) if start else []
    code = boss_exit(rom, code, g, castle_req(go, ids))
    rom.put(CODE, code)
    gfx_lines = insanity_gfx.apply(rom.b, vanilla, ids)   # itens com gráfico/paleta próprios (BF:D600)
    fix_checksum(rom.b)
    write.gfx_report = gfx_lines
    return bytes(rom.b), ids


# --- Fim de área depois do drop de chefe: decidido pelo LUGAR, não pelo item (25/09) ---------------------------
# No original quem encerra a área é o item: HP de subtipo 0-4/6 (82:EB28) e toda crest (estado 2, 82:EB7C) pulam
# para 80:BB58 (próxima área = $81:97DA[área]). Com itens trocados isso encerrava a área no lugar errado e o chefe
# que soltava outra coisa travava o jogo. Agora: o item nunca encerra; o drop de chefe é marcado ao nascer
# (MARK = objeto, +2 = id, +4 = contador), e um vigia no fim do laço de objetos (82:86A7) chama 80:BB58 quando ele some
# (pego ou expirado) e não há caixa de mensagem (objeto tipo 8B). O marcador zera a cada carga de área (82:8B4D).
MARK = 0x7E1F80          # 26/09: $7E:1E71-1FFF nunca mudou em 46 min de jogo, 40 áreas (lua/wram_free.lua);
                         # $7F:6F00 (1ª escolha) era usado pelo jogo e virava lixo
# chamadas de drop de chefe que encerravam a área no original: (endereço do JSL, 'cria' 877B / 'vira' 87E9)
BOSS_SITES = [(0x8396D5, 'vira'),   # Somulo (cabeça)
              (0x82999B, 'vira'),   # Hippogriff 1 ($1DD8 = 0)
              (0x83E8DA, 'vira'),   # Belth
              (0xBD85AF, 'cria'), (0xBD8B9B, 'vira'),   # Skulla (2 caminhos)
              (0x83D7B9, 'cria'),   # Holothurion
              (0x83C6D6, 'cria'),   # Ovnunu
              (0x82CCFF, 'cria'),   # Flame Lord
              (0x82BA16, 'vira'),   # Crawler
              (0xBEE4E8, 'cria'),   # Arma 1 e 2 (tabela $81:F0A2)
              (0x82F00B, 'vira')]   # Arma 3 (objeto 4F vira a crest)
FLIER_SITES = [0x85DBA9, 0x85EF28]  # Flier: os DOIS encerram (Claw = crest; o 1F49 da área 34 também vai pro estado 2,
                                    # 82:EB2A) — 26/09 o Flier 2 não mudava de área porque só o subtipo 0 era marcado


def long3(a):
    return (a & 0xFF, a >> 8 & 0xFF, a >> 16)


def boss_exit(rom, code, grewon_tramp, castle=None):
    def here():
        return CODE + len(code)

    # o id guardado e o comparado ignoram o bit $4000 (não quica): a crest apaga esse bit do próprio subtipo ao nascer
    # (82:EA84) e o vigia achava que ela tinha sumido -> encerrava a área sem o item (Arma 3, 27/09)
    save = (0x8F,) + long3(MARK) + (0xA5, 0x02, 0x29, 0xFF, 0xBF, 0x8F) + long3(MARK + 2)   # STA mark / LDA $02 / AND / STA id
    zero_t = (0xA9, 0x00, 0x00, 0x8F) + long3(MARK + 4)                             # LDA #0 / STA timer

    vira = here()      # JSL 87E9 / PHP / REP #$30 / PHA / TDC / (save) / PLA / PLP / RTL
    code += bytes((0x22, 0xE9, 0x87, 0x82, 0x08, 0xC2, 0x30, 0x48, 0x7B) + save + zero_t + (0x68, 0x28, 0x6B))

    cria = here()      # JSL 877B / BCC fim / PHP / REP #$30 / PHA / TXA / (marca) / PLA / PLP / RTL
    mark = [0x8A, 0x8F, *long3(MARK), 0xBD, 0x02, 0x00, 0x29, 0xFF, 0xBF, 0x8F, *long3(MARK + 2), *zero_t]
    code += bytes([0x22, 0x7B, 0x87, 0x82, 0x90, 4 + len(mark) + 2, 0x08, 0xC2, 0x30, 0x48] + mark + [0x68, 0x28, 0x6B])

    for site, kind in BOSS_SITES:
        rom.expect(site, (0x22, 0x7B if kind == 'cria' else 0xE9, 0x87, 0x82))
        rom.put(site, (0x22,) + long3(cria if kind == 'cria' else vira))
    for site in FLIER_SITES:
        rom.expect(site, (0x22, 0x7B, 0x87, 0x82))
        rom.put(site, (0x22,) + long3(cria))
    # Grewon: o JSL comum do desvio vira um que marca só quando o subtipo é 0 (área 30); a 41 não encerrava
    assert bytes(code[grewon_tramp - CODE:][:2]) == b'\xA6\x03'
    gv = here()
    code += bytes((0x48, 0xA5, 0x03, 0xD0, 0x05, 0x68, 0x5C) + long3(vira) +          # PHA / LDA $03 / BNE / PLA / JML vira
                  (0x68, 0x5C, 0xE9, 0x87, 0x82))                                   # PLA / JML 87E9
    j = grewon_tramp - CODE + 24
    assert bytes(code[j:j + 4]) == bytes((0x22, 0xE9, 0x87, 0x82))
    code[j:j + 4] = bytes((0x22,) + long3(gv))

    # item não encerra mais a área
    rom.expect(0x82EB26, (0xC9, 0x07, 0x90, 0x9E))
    rom.put(0x82EB28, (0xEA, 0xEA))                                                 # HP de chefe = HP comum
    # crest (estado 2, 82:EB7C): no original espera o temporizador $3A (F0 = 240 quadros desde a coleta) e depois
    # $0EDB, que só o roteiro do chefe dono da crest liga; crest em outro lugar travava o Firebrand para sempre
    # ($0E5C = 8B), e com a caixa fechada antes do fim do temporizador ele ficava parado o resto do tempo (27/09,
    # "1 ou 2 s parado"). Agora, todo quadro desde a coleta: sem caixa de mensagem (objeto 8B) viva -> solta na hora.
    # ($0EDB não entra: roteiro de chefe pode ligá-lo com a caixa ainda aberta.)
    #   PHP / REP #$30 / PHX / LDX #$1080
    #   laço: LDA $00,X / AND #$FF / BEQ prox / LDA $02,X / AND #$FF / CMP #$8B / BEQ espera
    #   prox: TXA / CLC / ADC #$50 / TAX / CPX #$1D50 / BCC laço
    #   solta: PLX / PLP / SEC / RTL      espera: PLX / PLP / CLC / RTL
    cw = here()
    code += bytes.fromhex('08c230da' 'a28010'
                          'bd000029ff00f00bbd020029ff00c98b00f00f'
                          '8a18695000aae0501d90e2'
                          'fa2838' '6b' 'fa2818' '6b')
    rom.expect(0x82EB7C, bytes.fromhex('ee4210' 'a53af003c63a60' 'a502c949f005addb0ef0ea5c58bb80'))
    rom.put(0x82EB7F, bytes((0x22,) + long3(cw) + (0x90, 0x06)) +                   # JSL / BCC espera
            bytes.fromhex('9c5c0e4c5287' '60') + b'\xEA' * 9)                       # STZ $0E5C / JMP 8752 / espera: RTS

    # vigia (fim do laço de objetos, A/X 16 bits)
    w = here()
    body = bytearray()
    body += bytes((0xA9, 0x00, 0x00, 0x5B))                                          # LDA #0 / TCD (como o original)
    body += bytes((0xAF,) + long3(MARK)) + b'\xF0\x00'                               # LDA mark / BEQ fim
    j_done1 = len(body) - 1
    body += bytes((0xAA, 0xBD, 0x00, 0x00, 0x29, 0xFF, 0x00)) + b'\xF0\x00'          # TAX / LDA $00,X / AND / BEQ sumiu
    j_gone1 = len(body) - 1
    body += bytes((0xBD, 0x02, 0x00, 0x29, 0xFF, 0xBF, 0xCF) + long3(MARK + 2)) + b'\xD0\x00'   # LDA $02,X / AND / CMP id / BNE sumiu
    j_gone2 = len(body) - 1
    body += b'\x80\x00'                                                              # BRA fim
    j_done2 = len(body) - 1
    gone = len(body)
    body += bytes((0xA2, 0x80, 0x10))                                                # LDX #$1080
    loop = len(body)
    body += bytes((0xBD, 0x00, 0x00, 0x29, 0xFF, 0x00)) + b'\xF0\x00'                # LDA $00,X / AND / BEQ prox
    j_next = len(body) - 1
    body += bytes((0xBD, 0x02, 0x00, 0x29, 0xFF, 0x00, 0xC9, 0x8B, 0x00)) + b'\xF0\x00'   # tipo 8B? -> ocupado
    j_busy = len(body) - 1
    nxt = len(body)
    body += bytes((0x8A, 0x18, 0x69, 0x50, 0x00, 0xAA, 0xE0, 0x50, 0x1D)) + b'\x90\x00'   # prox: X += $50 / CPX / BCC loop
    j_loop = len(body) - 1
    body += bytes((0xAF,) + long3(MARK + 4) + (0x1A, 0x8F) + long3(MARK + 4) +       # timer++
                  (0xC9, 0x28, 0x00)) + b'\x90\x00'                                  # CMP #40 / BCC fim
    j_done3 = len(body) - 1
    body += bytes((0xAD, 0x8D, 0x00, 0x29, 0xFF, 0x00, 0xAA, 0xBF) + long3(LOCBIT) +   # lugar feito: LOC |= LOCBIT[área]
                  (0x0F,) + long3(LOC) + (0x8F,) + long3(LOC))
    body += bytes((0xA9, 0x00, 0x00, 0x8F) + long3(MARK) + (0x8F,) + long3(MARK + 4) +
                  (0xE2, 0x30, 0x5C, 0x58, 0xBB, 0x80))                              # zera / SEP #$30 / JML 80:BB58
    busy = len(body)
    body += bytes((0xA9, 0x00, 0x00, 0x8F) + long3(MARK + 4))                        # ocupado: timer = 0
    done = len(body)
    body += bytes((0xE2, 0x30, 0x6B))                                                # fim: SEP #$30 / RTL

    def rel(at, target):
        d = target - (at + 1)
        assert -128 <= d <= 127
        body[at] = d & 0xFF
    rel(j_done1, done); rel(j_gone1, gone); rel(j_gone2, gone); rel(j_done2, done)
    rel(j_next, nxt); rel(j_busy, busy); rel(j_loop, loop); rel(j_done3, done)
    code += body
    rom.expect(0x8286A7, bytes.fromhex('a900005be2306b'))
    rom.put(0x8286A7, (0x5C,) + long3(w))

    # zera o marcador a cada carga de área (82:8B4D JSL 82:86AE, que limpa as vagas de objeto)
    c = here()
    code += bytes((0x08, 0xC2, 0x20, 0xA9, 0x00, 0x00, 0x8F) + long3(MARK) + (0x8F,) + long3(MARK + 4) +
                  (0x28, 0x5C, 0xAE, 0x86, 0x82))                                   # PHP / zera / PLP / JML 82:86AE
    rom.expect(0x828B4D, (0x22, 0xAE, 0x86, 0x82))
    rom.put(0x828B4D, (0x22,) + long3(c))
    return progress(rom, code, castle)


# --- Progresso por LUGAR (25/09, teste da seed 2) ----------------------------------------------------------------
# O jogo deduz progresso dos bits de item (cartucho sem SRAM, só senha):
#   portão de chefe 80:A45F: $81:80A1[área] -> [índice][máscara], AND $1E51,X -> "já tem" = chefe pulado ($0EAA)
#   mapa-múndi 85:A1EE: 5 grupos (crest OU HP de chefe, $81:8D61/8D6B) -> Y -> $81:E1D2[Y] = fases visíveis ($37)
# Agora: flag de lugar LOC ($7E:1F90, 1 bit por chefe, ligada pelo vigia ao encerrar a área) no portão; mapa com
# todas as fases e castelo só com os 5 vellums (regra do Neitan). LOC zera no jogo novo e ao carregar senha
# (a senha estendida, que vai guardar LOC, ainda não existe).
LOC = 0x7E1F90
LOCBIT = 0xC08400        # tabela por área*2 (116 áreas): bit de LOC daquele chefe (0 = nenhum)
LOC_AREAS = {1: 0x0001,                    # Hippogriff 1
             3: 0x0002,                    # Arma 1
             9: 0x0004,                    # Belth
             13: 0x0008,                   # Skulla
             14: 0x0010, 50: 0x0010, 51: 0x0010,   # Flame Lord
             19: 0x0020,                   # Flier 1
             34: 0x4000,                   # Flier 2 (27/09, All Bosses)
             23: 0x0040,                   # Arma 2
             26: 0x0080,                   # Holothurion
             27: 0x0100,                   # Crawler
             30: 0x0200,                   # Grewon
             36: 0x0400,                   # Arma 3
             17: 0x0800,                   # Somulo (cabeça)
             8: 0x1000,                    # Ovnunu
             52: 0x2000, 53: 0x2000, 54: 0x2000}   # Trio the Pago


def progress(rom, code, castle=None):
    """castle = None: castelo com os 5 vellums (código validado no jogo). Senão, lista (endereço, máscara) de
    castle_req: o mapa chama uma rotina que confere todas."""
    def here():
        return CODE + len(code)

    table = bytearray(116 * 2)
    for area, bit in LOC_AREAS.items():
        table[area * 2:area * 2 + 2] = bytes((bit & 0xFF, bit >> 8))
    rom.put(LOCBIT, table)

    # portão de chefe: 80:A47D LDA $0001 / AND #$FF / AND $1E51,X / BEQ  ->  JSL gate / BEQ
    gate = here()
    code += bytes((0xAD, 0x8D, 0x00, 0x29, 0xFF, 0x00, 0xAA,          # LDA $8D / AND #$FF / TAX (área*2)
                   0xBF) + long3(LOCBIT) + (0x2F,) + long3(LOC) +      # LDA LOCBIT,X / AND LOC
                  (0xF0, 0x07,                                         # BEQ não-feito
                   0xAD, 0x01, 0x00, 0x29, 0xFF, 0x00, 0x6B,           # A = máscara original (p/ TSB $0EAA) / RTL
                   0xA9, 0x00, 0x00, 0x6B))                            # não-feito: A = 0 / RTL
    rom.expect(0x80A47D, bytes.fromhex('ad010029ff003d511ef009'))
    rom.put(0x80A47D, (0x22,) + long3(gate) + (0xF0, 0x0E) + (0xEA,) * 5)

    # mapa: 85:A1EE -> Y = 3 (crest de bit 8, como o original), 0 (5 vellums: $E1D2[0] = 7F, com castelo)
    #                  ou 1 ($E1D2[1] = 3F: fases 1-6)
    rom.expect(0x85A1EE, bytes.fromhex('c220ad581e890100d035a003ad511e890001d018'))
    if castle is None:
        rom.put(0x85A1EE, bytes.fromhex('c220' 'a003' 'ad511e' '890001' 'd00f'
                                        'ad561e' '291f00' 'a001' 'c91f00' 'd002' 'a000' 'e2206b'))
    else:
        # castelo (dif. 1/4/5): Y = 1 (fases 1-6); Y = 0 ($E1D2[0] = 7F, com castelo) se todas as máscaras batem
        #   LDY #1 / {LDA long / AND #m / CMP #m / BNE fechado}... / LDY #0 / fechado: RTL   (A 16 bits, Y 8 bits)
        cs = here()
        n = len(castle)
        for k, (a, m) in enumerate(castle):
            skip = (n - k - 1) * 12 + 2                     # cada conferência = 12 bytes; +2 pula o LDY #0
            code += bytes((0xAF,) + long3(a) + (0x29, m & 0xFF, m >> 8, 0xC9, m & 0xFF, m >> 8, 0xD0, skip))
        code[cs - CODE:cs - CODE] = bytes((0xA0, 0x01))
        code += bytes((0xA0, 0x00, 0x6B))
        new = bytes.fromhex('c220' 'a003' 'ad511e' '890001' 'd004') + bytes((0x22,) + long3(cs)) + bytes.fromhex('e2206b')
        rom.put(0x85A1EE, new + b'\xEA' * (30 - len(new)))

    # LOC = 0 no jogo novo (84:8906 LDA #4 / STA $1E50) e ao carregar senha (84:C17F STA $1E50 / STA $1062)
    ng = here()
    code += bytes((0x08, 0xC2, 0x20, 0xA9, 0x00, 0x00, 0x8F) + long3(LOC) +
                  (0x28, 0xA9, 0x04, 0x8D, 0x50, 0x1E, 0x6B))
    rom.expect(0x848906, bytes.fromhex('a9048d501e'))
    rom.put(0x848906, (0x22,) + long3(ng) + (0xEA,))
    pw = here()
    code += bytes((0x8D, 0x50, 0x1E, 0x8D, 0x62, 0x10, 0x08, 0xC2, 0x20, 0x48, 0xA9, 0x00, 0x00, 0x8F) + long3(LOC) +
                  (0x68, 0x28, 0x6B))
    rom.expect(0x84C17F, bytes.fromhex('8d501e8d6210'))
    rom.put(0x84C17F, (0x22,) + long3(pw) + (0xEA, 0xEA))
    # outros testes de "já tem o item do chefe" (medido 26/09: Skulla e Arma 1 sumiam) -> flag do lugar
    hooks = {}
    def m8_hook(bit):               # LDA LOC (byte certo) / BIT #máscara / RTL  (A 8 bits; o desvio seguinte usa Z)
        if bit not in hooks:
            hooks[bit] = here()
            code.extend((0xAF,) + long3(LOC + (1 if bit > 0xFF else 0)) + (0x89, (bit >> 8 if bit > 0xFF else bit), 0x6B))
        return hooks[bit]
    BY_ITEM = {(0x51, 0x01): 0x1000, (0x54, 0x04): 0x0004, (0x51, 0x02): 0x0010, (0x54, 0x08): 0x0008,
               (0x51, 0x04): 0x0020, (0x54, 0x20): 0x0080, (0x51, 0x40): 0x0100, (0x51, 0x08): 0x0200,
               (0x51, 0x80): 0x0400}
    # roteiro de entrada das fases (BE:8326-845B): LDA $1E5x / BIT #máscara (8 bits)
    for a in (0xBE8326, 0xBE8333, 0xBE8340, 0xBE8350, 0xBE8360, 0xBE83E4, 0xBE83F1, 0xBE83FE, 0xBE840B,
              0xBE841B, 0xBE842B, 0xBE843B, 0xBE844B, 0xBE845B):
        lo, mask = rom.u8(a + 1), rom.u8(a + 4)
        rom.expect(a, (0xAD, lo, 0x1E, 0x89, mask))
        rom.put(a, (0x22,) + long3(m8_hook(BY_ITEM[lo, mask])) + (0xEA,))
    # evento de entrada da área 1 (84:9902 LDA $1E54 / AND #$02): intro do Hippogriff
    rom.expect(0x849902, bytes.fromhex('ad541e2902'))
    rom.put(0x849902, (0x22,) + long3(m8_hook(0x0001)) + (0xEA,))
    # troca de área por item (84:8949 JSR ($8950,X) por área): área 8 com Buster vira 60 (sem Ovnunu), área 27 com
    # Water vira 59 (sem Crawler); e 84:8564: áreas 0-3/17 sem Earth Crest (= Arma 1 não vencido) seguem outro fluxo
    for a, want, loc in ((0x8489F7, 'ad511e2901', 0x1000), (0x848A18, 'ad511e2940', 0x0100),
                         (0x848564, 'ad511e2910', 0x0002)):
        rom.expect(a, bytes.fromhex(want))
        rom.put(a, (0x22,) + long3(m8_hook(loc)) + (0xEA,))
    # Trio the Pago (BC:AAEC LDA $1E54 / BIT #$0800, 16 bits)
    t = here()
    code += bytes((0xAF,) + long3(LOC) + (0x89, 0x00, 0x20, 0x6B))
    rom.expect(0xBCAAEC, bytes.fromhex('ad541e890008'))
    rom.put(0xBCAAEC, (0x22,) + long3(t) + (0xEA, 0xEA))
    # Arma (BE:E3E1 LDA $1E51 / AND #$80: com a Time Crest TODO Arma se apagava) -> cada Arma olha o próprio lugar
    #   subtipo 0 = Arma 1 (LOC 0002), 2 = Arma 2 (0040), 4 = Arma 3 (0400); A 8 bits, DP = o Arma
    arma = here()
    code += bytes((0xA5, 0x03, 0xC9, 0x02, 0xF0, 0x09, 0xB0, 0x0E,            # LDA $03 / CMP #2 / BEQ a2 / BCS a3
                   0xAF) + long3(LOC) + (0x29, 0x02, 0x6B,                    # a1: LOC & 02
                   0xAF) + long3(LOC) + (0x29, 0x40, 0x6B,                    # a2: LOC & 40
                   0xAF) + long3(LOC + 1) + (0x29, 0x04, 0x6B))               # a3: LOC+1 & 04
    rom.expect(0xBEE3E1, bytes.fromhex('ad511e2980f008'))
    rom.put(0xBEE3E1, (0x22,) + long3(arma) + (0xEA,))

    # Crawler (29/09, seed "Castle Grewon Realm Hippogriff Holothurion", achado pelo Neitan): o evento da arena
    # (84:996F, A 16 bits, com o Firebrand em X >= 0270) liga $0EAA bit 40 = "chefe já vencido" se $1E51 tem a
    # Water Crest (e não o bit 0100) -> quem tinha Water de outro lugar entrava e era mandado pro mapa. Agora é a flag
    # do lugar (LOC 0100, só ligada quando o drop do Crawler some). O gancho devolve A = 40 com Z=1 (vencido: o BNE
    # seguinte não pula e o AND #$40 liga o bit) ou A = 0 (não vencido: nada acontece).
    crawl = here()
    code += bytes((0xAF,) + long3(LOC) + (0x29, 0x00, 0x01, 0xF0, 0x07,          # LDA LOC / AND #$0100 / BEQ não
                                          0xA9, 0x40, 0x00, 0x89, 0x00, 0x00, 0x6B,  # LDA #$40 / BIT #0 (Z=1) / RTL
                                          0xA9, 0x00, 0x00, 0x6B))                  # não: LDA #0 / RTL
    rom.expect(0x84996F, bytes.fromhex('ad511e890001'))
    rom.put(0x84996F, (0x22,) + long3(crawl) + (0xEA, 0xEA))

    assert CODE + len(code) < LOCBIT, 'código passou da tabela LOCBIT'
    return code
