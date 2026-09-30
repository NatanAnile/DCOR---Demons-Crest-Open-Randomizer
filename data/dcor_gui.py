"""DCOR - Demon's Crest Open Randomizer: janela do executável (26/09).

O executável (Demon's Crest Open Randomizer.exe) é só o lançador (Python embutido): todo o código fica aqui na pasta
data e é lido ao abrir, então mexer no rando não pede compilar de novo (27/09, pedido do Neitan, pensando em abrir o
código no git). Sem o exe: python data/dcor_gui.py.

Gera a ROM com insanity_rando.build_seed. Controles (Neitan, 26-28/09):
  - Idioma (28/09): bandeiras BR/EUA no canto de cima; troca todos os textos na hora (TEXTS, tr). Spoiler em inglês.
  - Modo (MODE_KEYS): o que é randomizado. Limitado, Clássico e Clássico Extra funcionam; o Insano depende das
    localizações novas (quebráveis sem item) e da lógica delas, e trava o botão Gerar.
  - Dificuldade 1-5 (DOCUMENTACAO §3.4.1): esferas, itens fortes, HP; a 5 tira de 2 a 4 crests do jogo.
  - Objetivo (antigo "Go Mode"): o que libera o castelo do Phalanx. "4 crests" não combina com a dificuldade 5.
  - Prevenção Anti-Softlock: patches de mapa (DCOR/patch). A dificuldade 5 liga sozinho; desligar com ela pede confirmação.
Pastas ao lado do exe: ROM (de onde vem a ROM original), Seed (DemonRando - Nome.sfc), Spoiler (DemonRando - Nome.txt).
O nome da seed são 5 palavras do jogo (WORDS) e o número vem do hash do nome.
Visual: tema escuro do modelo do Neitan, sem ícones (28/09); janela redimensionável: cartões, linhas e barra esticam
com a janela e as letras crescem junto (fontes nomeadas, escala pela largura/altura). Tkinter puro.
Ícone da janela: data/dcor.ico (make_dcor_icon.py). Lançador: data/dcor_launcher.py; build: data/build_dcor.ps1.
"""
import ctypes
import hashlib
import json
import math
import os
import random
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as msgbox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import insanity_rando as R  # noqa: E402

VERSION = '0.2.1'
VANILLA_SHA1 = '743d60ee1536b0c7c24dbb8ba39d14ed5937c0d5'   # Demon's Crest (USA), sem cabeçalho

# Idioma (28/09): todo texto da janela vem de TEXTS[LANG] via tr(); trocar a bandeira troca na hora (App.set_lang).
# O spoiler sai em inglês (padrão do Neitan, 29/09).
LANGS = ('pt', 'en')
LANG = 'pt'
MODE_KEYS = ['limitado', 'classico', 'extra', None]      # modo no gerador (None = ainda não gera)
DEFAULT_MODE = 2
DIFF_MIN, DIFF_MAX, DEFAULT_DIFF = 1, 5, 3
GO_KEYS = ['vellum', 'bosses', 'crests', 'hp']            # Objetivo (antigo Go Mode): o que libera o castelo do Phalanx
DEFAULT_GO = 'vellum'
FRED_URL = 'https://github.com/FredYeye/Demon-s-Crest-Rando'
SOCIAL = (('youtube', 'https://www.youtube.com/@NatanAnile'), ('twitch', 'https://www.twitch.tv/natan_anile'))


def social_icon(cv, kind, w, h):
    """Ícone desenhado (sem imagem): YouTube = retângulo vermelho com play; Twitch = balão roxo com 2 barras."""
    if kind == 'youtube':
        round_rect(cv, 1, 2, w - 1, h - 2, h * 0.3, fill='#ff0033', outline='')
        cx, cy, r = w / 2, h / 2, h * 0.24
        cv.create_polygon(cx - r * 0.8, cy - r, cx - r * 0.8, cy + r, cx + r, cy, fill='white', outline='')
    else:
        x0, x1, y0, y1 = w * 0.18, w * 0.82, 1, h * 0.78
        cv.create_polygon(x0, y0, x1, y0, x1, y1 - h * 0.18, x1 - h * 0.18, y1, x0 + h * 0.32, y1, x0 + h * 0.12,
                          h - 1, x0 + h * 0.12, y1, x0, y1, fill='#9146ff', outline='')
        bw, by0, by1 = max(2, h * 0.09), h * 0.2, h * 0.48
        for bx in (w * 0.44, w * 0.62):
            cv.create_rectangle(bx - bw / 2, by0, bx + bw / 2, by1, fill='white', width=0)
# dificuldades: todas com pelo menos 5 esferas. "Itens fortes" = Time Crest, Demon Fire, Fang, Armor, Air Crest.
TEXTS = {
    'pt': {
        'lang': 'Idioma', 'lang_tip': 'Português (Brasil)',
        'seed': 'Seed', 'seed_ph': 'Deixe em branco para uma seed aleatória...',
        'seed_tip': 'Nome da seed: 5 palavras do jogo. Em branco = sorteia um nome. O mesmo nome com as mesmas opções '
                    'gera sempre a mesma ROM. Gerar de novo sem mexer no nome sorteia uma seed nova.',
        'roll': 'Sortear', 'roll_tip': 'Sortear um nome de seed',
        'logic': 'Lógica', 'diff': 'Dificuldade', 'mode': 'Modo', 'go': 'Objetivo', 'extras': 'Extras',
        'diff_tip': 'Dificuldade {v} (de 1 a 5, afeta todos os modos):\n{d}',
        'modes': ['Limitado', 'Clássico', 'Clássico Extra', 'Insano'],
        'mode_desc': [
            'Randomiza apenas Crests, Potion, Vellums e Talismãs. HP permanecem vanilla.',
            'Randomiza Crests, Potion, Vellums e Talismãs e HP.',
            'Randomiza Crests, Potion, Vellums e Talismãs, HP, Refil de HP em bosses e potes e potes de moedas 20G.',
            'Randomiza todos os itens em todos os potes, estátuas de gárgula, estátuas quebráveis por Earth Crest, '
            'janelas da Fase 2, blocos na parede da fase 6.'],
        'soon': '(em breve)', 'not_yet': '(Ainda não disponível.)',
        'x_crest': 'Randomizar Crest inicial',
        'x_crest_desc': 'O Firebrand começa com uma crest sorteada (nunca a Tornado). O tiro básico vira o item '
                        'Fire Crest, que entra na pool.',
        'x_head': 'Randomizar Head Butt',
        'x_head_desc': 'A cabeçada vira item da pool: sem ela não dá pra quebrar estátuas nem janelas.',
        'diff_desc': {
            1: 'Itens fortes nas esferas 1 a 3, mais HP no começo. No início do jogo, no máximo 3 crests/Armor.',
            2: 'Itens fortes nas esferas 2 e 3, mais HP no começo. No início do jogo, no máximo 2 crests/Armor. A '
               'lógica aceita Time Crest com HP em alguns lugares.',
            3: 'Moderada: 5 esferas com 1 item forte em cada (Time Crest nunca nas 2 primeiras). No início do jogo, no '
               'máximo 2 crests/Armor e 5 HP. Mais caminhos com Time Crest e HP.',
            4: 'Itens fortes só a partir da esfera 4, 5 HPs a menos no jogo. No início do jogo, no máximo 1 '
               'crest/Armor e 2 HP. A lógica aceita caminhos com HP, Armor e Tornado no lugar de algumas crests.',
            5: 'Itens mais fortes sempre nas últimas esferas, com Time Crest (quando no jogo) e Fang no castelo final. '
               "De 2 a 4 itens, entre Air Crest, Time Crest, Tornado e Demon Fire, fora do jogo. A lógica pode exigir "
               "checks debaixo d'água sem Water Crest. Prevenção Anti-Softlock obrigatória."},
        'go_names': {'vellum': '5 Vellums', 'bosses': 'All Bosses', 'crests': 'All 4 Main Crests', 'hp': 'All HP'},
        'go_desc': {
            'vellum': 'O castelo do Phalanx aparece com os 5 Vellums.',
            'bosses': 'O castelo aparece depois de vencer os 15 chefes: Somulo, Hippogriff 1 e 2, Arma 1, 2 e 3, '
                      'Belth, Ovnunu, Flame Lord, Skulla, Flier 1 e 2, Holothurion, Crawler e Grewon. O Trio the '
                      'Pago (minigame) não conta.',
            'crests': 'O castelo aparece com as 4 crests de transformação: Earth, Air, Water e Time. Não disponível '
                      'na dificuldade 5 (ela pode tirar Air e Time do jogo).',
            'hp': 'O castelo aparece com todos os HPs do jogo (fora o do castelo). Na dificuldade 4 contam só os que '
                  'sobraram.'},
        'no_d5': '(não na dificuldade 5)',
        'go_d5': 'Objetivo "All 4 Main Crests" não combina com a dificuldade 5: trocado por 5 Vellums.',
        'anti': 'Prevenção Anti-Softlock',
        'anti_desc': 'Patches de mapa contra softlock. Área 27: quem entrar sem a Earth Crest pode morrer pra sair. '
                     'Dificuldade 5 sem Air Crest e sem Tornado: as áreas 29 e 38 ganham caminho pela Claw '
                     '(inclusive o acesso ao Phalanx).',
        'anti_warn': 'Desativar o patch anti-softlock com a dificuldade 5 selecionada pode tornar a seed impossível '
                     'de finalizar. Desative por conta e risco.\n\nDesativar mesmo assim?',
        'on': 'ligado', 'off': 'desligado',
        'info': '{m}\n\nDificuldade {v}: {d}\n\nObjetivo: {g}\n{a}: {s}',
        'generate': 'Gerar', 'about': 'Sobre', 'about_tip': 'Créditos e versão do gerador',
        'rom': 'ROM: {n}',
        'rom_bad': "Essa não é a ROM original de Demon's Crest (USA).",
        'rom_none_ok': "Nenhuma ROM da pasta {d} é a original de Demon's Crest (USA).",
        'rom_missing': "Coloque a ROM original de Demon's Crest (USA) na pasta {d}.",
        'generating': 'Gerando {n}...',
        'done': 'Pronto: {d}\\{b}.sfc\nSpoiler em {s}\\{b}.txt',
        'error': 'Erro: {e}',
        'no_fill': '"{n}" não fechou a lógica; tente outro nome',
        'follow': 'Siga o Natan nas redes:',
        'about_title': 'Sobre o DCOR', 'version': 'Versão {v}', 'close': 'Fechar',
        'credits': [
            ('Criado por Natan Anile', [
                '• Ideia, direção, visual e ícone do gerador',
                '• Lógica de progressão, dificuldades, modos e objetivos',
                '• Mapeamento dos itens do jogo: potes, estátuas, quebráveis e chefes',
                '• Patches de mapa da Prevenção Anti-Softlock',
                '• Testes de tudo no jogo']),
            ('Colaboração: Asvel', [
                '• Lógica e ideias']),
            ('Referência', [
                "FredYeye, Demon's Crest Rando: os valores que ele mapeou foram usados só para conferir os que "
                'coletamos. Nenhum código dele está no DCOR.'])],
    },
    'en': {
        'lang': 'Language', 'lang_tip': 'English',
        'seed': 'Seed', 'seed_ph': 'Leave blank for a random seed...',
        'seed_tip': 'Seed name: 5 words from the game. Blank = a random name. The same name with the same options '
                    'always makes the same ROM. Generating again without changing the name rolls a new seed.',
        'roll': 'Roll', 'roll_tip': 'Roll a seed name',
        'logic': 'Logic', 'diff': 'Difficulty', 'mode': 'Mode', 'go': 'Goal', 'extras': 'Extras',
        'diff_tip': 'Difficulty {v} (1 to 5, affects every mode):\n{d}',
        'modes': ['Limited', 'Classic', 'Classic Extra', 'Insane'],
        'mode_desc': [
            'Randomizes only Crests, Potion, Vellums and Talismans. HP stay vanilla.',
            'Randomizes Crests, Potion, Vellums, Talismans and HP.',
            'Randomizes Crests, Potion, Vellums, Talismans, HP, HP refills from bosses and pots, and 20G coin pots.',
            'Randomizes every item in every pot, gargoyle statue, Earth Crest breakable statue, Stage 2 windows and '
            'Stage 6 wall blocks.'],
        'soon': '(coming soon)', 'not_yet': '(Not available yet.)',
        'x_crest': 'Randomize starting Crest',
        'x_crest_desc': 'Firebrand starts with a random crest (never Tornado). The basic shot becomes the Fire '
                        'Crest item, which goes into the pool.',
        'x_head': 'Randomize Head Butt',
        'x_head_desc': 'The head butt becomes a pool item: without it you cannot break statues or windows.',
        'diff_desc': {
            1: 'Strong items in spheres 1 to 3, more HP at the start. Early game: at most 3 crests/Armor.',
            2: 'Strong items in spheres 2 and 3, more HP at the start. Early game: at most 2 crests/Armor. The '
               'logic accepts Time Crest with HP in some places.',
            3: 'Moderate: 5 spheres with 1 strong item in each (Time Crest never in the first 2). Early game: at most '
               '2 crests/Armor and 5 HP. More paths with Time Crest and HP.',
            4: 'Strong items only from sphere 4 on, 5 fewer HP in the game. Early game: at most 1 crest/Armor and '
               '2 HP. The logic accepts paths with HP, Armor and Tornado instead of some crests.',
            5: 'Strongest items always in the last spheres, with Time Crest (when in the game) and Fang in the final '
               'castle. 2 to 4 items among Air Crest, Time Crest, Tornado and Demon Fire are out of the game. The logic '
               'may require underwater checks without the Water Crest. Anti-Softlock Prevention required.'},
        'go_names': {'vellum': '5 Vellums', 'bosses': 'All Bosses', 'crests': 'All 4 Main Crests', 'hp': 'All HP'},
        'go_desc': {
            'vellum': "Phalanx's castle appears with the 5 Vellums.",
            'bosses': 'The castle appears after beating the 15 bosses: Somulo, Hippogriff 1 and 2, Arma 1, 2 and 3, '
                      'Belth, Ovnunu, Flame Lord, Skulla, Flier 1 and 2, Holothurion, Crawler and Grewon. Trio the '
                      "Pago (a minigame) doesn't count.",
            'crests': 'The castle appears with the 4 transformation crests: Earth, Air, Water and Time. Not available '
                      'on difficulty 5 (it may remove Air and Time from the game).',
            'hp': 'The castle appears with every HP in the game (except the one in the castle). On difficulty 4 only '
                  'the remaining ones count.'},
        'no_d5': '(not on difficulty 5)',
        'go_d5': 'Goal "All 4 Main Crests" doesn\'t work with difficulty 5: switched to 5 Vellums.',
        'anti': 'Anti-Softlock Prevention',
        'anti_desc': 'Map patches against softlocks. Area 27: entering without the Earth Crest, you can die to get '
                     'out. Difficulty 5 without Air Crest and Tornado: areas 29 and 38 get a path with the Claw '
                     '(including the way to Phalanx).',
        'anti_warn': 'Disabling the anti-softlock patch with difficulty 5 selected may make the seed impossible to '
                     'finish. Disable at your own risk.\n\nDisable anyway?',
        'on': 'on', 'off': 'off',
        'info': '{m}\n\nDifficulty {v}: {d}\n\nGoal: {g}\n{a}: {s}',
        'generate': 'Generate', 'about': 'About', 'about_tip': 'Credits and generator version',
        'rom': 'ROM: {n}',
        'rom_bad': "This is not the original Demon's Crest (USA) ROM.",
        'rom_none_ok': "No ROM in the {d} folder is the original Demon's Crest (USA).",
        'rom_missing': "Put the original Demon's Crest (USA) ROM in the {d} folder.",
        'generating': 'Generating {n}...',
        'done': 'Done: {d}\\{b}.sfc\nSpoiler in {s}\\{b}.txt',
        'error': 'Error: {e}',
        'no_fill': '"{n}" did not pass the logic; try another name',
        'follow': 'Follow Natan:',
        'about_title': 'About DCOR', 'version': 'Version {v}', 'close': 'Close',
        'credits': [
            ('Created by Natan Anile', [
                '• Idea, direction, look and icon of the generator',
                '• Progression logic, difficulties, modes and goals',
                "• Mapping of the game's items: pots, statues, breakables and bosses",
                '• Anti-Softlock Prevention map patches',
                '• Testing everything in the game']),
            ('Collaboration: Asvel', [
                '• Logic and ideas']),
            ('Reference', [
                "FredYeye, Demon's Crest Rando: the values he mapped were used only to cross-check the ones we "
                'collected. None of his code is in DCOR.'])],
    },
}


def tr(key, lang=None, **kw):
    t = TEXTS[lang or LANG][key]
    return t.format(**kw) if kw else t


def mode_ok(i):
    return MODE_KEYS[i] is not None


def diff_desc(v):
    return tr('diff_desc')[v]


def go_name(k, lang=None):
    return tr('go_names', lang)[k]


# cores do modelo
BG, CARD, CARD_LINE = '#0b1020', '#0f172e', '#223057'
FIELD, FIELD_LINE, FIELD_FOCUS = '#0a0f1f', '#2b3a66', '#4f7cff'
TEXT, MUTED, DIM = '#eef1ff', '#b3bde0', '#7f8bb3'          # contraste maior (leitura, 29/09)
ACCENT, ACCENT_HI, SEL = '#4a63f0', '#5d78ff', '#1a2a5c'
BTN, BTN_HI = '#1c2a52', '#26386b'
CYAN = '#4fc3f7'
OK, ERR = '#4ade80', '#f87171'

RES = os.path.dirname(os.path.abspath(__file__))          # a pasta data (código e ícone)
HOME = os.path.dirname(RES)                                # a pasta do DCOR (ROM, Seed, Spoiler, config)
CONFIG = os.path.join(HOME, 'dcor_config.json')

BASE_W, BASE_H = 720, 940          # tamanho inicial da janela
MIN_S, MAX_S = 0.8, 1.8            # faixa da escala das letras (pela largura; o que não couber rola)
MIN_SIZE = (320, 240)              # dá pra encolher além do conteúdo: aparecem as barras de rolagem (29/09)
MIN_CONTENT_W = BASE_W                # abaixo desta largura (x escala) o conteúdo não espreme: rola na horizontal
# fontes nomeadas: mudar o tamanho delas atualiza tudo que as usa (rótulos e textos de Canvas).
# 'medium' = família do peso médio (Roboto Medium; sem a Roboto, Segoe UI Semibold).
FONT_SPECS = {'base': (11, 'normal', 'roman'), 'small': (10, 'normal', 'roman'), 'italic': (10, 'normal', 'italic'),
              'label': (12, 'bold', 'roman'), 'title': (15, 'bold', 'roman'), 'big': (16, 'bold', 'roman'),
              'num': (15, 'bold', 'roman'),
              'desc': (11, 'normal', 'roman', 'medium')}   # painel de descrição: peso médio (28-29/09)
F = {}
# Fonte (Neitan, 29/09): Roboto, levada junto em data/fonts e carregada só pelo programa (não instala no Windows).
# Sem os arquivos, a parecida que todo Windows tem: Segoe UI.
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
FAMILY = {'text': 'Segoe UI', 'medium': 'Segoe UI Semibold'}


def load_fonts():
    """Carrega os .ttf de data/fonts como fonte privada do processo (AddFontResourceEx, FR_PRIVATE). Chamar antes do
    tk.Tk(). Se a Roboto carregar, ela vira a fonte da janela."""
    try:
        names = sorted(n for n in os.listdir(FONT_DIR) if n.lower().endswith(('.ttf', '.otf')))
    except OSError:
        return
    loaded = set()
    for n in names:
        try:
            if ctypes.windll.gdi32.AddFontResourceExW(os.path.join(FONT_DIR, n), 0x10, 0):
                loaded.add(n.lower())
        except (AttributeError, OSError):
            return
    if 'roboto-regular.ttf' in loaded:
        FAMILY['text'] = 'Roboto'
        FAMILY['medium'] = 'Roboto Medium' if 'roboto-medium.ttf' in loaded else 'Roboto'


def make_fonts(root):
    for k, (size, weight, slant, *family) in FONT_SPECS.items():
        fam = FAMILY['medium'] if family else FAMILY['text']
        F[k] = tkfont.Font(root, family=fam, size=size, weight=weight, slant=slant)


def scale_fonts(s):
    for k, (size, *_) in FONT_SPECS.items():
        F[k].configure(size=max(7, round(size * s)))


def _rgb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


_AA = {}


def aa_radio(d, ring, bg, dot=None, ring_w=2.0, dot_r=0.0):
    """Bolinha de seleção lisa (o Canvas do Tk não suaviza bordas): imagem d x d calculada com 4x4 amostras por
    pixel, anel de espessura ring_w e ponto central de raio dot_r, misturados com a cor de fundo. Guardada em cache."""
    key = (d, ring, bg, dot, ring_w, dot_r)
    if key in _AA:
        return _AA[key]
    c, R = d / 2, d / 2 - 0.5
    bgc, rc, dc = _rgb(bg), _rgb(ring), _rgb(dot) if dot else None
    sub = [(i + 0.5) / 4 for i in range(4)]
    rows = []
    for y in range(d):
        row = []
        for x in range(d):
            nr = nd = 0
            for sy in sub:
                for sx in sub:
                    r = math.hypot(x + sx - c, y + sy - c)
                    if R - ring_w <= r <= R:
                        nr += 1
                    elif dc and r <= dot_r:
                        nd += 1
            px = [bgc[k] + (rc[k] - bgc[k]) * nr / 16 for k in range(3)]
            if dc:
                px = [px[k] + (dc[k] - px[k]) * nd / 16 for k in range(3)]
            row.append('#%02x%02x%02x' % tuple(round(v) for v in px))
        rows.append('{' + ' '.join(row) + '}')
    img = tk.PhotoImage(width=d, height=d)
    img.put(' '.join(rows))
    _AA[key] = img
    return img


def round_rect(cv, x0, y0, x1, y1, r, **kw):
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1, x0, y1,
           x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)


class Tip:
    """Descrição que aparece com o mouse parado em cima (text pode ser função)."""

    def __init__(self, widget, text):
        self.w, self.text, self.win, self.job = widget, text, None, None
        widget.bind('<Enter>', self.enter, add='+')
        widget.bind('<Leave>', self.leave, add='+')
        widget.bind('<ButtonPress>', self.leave, add='+')

    def enter(self, _=None):
        self.cancel()
        self.job = self.w.after(400, self.show)

    def cancel(self):
        if self.job:
            self.w.after_cancel(self.job)
            self.job = None

    def show(self):
        text = self.text() if callable(self.text) else self.text
        x, y = self.w.winfo_pointerx() + 12, self.w.winfo_pointery() + 16
        self.win = tk.Toplevel(self.w)
        self.win.wm_overrideredirect(True)
        self.win.wm_geometry(f'+{x}+{y}')
        tk.Label(self.win, text=text, justify='left', bg='#1b2547', fg=TEXT, relief='solid', borderwidth=1,
                 wraplength=360, padx=8, pady=5, font=F['small']).pack()

    def leave(self, _=None):
        self.cancel()
        if self.win:
            self.win.destroy()
            self.win = None


class ScrollBar(tk.Canvas):
    """Barra de rolagem escura desenhada (a do Windows é clara e o ttk não vai no exe): trilho fino, alça arredondada,
    arrastar e clicar no trilho. show() põe/tira da grade."""

    def __init__(self, master, axis, view):
        super().__init__(master, bg=BG, highlightthickness=0, **({'width': 12} if axis == 'y' else {'height': 12}))
        self.axis, self.view, self.first, self.last, self.visible, self.grab = axis, view, 0.0, 1.0, False, None
        self.bind('<Configure>', lambda _: self.draw())
        self.bind('<Button-1>', self.press)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<ButtonRelease-1>', lambda _: setattr(self, 'grab', None))

    def length(self):
        return max(1, self.winfo_height() if self.axis == 'y' else self.winfo_width())

    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self.draw()

    def show(self, on, **grid):
        if on != self.visible:
            self.visible = on
            self.grid(**grid) if on else self.grid_remove()

    def draw(self):
        self.delete('all')
        n, t = self.length(), 12
        a, b = self.first * n, max(self.first * n + 24, self.last * n)
        if self.axis == 'y':
            round_rect(self, 3, a + 2, t - 3, b - 2, 4, fill=BTN_HI, outline='')
        else:
            round_rect(self, a + 2, 3, b - 2, t - 3, 4, fill=BTN_HI, outline='')

    def pos(self, e):
        return (e.y if self.axis == 'y' else e.x) / self.length()

    def press(self, e):
        p = self.pos(e)
        if self.first <= p <= self.last:
            self.grab = p - self.first
        else:                                             # clique no trilho: pula uma página
            self.view('scroll', 1 if p > self.last else -1, 'pages')

    def drag(self, e):
        if self.grab is not None:
            self.view('moveto', self.pos(e) - self.grab)


class Card(tk.Canvas):
    """Cartão de borda arredondada que estica com o espaço dado; o conteúdo vai em self.inner (Frame, use grid).
    hug=True: a largura também é a do conteúdo (cartão do idioma, ao lado do da seed)."""

    def __init__(self, master, fill=CARD, line=CARD_LINE, bg=BG, r=12, pad=14, hug=False):
        super().__init__(master, bg=bg, highlightthickness=0, height=40, width=1)
        self.fill, self.line, self.r, self.pad, self.hug = fill, line, r, pad, hug
        self.inner = tk.Frame(self, bg=fill)
        self.win = self.create_window(pad, pad, window=self.inner, anchor='nw')
        self.shape = None
        self.bind('<Configure>', self.redraw)
        self.inner.bind('<Configure>', self.fit)

    def fit(self, _=None):                        # altura mínima = a do conteúdo
        need = self.inner.winfo_reqheight() + 2 * self.pad
        if int(self.cget('height')) != need:
            self.configure(height=need)
        if self.hug and int(self.cget('width')) != self.inner.winfo_reqwidth() + 2 * self.pad:
            self.configure(width=self.inner.winfo_reqwidth() + 2 * self.pad)

    def redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if self.shape:
            self.delete(self.shape)
        self.shape = round_rect(self, 1, 1, w - 2, h - 2, self.r, fill=self.fill, outline=self.line)
        self.tag_lower(self.shape)
        self.itemconfigure(self.win, width=max(1, w - 2 * self.pad),
                           height=max(self.inner.winfo_reqheight(), h - 2 * self.pad))


class RButton(tk.Canvas):
    """Botão arredondado só com texto; tamanho vem do texto (cresce com a fonte)."""

    def __init__(self, master, text, command, font, bg=CARD, fill=BTN, hover=BTN_HI, line=FIELD_LINE, fg=TEXT,
                 padx=18, pady=8, r=8):
        super().__init__(master, bg=bg, highlightthickness=0, cursor='hand2')
        self.text, self.command, self.font = text, command, font
        self.fill, self.hover, self.line, self.fg = fill, hover, line, fg
        self.padx, self.pady, self.r, self.enabled, self.over = padx, pady, r, True, False
        self.bind('<Configure>', lambda _: self.draw())
        self.bind('<Enter>', lambda _: self.set_over(True))
        self.bind('<Leave>', lambda _: self.set_over(False))
        self.bind('<Button-1>', lambda _: self.enabled and self.command and self.command())
        self.rescale()

    def rescale(self):
        w = self.font.measure(self.text) + 2 * self.padx
        h = self.font.metrics('linespace') + 2 * self.pady
        self.configure(width=w, height=h)
        self.draw()

    def set_text(self, text):
        self.text = text
        self.rescale()

    def set_over(self, on):
        self.over = on
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            w, h = int(self.cget('width')), int(self.cget('height'))
        body = (self.hover if self.over else self.fill) if self.enabled else BTN
        round_rect(self, 1, 1, w - 2, h - 2, self.r, fill=body, outline=self.line)
        self.create_text(w // 2, h // 2, text=self.text, fill=self.fg if self.enabled else DIM, font=self.font)

    def set_enabled(self, on):
        self.enabled = on
        self.config(cursor='hand2' if on else 'arrow')
        self.draw()


class Field(tk.Frame):
    """Campo de texto escuro com borda que acende no foco e texto de exemplo quando vazio."""

    def __init__(self, master, placeholder, value=''):
        super().__init__(master, bg=FIELD_LINE, padx=1, pady=1)
        self.ph, self.var = placeholder, tk.StringVar(value=value)
        self.e = tk.Entry(self, textvariable=self.var, bg=FIELD, fg=TEXT, relief='flat', insertbackground=TEXT,
                          font=F['base'], disabledbackground=FIELD)
        self.e.pack(fill='both', expand=True, ipady=6, ipadx=8)
        self.e.bind('<FocusIn>', self.focus_in)
        self.e.bind('<FocusOut>', self.focus_out)
        self.showing_ph = False
        self.focus_out()

    def focus_in(self, _=None):
        self.config(bg=FIELD_FOCUS)
        if self.showing_ph:
            self.showing_ph = False
            self.var.set('')
            self.e.config(fg=TEXT)

    def focus_out(self, _=None):
        self.config(bg=FIELD_LINE)
        if not self.var.get():
            self.showing_ph = True
            self.var.set(self.ph)
            self.e.config(fg=DIM)

    def set_placeholder(self, ph):
        self.ph = ph
        if self.showing_ph:
            self.var.set(ph)

    def get(self):
        return '' if self.showing_ph else self.var.get()

    def set(self, v):
        self.showing_ph = False
        self.var.set(v)
        self.e.config(fg=TEXT)
        if not v:
            self.focus_out()


class DiffBar(tk.Canvas):
    """Barra de dificuldade: caixa com o número + 5 segmentos; clique ou arraste. Estica com a largura."""

    def __init__(self, master, value, on_change):
        super().__init__(master, bg=CARD, highlightthickness=0, cursor='hand2', width=1)
        self.value, self.on_change = value, on_change
        self.bind('<Button-1>', self.click)
        self.bind('<B1-Motion>', self.click)
        self.bind('<Configure>', lambda _: self.draw())
        self.rescale()

    def rescale(self):
        self.configure(height=F['num'].metrics('linespace') + 16)
        self.draw()

    def geom(self):
        w, h = max(self.winfo_width(), 120), max(self.winfo_height(), 20)
        box = h + 10
        return w, h, box, (w - box - 12) / (DIFF_MAX - DIFF_MIN + 1)

    def click(self, e):
        w, h, box, seg = self.geom()
        if e.x < box + 6:
            return
        v = DIFF_MIN + min(DIFF_MAX - DIFF_MIN, max(0, int((e.x - box - 6) // seg)))
        if v != self.value:
            self.value = v
            self.draw()
            self.on_change(v)

    def draw(self):
        self.delete('all')
        w, h, box, seg = self.geom()
        round_rect(self, 1, 1, w - 2, h - 2, 8, fill=FIELD, outline=FIELD_LINE)
        round_rect(self, 1, 1, box, h - 2, 8, fill=SEL, outline=ACCENT)
        self.create_text(box // 2, h // 2, text=str(self.value), fill=TEXT, font=F['num'])
        for i in range(DIFF_MAX - DIFF_MIN + 1):
            x0 = box + 6 + i * seg
            on = i < self.value - DIFF_MIN + 1
            self.create_rectangle(x0 + 3, h * 0.35, x0 + seg - 3, h * 0.65, width=0, fill=CYAN if on else '#1e2a4d')


class OptRow(tk.Canvas):
    """Linha de opção: bolinha (ou quadradinho, box=True), nome e nota ("em breve" etc.); estica com a largura.
    on_pick recebe key. Travada (enabled=False): cinza e sem clique."""

    def __init__(self, master, name, key, on_pick, box=False, note=''):
        super().__init__(master, bg=CARD, highlightthickness=0, width=1)
        self.name, self.key, self.on_pick, self.box, self.note = name, key, on_pick, box, note
        self.on, self.enabled = False, True
        self.bind('<Configure>', lambda _: self.draw())
        self.bind('<Button-1>', lambda _: self.enabled and self.on_pick and self.on_pick(self.key))
        self.rescale()

    def rescale(self):
        self.configure(height=F['base'].metrics('linespace') + 16)
        self.draw()

    def set_enabled(self, on, note=None):
        self.enabled = on
        if note is not None:
            self.note = note
        self.config(cursor='hand2' if on else 'arrow')
        self.draw()

    def select(self, on):
        self.on = on
        self.draw()

    def set_text(self, name, note=None):
        self.name = name
        if note is not None:
            self.note = note
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = max(self.winfo_width(), 60), max(self.winfo_height(), 20)
        if self.on:
            round_rect(self, 0, 1, w - 1, h - 2, 8, fill=SEL, outline=SEL)
        r = max(6, min(round(F['base'].metrics('linespace') * 0.45), h // 2 - 4))
        cy, cx = h // 2, 12 + r
        ring = ACCENT_HI if self.on else (MUTED if self.enabled else DIM)
        if self.box:
            self.create_rectangle(cx - r, cy - r, cx + r, cy + r, outline=ring, width=2)
            if self.on:
                self.create_rectangle(cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5, fill=TEXT, width=0)
        else:                                             # liso: imagem suavizada (aa_radio), não create_oval
            d = 2 * r + 2
            self.create_image(cx, cy, image=aa_radio(d, ring, SEL if self.on else CARD, TEXT if self.on else None,
                                                     max(1.6, d / 11), d * 0.22))
        x = cx + r + 12
        t = self.create_text(x, cy, text=self.name, anchor='w', fill=TEXT if self.enabled else MUTED, font=F['base'])
        if self.note:
            self.create_text(self.bbox(t)[2] + 6, cy, text=self.note, anchor='w', fill=DIM, font=F['italic'])


class FlagPicker(tk.Canvas):
    """Bandeiras do idioma, uma em cima da outra (Brasil em cima, EUA embaixo; pedido do Neitan, 28/09).
    Desenhadas no Canvas (sem imagem), crescem com a letra. A escolhida fica num fundo aceso; on_pick recebe o idioma."""
    ORDER = ('pt', 'en')

    def __init__(self, master, lang, on_pick, bg=CARD):
        super().__init__(master, bg=bg, highlightthickness=0, cursor='hand2')
        self.lang, self.on_pick = lang, on_pick
        self.bind('<Button-1>', self.click)
        self.rescale()

    def rescale(self):
        self.fh = round(F['label'].metrics('linespace') * 2.1)
        self.fw, self.p, self.gap = round(self.fh * 1.75), 5, 8
        self.configure(width=self.fw + 2 * self.p, height=2 * (self.fh + 2 * self.p) + self.gap)
        self.draw()

    def select(self, lang):
        self.lang = lang
        self.draw()

    def slot_y(self, i):
        return i * (self.fh + 2 * self.p + self.gap)

    def click(self, e):
        i = 0 if e.y < self.slot_y(1) - self.gap / 2 else 1
        if self.ORDER[i] != self.lang:
            self.on_pick(self.ORDER[i])

    def draw(self):
        self.delete('all')
        p = self.p
        for i, lang in enumerate(self.ORDER):
            y = self.slot_y(i)
            if lang == self.lang:
                round_rect(self, 1, y + 1, self.fw + 2 * p - 2, y + self.fh + 2 * p - 2, 7, fill=SEL, outline=ACCENT_HI)
            (self.brazil if lang == 'pt' else self.usa)(p, y + p, self.fw, self.fh)
            self.create_rectangle(p, y + p, p + self.fw, y + p + self.fh, outline='#05070f')

    def brazil(self, x, y, w, h):
        self.create_rectangle(x, y, x + w, y + h, fill='#009c3b', width=0)
        mx, my = w * 0.085, h * 0.12
        self.create_polygon(x + mx, y + h / 2, x + w / 2, y + my, x + w - mx, y + h / 2, x + w / 2, y + h - my,
                            fill='#fedf00', outline='')
        cx, cy, r = x + w / 2, y + h / 2, h * 0.25
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill='#002776', width=0)
        # faixa branca: pedaço de um círculo grande com centro embaixo, só a parte dentro do globo
        bx, by, big, bw = cx - r * 0.3, cy + r * 2.2, r * 2.3, max(1.5, r * 0.18)
        pts = []
        for k in range(61):
            a = 3.1416 * (0.25 + 0.5 * k / 60)
            px, py = bx + big * math.cos(a), by - big * math.sin(a)
            if (px - cx) ** 2 + (py - cy) ** 2 < (r - bw / 2) ** 2:
                pts += [px, py]
        if len(pts) >= 4:
            self.create_line(*pts, fill='white', width=bw)
        d = max(0.6, r * 0.045)
        for sx, sy in ((-0.45, 0.45), (-0.05, 0.65), (0.4, 0.45), (0.15, 0.35), (-0.3, 0.3)):
            self.create_oval(cx + sx * r - d, cy + sy * r - d, cx + sx * r + d, cy + sy * r + d, fill='white', width=0)

    def usa(self, x, y, w, h):
        s = h / 13
        for k in range(13):
            self.create_rectangle(x, y + k * s, x + w, y + (k + 1) * s, fill='#b22234' if k % 2 == 0 else 'white',
                                  width=0)
        cw, ch = w * 0.4, s * 7
        self.create_rectangle(x, y, x + cw, y + ch, fill='#3c3b6e', width=0)
        d = max(0.6, h / 60)
        for row in range(4):
            for col in range(5 - row % 2):
                sx = x + cw * (col + 0.5 + 0.5 * (row % 2)) / 5
                sy = y + ch * (row + 0.5) / 4
                self.create_oval(sx - d, sy - d, sx + d, sy + d, fill='white', width=0)


def load_config():
    try:
        return json.load(open(CONFIG, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    try:
        json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    except OSError:
        pass


def read_vanilla(path):
    """Bytes da ROM original ou erro legível. Aceita ROM com cabeçalho de copiadora (512 bytes)."""
    b = open(path, 'rb').read()
    if len(b) % 1024 == 512:
        b = b[512:]
    if hashlib.sha1(b).hexdigest() != VANILLA_SHA1:
        raise ValueError(tr('rom_bad'))
    return b


# Nome da seed: 5 palavras do jogo (37 palavras = ~45 milhões de nomes; eram 4 até 28/09) (chefes, crests, itens, talismãs, lugares), como "MFOR - Adam Arachnus Dachora
# Space". O nome É a seed: o número vem do hash do nome, então digitar o mesmo nome refaz a mesma ROM.
WORDS = [
    # chefes
    'Somulo', 'Hippogriff', 'Arma', 'Belth', 'Ovnunu', 'Skulla', 'Flier', 'Crawler', 'Holothurion', 'Grewon',
    'Pago', 'Phalanx', 'Flamelord',
    # crests e poderes
    'Buster', 'Tornado', 'Claw', 'Demonfire', 'Earth', 'Air', 'Water', 'Time', 'Crest',
    # itens e talismãs
    'Vellum', 'Potion', 'Skull', 'Armor', 'Fang', 'Hand', 'Crown', 'Talisman',
    # personagens e lugares
    'Firebrand', 'Gargoyle', 'Ghoul', 'Realm', 'Colosseum', 'Castle', 'Demon',
]
ROM_DIR, SEED_DIR, SPOILER_DIR = 'ROM', 'Seed', 'Spoiler'
PREFIX = 'DemonRando'


def seed_name(rng=random):
    return ' '.join(rng.sample(WORDS, 5))


def seed_from_name(text):
    """(nome arrumado, número da seed). Qualquer texto vale; maiúsculas/espaços extras não mudam a seed."""
    words = [w.capitalize() for w in text.split()]
    name = ' '.join(words)
    return name, int.from_bytes(hashlib.sha1(name.lower().encode()).digest()[:4], 'big') & 0x7FFFFFFF


def find_rom(home=None):
    """Primeira ROM original de Demon's Crest (USA) na pasta ROM. Devolve (bytes, nome do arquivo)."""
    d = os.path.join(home or HOME, ROM_DIR)
    names = sorted(n for n in os.listdir(d) if n.lower().endswith(('.sfc', '.smc'))) if os.path.isdir(d) else []
    for n in names:
        try:
            return read_vanilla(os.path.join(d, n)), n
        except (OSError, ValueError):
            continue
    if names:
        raise ValueError(tr('rom_none_ok', d=ROM_DIR))
    raise ValueError(tr('rom_missing', d=ROM_DIR))


def make_dirs(home=None):
    for d in (ROM_DIR, SEED_DIR, SPOILER_DIR):
        os.makedirs(os.path.join(home or HOME, d), exist_ok=True)


def write_seed(text, van, mode, diff, go='vellum', anti=False, home=None):
    """Gera e grava Seed/DemonRando - Nome.sfc e Spoiler/DemonRando - Nome.txt (mode = índice em MODE_KEYS, go = chave
    de GO_KEYS, anti = Anti-Softlock). Devolve o nome do arquivo. O spoiler sai sempre em inglês (29/09)."""
    home = home or HOME
    name, seed = seed_from_name(text)
    res = R.build_seed(seed, van, R.Logic(diff, MODE_KEYS[mode], go, anti))
    if res is None:
        raise RuntimeError(tr('no_fill', n=name))
    data, lines, _ = res
    lines[0] = f'{PREFIX} - {name}' + lines[0][lines[0].index(':'):]
    base = f'{PREFIX} - {name}'
    make_dirs(home)
    open(os.path.join(home, SEED_DIR, base + '.sfc'), 'wb').write(data)
    with open(os.path.join(home, SPOILER_DIR, base + '.txt'), 'w', encoding='utf-8') as f:
        f.write(f"DCOR {VERSION} - {tr('modes', 'en')[mode]}, difficulty {diff}, Goal: {go_name(go, 'en')}, "
                f"{tr('anti', 'en')}: {'yes' if anti else 'no'} (internal seed {seed})\n" + '\n'.join(lines) + '\n')
    return base


def dark_title_bar(root):
    """Barra de título escura no Windows 10/11 (DWMWA_USE_IMMERSIVE_DARK_MODE)."""
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        on = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(on), ctypes.sizeof(on)) == 0:
                break
    except (AttributeError, OSError):
        pass


def label(master, text, font, fg=TEXT, **kw):
    return tk.Label(master, text=text, font=font, fg=fg, bg=master.cget('bg'), anchor='w', **kw)


class App:
    def __init__(self, root):
        global LANG
        self.root = root
        self.cfg = load_config()
        LANG = self.cfg.get('lang') if self.cfg.get('lang') in LANGS else 'pt'
        self.last = None                   # nome da última seed gerada: Gerar de novo com ele no campo sorteia outro
        self.msg = None                    # status atual (função que monta o texto no idioma da vez, cor)
        self.about_win = None
        make_fonts(root)
        root.title(f"DCOR - Demon's Crest Open Randomizer {VERSION}")
        root.configure(bg=BG)
        root.geometry(f'{BASE_W}x{BASE_H}')
        ico = os.path.join(RES, 'dcor.ico')
        if os.path.exists(ico):
            root.iconbitmap(default=ico)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.minsize(*MIN_SIZE)
        # tudo dentro de um Canvas que rola (29/09): a janela encolhe além do conteúdo e aparecem as barras
        self.view = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.view.grid(row=0, column=0, sticky='nsew')
        self.vbar = ScrollBar(root, 'y', self.view.yview)
        self.hbar = ScrollBar(root, 'x', self.view.xview)
        self.view.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        body = self.body = tk.Frame(self.view, bg=BG)
        self.body_win = self.view.create_window(0, 0, window=body, anchor='nw')
        body.columnconfigure(0, weight=1)
        self.view.bind('<Configure>', lambda e: self.relayout())
        body.bind('<Configure>', lambda e: self.relayout())
        root.bind_all('<MouseWheel>', self.wheel)
        root.bind_all('<Shift-MouseWheel>', lambda e: self.wheel(e, 'x'))
        self.scalables, self.scale = [], 1.0
        self.texts = []                    # (rótulo, chave de TEXTS): refeitos ao trocar o idioma
        pad = 16

        # --- seed e ROM (pastas fixas ao lado do exe: ROM, Seed, Spoiler) | idioma
        make_dirs()
        head = tk.Frame(body, bg=BG)
        head.grid(row=0, column=0, sticky='nsew', padx=pad, pady=(pad, 8))
        head.columnconfigure(0, weight=1)
        top = Card(head)
        top.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        t = top.inner
        t.columnconfigure(0, weight=1)
        self.text(label(t, '', F['label']), 'seed').grid(row=0, column=0, columnspan=2, sticky='w')
        self.seed = Field(t, tr('seed_ph'))
        self.seed.grid(row=1, column=0, sticky='nsew', pady=(6, 0), padx=(0, 10))
        Tip(self.seed.e, lambda: tr('seed_tip'))
        self.roll = RButton(t, tr('roll'), self.roll_seed, F['base'])
        self.roll.grid(row=1, column=1, pady=(6, 0))
        Tip(self.roll, lambda: tr('roll_tip'))
        self.scalables.append(self.roll)
        self.rom_label = label(t, '', F['small'])
        self.rom_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(8, 0))
        self.check_rom()
        lc = Card(head, hug=True)
        lc.grid(row=0, column=1, sticky='nsew')
        self.text(tk.Label(lc.inner, font=F['title'], fg=TEXT, bg=CARD), 'lang').pack()
        self.flags = FlagPicker(lc.inner, LANG, self.set_lang)
        self.flags.pack(pady=(4, 0))
        Tip(self.flags, lambda: f"{tr('lang_tip', 'pt')} / {tr('lang_tip', 'en')}")
        self.scalables.append(self.flags)
        self.cards = [top, lc]

        # --- lógica: dificuldade + modos | descrição
        logic = self.logic_card = Card(body)
        self.cards.append(logic)
        logic.grid(row=1, column=0, sticky='nsew', padx=pad, pady=8)
        body.rowconfigure(1, weight=1)
        L = logic.inner
        L.columnconfigure(0, weight=1, uniform='l')    # descrição com metade do cartão (antes 2/5; 28/09)
        L.columnconfigure(1, weight=1, uniform='l')
        L.rowconfigure(1, weight=1)
        self.text(label(L, '', F['title']), 'logic').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        left = tk.Frame(L, bg=CARD)
        left.grid(row=1, column=0, sticky='nsew', padx=(0, 12))
        left.columnconfigure(0, weight=1)
        self.text(label(left, '', F['label']), 'diff').grid(row=0, column=0, sticky='w')
        self.diff = DiffBar(left, self.cfg.get('diff', DEFAULT_DIFF), self.set_diff)
        self.diff.grid(row=1, column=0, sticky='ew', pady=(6, 10))
        Tip(self.diff, lambda: tr('diff_tip', v=self.diff.value, d=diff_desc(self.diff.value)))
        self.scalables.append(self.diff)
        self.text(label(left, '', F['label']), 'mode').grid(row=2, column=0, sticky='w', pady=(0, 4))
        self.mode = self.cfg.get('mode', DEFAULT_MODE)
        self.rows = []
        for i in range(len(MODE_KEYS)):
            r = OptRow(left, '', i, self.set_mode)
            r.set_enabled(mode_ok(i))
            r.grid(row=3 + i, column=0, sticky='ew', pady=1)
            Tip(r, lambda i=i: self.mode_text(i))
            self.rows.append(r)
            self.scalables.append(r)
        info = tk.Frame(L, bg='#0c1430', highlightthickness=1, highlightbackground=CARD_LINE)
        info.grid(row=1, column=1, sticky='nsew')
        # width=1: o texto que quebra linha não pede largura (senão a quebra muda o layout, que muda a quebra... e a
        # janela travava num laço ao redimensionar, 28/09)
        self.info = tk.Label(info, text='', justify='left', anchor='nw', bg='#0c1430', fg='#d6ddf7', font=F['desc'],
                             padx=14, pady=12, width=1)
        self.info.pack(fill='both', expand=True)
        self.info.bind('<Configure>', self.info_wrap)

        # --- objetivo (o que libera o castelo) | extras
        gm = Card(body)
        self.cards.append(gm)
        gm.grid(row=2, column=0, sticky='nsew', padx=pad, pady=8)
        G = gm.inner
        G.columnconfigure(0, weight=1, uniform='g')
        G.columnconfigure(1, weight=1, uniform='g')
        self.text(label(G, '', F['title']), 'go').grid(row=0, column=0, sticky='w', pady=(0, 6))
        self.text(label(G, '', F['title']), 'extras').grid(row=0, column=1, sticky='w', pady=(0, 6), padx=(12, 0))
        self.gomode = self.cfg.get('go', DEFAULT_GO)
        if self.gomode not in GO_KEYS:
            self.gomode = DEFAULT_GO
        self.go_rows = {}
        for i, k in enumerate(GO_KEYS):
            r = OptRow(G, '', k, self.set_go)
            r.grid(row=1 + i, column=0, sticky='ew', pady=1, padx=(0, 12))
            Tip(r, lambda k=k: tr('go_desc')[k])
            self.go_rows[k] = r
            self.scalables.append(r)
        self.anti = bool(self.cfg.get('antisoftlock', False))
        self.anti_row = OptRow(G, '', 'anti', self.toggle_anti, box=True)
        self.anti_row.grid(row=1, column=1, sticky='ew', pady=1, padx=(12, 0))
        Tip(self.anti_row, lambda: tr('anti_desc'))
        self.scalables.append(self.anti_row)
        # extras do handoff de 29/09 (Fire Crest / crest inicial / cabeçada): na janela, mas travados até a ROM ter
        self.soon_rows = []
        for i, k in enumerate(('x_crest', 'x_head')):
            r = OptRow(G, '', k, None, box=True)
            r.set_enabled(False)
            r.grid(row=2 + i, column=1, sticky='ew', pady=1, padx=(12, 0))
            Tip(r, lambda k=k: tr(k + '_desc') + '\n\n' + tr('not_yet'))
            self.soon_rows.append((r, k))
            self.scalables.append(r)

        # --- gerar
        bottom = tk.Frame(body, bg=BG)
        bottom.grid(row=3, column=0, sticky='ew', padx=pad, pady=(8, pad))
        bottom.columnconfigure(1, weight=1)
        self.go = RButton(bottom, tr('generate'), self.generate, F['big'], bg=BG, fill=ACCENT, hover=ACCENT_HI,
                          line=ACCENT_HI, padx=48, pady=12, r=10)
        self.go.grid(row=0, column=0, sticky='w')
        self.scalables.append(self.go)
        self.status = label(bottom, '', F['small'], fg=MUTED, justify='left', width=1)
        self.status.grid(row=0, column=1, sticky='ew', padx=(16, 0))
        self.status.bind('<Configure>', lambda e: self.status.configure(wraplength=max(80, e.width)))
        self.about_btn = RButton(bottom, tr('about'), self.about, F['base'], bg=BG)
        self.about_btn.grid(row=0, column=2, sticky='e', padx=(12, 0))
        Tip(self.about_btn, lambda: tr('about_tip'))
        self.scalables.append(self.about_btn)

        self.retext()
        self.set_go(self.gomode)
        self.anti_row.select(self.anti)
        self.set_mode(self.mode)
        self.apply_scale(1.0)
        root.update_idletasks()
        self.refit()
        dark_title_bar(root)

    # --- idioma: troca na hora, sem reiniciar
    def text(self, widget, key):
        self.texts.append((widget, key))
        return widget

    def mode_text(self, i):
        d = tr('mode_desc')[i]
        return d if mode_ok(i) else d + '\n\n' + tr('not_yet')

    def retext(self):
        for w, k in self.texts:
            w.configure(text=tr(k))
        self.seed.set_placeholder(tr('seed_ph'))
        for b, k in ((self.roll, 'roll'), (self.go, 'generate'), (self.about_btn, 'about')):
            b.set_text(tr(k))
        for i, r in enumerate(self.rows):
            r.set_text(tr('modes')[i], '' if mode_ok(i) else tr('soon'))
        for k, r in self.go_rows.items():
            r.set_text(go_name(k))
        self.anti_row.set_text(tr('anti'))
        for r, k in self.soon_rows:
            r.set_text(tr(k), tr('soon'))
        self.check_rom()
        self.set_diff(self.diff.value, first=True)       # nota do "4 crests" e painel de descrição
        if self.msg:
            self.say(*self.msg)

    def set_lang(self, lang):
        global LANG
        LANG = lang
        self.cfg['lang'] = lang
        save_config(self.cfg)
        self.flags.select(lang)
        self.retext()
        self.relayout()
        if self.about_win and self.about_win.winfo_exists():
            self.about_win.destroy()
            self.about()

    # --- tamanho: letras e alturas acompanham a janela
    def apply_scale(self, s):
        self.scale = s
        scale_fonts(s)
        for w in self.scalables:
            w.rescale()
        self.root.update_idletasks()
        for c in self.cards:                       # altura dos cartões = conteúdo (sem esperar o evento)
            c.fit()
        self.root.update_idletasks()

    def relayout(self):
        """Escala das letras pela largura da janela; o conteúdo ocupa no mínimo a área visível e, se passar dela, as
        barras de rolagem aparecem (29/09: antes a janela não encolhia além do conteúdo)."""
        vw, vh = self.view.winfo_width(), self.view.winfo_height()
        if vw < 10:
            return
        s = max(MIN_S, min(MAX_S, vw / BASE_W))
        if abs(s - self.scale) >= 0.03:
            self.apply_scale(s)
        cw = max(vw, self.body.winfo_reqwidth(), round(MIN_CONTENT_W * MIN_S))
        ch = max(vh, self.body.winfo_reqheight())
        if (cw, ch) != getattr(self, '_content', None):
            self._content = cw, ch
            self.view.itemconfigure(self.body_win, width=cw, height=ch)
            self.view.configure(scrollregion=(0, 0, cw, ch))
        self.vbar.show(ch > vh, row=0, column=1, sticky='ns')
        self.hbar.show(cw > vw, row=1, column=0, sticky='ew')

    def wheel(self, e, axis='y'):
        if (self.vbar if axis == 'y' else self.hbar).visible and str(e.widget).startswith(str(self.root)):
            (self.view.yview_scroll if axis == 'y' else self.view.xview_scroll)(int(-e.delta / 120) * 3, 'units')

    def info_wrap(self, e):
        """A descrição quebra linha pela largura dela; a altura nova faz o cartão crescer (e a janela rolar)."""
        self.info.configure(wraplength=max(80, e.width - 28))
        self.root.after_idle(self.refit)

    def refit(self):
        """Cartões na altura do conteúdo de novo e a área que rola recalculada (o texto pode ter encolhido)."""
        for _ in range(3):                                # até estabilizar (a quebra de linha muda a altura pedida)
            self.root.update_idletasks()
            before = [c.cget('height') for c in self.cards]
            for c in self.cards:
                c.fit()
            if [c.cget('height') for c in self.cards] == before:
                break
        self.root.update_idletasks()
        self.relayout()

    # --- opções
    def set_diff(self, v, first=False):
        if v == 5:
            self.go_rows['crests'].set_enabled(False, tr('no_d5'))
            if self.gomode == 'crests':
                self.set_go(DEFAULT_GO)
                self.say(lambda: tr('go_d5'), MUTED)
            if not first and not self.anti:            # a dificuldade 5 liga o anti-softlock sozinha
                self.anti = True
                self.anti_row.select(True)
        else:
            self.go_rows['crests'].set_enabled(True, '')
        self.update_info()

    def set_go(self, k):
        self.gomode = k
        for key, r in self.go_rows.items():
            r.select(key == k)
        self.update_info()

    def toggle_anti(self, _k):
        if self.anti and self.diff.value == 5 and not msgbox.askyesno('DCOR', tr('anti_warn'), icon='warning',
                                                                      parent=self.root):
            return
        self.anti = not self.anti
        self.anti_row.select(self.anti)
        self.update_info()

    def set_mode(self, i):
        self.mode = i
        for k, r in enumerate(self.rows):
            r.select(k == i)
        self.update_info()

    def update_info(self):
        if not hasattr(self, 'go') or not hasattr(self, 'rows'):
            return
        v = self.diff.value
        self.info.configure(text=tr('info', m=self.mode_text(self.mode), v=v, d=diff_desc(v), g=go_name(self.gomode),
                                    a=tr('anti'), s=tr('on') if self.anti else tr('off')))
        self.go.set_enabled(mode_ok(self.mode))

    def check_rom(self):
        """Mostra qual ROM da pasta ROM vai ser usada (confere de novo a cada Gerar)."""
        try:
            self.van, n = find_rom()
            self.rom_label.configure(text=tr('rom', n=n), fg=OK)
        except ValueError as e:
            self.van = None
            self.rom_label.configure(text=str(e), fg=ERR)
        return self.van

    def roll_seed(self):
        self.seed.set(seed_name())

    def about(self):
        """Janela Sobre: versão e créditos (TEXTS 'credits')."""
        if self.about_win and self.about_win.winfo_exists():
            return self.about_win.lift()
        w = self.about_win = tk.Toplevel(self.root, bg=BG)
        w.title(tr('about_title'))
        w.resizable(False, False)
        w.transient(self.root)
        f = tk.Frame(w, bg=BG, padx=24, pady=18)
        f.pack(fill='both', expand=True)
        label(f, "Demon's Crest Open Randomizer", F['title']).pack(anchor='w')
        label(f, tr('version', v=VERSION), F['base'], fg=MUTED).pack(anchor='w', pady=(0, 10))
        for title, lines in tr('credits'):
            label(f, title, F['label']).pack(anchor='w', pady=(8, 2))
            for ln in lines:
                label(f, ln, F['base'], fg=MUTED, justify='left', wraplength=round(440 * self.scale)).pack(anchor='w')
        link = label(f, FRED_URL, F['small'], fg=CYAN, cursor='hand2')
        link.pack(anchor='w', pady=(4, 0))
        link.bind('<Button-1>', lambda _: os.startfile(FRED_URL))   # os.startfile: webbrowser não está no exe
        label(f, tr('follow'), F['label']).pack(anchor='w', pady=(14, 4))
        for kind, url in SOCIAL:
            row = tk.Frame(f, bg=BG, cursor='hand2')
            row.pack(anchor='w', pady=2)
            h = F['base'].metrics('linespace') + 4
            ic = tk.Canvas(row, width=round(h * 1.4), height=h, bg=BG, highlightthickness=0, cursor='hand2')
            social_icon(ic, kind, round(h * 1.4), h)
            ic.pack(side='left')
            t = label(row, url, F['base'], fg=CYAN, cursor='hand2')
            t.pack(side='left', padx=(8, 0))
            for w_ in (row, ic, t):
                w_.bind('<Button-1>', lambda _, u=url: os.startfile(u))
        b = RButton(f, tr('close'), w.destroy, F['base'], bg=BG)
        b.pack(anchor='e', pady=(16, 0))
        w.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - w.winfo_reqheight()) // 3
        w.geometry(f'+{max(0, x)}+{max(0, y)}')
        dark_title_bar(w)
        w.bind('<Escape>', lambda _: w.destroy())
        w.focus_set()

    def say(self, text, color=MUTED):
        """Status ao lado do Gerar. text pode ser função (refeita no idioma novo ao trocar a bandeira)."""
        self.msg = text, color
        self.status.configure(text=text() if callable(text) else text, fg=color)

    def generate(self):
        van = self.check_rom()
        if van is None:
            return self.say(lambda: self.rom_label.cget('text'), ERR)
        text = self.seed.get().strip()
        if not text or text == self.last:  # nome digitado/sorteado é respeitado; o que acabou de sair não se repete
            text = seed_name()
        name, _ = seed_from_name(text)
        self.seed.set(name)
        self.last = name
        self.cfg.update(mode=self.mode, diff=self.diff.value, go=self.gomode, antisoftlock=self.anti)
        save_config(self.cfg)
        self.go.set_enabled(False)
        self.say(lambda: tr('generating', n=name), TEXT)
        self.result = None
        threading.Thread(target=self.work, args=(name, van, self.mode, self.diff.value, self.gomode, self.anti),
                         daemon=True).start()
        self.root.after(100, self.poll)

    def work(self, name, van, mode, diff, go, anti):
        try:
            base = write_seed(name, van, mode, diff, go, anti)
            msg, color = (lambda: tr('done', d=SEED_DIR, b=base, s=SPOILER_DIR)), OK
        except Exception as e:                                          # mostra qualquer falha na janela
            err = str(e)
            msg, color = (lambda: tr('error', e=err)), ERR
        self.result = msg, color                   # a janela só é mexida pela thread principal (poll)

    def poll(self):
        if self.result is None:
            self.root.after(100, self.poll)
            return
        self.say(*self.result)
        self.update_info()


def main():
    if '--seed' in sys.argv:        # sem janela (conferência):
        # "Demon's Crest Open Randomizer.exe" --seed "Nome Da Seed" [--modo limitado|classico|extra] [--dif 1-5]
        #   [--go vellum|bosses|crests|hp] [--anti 1] [--home PASTA]
        a = dict(zip(sys.argv[1::2], sys.argv[2::2]))
        home = a.get('--home', HOME)
        mode = MODE_KEYS.index(a.get('--modo', 'extra'))
        write_seed(a['--seed'], find_rom(home)[0], mode, int(a.get('--dif', DEFAULT_DIFF)), a.get('--go', DEFAULT_GO),
                   a.get('--anti', '0') == '1', home)
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)                   # texto nítido em tela com escala
    except (AttributeError, OSError):
        pass
    load_fonts()                                                        # Roboto de data/fonts, se houver
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
