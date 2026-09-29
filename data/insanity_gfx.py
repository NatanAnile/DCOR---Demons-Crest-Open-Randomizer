"""DCOR - itens com gráfico e paleta próprios (26/09).

Usa as peças de item_gfx.py (planejamento, registro de 22 B, código 65816) sobre a ROM original:
  - "que item está em qual lugar" vem da tabela de checks do gerador (insanity_rando);
  - VRAM planejada EM SEQUÊNCIA dentro da área: dois itens da mesma área não caem no mesmo lugar;
  - até 6 itens com gráfico próprio por área, nas entradas de sprite que a área não usa (contadas de $1E para
    baixo); buffers de cada entrada em $7F:E100-EE7F (medido intocado: 46 min, 40 áreas); código e dados no banco
    $C1 (metade nova da ROM de 4 MB, sem limite de espaço);
  - sem slot de paleta livre: o item PEGA o slot com menos donos e a paleta original volta quando ele some
    (pal_restore no 82:8752, por onde todo objeto passa ao se apagar);
  - se mesmo assim faltar entrada, ficam os de progressão (crest > Armor > vellum > talismã > potion).
HP, 20G e recarga não precisam: o gráfico deles está nos conjuntos fixos.
"""
import item_gfx as P
import palettes as cp
import rom_tables as v

# check -> (área onde o item nasce, lista do item original, item original no vocabulário do item_gfx, chefe?)
# 'TileSet' = o item original vem da lista principal da área; 'MidStage' = da lista do meio (drop de chefe).
# Itens originais 20G/recarga entram como 'Hp' (gráfico nos conjuntos fixos: o item novo precisa de VRAM própria).
GFX_INFO = {
    'Trio the Pago': ([52, 53, 54], 'MidStage', 'Hp', True),
    'Somulo (cabeça)': ([17], 'MidStage', 'Hp', True),
    'Pote 20G área 1': ([1], 'TileSet', 'Hp', False),
    'Estátua Vellum 00': ([1], 'TileSet', 'Vellum', False),
    'Hippogriff 1': ([1], 'MidStage', 'Hp', True),
    'Potion 0A': ([2], 'TileSet', 'Potion', False),
    'HP 07 chão': ([3], 'TileSet', 'Hp', False),
    'Pote recarga fase 1': ([1], 'TileSet', 'Hp', False),
    'Arma 1': ([3], 'MidStage', 'EarthCrest', True),
    'Potion 0C': ([5], 'TileSet', 'Potion', False),
    'Hand': ([5], 'TileSet', 'Hand', False),
    'Pote Vellum 02': ([6], 'TileSet', 'Vellum', False),
    'Pote HP 08': ([7], 'TileSet', 'Hp', False),
    'HP 0A pós-Flame Lord': ([50, 51], 'TileSet', 'Hp', False),
    'Pote recarga área 7': ([7], 'TileSet', 'Hp', False),
    'Pote 20G área 6': ([6], 'TileSet', 'Hp', False),
    'Ovnunu': ([8], 'MidStage', 'Buster', True),
    'Ossos HP 09': ([9], 'TileSet', 'Hp', False),
    'Belth': ([9], 'MidStage', 'Hp', True),
    'Pote 20G área 10 a': ([10], 'TileSet', 'Hp', False),
    'Pote 20G área 10 b': ([10], 'TileSet', 'Hp', False),
    'Pote 20G área 10 c': ([10], 'TileSet', 'Hp', False),
    'Potion 0E': ([10], 'TileSet', 'Potion', False),
    'Pote recarga área 11': ([11], 'TileSet', 'Hp', False),
    'Pote Vellum 04': ([11], 'TileSet', 'Vellum', False),
    'Skulla': ([13], 'MidStage', 'Hp', True),
    'Pote 20G área 13 a': ([13], 'TileSet', 'Hp', False),
    'Pote 20G área 13 b': ([13], 'TileSet', 'Hp', False),
    'Pote 20G área 13 c': ([13], 'TileSet', 'Hp', False),
    'Pote 20G área 13 d': ([13], 'TileSet', 'Hp', False),
    'Pote 20G área 13 e': ([13], 'TileSet', 'Hp', False),
    'Pote recarga área 14': ([14, 50, 51], 'TileSet', 'Hp', False),
    'Flame Lord': ([14, 50, 51], 'MidStage', 'Tornado', True),
    'Pote HP 0B': ([15], 'TileSet', 'Hp', False),
    'Skull': ([16], 'TileSet', 'Skull', False),
    'Potion 10': ([18], 'TileSet', 'Potion', False),
    'Pote 20G área 18': ([18], 'TileSet', 'Hp', False),
    'Pote recarga área 19': ([19], 'TileSet', 'Hp', False),
    'Flier 1': ([19], 'MidStage', 'Claw', True),
    'Hippogriff 2': ([20], 'MidStage', 'Hp', True),
    'Crown': ([22], 'TileSet', 'Crown', False),
    'Vellum 06': ([23], 'TileSet', 'Vellum', False),
    'Arma 2': ([23], 'MidStage', 'AirCrest', True),
    'Pote HP 0D': ([25], 'TileSet', 'Hp', False),
    'Holothurion': ([26], 'MidStage', 'Hp', True),
    'Crawler': ([27], 'MidStage', 'WaterCrest', True),
    'Estátua HP 0E': ([27], 'TileSet', 'Hp', False),
    'Estátua HP 05': ([28], 'TileSet', 'Hp', False),
    'Potion 12': ([29], 'TileSet', 'Potion', False),
    'Ossos Vellum 08': ([30], 'TileSet', 'Vellum', False),
    'Pote recarga área 30': ([30], 'TileSet', 'Hp', False),
    'Grewon': ([30], 'MidStage', 'DemonFire', True),
    'Pote HP 0F': ([32], 'TileSet', 'Hp', False),
    'Flier 2': ([34], 'MidStage', 'Hp', True),
    'Armor': ([35], 'TileSet', 'Armor', False),
    'Arma 3': ([36], 'MidStage', 'TimeCrest', True),
    'Sino HP 10': ([38], 'TileSet', 'Hp', False),
    'Fang': ([39], 'TileSet', 'Fang', False),
}
K = 6                                    # itens com gráfico próprio por área (buffers abaixo)
LAY = dict(work=0xE100, fr=0xE700, an=0xEA00, save=0xED00, emin=0x1E - 2 * (K - 1))
FIXED_BITS = (0x08, 0x02, 0x04)          # conjuntos fixos (rom_tables.FIXED_SETS): cada um usa 1 entrada
VANILLA_SET = {'Vellum': 0x138, 'Potion': 0x0F8, 'Crown': 0x144, 'Skull': 0x140, 'Armor': 0x100, 'Fang': 0x13C,
               'Hand': 0x148}


def priority(type_, sub):
    """menor = mais importante (quem fica com gráfico próprio quando a área passa de 2)."""
    if type_ == 0x48:
        return 0
    if type_ == 0x2E and sub == 0x04:
        return 1                                      # Armor (entra na lógica)
    if type_ == 0x2D and sub < 0x0A:
        return 2                                      # vellum (5 abrem o castelo)
    return 3 if type_ == 0x2E else 4


def tiles_of(vram, units):
    return {vram + 2 * k + d for k in range(units) for d in (0, 1, 16, 17)}


def apply(rom, van_bytes, ids):
    """rom: bytearray da ROM do Insanity (4 MB, itens já gravados); ids: check -> id do item. Devolve linhas."""
    van = v.Rom(van_bytes)
    lines = []
    pref_sprite = {}
    for sid in (0x4D, 0x4E, 0x4F, 0x50):
        cnt = cp.item_palettes(van)[0].get(sid)
        pref_sprite[sid] = [p for p, _ in cnt.most_common() if p in P.ITEM_PAL][0] if cnt else 0x45
    keys = {a: (van.u16(v.TBL_TILES + a * 2), van.u16(v.TBL_SPR + a * 2),
                van.u16((0xBD0000 | van.u16(v.MID_OPERAND)) + a * 2)) for a in range(116)}

    # candidatos por área (a área "dona" é a 1ª da lista; gêmeas com as mesmas tabelas recebem o mesmo registro)
    wanted = []
    for loc, (areas, vlist, vitem, boss) in GFX_INFO.items():
        i = ids[loc]
        type_, sub = i & 0xFF, (i >> 8) & 0x3F
        if P.item_def(van, type_, sub) is None:
            continue                                  # HP / 20G / recarga: conjuntos fixos
        for area in areas:
            wanted.append((priority(type_, sub), loc, area, vlist, vitem, boss, type_, sub))
    by_area = {}
    for w in sorted(wanted):
        by_area.setdefault(keys[w[2]], []).append(w)

    records, all_recs = {}, []
    def plan_area(key, ws, no_sparkle):
        occupied, placed, out, failed = set(), [], [], False
        for pr, loc, area, vlist, vitem, boss, type_, sub in ws:
            if any(r['loc'] == loc for r in placed):
                continue                              # mesmo check em área gêmea: já planejado
            twins = [a2 for a2 in range(116) if keys[a2] == key]
            used = max(2 + sum(1 for b in FIXED_BITS if van.u8(v.TBL_FLAG + a2) & b) + len(van.sprite_list(a2))
                       for a2 in twins)
            E = 0x1E - 2 * len(placed)
            if len(placed) >= K or E < 2 * used:
                out.append('%-22s área %3d: sem entrada de sprite livre (área usa %d), comportamento original'
                           % (loc, area, used))
                continue
            name, sid, tset, qs, anim = P.item_def(van, type_, sub)
            twin = next((q for q in placed if (q['sid'], q['tset'], tuple(q['qs'])) == (sid, tset, tuple(qs))), None)
            if twin is not None:                      # mesmo desenho já na área: divide VRAM e paleta
                r = dict(twin, loc=loc, area=area, type=type_, sub=sub, name=name)
                out.append('%-22s área %3d %-10s divide VRAM %03X e paleta slot %d com %s' % (
                    loc, area, name, r['vram'], r['slot'], twin['loc']))
            else:
                r = plan(van, loc, area, vlist, vitem, boss, type_, sub, occupied, pref_sprite, out, no_sparkle)
                if r is None:
                    failed = True
                    continue
                occupied |= tiles_of(r['vram'], r['units'])
            r['E'] = E
            placed.append(r)
        return placed, out, failed

    for key, ws in by_area.items():
        placed, out, failed = plan_area(key, ws, False)
        if failed:                                    # área apertada: todos só com o desenho parado (1 unidade)
            placed2, out2, failed2 = plan_area(key, ws, True)
            if len(placed2) > len(placed):
                placed, out = placed2, out2 + ['   (área apertada: itens sem brilho para caber mais)']
        lines.extend(out)
        all_recs.extend(placed)
        for r in placed:
            for a2 in range(116):
                if keys[a2] == key:
                    records.setdefault(a2, []).append(r)

    write(rom, van, records, all_recs, lines)
    apply.records = [r for r in all_recs if not r.get('dropped')]
    return lines


def expected_tiles(van, r):
    """{tile de VRAM: 32 bytes} que o registro r deve deixar na VRAM (mesma regra do item_gfx.build_record)."""
    qd = P.frames(van, r['sid'])
    used = [qd[q] for q in r['qs']]
    units = sorted({P.unit_of_tile(p[3]) for q in used for p in q})
    if len(units) > r['units']:
        used = [used[0]] * len(used)
        units = sorted({P.unit_of_tile(p[3]) for q in used for p in q})
    src, B, out = P.tiles_of_set(van, r['tset']), r['vram'], {}
    if len(units) > r['units']:                       # desenho parado reempacotado numa unidade
        for t, d in zip(sorted({p[3] for p in used[0]}), (0, 1, 16, 17)):
            out[B + d] = bytes(src[t])
    else:
        for block, u in enumerate(units):
            rel = (u // 8) * 32 + 2 * (u % 8)
            for d in (0, 1, 16, 17):
                if rel + d in src:
                    out[B + 2 * block + d] = bytes(src[rel + d])
    return out


def plan(van, loc, area, vlist, vitem, boss, type_, sub, occupied, pref_sprite, lines, no_sparkle=False):
    """VRAM e slot de paleta de um item, com a VRAM já ocupada por outro item da área."""
    name, sid, tset, qs, anim = P.item_def(van, type_, sub)
    ents, last_used, fixed = P.layout(van, area)
    before, after = cp.states(van, area)
    state = before if vlist == 'TileSet' else after
    item_frames = P.frames(van, sid)
    idle = item_frames[qs[0]]
    minimum = len({P.unit_of_tile(x[3]) for x in idle})
    ideal = len({P.unit_of_tile(x[3]) for q in qs for x in item_frames[q]})
    packable = minimum > 1 and len({x[3] for x in idle}) <= 4 and not any(x[4] & 0x10 for x in idle)
    vanilla_set = None
    if vitem != 'Hp':
        vanilla_set = VANILLA_SET.get(vitem, 0x0F4 if 'Crest' in vitem else 0x0FC)
    free = lambda b, n: P.fits(b, n) and not (tiles_of(b, n) & occupied)
    vram, units, in_pot = None, 0, False
    for need, top in [(minimum, minimum if no_sparkle else ideal)] + ([(1, 1)] if packable else []):
        if vram is not None:
            break
        if vanilla_set is not None:
            kind = 'p' if vlist == 'TileSet' else 'm'
            cands = [b for k, t, b in ents if t == vanilla_set and k == kind] or \
                    [b for k, t, b in ents if t == vanilla_set]
            for c in cands:
                avail = min(2, van.units(vanilla_set))
                while avail > need and not free(c, avail):
                    avail -= 1
                if avail >= need and free(c, need):
                    vram, units = c, min(avail, top)
                    break
        if vram is None:
            fixed_above = min([x for x in fixed if x >= last_used] or [0x200])
            b = last_used
            while b < fixed_above and not (free(b, need) and b + 16 + 2 * need - 1 < fixed_above):
                b += 1
            if b < fixed_above:
                vram = b
                units = top if free(b, top) and b + 16 + 2 * top - 1 < fixed_above else need
        if vram is None and area in P.POT_SPOT and need == 1 and not (tiles_of(P.POT_SPOT[area], 1) & occupied):
            vram, units, in_pot = P.POT_SPOT[area], 1, True
    if packable:
        minimum = 1
    slot, writes = None, None
    if vitem != 'Hp':
        vanilla_spr = {0x0F4: 0x4D, 0x0FC: 0x4F, 0x138: 0x4E, 0x0F8: 0x4E}.get(vanilla_set, 0x50)
        pals = [p // 2 for s, p in van.sprite_list(area) if s == vanilla_spr]
        if pals:
            slot = pals[-1]
    else:
        owners = P.slot_owners(van, area)
        stable = [s for s in before if before[s] in P.ITEM_PAL and after.get(s) == before[s]]
        free_slots = [s for s in range(1, 6) if s not in before and s not in after]
        item_only = [s for s in range(1, 6) if (s in before or s in after)
                     and owners.get(s) and owners[s] <= set(cp.ITEMS)]
        boss_slots = []
        if boss:
            boss_slots = sorted(cp.mid_palettes(van, area))
            n_mid = len(van.mid(area)[1])
            if not boss_slots and n_mid:
                boss_sprites = {s for s, _ in van.sprite_list(area)[:n_mid]}
                boss_slots = sorted(s for s, own in owners.items() if own and own <= boss_sprites)
            if not boss_slots and area in P.MEASURED_SLOT:
                boss_slots = [P.MEASURED_SLOT[area]]
        slot = (stable or free_slots or item_only or boss_slots or [None])[0]
    steal = None
    if slot is None:
        # nenhum slot livre: pega o de menos donos (1-5; 0 é a paleta comum, 6-7 são do Firebrand). A paleta original
        # volta quando o item some (pal_restore). Desempate: o de número maior (os primeiros costumam ser do chefe).
        owners = P.slot_owners(van, area)
        slot = min(range(1, 6), key=lambda s_: (len(owners.get(s_, ())), -s_))
        steal = sorted(owners.get(slot, ()))
    if slot is not None and state.get(slot) not in P.ITEM_PAL:
        writes = pref_sprite[sid]
    status = []
    if vram is None:
        lines.append('%-22s área %3d %-10s (original %-10s) SEM VRAM: comportamento original' % (loc, area, name, vitem))
        return None
    if in_pot:
        status.append('na unidade do pote')
    if steal is not None:
        status.append('pega o slot %d (dono: %s), devolve ao sumir' % (slot, ' '.join('%02X' % x for x in steal) or '-'))
    lines.append('%-22s área %3d %-10s (original %-10s) VRAM %03X x%d paleta slot %d %s%s' % (
        loc, area, name, vitem, vram, units, slot,
        'grava %02X' % writes if writes else '(já %02X)' % state.get(slot, 0), '  ' + '; '.join(status) if status else ''))
    return dict(loc=loc, area=area, type=type_, sub=sub, name=name, sid=sid, tset=tset, qs=qs, anim=anim,
                vram=vram, units=units, minimum=minimum, slot=slot, writes=writes, borrow=None, steal=steal)


def write(rom, van, records, all_recs, lines):
    """código + tabela por área + registros no banco $C1, ganchos dos itens, da caixa de mensagem e do apagar objeto."""
    code, labels = P.build_code(LAY)
    data_start = P.BASE + 232 + len(code)

    def build():
        data, positions = bytearray(), {}
        def put(b):
            b = bytes(b)
            if b not in positions:
                positions[b] = data_start + len(data)
                data.extend(b)
            return positions[b]
        pal_cache, area_list, done = {}, {}, {}
        for area, recs in sorted(records.items()):
            alive = [r for r in recs if not r.get('dropped')]
            if not alive:
                continue
            body = bytearray([len(alive)])
            for r in alive:
                k = (r['loc'], r['E'])
                if k not in done:
                    done[k] = put(P.build_record(van, r, put, pal_cache, r['E']))
                body += done[k].to_bytes(2, 'little')
            area_list[area] = put(bytes(body))
        return data, area_list

    data, area_list = build()
    assert data_start + len(data) <= P.LIMIT, 'dados passam do banco $C1'
    base = (P.BANK << 16) | P.BASE

    def put_at(addr, b):
        o = v.ea(addr)
        rom[o:o + len(b)] = b
    area_table = bytearray(232)
    for area, p in area_list.items():
        area_table[2 * area:2 * area + 2] = p.to_bytes(2, 'little')
    o = v.ea(base)
    assert not any(rom[o:o + 232 + len(code) + len(data)]), 'banco $C1 não está vazio'
    put_at(base, area_table)
    put_at(base + 232, code)
    put_at((P.BANK << 16) | data_start, data)
    for addr, name, expected in ((0x82E086, 'h_talisman', 'ad800d80'), (0x82E09B, 'h_vellum', 'ad7e0d85'),
                                 (0x82EA0F, 'h_crest', 'b9300d29')):
        assert rom[v.ea(addr):v.ea(addr) + 4].hex() == expected, '%06X: bytes inesperados' % addr
        put_at(addr, bytes([0x5C]) + labels[name].to_bytes(3, 'little'))
    for addr, name, n, expected in ((0xBEDC77, 'box_open', 5, 'a9308d5b0e'),
                                    (0xBEDE92, 'box_close', 6, '9cb4009cb500'),
                                    (0xBEDC88, 'box_math', 5, 'a9200cb200'),
                                    (0xBEDC8D, 'box_color', 15, 'a9108db600a9088db400a9018db500')):
        assert rom[v.ea(addr):v.ea(addr) + n].hex() == expected, '%06X: bytes inesperados' % addr
        put_at(addr, bytes([0x22]) + labels[name].to_bytes(3, 'little') + bytes([0xEA]) * (n - 4))
    # apagar objeto (82:8752 SEP #$30 / LDA $00): devolve a paleta que um item pegou emprestada
    assert rom[v.ea(0x828752):v.ea(0x828752) + 4].hex() == 'e230a500', '82:8752: bytes inesperados'
    put_at(0x828752, bytes([0x5C]) + labels['pal_restore'].to_bytes(3, 'little'))
    lines.append('%d B de código, %d B de dados ($C1:8000-%04X), %d áreas com registro, %d itens' % (
        len(code), len(data), data_start + len(data) - 1, len(area_list), len(all_recs)))
