"""DCOR - lógica e distribuição de itens (código nosso, do zero). A ROM é gravada por insanity_rom.py.

uso: python insanity_rando.py [-s SEED] [-m MODO] [-d DIF] [-g GO] [--lote N] [--rom [ROM]] [-o PASTA]
  -s SEED    gera uma seed e imprime o spoiler
  --lote N   gera N seeds e confere cada uma (todos os checks alcançáveis a partir do nada)
  --rom      grava a ROM (sem caminho = a ROM original da pasta ROM do DCOR)

Lógica: lógica_demonRando_V3.txt (Neitan, 29/09). Requisito: ',' ou '+' ou ' e ' = E; '/' ou ' ou ' = OU; 'n/a' = livre.
Dificuldade entre parênteses em cada alternativa (V3): '(5)', '(4 e 5)', '(1 a 3)'. O MENOR número é o piso — a
alternativa vale dali pra cima, nunca abaixo; a faixa diz onde ela é o caminho PRINCIPAL (não obrigatório).
Sem parênteses = vale em qualquer dificuldade.
'X+ HP' = barra de vida total = 4 (início, 84:8906) + nº de HPs pegos. 'beat <chefe>' = alcançar o check do chefe.
Castelo do Phalanx (Go Mode, escolha do jogador desde 27/09, -g): 5 vellum (padrão), 15 chefes, 4 crests de transformação ou todos os HP.
Pool (decisão do Neitan, 25/09): só localizações que soltam algo no original; quebráveis sem item ficam de fora.
"""
import argparse
import os
import random
import re
from collections import Counter

START_HP = 4
VELLUMS_FOR_CASTLE = 5

# (nome, área, origem na ROM, item original, requisito como na V3)
LOCATIONS = [
    ('Trio the Pago', '52-54', 'código BC:A13E', 'HP', 'n/a'),
    # Fase 1
    ('Somulo (cabeça)', '17', 'código 83:96D3', 'HP', 'n/a'),
    ('Pote 20G área 1', '1', 'pote 392,376', '20G', 'n/a'),
    ('Estátua Vellum 00', '1', 'quebrável $A0 81:B4F9', 'Vellum', 'n/a'),
    ('Hippogriff 1', '1', 'código 82:9999', 'HP', 'n/a'),
    ('Potion 0A', '2', 'objeto 1624,392', 'Potion', 'n/a'),
    ('HP 07 chão', '3', 'objeto 432,440', 'HP', 'Buster ou Time Crest'),
    ('Pote recarga fase 1', '1?', 'pote 1640,408 (ou área 3 408,168?)', 'Recarga', 'n/a'),
    ('Arma 1', '3', 'não achado', 'Earth Crest', 'n/a'),
    # Fase 2
    ('Potion 0C', '5', 'objeto 1304,424', 'Potion', 'Water Crest (1 a 3) / 4+ HP (5) / Time Crest, 4+ de HP (4)'),
    ('Hand', '5', 'objeto 1960,424', 'Hand', 'Water Crest (1 a 3) / 6+ HP (5) / Time Crest, 4+ de HP (3 e 4)'),
    ('Pote Vellum 02', '6', 'pote 456,328', 'Vellum', 'Earth Crest + Buster / Earth Crest + Time Crest'),
    ('Pote HP 08', '7', 'pote 56,424', 'HP', 'Earth Crest + Buster / Earth Crest + Time Crest'),
    ('HP 0A pós-Flame Lord', '50', 'objeto 560,240', 'HP', 'n/a / beat Flame Lord'),
    ('Pote recarga área 7', '7', 'pote 912,424', 'Recarga', 'Earth Crest'),
    ('Pote 20G área 6', '6', 'pote 472,536', '20G', 'Earth Crest'),
    ('Ovnunu', '8', 'código 83:C6D4', 'Buster', 'Earth Crest'),
    ('Ossos HP 09', '9', 'quebrável $E0 B667 536,192', 'HP', 'Earth Crest'),
    ('Belth', '9', 'código 83:E8D8', 'HP', '8+ HP'),
    # Fase 3
    ('Pote 20G área 10 a', '10', 'pote 472,104', '20G', 'n/a'),
    ('Pote 20G área 10 b', '10', 'pote 784,360', '20G', 'n/a'),
    ('Pote 20G área 10 c', '10', 'pote 840,104', '20G', 'n/a'),
    ('Potion 0E', '10', 'objeto 1133,200', 'Potion', 'n/a'),
    ('Pote recarga área 11', '11', 'pote 560,426', 'Recarga', 'Water Crest / 6+ HP (4) / Time Crest e 4+ de HP (2 e 3) / '
                                                              '4+ Hp e armor (4 e 5)'),
    ('Pote Vellum 04', '11', 'pote 1480,88', 'Vellum', 'Water Crest / Time Crest / Buster'),
    ('Skulla', '13', 'código BD:85AD', 'HP', 'n/a'),
] + [(f'Pote 20G área 13 {c}', '13', f'pote {p}', '20G', '10+ HP (5) / 10+ HP, Armor (4) / Water Crest / 8+ HP, Time Crest (3)')
     for c, p in zip('abcde', ('472,216', '536,280', '632,328', '712,232', '808,264'))] + [
    ('Pote recarga área 14', '14', 'pote 1528,216', 'Recarga', 'n/a'),
    ('Flame Lord', '14', 'código 82:CCFD', 'Tornado', 'Claw / Buster / Demon Fire / Earth Crest / Water Crest / Air Crest / Time Crest'),
    ('Pote HP 0B', '15', 'pote 256,170', 'HP', 'Buster, 10+ HP (5) / Buster, 10+ HP e Armor (4) / Water Crest / '
                                                '8+ HP, Time Crest (3)'),
    ('Skull', '16', 'objeto 208,170', 'Skull', 'Buster / Time Crest'),
    # Fase 4
    ('Potion 10', '18', 'objeto 536,408', 'Potion', 'Buster / Time Crest'),
    ('Pote 20G área 18', '18', 'pote 40,296', '20G', 'n/a'),
    ('Pote recarga área 19', '19', 'pote 1656,120', 'Recarga', 'n/a'),
    ('Flier 1', '19', 'código 85:DBA0', 'Claw', 'n/a / 10+hp'),
    ('Hippogriff 2', '20', 'código 82:99A7', 'Recarga', 'n/a'),
    ('Crown', '22', 'quebrável $A0 81:B501', 'Crown', 'n/a'),
    ('Vellum 06', '23', 'objeto 440,264', 'Vellum', 'n/a'),
    ('Arma 2', '23', 'não achado', 'Air Crest', '10+hp'),
    # Fase 5
    ('Pote HP 0D', '25', 'pote 56,472', 'HP', 'Water Crest / 15HP, Time Crest, Armor (4 e 5)'),
    ('Holothurion', '26', 'código 83:D7B7', 'HP', 'Water Crest, 8+ HP'),
    ('Crawler', '27', 'código 82:BA12', 'Water Crest', 'Earth Crest, 8+ hp'),
    ('Estátua HP 0E', '27', 'quebrável $E0 B6B5 644,456', 'HP', 'Earth Crest'),
    ('Estátua HP 05', '28', 'quebrável $E0 B6B5 436,136', 'HP', 'Water Crest, Earth Crest / beat Crawler, Earth Crest'),
    # Fase 6
    ('Potion 12', '29', 'objeto 152,56', 'Potion', 'Air Crest / Tornado'),
    ('Ossos Vellum 08', '30', 'quebrável $E0 B703 1480,168', 'Vellum', 'Earth Crest'),
    ('Pote recarga área 30', '30', 'pote 1144,408', 'Recarga', 'n/a'),
    ('Grewon', '30', 'código BE:9E23', 'Demon Fire', '10+hp'),
    ('Pote HP 0F', '32', 'pote 456,184', 'HP', 'Air Crest / Tornado, Buster / Tornado, Demon Fire / Tornado, Eath Crest / '
                                                   'Tornado, Time Crest / Tornado, Water Crest / Tornado + Vellum + Shock Spell'),
    ('Flier 2', '34', 'código 85:DBA7', 'Recarga', 'Earth Crest, Tornado, 10+hp (4 a 5) / Air Crest, Earth Crest, 10+hp'),
    ('Armor', '35', 'quebrável $E0 B733 680,392', 'Armor', 'Earth Crest, Air Crest / Earth Crest, Tornado'),
    ('Arma 3', '36', 'não achado', 'Time Crest', 'Earth Crest, Air Crest, 10+hp / Earth Crest, Tornado, 10+ hp'),
    # Phalanx (go mode)
    ('Sino HP 10', '38', 'código BE:FA01 (pote 1257)', 'HP', 'Air Crest / Tornado'),
    ('Fang', '39', 'objeto 1960,440', 'Fang', 'Air Crest / Tornado'),
]
CASTLE = {'Sino HP 10', 'Fang'}

ITEM_ALIASES = {
    'buster': 'Buster', 'tornado': 'Tornado', 'claw': 'Claw', 'demon fire': 'Demon Fire',
    'earth crest': 'Earth Crest', 'eath crest': 'Earth Crest', 'air crest': 'Air Crest',
    'water crest': 'Water Crest', 'time crest': 'Time Crest', 'armor': 'Armor', 'vellum': 'Vellum',
}
IGNORED = {'shock spell'}   # comprado na loja com vellum: basta o vellum (dinheiro não entra na lógica)
PROGRESSION = {'Buster', 'Tornado', 'Claw', 'Demon Fire', 'Earth Crest', 'Air Crest', 'Water Crest',
               'Time Crest', 'Armor', 'Vellum', 'HP'}


DIFF_TAG = re.compile(r'\(\s*(\d)\s*(?:(a|e)\s*(\d)\s*)?\)')


def parse(req):
    """Requisito -> lista de alternativas (termos, piso, principal): termos = ('item', nome) / ('hp', n) / ('beat', loc);
    piso = menor dificuldade em que a alternativa vale (1 sem parênteses); principal = dificuldades em que ela é o
    caminho principal (vazio = sem indicação)."""
    req = req.strip().lower()
    if req.startswith('n/a'):
        return [([], 1, frozenset())]
    alts = []
    for alt in re.split(r'/| ou ', req):
        low, main = 1, frozenset()
        m = DIFF_TAG.search(alt)
        if m:
            a, how, b = int(m.group(1)), m.group(2), m.group(3)
            main = frozenset(range(a, int(b) + 1) if how == 'a' else {a, int(b)} if how == 'e' else {a})
            low = min(main)
            alt = alt[:m.start()] + alt[m.end():]
        terms = []
        for t in re.split(r',| \+ | e/ou | e ', alt):
            t = t.strip()
            if not t or t in IGNORED:
                continue
            m = re.fullmatch(r'(\d+)\s*\+?\s*(?:ou mais de )?(?:de )?hp', t)
            if m:
                terms.append(('hp', int(m.group(1))))
            elif t.startswith('beat '):
                terms.append(('beat', t[5:].strip()))
            elif t in ITEM_ALIASES:
                terms.append(('item', ITEM_ALIASES[t]))
            else:
                raise ValueError(f'termo desconhecido: {t!r} em {req!r}')
        alts.append((terms, low, main))
    return alts


# Dificuldade 1-5 (proposta do Neitan, 26/09): esferas, itens fortes, HP por esfera e HP removido.
STRONG = {'Time Crest', 'Demon Fire', 'Fang', 'Armor', 'Air Crest'}
MIN_SPHERES = 5
HP_REMOVED = {4: 5}                          # cada HP removido vira 20G e Recarga, alternando
# Dif. 5 (Neitan, 28/09; antes tirava 10 HP): sorteia de 2 a 4 destes pra sair da pool (viram 20G/Recarga).
REMOVABLE = ('Air Crest', 'Time Crest', 'Tornado', 'Demon Fire')
REMOVE_RANGE = {5: (2, 4)}
# Anti-softlock (patches de mapa em DCOR/patch): o 27 entra sempre que a opção está ligada; o 29 e o 38 só se a
# opção está ligada E Air Crest + Tornado saíram da pool — aí, na lógica, a Claw vale onde o requisito pede Air ou
# Tornado (os mapas abrem esses caminhos pra Claw).
CLAW_SUB = {'Air Crest', 'Tornado'}
FORBIDDEN = {'Holothurion': {'Water Crest'}}      # regra dura do Neitan (26/09), vale em qualquer preenchimento
CASTLE_FIXED = {5: ('Time Crest', 'Fang')}        # dif. 5: esses dois no castelo (cedem ao Go Mode)
# 1ª esfera (0.3, Neitan 29/09: "controlar a primeira esfera"): ~22 checks abrem sem nada; máximo de itens que abrem
# caminho caindo ali. 'chave' = crests + Armor; 'HP' = HP (conta pros "X+ HP"). Sem 'HP' nas dif. 1 e 2: "mais HP no
# começo" é a proposta delas. O item-chave que o gerador PRECISA pôr pra abrir a 2ª esfera entra mesmo acima do limite.
SPHERE1_MAX = {1: {'chave': 3}, 2: {'chave': 2}, 3: {'chave': 2, 'HP': 5}, 4: {'chave': 1, 'HP': 2},
               5: {'chave': 1, 'HP': 3}}


def sphere1_kind(item):
    return 'HP' if item == 'HP' else 'chave' if item in PROGRESSION and item != 'Vellum' else None

# Go Mode (Neitan, 27/09): o jogador escolhe o que libera o castelo do Phalanx (antes era por dificuldade).
# Item exigido pelo Go Mode nunca vai pro castelo (não dá pra precisar dele pra entrar onde ele está).
GO_MODES = ('vellum', 'bosses', 'crests', 'hp')
GO_ITEMS = {'vellum': {'Vellum'}, 'bosses': set(), 'crests': {'Earth Crest', 'Air Crest', 'Water Crest', 'Time Crest'},
            'hp': {'HP'}}
BOSSES = ('Somulo (cabeça)', 'Hippogriff 1', 'Hippogriff 2', 'Arma 1', 'Belth', 'Ovnunu', 'Flame Lord', 'Skulla',
          'Flier 1', 'Flier 2', 'Arma 2', 'Holothurion', 'Crawler', 'Grewon', 'Arma 3')   # 15: Trio é minigame


def strong_targets(rng, diff):
    """Esfera-alvo de cada item forte. Dif. 1: sorteio igual entre 1-3. Dif. 3: um por esfera (1-5), Time nunca
    na 1 nem na 2 (Time é o item mais forte: dar de cara facilita o jogo inteiro)."""
    items = sorted(STRONG)
    if diff == 1:
        return {it: rng.randint(1, 3) for it in items}
    if diff == 3:
        order = [1, 2, 3, 4, 5]
        rng.shuffle(order)
        t = dict(zip(items, order))
        if t['Time Crest'] <= 2:
            swap = rng.choice([it for it in items if t[it] >= 3])
            t['Time Crest'], t[swap] = t[swap], t['Time Crest']
        return t
    return {}


CASTLE_ORDER = ('Fang', 'Sino HP 10')           # ordem das vagas do castelo (Time vai na 1ª sorteável)

# Modos (Neitan, 27/09): o que entra no sorteio. Local fora do modo fica com o item original.
CRESTS = {'Buster', 'Tornado', 'Claw', 'Demon Fire', 'Earth Crest', 'Air Crest', 'Water Crest', 'Time Crest'}
TALISMANS = {'Crown', 'Skull', 'Armor', 'Fang', 'Hand'}
MODES = {'limitado': CRESTS | TALISMANS | {'Potion', 'Vellum'},       # HP ficam vanilla
         'classico': CRESTS | TALISMANS | {'Potion', 'Vellum', 'HP'},
         'extra': None}                                                 # tudo (58 checks, com 20G e recarga)


def shuffled(mode):
    cats = MODES[mode]
    return [l[0] for l in LOCATIONS if cats is None or l[3] in cats]


def castle_fixed(diff, go, removed=()):
    return tuple(it for it in CASTLE_FIXED.get(diff, ()) if it not in GO_ITEMS[go] and it not in removed)


def accept(diff, p, got, sph, mode='extra', go='vellum', removed=()):
    """Regras que a seed pronta tem que cumprir."""
    if len(got) != len(LOCATIONS) or any(p[l] in bad for l, bad in FORBIDDEN.items()):
        return False
    if any(p[l] in GO_ITEMS[go] for l in CASTLE if l in shuffled(mode)):
        return False
    if diff is None:
        return True
    if len(sph) < MIN_SPHERES:
        return False
    at = {p[l]: i for i, s in enumerate(sph, 1) for l in s if p[l] in STRONG}
    if diff == 1:
        return all(i <= 3 for i in at.values())
    if diff == 3:
        return len(sph) == 5 and set(at.values()) == {1, 2, 3, 4, 5} and at['Time Crest'] >= 3
    if diff == 5:
        free = [l for l in CASTLE_ORDER if l in shuffled(mode)]
        return all(p[l] == it for l, it in zip(free, castle_fixed(diff, go, removed)))
    return True


def strong_weight(diff, s):
    """Peso de um item forte na esfera s (0 = só se não houver outra saída)."""
    return {1: 20 if s <= 2 else 0.05, 2: 20 if s in (2, 3) else 0.05, 4: 0 if s < 4 else 5, 5: 0}.get(diff, 1)


def hp_weight(diff, s):
    return {1: 4 if s <= 2 else 0.5, 2: 4 if s <= 2 else 0.5, 4: 0.25 if s <= 3 else 1.5}.get(diff, 1)


def pool_for(diff, mode='extra', rng=None, removed=()):
    """(itens sorteáveis, {local fixo: item}). HP removido vira 20G/Recarga alternando; no modo em que o HP não é
    sorteado (Limitado), os HPs removidos são locais de HP sorteados que ficam com o 20G/Recarga no lugar.
    removed = itens da dif. 5 que saem da pool (crests: sorteadas em todo modo), também viram 20G/Recarga."""
    free = set(shuffled(mode))
    pool = [l[3] for l in LOCATIONS if l[0] in free]
    fixed = {l[0]: l[3] for l in LOCATIONS if l[0] not in free}
    hp_fixed = [loc for loc, it in fixed.items() if it == 'HP']
    if rng is not None:
        rng.shuffle(hp_fixed)
    for i in range(HP_REMOVED.get(diff, 0)):
        filler = '20G' if i % 2 == 0 else 'Recarga'
        if 'HP' in pool:
            pool.remove('HP')
            pool.append(filler)
        else:
            fixed[hp_fixed.pop()] = filler
    for i, it in enumerate(removed):
        pool.remove(it)
        pool.append('20G' if i % 2 == 0 else 'Recarga')
    return pool, fixed


def pick_removed(rng, diff, go):
    """Dif. 5: 2 a 4 de REMOVABLE, sorteados. O objetivo "4 crests" com a dif. 5 é bloqueado (Neitan, 28/09)."""
    if diff not in REMOVE_RANGE:
        return ()
    if go == 'crests':
        raise ValueError('o objetivo "All 4 Main Crests" não combina com a dificuldade 5')
    lo, hi = REMOVE_RANGE[diff]
    return tuple(sorted(rng.sample(REMOVABLE, rng.randint(lo, hi))))


class Logic:
    def __init__(self, diff=None, mode='extra', go='vellum', antisoftlock=False):
        self.diff, self.mode, self.go, self.antisoftlock = diff, mode, go, antisoftlock
        self.removed = ()          # itens fora da pool nesta seed (dif. 5); definido a cada tentativa de preenchimento
        self.claw = False          # Claw vale por Air/Tornado (patches 29/38 aplicados)
        self.need = {'Vellum': VELLUMS_FOR_CASTLE}   # Go Mode por item: quantos de cada (set_need)
        self.locs = [l[0] for l in LOCATIONS]
        # V3: só as alternativas cujo piso de dificuldade <= a dificuldade da seed (sem dificuldade: todas)
        self.alts = {l[0]: parse(l[4]) for l in LOCATIONS}
        self.req = {loc: [terms for terms, low, _ in alts if diff is None or low <= diff]
                    for loc, alts in self.alts.items()}
        lower = {n.lower(): n for n in self.locs}
        for alts in self.req.values():
            for terms in alts:
                for i, (k, v) in enumerate(terms):
                    if k == 'beat':
                        terms[i] = (k, next(n for low, n in lower.items() if low.startswith(v)))

    def reachable(self, have):
        """Conjunto de checks alcançáveis com o inventário `have` (Counter), resolvendo 'beat' por ponto fixo."""
        hp = START_HP + have['HP']
        done = set()
        changed = True
        while changed:
            changed = False
            for loc in self.locs:
                if loc in done:
                    continue
                if loc in CASTLE and not self.castle_ok(have, done):
                    continue
                if any(all(self.term_ok(t, have, hp, done) for t in terms) for terms in self.req[loc]):
                    done.add(loc)
                    changed = True
        return done

    def set_need(self, items_outside):
        """Quantos de cada item do Go Mode existem fora do castelo (All HP depende do HP removido e do modo)."""
        c = Counter(items_outside)
        self.need = {k: (VELLUMS_FOR_CASTLE if k == 'Vellum' else c[k]) for k in GO_ITEMS[self.go]}

    def castle_ok(self, have, done):
        """Go mode: quando o castelo do Phalanx aparece."""
        if self.go == 'bosses':
            return all(b in done for b in BOSSES)
        return all(have[k] >= n for k, n in self.need.items())

    def term_ok(self, t, have, hp, done):
        k, v = t
        if k == 'item':
            return have[v] > 0 or (self.claw and v in CLAW_SUB and have['Claw'] > 0)
        return hp >= v if k == 'hp' else v in done

    def set_removed(self, removed):
        self.removed = tuple(removed)
        self.claw = self.antisoftlock and CLAW_SUB <= set(self.removed)

    def patches(self):
        """Patches de mapa desta seed (DCOR/patch): 27 com o anti-softlock; 29 e 38 só com Air + Tornado fora."""
        return ([27] if self.antisoftlock else []) + ([29, 38] if self.claw else [])

    def sweep(self, placement):
        """Joga a seed do zero: pega tudo que alcança, repete. Devolve (checks alcançados, esferas)."""
        self.set_need(it for loc, it in placement.items() if loc not in CASTLE)
        have, got, spheres = Counter(), set(), []
        while True:
            new = self.reachable(have) - got
            if not new:
                return got, spheres
            spheres.append(sorted(new))
            got |= new
            for loc in new:
                have[placement[loc]] += 1


def generate(seed, logic, tries=50):
    """Mesma seed = mesmo resultado. Se o preenchimento cair num beco, tenta de novo com o mesmo gerador."""
    rng = random.Random(seed)
    if logic.diff is not None:
        tries = 500
    for _ in range(tries):
        if logic.diff is None:
            p = fill(rng, logic)
            if p is not None:
                return p
            continue
        p = fill_spheres(rng, logic)
        if p is None:
            continue
        got, sph = logic.sweep(p)
        if accept(logic.diff, p, got, sph, logic.mode, logic.go, logic.removed):
            return p
    return None


def fill_spheres(rng, logic):
    """Preenchimento por esfera (dificuldade 1-5): cada rodada preenche TODAS as vagas que acabaram de abrir, então a
    esfera s do spoiler é exatamente a rodada s. Local fora do modo (fixo) recebe o item original quando abre. Poucos
    itens-chave abrem a próxima (preferência pelos que abrem menos, pra dar profundidade); o resto das vagas é
    sorteado com peso por dificuldade (itens fortes, HP). Vaga do castelo nunca recebe item do Go Mode, e o pool
    guarda itens que não são do Go Mode para as vagas do castelo que ainda vão abrir."""
    diff, mode, go = logic.diff, logic.mode, logic.go
    removed = pick_removed(rng, diff, go)                           # dif. 5: 2-4 fora da pool (sorteio por tentativa)
    logic.set_removed(removed)
    pool, fixed = pool_for(diff, mode, rng, removed)
    free_castle = [l for l in CASTLE_ORDER if l not in fixed]
    for loc, it in zip(free_castle, castle_fixed(diff, go, removed)):   # dif. 5: Time (e Fang) no castelo
        fixed[loc] = it
        pool.remove(it)
    logic.set_need(pool + [it for loc, it in fixed.items() if loc not in CASTLE])
    rng.shuffle(pool)
    gi = GO_ITEMS[go]
    prog = PROGRESSION
    target = strong_targets(rng, diff)
    placement, have, s = {}, Counter(), 0

    def w(item, sph, key=False):
        if item in target:                             # atrasado em relação ao alvo: entra assim que puder
            return 50 if sph >= target[item] else 0
        if item in STRONG:
            return strong_weight(diff, sph)
        if item == 'HP':
            return hp_weight(diff, sph)
        return 1 if key or item not in prog else 0.3   # progressão fora das chaves: pouca, pra não achatar

    def draw(sph, allowed):
        cand = [it for it in pool if allowed(it)]
        if not cand:
            return None
        ws = [w(it, sph) for it in cand]
        it = rng.choices(cand, ws if any(ws) else None)[0]
        pool.remove(it)
        return it

    while len(placement) < len(LOCATIONS):
        reach = logic.reachable(have)
        slots = [l for l in logic.locs if l in reach and l not in placement]
        if not slots:
            return None
        s += 1
        rng.shuffle(slots)
        sphere = set(slots)
        for loc in [l for l in slots if l in fixed]:
            placement[loc] = it = fixed[loc]
            have[it] += 1
            slots.remove(loc)
        castle_now = [l for l in slots if l in CASTLE]
        others = [l for l in slots if l not in CASTLE]
        castle_later = sum(1 for l in CASTLE if l not in placement and l not in sphere and l not in fixed)
        keys = []
        left = [l for l in logic.locs if l not in placement and l not in sphere]
        if left:
            reach2 = logic.reachable(have)                        # os fixos desta esfera já podem abrir algo
            if not any(l in reach2 and l not in sphere for l in left):
                keys = pick_keys(rng, logic, pool, prog, have, reach2, len(others), lambda it: w(it, s, True))
                if keys is None:
                    return None
        for it in keys:
            pool.remove(it)
        cap = dict(SPHERE1_MAX.get(diff, {})) if s == 1 else {}   # 1ª esfera: quanto ainda cabe de cada tipo
        for it in keys:
            if sphere1_kind(it) in cap:
                cap[sphere1_kind(it)] -= 1
        fits = lambda x: cap.get(sphere1_kind(x), 1) > 0

        def take(it):
            if sphere1_kind(it) in cap:
                cap[sphere1_kind(it)] -= 1
            return it
        got = {}
        for loc in castle_now:                                    # castelo: nunca item do Go Mode
            it = draw(s, lambda x: x not in gi and fits(x))
            if it is None:
                return None
            got[loc] = take(it)
        rest = [l for l in others]
        for loc, it in zip(rest, keys):
            got[loc] = it
        for loc in rest[len(keys):]:
            spare = sum(1 for x in pool if x not in gi) - castle_later   # reserva pras vagas do castelo
            it = draw(s, lambda x: (x in gi or spare > 0) and fits(x))
            if it is None:
                return None
            got[loc] = take(it)
        for loc, it in got.items():
            placement[loc] = it
            have[it] += 1
    return placement

def pick_keys(rng, logic, pool, prog, have, reach, room, weight):
    """Itens (do pool) que, somados ao inventário, abrem pelo menos um check novo. Tenta 1 item, depois N HPs,
    depois pares. Peso = preferência da dificuldade / nº de checks abertos."""
    def gain(items):
        h = have + Counter(items)
        return len(logic.reachable(h) - reach)

    if room < 1:
        return None

    kinds = sorted({it for it in pool if it in prog})
    opts = []
    for k in kinds:
        g = gain([k])
        if g:
            opts.append(([k], g))
    if not opts:
        for n in range(2, min(pool.count('HP'), room) + 1):
            g = gain(['HP'] * n)
            if g:
                opts.append((['HP'] * n, g))
                break
    if not opts and room >= 2:
        for i, a in enumerate(kinds):
            for b in kinds[i:]:
                if (a != b or pool.count(a) > 1) and gain([a, b]):
                    opts.append(([a, b], gain([a, b])))
    if not opts:
        return None
    ws = [max(min(weight(it) for it in items), 0.001) / g for items, g in opts]
    return list(rng.choices(opts, ws)[0][0])


def fill(rng, logic):
    pool = [l[3] for l in LOCATIONS]
    prog = [i for i in pool if i in PROGRESSION]
    rest = [i for i in pool if i not in PROGRESSION]
    rng.shuffle(prog)
    placement, empty = {}, list(logic.locs)
    # assumed fill: cada item de progressão vai para um check alcançável com os que ainda faltam colocar
    while prog:
        item = prog.pop()
        have = Counter(prog)
        reach = logic.reachable(have)
        ok = [loc for loc in empty if loc in reach]      # ordem fixa (set de texto muda de ordem a cada execução)
        if not ok:
            return None
        loc = rng.choice(ok)
        placement[loc] = item
        empty.remove(loc)
    rng.shuffle(rest)
    for loc, item in zip(empty, rest):
        placement[loc] = item
    return placement


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--seed', type=int, default=None)
    ap.add_argument('--lote', type=int, default=0)
    ap.add_argument('--rom', nargs='?', const='', default=None,
                    help='grava a ROM (sem valor = a ROM original da pasta ROM do DCOR)')
    ap.add_argument('-o', '--out', default=None, help='pasta de saída (padrão: pasta atual)')
    ap.add_argument('-d', '--dif', type=int, default=None, help='dificuldade 1-5 (sem = preenchimento antigo)')
    ap.add_argument('-m', '--modo', default='extra', choices=list(MODES), help='o que é sorteado')
    ap.add_argument('-g', '--go', default='vellum', choices=GO_MODES, help='objetivo: o que libera o castelo do Phalanx')
    ap.add_argument('-a', '--antisoftlock', action='store_true', help='patches anti-softlock (DCOR/patch)')
    a = ap.parse_args()
    if a.dif is None and (a.modo != 'extra' or a.go != 'vellum'):
        ap.error('o preenchimento antigo só existe no modo extra com go vellum: passe -d')
    logic = Logic(a.dif, a.modo, a.go, a.antisoftlock)
    pool = Counter(pool_for(a.dif, a.modo)[0])
    print(f'{len(LOCATIONS)} checks; pool: ' + ', '.join(f'{k}×{v}' for k, v in sorted(pool.items())))
    if a.lote:
        bad = fail = 0
        depth, strong_at, hp_at = Counter(), Counter(), Counter()
        for s in range(a.lote):
            p = generate(s, logic)
            if p is None:
                fail += 1
                continue
            got, sph = logic.sweep(p)
            if len(got) != len(LOCATIONS):
                bad += 1
            depth[len(sph)] += 1
            for i, sp in enumerate(sph, 1):
                tag = i if i < len(sph) else 'última'
                for loc in sp:
                    strong_at[tag] += p[loc] in STRONG
                    hp_at[tag] += p[loc] == 'HP'
        ok = a.lote - fail
        print(f'{a.lote} seeds: {fail} sem solução no preenchimento, {bad} com check inalcançável; '
              f'esferas: {dict(sorted(depth.items()))}')
        if ok:
            fmt = lambda c: ', '.join(f'{k}: {c[k] / ok:.2f}' for k in sorted(c, key=lambda k: (k == 'última', str(k).zfill(3))))
            print(f'itens fortes por esfera (média por seed): {fmt(strong_at)}')
            print(f'HP por esfera (média por seed): {fmt(hp_at)}')
        return
    seed = a.seed if a.seed is not None else random.randrange(1 << 31)
    home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # pasta do DCOR (data/..)
    van = None
    if a.rom is not None:
        if a.rom:
            van = open(a.rom, 'rb').read()
        else:                                                               # sem valor: a pasta ROM do DCOR
            import dcor_gui
            van = dcor_gui.find_rom(home)[0]
    res = build_seed(seed, van, logic)
    if res is None:
        print(f'seed {seed}: preenchimento falhou')
        return
    data, lines, gfx = res
    print('\n'.join(lines))
    if data:
        out = a.out or os.getcwd()
        rom_path = os.path.join(out, f"Demon's Crest Insanity - seed {seed}.sfc")
        open(rom_path, 'wb').write(data)
        with open(os.path.join(out, f'log Insanity - seed {seed}.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print('\n-- gráficos\n' + '\n'.join(gfx))
        print('\n->', rom_path)


# Spoiler em inglês (padrão do Neitan, 29/09): os nomes internos (PT) só mudam na saída.
SPOILER_EN = (('Somulo (cabeça)', 'Somulo (head)'), ('pós-Flame Lord', 'after Flame Lord'), ('Estátua', 'Statue'),
              ('Ossos', 'Bones'), ('Pote recarga', 'Refill pot'), ('Pote', 'Pot'), ('Sino', 'Bell'), ('chão', 'floor'),
              ('fase', 'stage'), ('área', 'area'), ('Recarga', 'Refill'))


def en(name):
    for a, b in SPOILER_EN:
        name = name.replace(a, b)
    return name


def build_seed(seed, van=None, logic=None):
    """Gera a seed. van = bytes da ROM original (None = só spoiler). Devolve (rom, linhas do spoiler, relatório de
    gráficos) ou None se o preenchimento falhar. Usado pela linha de comando e pela UI (dcor_gui.py)."""
    logic = logic or Logic()
    p = generate(seed, logic)
    if p is None:
        return None
    got, sph = logic.sweep(p)
    lines = [f"Demon's Crest Insanity - seed {seed}: {len(got)}/{len(LOCATIONS)} checks reachable, "
             f'{len(sph)} spheres',
             'out of the pool: ' + (', '.join(logic.removed) or 'none') + ' | map patches: ' +
             (', '.join(str(x) for x in logic.patches()) or 'none') +
             (' (Claw counts as Air/Tornado)' if logic.claw else ''), '']
    area = {l[0]: l[1] for l in LOCATIONS}
    data = ids = None
    gfx = []
    if van is not None:
        import insanity_rom
        data, ids = insanity_rom.write(van, p, random.Random(seed ^ 0x5EED), logic.go, logic.patches())
        gfx = list(insanity_rom.write.gfx_report)
    free = set(shuffled(logic.mode))
    for i, s in enumerate(sph, 1):
        lines.append(f'-- sphere {i}')
        for loc in s:
            lines.append(f'   area {area[loc]:>5}  {en(loc):28s} -> {en(p[loc])}' + (f' ({ids[loc]:04X})' if ids else '') +
                         ('' if loc in free else '   [not shuffled]'))
    return data, lines, gfx


if __name__ == '__main__':
    main()
