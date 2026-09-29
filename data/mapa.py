# Cópia de DemonsCrest Editor/mapa.py (28/09): o DCOR usa pra aplicar os patches de mapa do anti-softlock.
# A fonte é a do editor; se ela mudar, copiar de novo.
"""Mapa editado de uma fase: formato do arquivo e gravação na ROM. Só biblioteca padrão — roda sem o editor.

Uso:
  python mapa.py exportar ROM ÁREA [ÁREA...] saida.dcmapa.json   mapa atual da ROM (ponto de partida)
  python mapa.py aplicar ROM mapa.dcmapa.json [saida.sfc]        grava no jogo (padrão: "<ROM> - mapa.sfc")

Arquivo (.dcmapa.json): {"formato": "demons-crest-mapa", "versao": 2, "areas": [doc, ...]}; doc de cada área:
  area, conjunto, largura, altura, grade (linhas de slots do BG1, só conferência), telas {slot: {tela, blocos: 16 linhas
  de 16 fichas}}, blocos_novos {"N0": {tiles: [4 × u16 hex], atributo: hex, origem: texto}},
  objetos {"normal": [[id hex, X, Y], ...], "limpa": [...]} (versão 2; "limpa" só nas áreas 0-63),
  eventos {saida: hex (próxima área*2 ou F0-FF = mapa), portao: "IIMM" ([índice][máscara]) ou "-", chefes: {"TT.VV":
  {vida: [n...], drop: hex}}, minigames: {"TT.VV": {drop: hex}}} (saída/portão só nas áreas 0-63; chefes/minigames =
  os da lista de objetos; ver chefes.py — Trio the Pago é minigame, não chefe).
  Ficha = índice do bloco 16x16 no conjunto (hex, "1AE") ou "N<k>" = bloco novo definido no próprio doc.

Gravação (ROM US, com ou sem rando/4 MB — o rando não toca nessas regiões):
- Tela editada é regravada NO LUGAR (banco $8F+n, $8000 + tela*128): toda área que usa aquela tela muda junto
  (gêmeas e salas repetidas — a tela é a unidade do jogo). A tela comum (slot 0) não é editável.
- Superblocos (32x32, banco $92+n) e blocos novos (banco $95+n + atributo $98:8000+(n<<12)+bloco) reaproveitam um
  igual já existente; senão vão pro fim do banco, depois do fim original da tabela (FIM). Evidência de que esse
  fim é livre: conjuntos 0/1 — dados idênticos na ROM japonesa e o resto do banco difere (lixo de compilação);
  todos — nenhuma tela ou lista de troca de quebrável ($81:B513) aponta pra lá. Superbloco/bloco da faixa nova que
  nenhuma tela usa mais volta a ficar livre.
- Objetos (itens, potes, inimigos): lista da área = ponteiro de 24 bits em $81:C874 (normal) / $81:C9D0 (área já
  limpa) → [n] + n × [id][X][Y]. Só o carregador 82:8BDB lê essas tabelas, com LDA [ptr],Y: a lista pode morar em
  qualquer banco. Máximo 255 por lista (n é 1 byte; o "já nasceu" é um mapa de 256 bits em $09C0-$09DF). Lista
  menor ou igual à original: regravada no lugar. Maior: vai pra metade nova da ROM de 4 MB, alocada do fim ($FF:FFFF)
  pra baixo (a ROM de 2 MB é expandida com rom_expand, validado); uma lista que já estava lá e se mudou é zerada.
  O rando grava item pelo endereço do registro: aplicar o mapa DEPOIS do rando (ou refazer o rando sobre ele).
"""
import json
import os
import struct
import sys

import chefes

FORMATO, VERSAO = 'demons-crest-mapa', 2
TABS = {'normal': 0xC874, 'limpa': 0xC9D0}         # listas de objetos; "limpa" só nas áreas 0-63
N_LIMPA = 64
N_AREAS = 113                                     # 113-115 não são áreas
FIM = {0: (232, 3835, 3776), 1: (239, 3190, 3033), 2: (179, 2617, 2312)}   # fim original: telas, superblocos, blocos
LIMITE = (256, 4096, 4096)                        # 32 KB por banco / índice de 12 bits do bloco


class MapaErro(Exception):
    pass


def lo(bank, addr):
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


class R:
    def __init__(self, d):
        self.d = d

    def u8(self, b, a):
        return self.d[lo(b, a)]

    def u16(self, b, a):
        return struct.unpack_from('<H', self.d, lo(b, a))[0]

    def w16(self, b, a, v):
        struct.pack_into('<H', self.d, lo(b, a), v)


def area_info(r, a):
    """conjunto, telas da lista (slot k = telas[k-1]), grade de slots do BG1 e do BG2 (80:C5CE)."""
    p = r.u16(0x81, 0xA291 + a * 2)
    n, qtd = r.u8(0x81, p), r.u8(0x81, p + 1)
    q = r.u16(0x81, 0xA6D8 + a * 2)
    w, h = r.u8(0x81, q), r.u8(0x81, q + 1)
    grid = [[r.u8(0x81, q + 2 + y * w + x) for x in range(w)] for y in range(h)]
    e = q + 2 + w * h
    g2 = []
    if r.u8(0x81, e) & 0x80:
        w2, h2 = r.u8(0x81, e + 1), r.u8(0x81, e + 2)
        g2 = [[r.u8(0x81, e + 3 + y * w2 + x) for x in range(w2)] for y in range(h2)]
    return {'conjunto': n, 'telas': [r.u8(0x81, p + 2 + k) for k in range(qtd)], 'largura': w, 'altura': h,
            'grade': grid, 'grade_bg2': g2, 'comum': r.u8(0x81, 0xA379 + n * 3 + 2)}


def screens_of(r, a):
    """números de tela que a área usa (BG1, BG2 e a comum)."""
    i = area_info(r, a)
    return set(i['telas']) | {i['comum']}


def rom_screen_sbs(r, n, t):
    return [r.u16(0x8F + n, 0x8000 + t * 128 + k * 2) for k in range(64)]


def rom_sb(r, n, s):
    return tuple(r.u16(0x92 + n, 0x8000 + s * 8 + j * 2) for j in range(4))


def rom_screen(r, n, t):
    """grade 16x16 de blocos da tela t."""
    g = [[0] * 16 for _ in range(16)]
    for k, s in enumerate(rom_screen_sbs(r, n, t)):
        sx, sy = (k % 8) * 2, (k // 8) * 2
        for j, b in enumerate(rom_sb(r, n, s)):
            g[sy + j // 2][sx + j % 2] = b
    return g


def rom_block(r, n, b):
    """(4 entradas de tilemap, atributo) do bloco b."""
    return (tuple(r.u16(0x95 + n, 0x8000 + b * 8 + j * 2) for j in range(4)), r.u8(0x98, 0x8000 + (n << 12) + b))


def u24(r, a):
    o = lo(a >> 16, a)
    return r.d[o] | r.d[o + 1] << 8 | r.d[o + 2] << 16


def list_ptr(r, tab, a):
    return u24(r, 0x810000 | TABS[tab] + a * 3)


def rom_objects(r, tab, a):
    """[(id, X, Y)] da lista de objetos da área (tabela "normal" ou "limpa")."""
    p = list_ptr(r, tab, a)
    o = lo(p >> 16, p)
    return [struct.unpack_from('<HHH', r.d, o + 1 + 6 * i) for i in range(r.d[o])]


def tabs_of(a):
    return ('normal', 'limpa') if a < N_LIMPA else ('normal',)


def r16(r, a):
    return r.u16(a >> 16, a & 0xFFFF)


def gfx_addrs(r, a):
    """endereços (SNES) de cada posição das listas de gráfico da área, na ordem das listas:
    tiles ($BD:9953, u16 até $FFFF), sprites ($81:AE11, [id][slot*2] até 0), paletas ($81:8479, u16 até 0),
    meio (tile sets do carregador de meio de fase, tabela no operando de 80:BFB5), seg (passos × tile sets do
    carregador de segmento, operando de 80:C11B; registros de 4 B)."""
    out = {'tiles': [], 'sprites': [], 'paletas': [], 'meio': [], 'seg': []}
    p = 0xBD0000 | r16(r, 0xBD9953 + a * 2)
    while r16(r, p) != 0xFFFF:
        out['tiles'].append(p)
        p += 2
    p = 0x810000 | r16(r, 0x81AE11 + a * 2)
    while r.u8(0x81, p):
        out['sprites'].append(p)
        p += 2
    p = 0x810000 | r16(r, 0x818479 + a * 2)
    while r16(r, p):
        out['paletas'].append(p)
        p += 2
    p = 0xBD0000 | r16(r, (0xBD0000 | r16(r, 0x80BFB5)) + a * 2)
    if r.u8(0xBD, p):
        y = 3
        while r.u8(0xBD, p + y) >= 0x10:
            y += 2
        if r.u8(0xBD, p + y):
            y += 1
            while r16(r, p + y):
                out['meio'].append(p + y)
                y += 2
    p = 0xBD0000 | r16(r, (0xBD0000 | r16(r, 0x80C11B)) + a * 2)
    c = r.u8(0xBD, p)
    if c:
        n, q = r.u8(0xBD, p + 1), p + 2 + 9 * c
        out['seg'] = [[q + 4 * (i * n + k) for k in range(n)] for i in range(c + 1)]
    return out


def read_gfx(r, a):
    """listas de gráfico da área (valores): tiles, sprites [(id, slot*2)], paletas, meio, seg [[...] por passo]."""
    ad = gfx_addrs(r, a)
    return {'tiles': [r16(r, x) for x in ad['tiles']],
            'sprites': [(r.u8(x >> 16, x), r.u8(x >> 16, x + 1)) for x in ad['sprites']],
            'paletas': [r16(r, x) for x in ad['paletas']], 'meio': [r16(r, x) for x in ad['meio']],
            'seg': [[r16(r, x) for x in one] for one in ad['seg']]}


def gfx_doc(g):
    return {'tiles': ['%03X' % v for v in g['tiles']], 'sprites': [['%02X' % s, b] for s, b in g['sprites']],
            'paletas': ['%04X' % v for v in g['paletas']], 'meio': ['%03X' % v for v in g['meio']],
            'seg': [['%03X' % v for v in one] for one in g['seg']]}


def gfx_parse(j):
    return {'tiles': [int(v, 16) for v in j['tiles']], 'sprites': [(int(s, 16), int(b)) for s, b in j['sprites']],
            'paletas': [int(v, 16) for v in j['paletas']], 'meio': [int(v, 16) for v in j['meio']],
            'seg': [[int(v, 16) for v in one] for one in j['seg']]}


def set_usage(r, n, skip=()):
    """{tela: [superblocos]} de todas as telas do conjunto usadas por alguma área, menos as de skip."""
    use = {}
    for a in range(N_AREAS):
        if area_info(r, a)['conjunto'] == n:
            for t in screens_of(r, a):
                if t not in skip and t not in use:
                    use[t] = rom_screen_sbs(r, n, t)
    return use


def boss_keys(objs):
    """chaves (tipo, variante) dos chefes com dados (chefes.SITES) numa lista de objetos, na ordem."""
    out = []
    for i, _, _ in objs:
        k = chefes.key_of(i & 0x7FFF)
        if k and k not in out:
            out.append(k)
    return out


def events_doc(r, a, objs, ev=None):
    """campo "eventos" do doc: saída, portão (áreas 0-63) e vida/drop dos chefes da lista; ev = edições do editor
    {'saida': v, 'portao': g, 'chefes': {chave: {'vida': [...], 'drop': id}}} por cima da ROM."""
    ev = ev or {}
    out = {}
    if a < chefes.N_EVENT_AREAS:
        out['saida'] = '%02X' % ev.get('saida', chefes.exit_read(r.d, a))
        g = ev['portao'] if 'portao' in ev else chefes.gate_read(r.d, a)
        out['portao'] = '-' if g is None else '%02X%02X' % g
    cs = {}
    for k in boss_keys(objs):
        v = dict(chefes.read(r.d, k))
        v.update(ev.get('chefes', {}).get(k, {}))
        cs.setdefault('minigames' if chefes.kind(k) == 'minigame' else 'chefes', {})['%02X.%02X' % k] = {
            'vida': list(v['vida']), 'drop': None if v['drop'] is None else '%04X' % v['drop']}
    out.update(cs)
    return out


def export(r, a, screens=None, blocks=None, objects=None, gfx=None, attrs=None, anims=None, events=None):
    """doc da área. screens = {tela: grade} editadas (senão lê da ROM); blocks = {id: (tiles, atributo, origem)}
    dos blocos novos, id >= $1000 (vira "N<id-$1000>"); objects = {tabela: [(id, X, Y)]} editadas; gfx = listas de
    gráfico editadas (read_gfx; troca de tipo de inimigo); attrs = {bloco: atributo} trocados no conjunto (colisão
    de bloco que já existe, vale pro conjunto inteiro); anims = {id: [durações]} das animações de tile editadas;
    events = edições de saída/portão/chefes (events_doc)."""
    i = area_info(r, a)
    n, screens, blocks = i['conjunto'], screens or {}, blocks or {}
    used, telas = set(), {}
    for slot in sorted({s for row in i['grade'] for s in row if s} | set(range(1, len(i['telas']) + 1))):
        # todas as telas da área: as do BG1 (grade) e as do BG2 (fundo), que também são editáveis
        if slot > len(i['telas']):
            continue
        t = i['telas'][slot - 1]
        g = screens.get(t) or rom_screen(r, n, t)
        used |= {b for row in g for b in row if b >= 0x1000}
        telas[str(slot)] = {'tela': t, 'blocos': [' '.join(tok(b) for b in row) for row in g]}
    novos = {tok(b): {'tiles': ['%04X' % v for v in blocks[b][0]], 'atributo': '%02X' % blocks[b][1],
                      'origem': blocks[b][2]} for b in sorted(used)}
    return {'area': a, 'conjunto': n, 'largura': i['largura'], 'altura': i['altura'],
            'grade': [' '.join(map(str, row)) for row in i['grade']],
            'telas': telas, 'blocos_novos': novos,
            'objetos': {k: [['%04X' % i, x, y] for i, x, y in (objects or {}).get(k, rom_objects(r, k, a))]
                        for k in tabs_of(a)},
            'graficos': gfx_doc(gfx or read_gfx(r, a)),
            'atributos': {'%03X' % b: '%02X' % v for b, v in sorted((attrs or {}).items())},
            'animacoes': {'%02X' % k: list(v) for k, v in sorted((anims or {}).items())},
            'eventos': events_doc(r, a, (objects or {}).get('normal', rom_objects(r, 'normal', a)), events)}


def tok(b):
    return 'N%d' % (b - 0x1000) if b >= 0x1000 else '%03X' % b


def untok(s):
    return 0x1000 + int(s[1:]) if s[0] in 'Nn' else int(s, 16)


def pack(docs):
    return {'formato': FORMATO, 'versao': VERSAO, 'areas': docs}


def save(path, docs):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pack(docs), f, ensure_ascii=False, indent=1)


def load(path):
    with open(path, encoding='utf-8') as f:
        return parse(json.load(f))


def parse(j):
    """lista de docs, com as grades já em números (blocos novos = $1000 + k, locais a cada doc)."""
    if j.get('formato') != FORMATO or j.get('versao', 0) > VERSAO:
        raise MapaErro('não é um mapa do Demon\'s Crest (formato %s, versão até %d)' % (FORMATO, VERSAO))
    for doc in j['areas']:
        for s in doc['telas'].values():
            s['grade'] = [[untok(x) for x in line.split()] for line in s['blocos']]
            if len(s['grade']) != 16 or any(len(row) != 16 for row in s['grade']):
                raise MapaErro('área %d tela %d: grade não é 16x16' % (doc['area'], s['tela']))
        doc['objs'] = {}
        for k, lst in doc.get('objetos', {}).items():
            if k not in tabs_of(doc['area']):
                raise MapaErro('área %d: não tem lista "%s"' % (doc['area'], k))
            doc['objs'][k] = [(int(i, 16), int(x), int(y)) for i, x, y in lst]
            if len(lst) > 255 or any(not (0 <= v <= 0xFFFF) for e in doc['objs'][k] for v in e):
                raise MapaErro('área %d lista %s: mais de 255 objetos ou valor fora de 16 bits' % (doc['area'], k))
        doc['gfx'] = gfx_parse(doc['graficos']) if 'graficos' in doc else None
        doc['attrs'] = {int(b, 16): int(v, 16) for b, v in doc.get('atributos', {}).items()}
        doc['anims'] = {int(k, 16): [int(x) for x in v] for k, v in doc.get('animacoes', {}).items()}
        if any(not 0 <= b < LIMITE[2] or not 0 <= v <= 0xFF for b, v in doc['attrs'].items()):
            raise MapaErro('área %d: atributo fora da faixa' % doc['area'])
        doc['novos'] = {untok(k): (tuple(int(x, 16) for x in v['tiles']), int(v['atributo'], 16), v.get('origem', ''))
                        for k, v in doc.get('blocos_novos', {}).items()}
        doc['ev'] = parse_events(doc)
    return j['areas']


def parse_events(doc):
    e, a, ev = doc.get('eventos', {}), doc['area'], {}
    if ('saida' in e or 'portao' in e) and a >= chefes.N_EVENT_AREAS:
        raise MapaErro('área %d: saída/portão só existem nas áreas 0-63' % a)
    if 'saida' in e:
        ev['saida'] = int(e['saida'], 16)
        if not 0 <= ev['saida'] <= 0xFF:
            raise MapaErro('área %d: saída fora da faixa' % a)
    if 'portao' in e:
        ev['portao'] = None if e['portao'] == '-' else (int(e['portao'][:2], 16), int(e['portao'][2:], 16))
    ev['chefes'] = {}
    for k, v in list(e.get('chefes', {}).items()) + list(e.get('minigames', {}).items()):
        key = tuple(int(x, 16) for x in k.split('.'))
        if key not in chefes.SITES:
            raise MapaErro('área %d: chefe %s sem dados (chefes.SITES)' % (a, k))
        vida = [int(x) for x in v.get('vida', [])]
        if any(not 1 <= x <= 0xFE for x in vida) or len(vida) != len(chefes.SITES[key]['vida']):
            raise MapaErro('área %d chefe %s: vida fora de 1-254 ou quantidade errada' % (a, k))
        ev['chefes'][key] = {'vida': vida, 'drop': None if v.get('drop') is None else int(v['drop'], 16)}
    return ev


def check(r, doc):
    """confere o doc contra a ROM: mesmo conjunto e as telas nos mesmos slots. Devolve {tela: grade}."""
    a = doc['area']
    i = area_info(r, a)
    if i['conjunto'] != doc['conjunto']:
        raise MapaErro('área %d: conjunto %d na ROM, %d no arquivo' % (a, i['conjunto'], doc['conjunto']))
    out = {}
    for slot, s in doc['telas'].items():
        slot = int(slot)
        if not 1 <= slot <= len(i['telas']) or i['telas'][slot - 1] != s['tela']:
            raise MapaErro('área %d: o slot %d não é a tela %d nesta ROM (arranjo mudou?)' % (a, slot, s['tela']))
        for row in s['grade']:
            for b in row:
                if b >= 0x1000 and b not in doc['novos']:
                    raise MapaErro('área %d tela %d: bloco %s sem definição' % (a, s['tela'], tok(b)))
                if b < 0x1000 and b >= LIMITE[2]:
                    raise MapaErro('área %d tela %d: bloco %03X fora da tabela' % (a, s['tela'], b))
        out[s['tela']] = s['grade']
    return out


def apply(rom, docs):
    """grava os docs na ROM (bytearray, alterado no lugar). Devolve linhas de relatório. MapaErro se não couber
    ou se o arquivo não bate com a ROM (nada é gravado nesse caso)."""
    r = R(bytearray(rom))
    report = []
    by_set = {}
    for doc in docs:
        for t, g in check(r, doc).items():
            n = doc['conjunto']
            if g == rom_screen(r, n, t):
                continue                              # igual à ROM: não conta (gêmea exportada antes da edição)
            prev = by_set.setdefault(n, {}).get(t)
            if prev and prev[0] != g:
                raise MapaErro('tela %d do conjunto %d editada de dois jeitos (áreas %d e %d)'
                               % (t, n, prev[1]['area'], doc['area']))
            by_set[n][t] = (g, doc)
    for n, edits in sorted(by_set.items()):
        report += apply_set(r, n, edits)
    report += apply_attrs(r, docs)
    report += apply_anims(r, docs)
    report += apply_events(r, docs)
    report += apply_gfx(r, docs)
    report += apply_objects(r, docs)
    if not report:
        report.append('nada a gravar: o mapa é igual ao da ROM')
    rom[:] = r.d
    fix_checksum(rom)
    return report


def apply_set(r, n, edits):
    fsb, fb = FIM[n][1:]
    common = r.u8(0x81, 0xA379 + n * 3 + 2)
    if common in edits:
        raise MapaErro('conjunto %d: a tela comum (%d) é de %s áreas — não é editável' % (n, common, 'várias'))
    others = set_usage(r, n, skip=edits)
    sb_used = {s for sbs in others.values() for s in sbs}
    blk_used = {b for s in sb_used for b in rom_sb(r, n, s)}
    blk_used |= {b for g, _ in edits.values() for row in g for b in row if b < 0x1000}   # já apontados pelo arquivo
    # blocos: igual existente (tabela original ou faixa nova ainda em uso) ou vaga na faixa nova
    known = {}
    for b in list(range(fb)) + sorted(x for x in blk_used if x >= fb):
        known.setdefault(rom_block(r, n, b), b)
    free_b = [b for b in range(fb, LIMITE[2]) if b not in blk_used]
    new_blocks, resolved = [], {}
    for t, (g, doc) in sorted(edits.items()):
        for row in g:
            for b in row:
                if b < 0x1000 or (id(doc), b) in resolved:
                    continue
                tiles, attr, _ = doc['novos'][b]
                key = (tuple(tiles), attr)
                if key not in known:
                    if not free_b:
                        raise MapaErro('conjunto %d: sem vaga pra bloco novo (%d livres)' % (n, LIMITE[2] - fb))
                    known[key] = free_b.pop(0)
                    new_blocks.append((known[key], key))
                resolved[(id(doc), b)] = known[key]
    # superblocos
    sb_known = {}
    for s in list(range(fsb)) + sorted(x for x in sb_used if x >= fsb):
        sb_known.setdefault(rom_sb(r, n, s), s)
    free_sb = [s for s in range(fsb, LIMITE[1]) if s not in sb_used]
    new_sbs, screens = [], {}
    for t, (g, doc) in sorted(edits.items()):
        g = [[resolved[(id(doc), b)] if b >= 0x1000 else b for b in row] for row in g]
        sbs = []
        for k in range(64):
            sx, sy = (k % 8) * 2, (k // 8) * 2
            q = (g[sy][sx], g[sy][sx + 1], g[sy + 1][sx], g[sy + 1][sx + 1])
            if q not in sb_known:
                if not free_sb:
                    raise MapaErro('conjunto %d: sem vaga pra superbloco novo (%d livres no total)'
                                   % (n, LIMITE[1] - fsb))
                sb_known[q] = free_sb.pop(0)
                new_sbs.append((sb_known[q], q))
            sbs.append(sb_known[q])
        screens[t] = sbs
    for b, (tiles, attr) in new_blocks:
        for j, v in enumerate(tiles):
            r.w16(0x95 + n, 0x8000 + b * 8 + j * 2, v)
        r.d[lo(0x98, 0x8000 + (n << 12) + b)] = attr
    for s, q in new_sbs:
        for j, v in enumerate(q):
            r.w16(0x92 + n, 0x8000 + s * 8 + j * 2, v)
    for t, sbs in screens.items():
        for k, s in enumerate(sbs):
            r.w16(0x8F + n, 0x8000 + t * 128 + k * 2, s)
    areas = sorted(a for a in range(N_AREAS) if area_info(r, a)['conjunto'] == n and screens_of(r, a) & set(edits))
    return ['conjunto %d: telas %s regravadas (aparecem nas áreas %s); %d blocos novos, %d superblocos novos; '
            'livres: %d blocos, %d superblocos' % (n, sorted(edits), areas, len(new_blocks), len(new_sbs),
                                                   len(free_b), len(free_sb))]


def apply_events(r, docs):
    """saída e portão por área; vida e drop por chefe (endereços de código/tabela: valem pra toda área que usa
    aquele chefe/variante — chefes.shared). Só grava o que difere da ROM; o mesmo chefe pedido com 2 valores é erro;
    código de chefe diferente do original (ROM modificada) com valor novo é erro."""
    report, want = [], {}
    for doc in docs:
        a, ev = doc['area'], doc.get('ev', {})
        if 'saida' in ev and ev['saida'] != chefes.exit_read(r.d, a):
            chefes.exit_write(r.d, a, ev['saida'])
            report.append('área %d: saída → %s' % (a, chefes.exit_name(ev['saida'])))
        if 'portao' in ev and ev['portao'] != chefes.gate_read(r.d, a):
            try:
                chefes.gate_write(r.d, a, ev['portao'])
            except ValueError as e:
                raise MapaErro('área %d: %s' % (a, e))
            report.append('área %d: portão do chefe → %s' % (a, chefes.gate_name(ev['portao'])))
        for key, v in ev.get('chefes', {}).items():
            cur = chefes.read(r.d, key)
            if v['vida'] == cur['vida'] and v['drop'] == cur['drop']:
                continue
            if want.get(key, v) != v:
                raise MapaErro('%s editado de dois jeitos em áreas diferentes' % chefes.boss_label(key))
            want[key] = v
    for key, v in want.items():
        bad = chefes.site_ok(r.d, key)
        if bad:
            raise MapaErro('%s: o código desta ROM não é o original (%s) — não dá pra gravar vida/drop'
                           % (chefes.boss_label(key), ', '.join(bad)))
        cur = chefes.read(r.d, key)
        try:
            chefes.write(r.d, key, v)
        except ValueError as e:
            raise MapaErro('%s: %s' % (chefes.boss_label(key), e))
        parts = []
        if v['vida'] != cur['vida']:
            parts.append('vida %s → %s' % (cur['vida'], v['vida']))
        if v['drop'] != cur['drop']:
            parts.append('%s %s → %s' % ('prêmio' if chefes.kind(key) == 'minigame' else 'drop',
                                          chefes.item_name(cur['drop']), chefes.item_name(v['drop'])))
        sh = chefes.shared(key)
        report.append('%s: %s%s' % (chefes.boss_label(key), ', '.join(parts),
                                    ' (mesmo código de %s)' % ', '.join(map(chefes.boss_label, sh)) if sh else ''))
    return report


def apply_attrs(r, docs):
    """colisão trocada de blocos que já existem: tabela $98:8000 + (conjunto<<12) + bloco, no lugar."""
    done = {}
    for doc in docs:
        for b, v in doc['attrs'].items():
            key = (doc['conjunto'], b)
            if done.get(key, v) != v:
                raise MapaErro('bloco %03X do conjunto %d com duas colisões diferentes no arquivo' % key[::-1])
            done[key] = v
    changed = 0
    for (n, b), v in done.items():
        o = lo(0x98, 0x8000 + (n << 12) + b)
        if r.d[o] != v:
            r.d[o] = v
            changed += 1
    return ['colisão trocada em %d blocos (vale pro conjunto inteiro)' % changed] if changed else []


def apply_anims(r, docs):
    """durações das animações de tile ($81:C125 + id*2 → registro; +3 nº de quadros; +7 [dur][u16] por quadro)."""
    done, out = {}, []
    for doc in docs:
        for i, durs in doc['anims'].items():
            if done.get(i, durs) != durs:
                raise MapaErro('animação %02X com duas durações diferentes no arquivo' % i)
            done[i] = durs
    for i, durs in sorted(done.items()):
        p = 0x810000 | r16(r, 0x81C125 + i * 2)
        n = r.u8(0x81, p + 3)
        if len(durs) != n or any(not 1 <= x <= 255 for x in durs):
            raise MapaErro('animação %02X: %d quadros na ROM, %d no arquivo (ou duração fora de 1-255)'
                           % (i, n, len(durs)))
        old = [r.u8(0x81, p + 7 + 3 * k) for k in range(n)]
        if old != durs:
            for k, x in enumerate(durs):
                r.d[lo(0x81, p + 7 + 3 * k)] = x
            out.append('animação de tile %02X: durações %s → %s (vale pra toda área que usa ela)' % (i, old, durs))
    return out


def flat(ad):
    return set(ad['tiles'] + ad['sprites'] + ad['paletas'] + ad['meio'] + [x for one in ad['seg'] for x in one])


def apply_gfx(r, docs):
    """listas de gráfico (sprites/tile sets/paletas da área) regravadas no lugar: mesmo formato e tamanho da ROM."""
    report, done = [], {}
    for doc in docs:
        a, g = doc['area'], doc['gfx']
        if g is None or g == read_gfx(r, a):
            continue
        ad = gfx_addrs(r, a)
        shape = lambda x: (len(x['tiles']), len(x['sprites']), len(x['paletas']), len(x['meio']),
                           [len(o) for o in x['seg']])
        if shape(g) != shape(read_gfx(r, a)):
            raise MapaErro('área %d: listas de gráfico com outro tamanho que o da ROM (só troca no lugar)' % a)
        writes = [(x, v, 2) for x, v in zip(ad['tiles'], g['tiles'])]
        writes += [(x, s | b << 8, 2) for x, (s, b) in zip(ad['sprites'], g['sprites'])]
        writes += [(x, v, 2) for x, v in zip(ad['paletas'], g['paletas'])]
        writes += [(x, v, 2) for x, v in zip(ad['meio'], g['meio'])]
        writes += [(x, v, 2) for xs, vs in zip(ad['seg'], g['seg']) for x, v in zip(xs, vs)]
        for x, v, _ in writes:
            if done.get(x, v) != v:
                raise MapaErro('área %d: lista de gráfico dividida com outra área editada de outro jeito' % a)
            done[x] = v
        for x, v, _ in writes:
            r.w16(x >> 16, x & 0xFFFF, v)
        mine = {x for x, _, _ in writes}
        users = sorted(b for b in range(116) if b != a and flat(gfx_addrs(r, b)) & mine)
        report.append('área %d: listas de gráfico regravadas (troca de tipo)%s'
                      % (a, ' — também valem pras áreas %s' % users if users else ''))
    return report


def apply_objects(r, docs):
    """listas de objetos editadas: no lugar se couber, senão na metade nova da ROM de 4 MB."""
    report, todo = [], []
    for doc in docs:
        for k, lst in doc['objs'].items():
            if lst != rom_objects(r, k, doc['area']):
                todo.append((doc['area'], k, lst))
    ptrs = lambda: {(k, a): list_ptr(r, k, a) for a in range(116) for k in tabs_of(a)}
    grow = [t for t in todo if len(t[2]) > len(rom_objects(r, t[1], t[0]))]
    if grow and len(r.d) < 0x400000:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rom_expand'))
        import rom_expand
        try:
            r.d = bytearray(rom_expand.expand(r.d)[0])
        except ValueError as e:
            raise MapaErro('lista de objetos maior precisa da ROM de 4 MB e a expansão falhou: %s' % e)
        report.append('ROM expandida pra 4 MB (lista de objetos maior que a original)')
    for a, k, lst in todo:
        p = list_ptr(r, k, a)
        old = rom_objects(r, k, a)
        shared = sum(1 for q in ptrs().values() if q == p) > 1
        data = bytes([len(lst)]) + b''.join(struct.pack('<HHH', *e) for e in lst)
        if len(lst) <= len(old) and not shared:
            where = 'no lugar'
        else:
            if p >> 16 >= 0xC0 and not shared:                  # lista nossa na metade nova: libera
                o = lo(p >> 16, p)
                r.d[o:o + 1 + 6 * len(old)] = bytes(1 + 6 * len(old))
            p = alloc(r, len(data), ptrs())
            e = lo(0x81, TABS[k] + a * 3)
            r.d[e:e + 3] = bytes([p & 0xFF, p >> 8 & 0xFF, p >> 16])
            where = 'movida pra %02X:%04X' % (p >> 16, p & 0xFFFF)
        o = lo(p >> 16, p)
        r.d[o:o + len(data)] = data
        report.append('área %d, lista %s: %d → %d objetos (%s)' % (a, k, len(old), len(lst), where))
    return report


def alloc(r, size, ptrs):
    """endereço pra size bytes na metade nova ($C0-$FF), do fim pra baixo, sem cruzar banco: bytes todos 0 (o
    enchimento do rom_expand) com 1 byte de folga dos dois lados e fora de qualquer lista já apontada pelas tabelas."""
    used = []
    for p in set(ptrs.values()):
        if p >> 16 >= 0xC0:
            o = lo(p >> 16, p)
            used.append((o, o + 1 + 6 * r.d[o]))
    for bank in range(0xFF, 0xBF, -1):
        b0 = lo(bank, 0x8000)
        top = b0 + 0x8000
        while top - size - 2 >= b0:
            s0 = top - size - 2                                  # folga, dados, folga
            hit = [u for u in used if u[0] < top + 1 and u[1] > s0 - 1]
            if hit:
                top = min(u[0] for u in hit) - 1
                continue
            seg = r.d[s0:top]
            bad = [i for i, v in enumerate(seg) if v]
            if not bad:
                p = s0 + 1
                return (0x80 | p // 0x8000) << 16 | 0x8000 + p % 0x8000
            top = s0 + bad[-1]
    raise MapaErro('sem espaço livre na metade nova da ROM pra lista de %d bytes' % size)


def fix_checksum(rom):
    """soma do cabeçalho LoROM ($7FDC complemento, $7FDE soma), igual a rom_expand."""
    rom[0x7FDC:0x7FE0] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    c = s ^ 0xFFFF
    rom[0x7FDC:0x7FE0] = bytes([c & 0xFF, c >> 8, s & 0xFF, s >> 8])


def main(argv):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')          # console do Windows sem UTF-8 (→, acentos)
    if len(argv) >= 4 and argv[0] == 'exportar':
        r = R(open(argv[1], 'rb').read())
        save(argv[-1], [export(r, int(a)) for a in argv[2:-1]])
        print('gravado', argv[-1])
    elif len(argv) in (3, 4) and argv[0] == 'aplicar':
        rom = bytearray(open(argv[1], 'rb').read())
        out = argv[3] if len(argv) == 4 else os.path.splitext(argv[1])[0] + ' - mapa.sfc'
        if os.path.abspath(out) == os.path.abspath(argv[1]):
            sys.exit('a saída não pode ser a própria ROM de entrada')
        try:
            for line in apply(rom, load(argv[2])):
                print(line)
        except MapaErro as e:
            sys.exit('erro: %s (nada foi gravado)' % e)
        open(out, 'wb').write(rom)
        print('gravado', out)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
