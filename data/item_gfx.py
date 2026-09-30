"""Itens com gráfico e paleta próprios: planejamento de VRAM/paleta, registro de 22 B e código 65816.

Cada item que não é HP/20G/recarga (esses vivem nos conjuntos fixos) ganha um registro por área: onde fica na VRAM,
que slot de paleta usa e os quadros/animação reconstruídos. Ganchos em 82:E086 (talismã), 82:E09B (vellum/potion) e
82:EA0F (crest): se a área tem registro do item, o código enfileira o DMA do gráfico, copia a paleta e aponta a
entrada de sprite para os quadros montados na WRAM; sem registro, segue o comportamento original.
Mais dois ganchos na caixa de mensagem (ver build_code) e o pal_restore (82:8752). Quem planeja por área e grava é o
insanity_gfx.py; aqui ficam as peças.
"""
import graphics as g
import rom_tables as v
from asm65816 import Asm

BANK, BASE, LIMIT = 0xC1, 0x8000, 0x10000           # código + dados: banco $C1 (metade nova da ROM de 4 MB)
ITEM_PAL = (0x45, 0x46, 0x47, 0x48)
TMP_KEY, TMP_N, TMP_REC = 0x7F7FF0, 0x7F7FF2, 0x7F7FF4
TMP_FILL, TMP_M0, TMP_M1, TMP_ADJUST = 0x7F7FF6, 0x7F7FF7, 0x7F7FF8, 0x7F7FFA
TMP_MASK, TMP_COUNT, TMP_OFF = 0x7F7FFC, 0x7F7FFD, 0x7F7FEE
REC = 22

# item: (type, subtype) -> sprite, tile set, main frame, animation
FIRE_SUB = {0x00: ('Buster', 2), 0x02: ('Tornado', 3), 0x04: ('Claw', 0), 0x06: ('DemonFire', 4),
            0x10: ('FireCrest', 1)}     # 10 = Fire Crest do DCOR (29/09): quadro 1 do sprite 4F, sem uso no original
CREST_SUB = {0x08: ('EarthCrest', 0), 0x0A: ('AirCrest', 2), 0x0C: ('WaterCrest', 1), 0x0E: ('TimeCrest', 3)}
TALISMAN_SET = {0x00: ('Crown', 0x144), 0x02: ('Skull', 0x140), 0x04: ('Armor', 0x100), 0x06: ('Fang', 0x13C),
                0x08: ('Hand', 0x148)}
# slot picked by LIVE MEASUREMENT for areas where the boss brings no palette through the mid-stage.
# 0: slot 1 (the one that flashed when the boss took damage, log from 22/09).
# 17 (Somulo): slot 4 instead of 1. Somulo uses slots 1 AND 2 (sprite 09 has pieces with palette bit 1) and
# palettes 11/12 are identical, so putting the item on 1 or 2 wrecks his head, which stays on screen after he
# dies. Slot 4 (owner = sprite 11) had zero usage in 19 captures of that room; slot 3 is the fire and 5 shows
# up now and then.
MEASURED_SLOT = {17: 4, 0: 1}
# area -> VRAM unit of a pot that holds the item (MEASURED, exclusive to these areas; idea from Neitan, 25/09): the
# area has a single pot, it is deleted when broken and never respawns, and the item only exists after it breaks — so
# the item can take the pot's unit for good. The fixed set is loaded again on the next area load. Idle drawing only.
# 25: pot = tiles 0AE/0AF/0BE/0BF of the fixed set 024 (the area has no free tile at all, 24/09).
POT_SPOT = {25: 0x0AE}


def frames_ptr(rom, sid):
    e = 0x8B8000 + sid * 3
    lo, b = rom.u16(e), rom.u8(e + 2)
    y = lo + 0x8000
    c = y > 0xFFFF
    y &= 0xFFFF
    if c:
        y |= 0x8000
    return ((0x8B + b + c) << 16) | y


def frames(rom, sid):
    """list of frames; each one = list of pieces (a, b, c, relative tile, attribute)."""
    f = g.Stream(rom, frames_ptr(rom, sid))
    n = f.byte()
    for _ in range(2 * n):
        f.byte()
    sg = lambda x: x - 256 if x > 127 else x
    out = []
    for _ in range(n):
        p = f.byte()
        out.append([(sg(f.byte()), sg(f.byte()), sg(f.byte()), f.byte(), f.byte()) for _ in range(p)])
    return out


def anim_script(rom, sid, anim):
    lo = rom.u16(0x8EC000 + sid * 2)
    y = lo + 0xC000
    c = y > 0xFFFF
    y &= 0xFFFF
    if c:
        y |= 0xC000
    f = g.Stream(rom, ((0x8E + c) << 16) | y)
    n = f.byte() | f.byte() << 8
    d = bytes(f.byte() for _ in range(n))
    off, seq = d[anim] | d[anim + 1] << 8, []
    while d[off] != 0:
        seq.append((d[off], d[off + 1]))
        off += 2
    return seq


def tiles_of_set(rom, tset):
    """dict relative_tile -> 32 bytes (allocator grid: unit k at 2k of the double row k//8)."""
    out = {}
    for k, u in enumerate(g.units(rom, tset)):
        r = (k // 8) * 32 + 2 * (k % 8)
        out[r], out[r + 1], out[r + 16], out[r + 17] = u
    return out


def item_def(rom, type_, sub):
    """(name, sprite, tile set, frames used [(idle), (sparkle), (drop)], animation script)."""
    if type_ == 0x48 and sub in FIRE_SUB:
        name, q = FIRE_SUB[sub]
        return name, 0x4F, 0x0FC, [q], [(1, 0)]
    if type_ == 0x48 and sub in CREST_SUB:
        name, q = CREST_SUB[sub]
        seq = anim_script(rom, 0x4D, rom.u8(0x81D744 + sub + 1))
        return name, 0x4D, 0x0F4, [q, 6 + q, 12], [(seq[0][0], 0), (seq[1][0], 1), (seq[2][0], 2)]
    if type_ == 0x2E and sub in TALISMAN_SET:
        name, t = TALISMAN_SET[sub]
        return name, 0x50, t, [0], [(1, 0)]
    if type_ == 0x2D:
        return ('Vellum' if sub < 0x0A else 'Potion'), 0x4E, (0x138 if sub < 0x0A else 0x0F8), [0], [(1, 0)]
    return None


def layout(rom, a):
    """bases per list: [('p'|'m'|'s', tile set, base)], last occupied tile, fixed bases."""
    flag = rom.u8(v.TBL_FLAG + a)
    al = v.Allocator(rom, flag)
    start = al.base()
    ents = []
    for t in rom.tile_list(a):
        ents.append(('p', t, al.base())); al.load(t)
    end = al.base()
    fx, ms = rom.mid(a)
    am = v.Allocator(rom, flag)
    for t in ms:
        ents.append(('m', t, am.base())); am.load(t)
    mid_end = am.base() if ms else start
    seg_end = end
    for one_pass in rom.segments(a):
        s2 = v.Allocator(rom, flag)
        for t in rom.tile_list(a):
            s2.load(t)
        for t in one_pass:
            ents.append(('s', t, s2.base())); s2.load(t)
        seg_end = max(seg_end, s2.base())
    return ents, max(end, mid_end, seg_end), fx


def slot_owners(rom, area):
    """{palette slot: sprites drawn with it}. The slot is the 2nd byte of the list (palette*2) PLUS the
    palette bits of each piece's attribute (80:D9A7/DA3C adds them): a large boss uses 2 slots (area 27:
    sprite 6F uses 3 and 4)."""
    d = {}
    for sid, pal in rom.sprite_list(area):
        try:
            bits = {(piece[4] >> 1) & 7 for q in frames(rom, sid) for piece in q}
        except Exception:
            bits = {0}                                # unreadable frame: count only the list slot
        for b in bits:
            d.setdefault(pal // 2 + b, set()).add(sid)
    return d


def fits(base, units):
    return base % 16 + 2 * units <= 16 and base + 16 + 2 * units - 1 < 0x200



def unit_of_tile(r):
    return (r // 32) * 8 + (r % 16) // 2


def unit_ptr(rom, tset, k):
    """address in the compressed stream where unit k starts (8 C300 calls per unit)."""
    ptr = rom.u16(v.DIR_SETS + tset) | rom.u8(v.DIR_SETS + tset + 2) << 16
    f = g.Stream(rom, ptr)
    for _ in range(8 * k):
        g.c300_call(f)
    return (f.bank << 16) | f.y


def c300_pack(unit):
    """128 bytes (one 16x16 unit, top row then bottom row) -> stream for the 80:C300 decompressor: 8 groups of
    [mask0][mask1][fill][literals]; a mask bit of 1 (bit 7 first) reads a literal, 0 writes the fill byte."""
    out = bytearray()
    for g0 in range(0, 128, 16):
        group = unit[g0:g0 + 16]
        fill = max(sorted(set(group)), key=group.count)      # most frequent; tie -> lowest value
        masks, lits = [], bytearray()
        for half in (group[:8], group[8:]):
            m = 0
            for k, b in enumerate(half):
                if b != fill:
                    m |= 0x80 >> k
                    lits.append(b)
            masks.append(m)
        out += bytes([masks[0], masks[1], fill]) + lits
    return bytes(out)


def build_record(van, r, put, pal_cache, E):
    """22-byte record + frames/animation built for sprite entry E."""
    qd = frames(van, r['sid'])
    used = [qd[q] for q in r['qs']]
    units = sorted({unit_of_tile(p[3]) for q in used for p in q})
    if len(units) > r['units']:                       # no room for the sparkle: idle drawing only
        used = [used[0]] * len(used)
        units = sorted({unit_of_tile(p[3]) for q in used for p in q})
    B = r['vram']
    raw = None
    if len(units) > r['units']:
        # repack: an idle drawing of <= 4 pieces of 8x8 goes into ONE unit, tiles in order at B, B+1, B+16, B+17,
        # stored raw (already decompressed) in the data block; the routine copies them instead of decompressing
        idle = used[0]
        tiles = sorted({p[3] for p in idle})
        if r['units'] != 1 or len(tiles) > 4 or any(p[4] & 0x10 for p in idle):
            # never: this would write over the neighbour's graphics
            raise SystemExit('%s: %d units in a space of %d' % (r['loc'], len(units), r['units']))
        tile_map = {t: B + d for t, d in zip(tiles, (0, 1, 16, 17))}
        src = tiles_of_set(van, r['tset'])
        raw = b''.join(bytes(src[t]) for t in tiles) + bytes(32 * (4 - len(tiles)))
    else:
        tile_map = {}
        for block, u in enumerate(units):
            rel_base = (u // 8) * 32 + 2 * (u % 8)
            for d in (0, 1, 16, 17):
                tile_map[rel_base + d] = B + 2 * block + d
    bodies = []
    for q in used:
        c = bytearray([len(q)])
        for a_, b_, c_, t, at in q:
            dst = tile_map[t]
            for x in (a_, b_, c_):
                c += (x & 0xFFFF).to_bytes(2, 'little')
            c += bytes([dst & 0xFF, (at + r['slot'] * 2 + (dst >> 8)) & 0xFF])
        bodies.append(c)
    table, off = bytearray(), 2 * len(bodies)
    for c in bodies:
        table += off.to_bytes(2, 'little')
        off += len(c)
    frames_bin = bytes(table) + b''.join(bodies)
    script = bytearray()
    for dur, q in r['anim']:
        script += bytes([dur, q])
    script += bytes([0, 0])
    n_anim = {0x4F: 5, 0x4D: 4}.get(r['sid'], 1)
    anim_bin = b''.join((2 * n_anim).to_bytes(2, 'little') for _ in range(n_anim)) + bytes(script)
    blob_ptr = put(frames_bin + anim_bin)
    pal_ptr = 0
    if r['writes']:
        pid = r['writes']
        if pid not in pal_cache:
            o = v.ea(0x999100 + pid * 32)
            pal_cache[pid] = put(van.b[o:o + 32])
        pal_ptr = pal_cache[pid]
    if raw is not None:                # the repacked unit, compressed in the game's own format: same decompressor
        srcs, n_units = [(BANK << 16) | put(c300_pack(raw)), 0], 1
    else:
        srcs, n_units = [unit_ptr(van, r['tset'], u) for u in units] + [0], len(units)
    rec = bytearray([r['type'], r['sub'], E, r['slot']])
    rec += (0x6000 + B * 16).to_bytes(2, 'little') + (64 * n_units).to_bytes(2, 'little')
    rec += bytes([n_units, 0]) + pal_ptr.to_bytes(2, 'little') + blob_ptr.to_bytes(2, 'little')
    rec += bytes([len(frames_bin), len(anim_bin)])
    rec += srcs[0].to_bytes(3, 'little') + srcs[1].to_bytes(3, 'little')
    assert len(rec) == REC
    return bytes(rec)


def build_code(L):
    """L = WRAM layout: work/fr/an = buffers per entry (decompressed tiles, frames, animation), save = palette save
    area, emin = lowest sprite entry used by items (entries are counted down from $1E)."""
    a = Asm((BANK << 16) | (BASE + 232))
    C = lambda off: (BANK << 16) | off
    def db7e():
        a.op('SEP', 'imm8', 0x20); a.op('LDA', 'imm8', 0x7E); a.op('PHA'); a.op('PLB'); a.op('REP', 'imm8', 0x20)

    # ---- decompressor (port of 80:C300 without the cooperative pause); A 8-bit, X/Y 16-bit ----
    # source: DB:Y (rolls the bank over and goes back to $8000, like 80:C345); destination: $7F0000+X
    a.label('read')
    a.op('LDA', 'absy', 0x0000); a.op('INY'); a.br('BNE', 'read_end')
    a.op('PHA'); a.op('PHB'); a.op('PLA'); a.op('INC', 'acc'); a.op('PHA'); a.op('PLB')
    a.op('LDY', 'imm16', 0x8000); a.op('PLA')
    a.label('read_end')
    a.op('RTS')
    a.label('mask')                                   # A = mask; 8 output bytes, bit 7 first
    a.op('STA', 'long', TMP_MASK); a.op('LDA', 'imm8', 8); a.op('STA', 'long', TMP_COUNT)
    a.label('m_loop')
    a.op('LDA', 'long', TMP_MASK); a.op('ASL', 'acc'); a.op('STA', 'long', TMP_MASK); a.br('BCS', 'm_lit')
    a.op('LDA', 'long', TMP_FILL); a.br('BRA', 'm_store')
    a.label('m_lit'); a.op('JSR', 'abs', 'read')
    a.label('m_store'); a.op('STA', 'longx', 0x7F0000); a.op('INX')
    a.op('LDA', 'long', TMP_COUNT); a.op('DEC', 'acc'); a.op('STA', 'long', TMP_COUNT); a.br('BNE', 'm_loop')
    a.op('RTS')
    a.label('group')
    a.op('JSR', 'abs', 'read'); a.op('STA', 'long', TMP_M0)
    a.op('JSR', 'abs', 'read'); a.op('STA', 'long', TMP_M1)
    a.op('JSR', 'abs', 'read'); a.op('STA', 'long', TMP_FILL)
    a.op('LDA', 'long', TMP_M0); a.op('JSR', 'abs', 'mask')
    a.op('LDA', 'long', TMP_M1); a.op('JSR', 'abs', 'mask')
    a.op('RTS')
    a.label('unit')                                   # top row (64 bytes), then skip to the bottom row
    for _ in range(4):
        a.op('JSR', 'abs', 'group')
    a.op('REP', 'imm8', 0x20); a.op('TXA'); a.op('CLC'); a.op('ADC', 'long', TMP_ADJUST); a.op('TAX')
    a.op('SEP', 'imm8', 0x20)
    for _ in range(4):
        a.op('JSR', 'abs', 'group')
    a.op('RTS')

    # ---- common routine: A = (subtype<<8)|type; C=1 and A=entry if found ----
    a.label('common')
    a.op('PHB'); a.op('PHX'); a.op('PHY')
    a.op('STA', 'long', TMP_KEY)
    db7e()
    a.op('LDA', 'abs', 0x008D); a.op('AND', 'imm16', 0x00FF); a.op('TAX')
    a.op('LDA', 'longx', C(BASE)); a.br('BEQ', 'not_found'); a.op('TAX')
    a.op('LDA', 'longx', C(0)); a.op('AND', 'imm16', 0x00FF); a.br('BEQ', 'not_found')
    a.op('STA', 'long', TMP_N); a.op('INX')
    a.label('loop')
    a.op('PHX'); a.op('LDA', 'longx', C(0)); a.op('TAX')
    a.op('LDA', 'longx', C(0)); a.op('CMP', 'long', TMP_KEY); a.br('BEQ', 'found_px')
    a.op('PLX'); a.op('INX'); a.op('INX')
    a.op('LDA', 'long', TMP_N); a.op('DEC', 'acc'); a.op('STA', 'long', TMP_N); a.br('BNE', 'loop')
    a.label('not_found')
    a.op('PLY'); a.op('PLX'); a.op('PLB'); a.op('CLC'); a.op('RTL')
    a.label('found_px')
    a.op('PLA')                                       # drop the saved list pointer
    a.op('TXA'); a.op('STA', 'long', TMP_REC)
    a.op('LDA', 'longx', C(2)); a.op('AND', 'imm16', 0x00FF)
    a.op('EOR', 'imm16', 0xFFFF); a.op('SEC'); a.op('ADC', 'imm16', 0x001E)   # OFF = ($1E - E) * $40
    for _ in range(6):
        a.op('ASL', 'acc')
    a.op('STA', 'long', TMP_OFF)
    # palette: ROM -> $7E:0400+slot*32 and a copy at $7F:A100+slot*32
    a.op('LDA', 'longx', C(10))
    a.br('BNE', 'has_pal'); a.op('BRL', 'rell', 'no_pal'); a.label('has_pal')   # no_pal: too far for a short branch
    a.op('PHA')
    a.op('LDA', 'longx', C(3)); a.op('AND', 'imm16', 0x00FF)
    for _ in range(5):
        a.op('ASL', 'acc')
    a.op('CLC'); a.op('ADC', 'imm16', 0x0400); a.op('TAY')
    # Keeps what was in the slot (32 B of palette + slot + area) at SAVE + OFF/2 so pal_restore can give it back
    # when the item goes away. Not again if this entry already holds a save from this same area (a 2nd spawn of
    # the item would save its own palette). A/X/Y 16-bit, DB = $7E, Y = $0400+slot*32, stack top = pal_ptr.
    a.op('PHY')                                                       # [.. pal_ptr, dest]
    a.op('LDA', 'long', TMP_OFF); a.op('LSR', 'acc'); a.op('CLC'); a.op('ADC', 'imm16', L['save']); a.op('TAX')
    a.op('LDA', 'longx', 0x7F0020); a.op('AND', 'imm16', 0xFF00); a.op('CMP', 'imm16', 0xA500)
    a.br('BNE', 'save_do')
    a.op('LDA', 'longx', 0x7F0022); a.op('AND', 'imm16', 0x00FF); a.op('STA', 'long', TMP_KEY)
    a.op('LDA', 'long', 0x7E008D); a.op('AND', 'imm16', 0x00FF); a.op('CMP', 'long', TMP_KEY)
    a.br('BEQ', 'save_skip')
    a.label('save_do')
    a.op('TXA'); a.op('TAY'); a.op('PLX'); a.op('PHX')                 # Y = save, X = $0400+slot*32
    a.op('LDA', 'imm16', 0x001F); a.mvn(0x7F, 0x7E)                    # DB = $7F, Y = save + $20
    a.op('LDA', 'long', TMP_REC); a.op('TAX'); a.op('SEP', 'imm8', 0x20)
    a.op('LDA', 'longx', C(3)); a.op('STA', 'absy', 0x0000)           # +20 slot
    a.op('LDA', 'imm8', 0xA5); a.op('STA', 'absy', 0x0001)             # +21 mark
    a.op('LDA', 'long', 0x7E008D); a.op('STA', 'absy', 0x0002)         # +22 area*2
    a.op('REP', 'imm8', 0x20)
    a.label('save_skip')
    a.op('PLY')                                                       # dest; stack top = pal_ptr again
    a.op('PLX'); a.op('PHY'); a.op('LDA', 'imm16', 0x001F); a.mvn(0x7E, BANK)
    a.op('PLX'); a.op('TXA'); a.op('CLC'); a.op('ADC', 'imm16', 0x9D00); a.op('TAY')
    a.op('LDA', 'imm16', 0x001F); a.mvn(0x7F, 0x7E)
    # $80 = "palette dirty": without it the NMI (80:8421) never sends the $0300 buffer to CGRAM and the color
    # does not change on screen
    a.op('SEP', 'imm8', 0x20); a.op('LDA', 'imm8', 0x01); a.op('STA', 'long', 0x7E0080); a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    a.label('no_pal')
    # graphics: decompress 1 or 2 units into the work area and queue 2 DMAs
    a.op('LDA', 'longx', C(8)); a.op('AND', 'imm16', 0x00FF); a.br('BNE', 'has_gfx'); a.op('BRL', 'rell', 'no_queue')
    a.label('has_gfx')
    a.op('LDA', 'longx', C(6)); a.op('SEC'); a.op('SBC', 'imm16', 0x0040); a.op('STA', 'long', TMP_ADJUST)
    a.op('PHB')
    a.op('LDA', 'longx', C(16)); a.op('TAY')
    a.op('SEP', 'imm8', 0x20); a.op('LDA', 'longx', C(18)); a.op('PHA'); a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'long', TMP_OFF); a.op('ASL', 'acc'); a.op('CLC'); a.op('ADC', 'imm16', L['work']); a.op('TAX')
    a.op('SEP', 'imm8', 0x20); a.op('PLB'); a.op('JSR', 'abs', 'unit'); a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    a.op('LDA', 'longx', C(8)); a.op('AND', 'imm16', 0x00FF); a.op('CMP', 'imm16', 0x0002); a.br('BNE', 'one_only')
    a.op('LDA', 'longx', C(19)); a.op('TAY')
    a.op('SEP', 'imm8', 0x20); a.op('LDA', 'longx', C(21)); a.op('PHA'); a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'long', TMP_OFF); a.op('ASL', 'acc'); a.op('CLC'); a.op('ADC', 'imm16', L['work'] + 0x40); a.op('TAX')
    a.op('SEP', 'imm8', 0x20); a.op('PLB'); a.op('JSR', 'abs', 'unit'); a.op('REP', 'imm8', 0x20)
    a.label('one_only')
    a.op('PLB')
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    db7e()
    a.op('LDA', 'abs', 0x0081); a.op('AND', 'imm16', 0x00FF); a.op('CMP', 'imm16', 0x00E0)
    a.br('BCC', 'queue_fits'); a.op('BRL', 'rell', 'no_queue')
    a.label('queue_fits')
    a.op('TAY')
    a.op('SEP', 'imm8', 0x20)
    a.op('LDA', 'imm8', 0x80); a.op('STA', 'absy', 0x0500); a.op('STA', 'absy', 0x0508)
    a.op('LDA', 'imm8', 0x7F); a.op('STA', 'absy', 0x0507); a.op('STA', 'absy', 0x050F)
    a.op('REP', 'imm8', 0x20)
    a.op('LDA', 'longx', C(4)); a.op('STA', 'absy', 0x0501); a.op('CLC'); a.op('ADC', 'imm16', 0x0100)
    a.op('STA', 'absy', 0x0509)
    a.op('LDA', 'longx', C(6)); a.op('STA', 'absy', 0x0503); a.op('STA', 'absy', 0x050B)
    a.op('LDA', 'long', TMP_OFF); a.op('ASL', 'acc'); a.op('CLC'); a.op('ADC', 'imm16', L['work'])
    a.op('STA', 'absy', 0x0505); a.op('CLC'); a.op('ADC', 'longx', C(6))
    a.op('STA', 'absy', 0x050D)
    a.op('TYA'); a.op('CLC'); a.op('ADC', 'imm16', 0x0010)
    a.op('SEP', 'imm8', 0x20); a.op('STA', 'abs', 0x0081); a.op('REP', 'imm8', 0x20)
    a.label('no_queue')
    # frames and animation: ROM -> $7F (FR, AN); entries $0960/$0980
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    a.op('LDA', 'long', TMP_OFF); a.op('CLC'); a.op('ADC', 'imm16', L['fr']); a.op('TAY')
    a.op('LDA', 'longx', C(14)); a.op('AND', 'imm16', 0x00FF); a.op('DEC', 'acc'); a.op('PHA')
    a.op('LDA', 'longx', C(12)); a.op('TAX'); a.op('PLA'); a.mvn(0x7F, BANK)
    a.op('PHX')
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    a.op('LDA', 'long', TMP_OFF); a.op('CLC'); a.op('ADC', 'imm16', L['an']); a.op('TAY')
    a.op('LDA', 'longx', C(15)); a.op('AND', 'imm16', 0x00FF); a.op('DEC', 'acc')
    a.op('PLX'); a.mvn(0x7F, BANK)
    db7e()
    a.op('LDA', 'long', TMP_REC); a.op('TAX')
    a.op('LDA', 'longx', C(2)); a.op('AND', 'imm16', 0x00FF); a.op('TAY')
    a.op('LDA', 'long', TMP_OFF); a.op('CLC'); a.op('ADC', 'imm16', L['fr'] - 0x1000); a.op('STA', 'absy', 0x0960)
    a.op('LDA', 'long', TMP_OFF); a.op('CLC'); a.op('ADC', 'imm16', L['an']); a.op('STA', 'absy', 0x0980)
    a.op('TYA')
    a.op('PLY'); a.op('PLX'); a.op('PLB'); a.op('SEC'); a.op('RTL')

    def hook(name, orig, type_, back):
        a.label(name)
        orig(a)
        a.op('PHP'); a.op('REP', 'imm8', 0x30); a.op('PHA')
        a.op('LDA', 'dp', 0x03); a.op('AND', 'imm16', 0x003F); a.op('XBA'); a.op('ORA', 'imm16', type_)
        a.op('JSL', 'long', 'common'); a.br('BCC', name + '_orig'); a.op('STA', 'sr', 1)
        a.label(name + '_orig')
        a.op('PLA'); a.op('PLP'); a.op('STA', 'dp', 0x08); a.op('JML', 'long', back)
    hook('h_talisman', lambda a: a.op('LDA', 'abs', 0x0D80), 0x2E, 0x82E0A0)
    hook('h_vellum', lambda a: a.op('LDA', 'abs', 0x0D7E), 0x2D, 0x82E0A0)
    hook('h_crest', lambda a: (a.op('LDA', 'absy', 0x0D30), a.op('AND', 'imm16', 0x00FF)), 0x48, 0x82EA17)

    # --- message box: give the color window back when it closes (engine bug) ---
    # The opening (BE:DC77) turns the color window on ($0E5B=30, CGWSEL|=20, CGADSUB|=20) so that no color
    # math is applied inside the box; the closing (BE:DE92) restores COLDATA/TMW/TSW but leaves CGWSEL and
    # $0E5B set. Out of water nobody notices (no color math is active); under water the water's own math ends
    # up disabled on the whole screen and the water becomes an opaque layer. Here the three values are saved
    # on opening and given back on closing — clearing the bits blindly would be wrong, the water uses bit $20
    # of CGADSUB on its own.
    MARK, SAVED = 0x7F7FE8, 0x7F7FE9                  # mark + 3 bytes (CGWSEL, CGADSUB, $0E5B)
    a.label('box_open')                               # replaces LDA #$30 ; STA $0E5B (A 8-bit)
    for k, addr in enumerate((0x7E00B2, 0x7E00B3, 0x7E0E5B)):
        a.op('LDA', 'long', addr); a.op('STA', 'long', SAVED + k)
    a.op('LDA', 'imm8', 0xA5); a.op('STA', 'long', MARK)
    a.op('LDA', 'imm8', 0x30); a.op('STA', 'long', 0x7E0E5B)
    a.op('RTL')
    a.label('box_close')                              # replaces STZ $00B4 ; STZ $00B5 (A 8-bit)
    a.op('PHP'); a.op('PHA')
    a.op('LDA', 'imm8', 0x00); a.op('STA', 'long', 0x7E00B4); a.op('STA', 'long', 0x7E00B5)
    a.op('LDA', 'long', MARK); a.op('CMP', 'imm8', 0xA5); a.br('BNE', 'box_end')
    for k, addr in enumerate((0x7E00B2, 0x7E00B3, 0x7E0E5B)):
        a.op('LDA', 'long', SAVED + k); a.op('STA', 'long', addr)
    a.op('LDA', 'imm8', 0x00); a.op('STA', 'long', MARK)
    a.label('box_end')
    a.op('PLA'); a.op('PLP'); a.op('RTL')
    # In an area with color math active (water), the box neither forbids the math (BE:DC88) nor applies its
    # own fixed color (BE:DC8D): forbidding erases the water, and allowing the math without removing the fixed
    # color tints the whole scene purple — both were seen live on 22/09. With no math active, everything
    # behaves exactly like vanilla.
    # The test reads CGADSUB as saved at BE:DC77, BEFORE the box's own TSB $B3 (#$20, BE:DC7C): reading the
    # live $B3 always saw that bit, so every box in every area lost its fixed color and went black (23/09).
    def has_math():                                   # Z=0 (BNE) if the area uses color math
        a.op('LDA', 'long', SAVED + 1); a.op('AND', 'imm8', 0x3F)
    a.label('box_math')                               # replaces LDA #$20 ; TSB $00B2
    has_math(); a.br('BNE', 'box_math_end')
    a.op('LDA', 'imm8', 0x20); a.op('TSB', 'abs', 0x00B2)
    a.label('box_math_end')
    a.op('RTL')
    a.label('box_color')                              # replaces the three COLDATA writes (10/08/01)
    has_math(); a.br('BNE', 'box_color_end')
    for val, addr in ((0x10, 0x00B6), (0x08, 0x00B4), (0x01, 0x00B5)):
        a.op('LDA', 'imm8', val); a.op('STA', 'abs', addr)
    a.label('box_color_end')
    a.op('RTL')

    # --- pal_restore: replaces 82:8752 SEP #$30 / LDA $00 (start of the routine every object calls to delete
    # itself). If the object is one of our items (entry $08 in [emin, $1E]) and its entry holds a palette saved in
    # this same area, copies it back to the CGRAM buffer ($0400+slot*32) and to the copy at $7F:A100, clears the
    # mark and sets $80 (palette dirty). DP = the object.
    a.label('pal_restore')
    a.op('PHP'); a.op('REP', 'imm8', 0x30); a.op('PHA'); a.op('PHX'); a.op('PHY'); a.op('PHB')
    a.op('LDA', 'dp', 0x08); a.op('AND', 'imm16', 0x00FF)
    a.op('CMP', 'imm16', L['emin']); a.br('BCC', 'pr_out'); a.op('CMP', 'imm16', 0x0020); a.br('BCS', 'pr_out')
    a.op('EOR', 'imm16', 0xFFFF); a.op('SEC'); a.op('ADC', 'imm16', 0x001E)     # $1E - E = 2k
    for _ in range(5):
        a.op('ASL', 'acc')                                                   # 64k
    a.op('CLC'); a.op('ADC', 'imm16', L['save']); a.op('TAX')
    a.op('LDA', 'longx', 0x7F0020); a.op('AND', 'imm16', 0xFF00); a.op('CMP', 'imm16', 0xA500)
    a.br('BNE', 'pr_out')
    a.op('LDA', 'longx', 0x7F0022); a.op('AND', 'imm16', 0x00FF); a.op('STA', 'long', TMP_KEY)
    a.op('LDA', 'long', 0x7E008D); a.op('AND', 'imm16', 0x00FF); a.op('CMP', 'long', TMP_KEY)
    a.br('BNE', 'pr_out')
    a.op('LDA', 'longx', 0x7F0020); a.op('AND', 'imm16', 0x00FF)
    for _ in range(5):
        a.op('ASL', 'acc')
    a.op('CLC'); a.op('ADC', 'imm16', 0x0400); a.op('TAY')
    a.op('PHX'); a.op('PHY')
    a.op('LDA', 'imm16', 0x001F); a.mvn(0x7E, 0x7F)                          # save -> $7E:0400+slot*32
    a.op('PLX'); a.op('TXA'); a.op('CLC'); a.op('ADC', 'imm16', 0x9D00); a.op('TAY')
    a.op('LDA', 'imm16', 0x001F); a.mvn(0x7F, 0x7E)                          # -> $7F:A100+slot*32
    a.op('PLX'); a.op('SEP', 'imm8', 0x20)
    a.op('LDA', 'imm8', 0x00); a.op('STA', 'longx', 0x7F0021)
    a.op('LDA', 'imm8', 0x01); a.op('STA', 'long', 0x7E0080)
    a.op('REP', 'imm8', 0x20)
    a.label('pr_out')
    a.op('PLB'); a.op('PLY'); a.op('PLX'); a.op('PLA'); a.op('PLP')
    a.op('SEP', 'imm8', 0x30); a.op('LDA', 'dp', 0x00); a.op('JML', 'long', 0x828756)

    return a.resolve(), a.labels
