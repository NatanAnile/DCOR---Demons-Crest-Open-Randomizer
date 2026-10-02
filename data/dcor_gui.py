"""DCOR - Demon's Crest Open Randomizer: janela do executável (26/09).

O executável (Demon's Crest Open Randomizer.exe) é só o lançador (Python embutido): todo o código fica aqui na pasta
data e é lido ao abrir, então mexer no rando não pede compilar de novo (27/09, pedido do Neitan, pensando em abrir o
código no git). Sem o exe: python data/dcor_gui.py.

Layout (01/10, modelo do Neitan): cartão da Lógica com título, bandeiras e Sobre em cima e as guias Simples e Avançado;
embaixo o cartão da Seed e o Gerar. Sem linha de ROM nem status: erro (ROM, lógica) e sucesso vêm numa caixa no visual
do launcher (App.dialog; a do gerador do Metroid Fusion como referência). As últimas opções das duas guias e a guia
aberta ficam no dcor_config.json (como o site do Archipelago guarda o último yaml).
  - Guia Simples: os presets de dificuldade (controles abaixo).
  - Guia Avançado (gera desde 02/10; ADV_*, adv_resolve): preset (.json), dificuldade 1-5/Custom (marca as opções
    como a da Simples), nível da lógica, acessibilidade, pool de itens, densidade, remoção de itens, HP disponível,
    objetivo, Starter Crest, Head Butt, Skip Somulo e Anti-Softlock. "Rando" = sorteado pela seed ao gerar.
    Acessibilidade Vanilla e Head Butt como item ainda não existem na ROM: ficam "(em breve)" na lista.
Gera a ROM com insanity_rando.build_seed. Controles da guia Simples (Neitan, 26-28/09):
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
import tkinter.filedialog as filedialog
import tkinter.font as tkfont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import insanity_rando as R  # noqa: E402

VERSION = '0.3.1'
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
            1: 'Itens fortes nas esferas 1 a 3, mais HP no começo. No início do jogo, no máximo 3 crests/Armor. A '
               "lógica aceita a Armor no lugar da Water Crest em alguns checks debaixo d'água.",
            2: 'Itens fortes nas esferas 2 e 3, mais HP no começo. No início do jogo, no máximo 2 crests/Armor. A '
               "lógica aceita a Armor no lugar da Water Crest em alguns checks debaixo d'água.",
            3: 'Moderada: no mínimo 5 esferas, e nenhum item forte nas 2 primeiras. No início do jogo, no máximo 2 '
               "crests/Armor e 5 HP. Debaixo d'água, a lógica também aceita Time Crest, ou Armor com 10+ HP, no lugar "
               'da Water Crest.',
            4: 'Itens fortes só a partir da esfera 4, 5 HPs a menos no jogo. No início do jogo, no máximo 1 '
               "crest/Armor e 2 HP. Debaixo d'água, a lógica também aceita Time Crest + Armor + 15 HP no trecho mais "
               'longo.',
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
        'info': '{m}\n\nDificuldade {v}: {d}\n\nObjetivo: {g}\n{a}: {s}\n{k}: {ks}',
        'skip': 'Skip Somulo',
        'skip_desc': 'Pula a luta do Somulo na abertura (que é praticamente uma cutscene): o jogo começa na área 1, '
                     'com o Somulo já vencido, e o item que ele soltaria aparece em cima do Firebrand.',
        'generate': 'Gerar', 'busy': 'Gerando...', 'about': 'Sobre', 'about_tip': 'Créditos e versão do gerador',
        'rom_bad': "Essa não é a ROM original de Demon's Crest (USA).",
        'rom_none_ok': "Nenhuma ROM da pasta {d} é a original de Demon's Crest (USA).",
        'rom_missing': "Coloque a ROM original de Demon's Crest (USA) na pasta {d}.",
        'no_fill': '"{n}" não fechou a lógica; tente outro nome.',
        'tab_simple': 'Simples', 'tab_adv': 'Avançado',
        'success': 'Sucesso!', 'added': '{b} foi adicionada à pasta {d}.', 'error_title': 'Erro',
        'warn_title': 'Atenção', 'ok': 'OK', 'yes': 'Sim', 'no': 'Não',
        'locked_removal': '(com remoção de itens)', 'locked_crests': '(precisa das Crests na pool)',
        'go_no_crests': 'Os objetivos "All Bosses" e "All 4 Main Crests" precisam das Crests na pool.',
        'no_fill_adv': '"{n}" não fechou a lógica com essas opções. Tente outro nome, ou mude a pool ou o objetivo.',
        'fixed_crests': '(fixa)', 'locked_anti': '(obrigatória com remoção de 4)',
        'go_removal': 'O objetivo "All 4 Main Crests" não combina com a remoção de itens.',
        'load': 'Carregar', 'load_tip': 'Carregar um preset (.json)', 'load_title': 'Carregar preset',
        'preset_bad': 'Não deu pra ler o preset:\n{e}', 'summary': 'Resumo',
        'adv_names': {'preset': 'Preset', 'diff': 'Dificuldade', 'access': 'Acessibilidade', 'pool': 'Pool de Itens',
                      'density': 'Densidade', 'removal': 'Remoção de itens', 'hp': 'HP disponível',
                      'goal': 'Objetivo', 'starter': 'Starter Crest', 'head': 'Randomizar Head Butt',
                      'somulo': 'Skip Somulo', 'level': 'Nível da lógica', 'anti': 'Anti-Softlock'},
        'adv_values': {'custom': 'Custom', 'rando': 'Rando', 'all': 'All Stages', 'vanilla': 'Vanilla',
                       'none': 'Nenhuma', 'sparse': 'Sparse', 'medium': 'Medium', 'full': 'Full', 'earth': 'Earth',
                       'buster': 'Buster', 'claw': 'Claw', 'no': 'Não', 'yes': 'Sim'},
        'pool_names': {'crests': 'Crests', 'vellum': 'Vellum', 'potion': 'Potion', 'talisman': 'Talismã',
                       'hp': 'HP', 'refill': 'Refil HP', 'coins': 'Moedas 20G', 'insanity': 'Insanity',
                       'rando': 'Rando'},
        'adv_desc': {
            'preset': 'Carrega as opções desta guia de um arquivo .json. Custom = as opções marcadas agora.',
            'diff': 'De 1 a 5: marca as opções abaixo como na dificuldade da guia Simples, menos o Nível da lógica, '
                    'que é separado. Mexer em qualquer outra opção abaixo troca para Custom.',
            'level': 'Até onde a lógica pode exigir truques (o piso de cada caminho da lógica). 1 = só o básico; '
                     "cada nível acima libera mais caminhos, como correr debaixo d'água sem a Water Crest. Independe da "
                     'Dificuldade (ex.: Dificuldade 1 com Nível 5).',
            'anti': 'Sim: patches de mapa contra softlock (área 27; e, sem Air Crest e sem Tornado, caminho pela Claw '
                    'nas áreas 29 e 38). Recomendado com remoção de itens.',
            'access': 'All Stages: libera as fases 5 e 6 desde o início.\nVanilla: o jogo começa só com as 4 fases '
                      'iniciais.\nRando: o gerador escolhe.',
            'pool': 'Quais itens entram no sorteio; o que ficar desmarcado continua no check original.\nRando: ao '
                    'gerar, o gerador escolhe de 1 a 7 categorias.\nInsanity: potes, estátuas e quebráveis que hoje '
                    'não têm item (em breve).\nCrests fixas na pool com crest inicial, remoção de itens ou objetivo '
                    'All Bosses / All 4 Main Crests.',
            'density': 'Quanto MENOR a densidade, mais fácil e rápida é a seed. Quanto MAIOR a densidade, mais '
                       'difícil e LENTA é a seed. (Decide onde caem os itens fortes e o HP; os truques ficam no Nível '
                       'da lógica.)',
            'removal': 'Quantos itens major saem do jogo, entre Air Crest, Time Crest, Tornado e Demon Fire (viram 20G '
                       'ou Refil HP).\nRando: o gerador escolhe 2, 3 ou 4.',
            'hp': 'Sparse: de 6 a 10 HP no jogo todo.\nMedium: de 11 a 15 HP.\nFull: todos os 16 HP.\nRando: o '
                  'gerador escolhe. Os HP que saem viram 20G ou Refil HP.',
            'goal': 'O que libera o castelo do Phalanx.\nRando: o gerador escolhe ao gerar.',
            'starter': 'Vanilla: começa com o tiro Fire, como no jogo original.\nEarth, Buster ou Claw: começa com '
                       'essa crest; o tiro Fire vira o item Fire Crest, que entra na pool.\nRando: o gerador escolhe.',
            'head': 'Não: cabeçada desde o começo, como no jogo original.\nSim: a cabeçada vira item da pool.\nRando: '
                    'o gerador decide se randomiza ou não.',
            'somulo': 'Sim: pula a luta do Somulo na abertura; o jogo começa na área 1, com o Somulo já vencido e o '
                      'item dele em cima do Firebrand.\nNão: começa no Coliseu, como no jogo original.'},
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
            1: 'Strong items in spheres 1 to 3, more HP at the start. Early game: at most 3 crests/Armor. The logic '
               'accepts the Armor instead of the Water Crest for some underwater checks.',
            2: 'Strong items in spheres 2 and 3, more HP at the start. Early game: at most 2 crests/Armor. The logic '
               'accepts the Armor instead of the Water Crest for some underwater checks.',
            3: 'Moderate: at least 5 spheres, and no strong items in the first 2. Early game: at most 2 crests/Armor '
               'and 5 HP. Underwater, the logic also accepts the Time Crest, or the Armor with 10+ HP, instead of the '
               'Water Crest.',
            4: 'Strong items only from sphere 4 on, 5 fewer HP in the game. Early game: at most 1 crest/Armor and '
               '2 HP. Underwater, the logic also accepts Time Crest + Armor + 15 HP for the longest stretch.',
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
        'info': '{m}\n\nDifficulty {v}: {d}\n\nGoal: {g}\n{a}: {s}\n{k}: {ks}',
        'skip': 'Skip Somulo',
        'skip_desc': 'Skips the opening Somulo fight (it is basically a cutscene): the game starts in area 1 with '
                     'Somulo already beaten, and the item he would drop appears on top of Firebrand.',
        'generate': 'Generate', 'busy': 'Generating...', 'about': 'About', 'about_tip': 'Credits and generator version',
        'rom_bad': "This is not the original Demon's Crest (USA) ROM.",
        'rom_none_ok': "No ROM in the {d} folder is the original Demon's Crest (USA).",
        'rom_missing': "Put the original Demon's Crest (USA) ROM in the {d} folder.",
        'no_fill': '"{n}" did not pass the logic; try another name.',
        'tab_simple': 'Simple', 'tab_adv': 'Advanced',
        'success': 'Success!', 'added': '{b} has been added to the {d} folder.', 'error_title': 'Error',
        'warn_title': 'Warning', 'ok': 'OK', 'yes': 'Yes', 'no': 'No',
        'locked_removal': '(with item removal)', 'locked_crests': '(needs Crests in the pool)',
        'go_no_crests': 'The "All Bosses" and "All 4 Main Crests" goals need Crests in the pool.',
        'no_fill_adv': '"{n}" did not pass the logic with these options. Try another name, or change the pool or goal.',
        'fixed_crests': '(locked)', 'locked_anti': '(required with removal of 4)',
        'go_removal': 'The "All 4 Main Crests" goal does not work with item removal.',
        'load': 'Load', 'load_tip': 'Load a preset (.json)', 'load_title': 'Load preset',
        'preset_bad': "Couldn't read the preset:\n{e}", 'summary': 'Summary',
        'adv_names': {'preset': 'Preset', 'diff': 'Difficulty', 'access': 'Accessibility', 'pool': 'Item Pool',
                      'density': 'Density', 'removal': 'Item removal', 'hp': 'Available HP', 'goal': 'Goal',
                      'starter': 'Starter Crest', 'head': 'Randomize Head Butt', 'somulo': 'Skip Somulo',
                      'level': 'Logic level', 'anti': 'Anti-Softlock'},
        'adv_values': {'custom': 'Custom', 'rando': 'Rando', 'all': 'All Stages', 'vanilla': 'Vanilla',
                       'none': 'None', 'sparse': 'Sparse', 'medium': 'Medium', 'full': 'Full', 'earth': 'Earth',
                       'buster': 'Buster', 'claw': 'Claw', 'no': 'No', 'yes': 'Yes'},
        'pool_names': {'crests': 'Crests', 'vellum': 'Vellum', 'potion': 'Potion', 'talisman': 'Talisman',
                       'hp': 'HP', 'refill': 'HP Refill', 'coins': '20G Coins', 'insanity': 'Insanity',
                       'rando': 'Rando'},
        'adv_desc': {
            'preset': 'Loads the options of this tab from a .json file. Custom = the options selected now.',
            'diff': '1 to 5: sets the options below like the Simple tab difficulty, except Logic level, which is '
                    'separate. Changing any other option below switches to Custom.',
            'level': 'How far the logic may require tricks (the floor of each logic path). 1 = basics only; each '
                     'level above opens more paths, like running underwater without the Water Crest. Independent of '
                     'Difficulty (e.g. Difficulty 1 with Level 5).',
            'anti': 'Yes: map patches against softlocks (area 27; and, without Air Crest and Tornado, a Claw path in '
                    'areas 29 and 38). Recommended with item removal.',
            'access': 'All Stages: stages 5 and 6 are open from the start.\nVanilla: the game starts with only the '
                      'first 4 stages.\nRando: the generator picks.',
            'pool': 'Which items are shuffled; anything unchecked stays in its original check.\nRando: when '
                    'generating, the generator picks 1 to 7 categories.\nInsanity: pots, statues and breakables '
                    'that have no item today (coming soon).\nCrests are locked in the pool with a starting crest, '
                    'item removal or the All Bosses / All 4 Main Crests goal.',
            'density': 'The LOWER the density, the easier and faster the seed. The HIGHER the density, the harder '
                       'and SLOWER the seed. (It decides where strong items and HP land; tricks are in Logic level.)',
            'removal': 'How many major items leave the game, among Air Crest, Time Crest, Tornado and Demon Fire '
                       '(they become 20G or HP Refill).\nRando: the generator picks 2, 3 or 4.',
            'hp': 'Sparse: 6 to 10 HP in the whole game.\nMedium: 11 to 15 HP.\nFull: all 16 HP.\nRando: the '
                  'generator picks. Removed HP become 20G or HP Refill.',
            'goal': "What opens Phalanx's castle.\nRando: the generator picks when generating.",
            'starter': 'Vanilla: starts with the Fire shot, like the original game.\nEarth, Buster or Claw: starts '
                       'with that crest; the Fire shot becomes the Fire Crest item, which goes into the pool.\nRando: '
                       'the generator picks.',
            'head': 'No: head butt from the start, like the original game.\nYes: the head butt becomes a pool '
                    'item.\nRando: the generator decides whether to randomize it.',
            'somulo': 'Yes: skips the opening Somulo fight; the game starts in area 1 with Somulo already beaten and '
                      'his item on top of Firebrand.\nNo: starts in the Colosseum, like the original game.'},
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


# Guia Avançado (Neitan, 30/09; gera desde 02/10). "Rando" = sorteado pela seed ao gerar (adv_resolve: o mesmo nome dá
# o mesmo resultado). As opções ficam no dcor_config.json ('adv') e um preset .json traz as mesmas chaves de
# ADV_DEFAULT (pode vir solto ou dentro de {"name": ..., "advanced": {...}}).
ADV_FIELDS = ('preset', 'diff', 'level', 'access', 'pool', 'density', 'removal', 'hp', 'goal', 'starter', 'head',
              'somulo', 'anti')
ADV_CHOICES = {'diff': ('1', '2', '3', '4', '5', 'custom'), 'level': ('1', '2', '3', '4', '5'),
               'access': ('all', 'vanilla', 'rando'),
               'removal': ('none', '2', '3', '4', 'rando'), 'hp': ('sparse', 'medium', 'full', 'rando'),
               'goal': tuple(GO_KEYS) + ('rando',), 'starter': ('vanilla', 'earth', 'buster', 'claw', 'rando'),
               'head': ('no', 'yes', 'rando'), 'somulo': ('no', 'yes'), 'anti': ('no', 'yes')}
# ainda sem ROM (Neitan, 02/10): na lista, travados "(em breve)". Hoje o mapa já abre as 6 fases (All Stages).
ADV_SOON = {'access': {'vanilla', 'rando'}, 'head': {'yes', 'rando'}}
POOL_KEYS = ('crests', 'vellum', 'potion', 'talisman', 'hp', 'refill', 'coins', 'insanity')
POOL_SOON = {'insanity'}                         # locais novos do modo Insano: ainda não existem
POOL_CLASSIC_EXTRA = [k for k in POOL_KEYS if k not in POOL_SOON]
ADV_DEFAULT = {'preset': 'custom', 'diff': '3', 'level': '3', 'access': 'all', 'pool': POOL_CLASSIC_EXTRA,
               'pool_rando': False, 'density': 50, 'removal': 'none', 'hp': 'full', 'goal': 'vellum',
               'starter': 'vanilla', 'head': 'no', 'somulo': 'no', 'anti': 'no'}
# Dificuldade 1-5 do Avançado = a da guia Simples no modo Clássico Extra, menos o Nível da lógica, que é separado
# (Neitan, 03/10: dá pra Dificuldade 1 com Nível 5) (o objetivo fica como está; a 5 troca o
# "4 crests" por 5 Vellums e liga o Anti-Softlock). Densidade: a ordem das dificuldades. HP: a 4 tira 5 dos 16
# (sobram 11 = Medium).
ADV_DIFF = {d: {'access': 'all', 'pool': POOL_CLASSIC_EXTRA, 'pool_rando': False, 'density': dens,
                'removal': rem, 'hp': hp, 'starter': 'vanilla', 'head': 'no', **({'anti': 'yes'} if d == 5 else {})}
            for d, dens, rem, hp in ((1, 0, 'none', 'full'), (2, 25, 'none', 'full'), (3, 50, 'none', 'full'),
                                     (4, 75, 'none', 'medium'), (5, 100, 'rando', 'full'))}
HP_TOTAL = 16
ADV_MIN_SPHERES = 4        # Neitan, 02/10: pool pequena = estrutura do jogo original (4 esferas); menos nunca
ADV_HP = {'sparse': (6, 10), 'medium': (11, 15), 'full': (16, 16)}        # HP que ficam no jogo (Neitan, 02/10)
ADV_REMOVAL = {'none': (), '2': (2, 2), '3': (3, 3), '4': (4, 4), 'rando': (2, 4)}
ADV_START = {'vanilla': False, 'earth': 'Earth Crest', 'buster': 'Buster', 'claw': 'Claw', 'rando': True}


def density_bucket(v):
    """Densidade 0-100 -> 1-5, a "dificuldade" que decide onde caem itens fortes e HP: 0-19 = 1 ... 80-100 = 5."""
    return min(5, v // 20 + 1)


GO_NEEDS_CRESTS = ('crests', 'bosses')   # com as crests no lugar original o castelo abriria na 3ª esfera (02/10)


def adv_needs_crests(adv):
    """Crests presas na pool: crest inicial, remoção de itens ou objetivo All Bosses / 4 crests."""
    return adv['starter'] != 'vanilla' or adv['removal'] != 'none' or adv['goal'] in GO_NEEDS_CRESTS


def adv_resolve(adv, seed, attempt=0):
    """Opções do Avançado -> (Logic, resolvido). Os "Rando" são sorteados pela seed (mesmo nome, mesmo resultado);
    attempt > 0 = novo sorteio dos Rando (write_seed_adv, quando a pool sorteada não fecha)."""
    rng = random.Random(seed ^ 0xADF00D ^ attempt * 0x9E3779B1)
    keys = list(adv['pool'])
    if adv['pool_rando']:
        keys = rng.sample(POOL_CLASSIC_EXTRA, rng.randint(1, len(POOL_CLASSIC_EXTRA)))
    if adv_needs_crests(adv) and 'crests' not in keys:
        keys.append('crests')
    keys = [k for k in POOL_KEYS if k in keys]
    hp = adv['hp'] if adv['hp'] != 'rando' else rng.choice(('sparse', 'medium', 'full'))
    left = rng.randint(*ADV_HP[hp])
    span = ADV_REMOVAL[adv['removal']]
    goal = adv['goal']
    if goal == 'rando':                            # "4 crests" sem remoção; All Bosses / 4 crests só com as Crests
        goal = rng.choice([g for g in GO_KEYS if not (span and g == 'crests')
                           and (g not in GO_NEEDS_CRESTS or 'crests' in keys)])
    if span and goal == 'crests':
        raise ValueError(tr('go_removal'))
    if goal in GO_NEEDS_CRESTS and 'crests' not in keys:
        raise ValueError(tr('go_no_crests'))
    anti = adv['anti'] == 'yes' or adv['removal'] == '4'          # remoção de 4: Air e Tornado fora (Claw)
    logic = R.Logic(density_bucket(adv['density']), R.pool_mode(keys), goal, anti,
                    ADV_START[adv['starter']], adv['somulo'] == 'yes', level=int(adv['level']),
                    hp_removed=HP_TOTAL - left, remove_span=span)
    logic.soft_cap = True
    logic.min_spheres = ADV_MIN_SPHERES
    return logic, {'pool': keys, 'hp': left, 'goal': goal, 'anti': anti}


def adv_clean(d):
    """Opções do Avançado válidas a partir de um dict qualquer (config ou preset): o que faltar ou vier errado fica
    no padrão."""
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in ADV_DEFAULT.items()}
    if not isinstance(d, dict):
        return out
    for k, keys in ADV_CHOICES.items():
        v = str(d.get(k, out[k])).lower()
        if v in keys and v not in ADV_SOON.get(k, ()):
            out[k] = v
    pool = d.get('pool')
    if isinstance(pool, list):
        pool = [k for k in POOL_KEYS if k in pool and k not in POOL_SOON]
        if pool:
            out['pool'] = pool
    out['pool_rando'] = bool(d.get('pool_rando', out['pool_rando']))
    try:
        out['density'] = max(0, min(100, int(d.get('density', out['density']))))
    except (TypeError, ValueError):
        pass
    if isinstance(d.get('preset'), str):
        out['preset'] = d['preset']
    return out


def adv_value(field, k):
    if field == 'goal' and k in GO_KEYS:
        return go_name(k)
    return tr('adv_values').get(k, k)


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

BASE_W, BASE_H = 720, 980          # tamanho inicial da janela (980: Skip Somulo, 01/10)
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
    """Bandeiras do idioma lado a lado no cabeçalho (Brasil, EUA; 30/09, modelo do Neitan com guias; antes uma em
    cima da outra). Desenhadas no Canvas (sem imagem), crescem com a letra. A escolhida fica num fundo aceso; on_pick
    recebe o idioma."""
    ORDER = ('pt', 'en')

    def __init__(self, master, lang, on_pick, bg=CARD):
        super().__init__(master, bg=bg, highlightthickness=0, cursor='hand2')
        self.lang, self.on_pick = lang, on_pick
        self.bind('<Button-1>', self.click)
        self.rescale()

    def rescale(self):
        self.fh = round(F['base'].metrics('linespace') * 1.25)
        self.fw, self.p, self.gap = round(self.fh * 1.75), 4, 6
        self.configure(width=2 * (self.fw + 2 * self.p) + self.gap, height=self.fh + 2 * self.p)
        self.draw()

    def select(self, lang):
        self.lang = lang
        self.draw()

    def slot_x(self, i):
        return i * (self.fw + 2 * self.p + self.gap)

    def click(self, e):
        i = 0 if e.x < self.slot_x(1) - self.gap / 2 else 1
        if self.ORDER[i] != self.lang:
            self.on_pick(self.ORDER[i])

    def draw(self):
        self.delete('all')
        p = self.p
        for i, lang in enumerate(self.ORDER):
            x = self.slot_x(i)
            if lang == self.lang:
                round_rect(self, x + 1, 1, x + self.fw + 2 * p - 2, self.fh + 2 * p - 2, 6, fill=SEL, outline=ACCENT_HI)
            (self.brazil if lang == 'pt' else self.usa)(x + p, p, self.fw, self.fh)
            self.create_rectangle(x + p, p, x + p + self.fw, p + self.fh, outline='#05070f')

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


class Dropdown(tk.Canvas):
    """Lista suspensa escura (a do Tk/ttk é clara): campo arredondado com o valor e uma seta; o clique abre uma lista
    logo abaixo (Toplevel sem borda). keys = valores; name(k) = texto mostrado (refeito a cada desenho, então segue
    o idioma). on_change recebe o valor novo."""

    def __init__(self, master, keys, name, value, on_change, bg=CARD, locked=None):
        super().__init__(master, bg=bg, highlightthickness=0, cursor='hand2', width=1)
        self.keys, self.name, self.value, self.on_change = list(keys), name, value, on_change
        self.locked = locked or (lambda: {})       # {valor: nota}: aparece cinza com a nota e não dá pra escolher
        self.pop, self.over = None, False
        self.bind('<Configure>', lambda _: self.draw())
        self.bind('<Button-1>', self.toggle)
        self.bind('<Enter>', lambda _: self.set_over(True), add='+')
        self.bind('<Leave>', lambda _: self.set_over(False), add='+')
        self.rescale()

    def rescale(self):
        self.configure(height=F['base'].metrics('linespace') + 14)
        self.draw()

    def set_over(self, on):
        self.over = on
        self.draw()

    def set(self, value):
        self.value = value
        self.draw()

    def set_keys(self, keys):
        self.keys = list(keys)
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = max(self.winfo_width(), 60), max(self.winfo_height(), 20)
        round_rect(self, 1, 1, w - 2, h - 2, 7, fill=BTN if self.over else FIELD,
                   outline=FIELD_FOCUS if self.pop else FIELD_LINE)
        self.create_text(12, h // 2, text=self.name(self.value), anchor='w', fill=TEXT, font=F['base'])
        a, cx, cy = max(4, h // 7), w - 16, h // 2
        self.create_line(cx - a, cy - a // 2, cx, cy + a // 2, cx + a, cy - a // 2, fill=MUTED, width=2)

    def toggle(self, _=None):
        if self.pop:
            return self.close()
        top = self.pop = tk.Toplevel(self, bg=FIELD_LINE)
        top.withdraw()                          # posiciona escondida: janela sem borda já mostrada ignora a posição
        top.wm_overrideredirect(True)
        box = tk.Frame(top, bg=FIELD)
        box.pack(fill='both', expand=True, padx=1, pady=1)
        locked = self.locked()
        for k in self.keys:
            bg = SEL if k == self.value else FIELD
            if k in locked:
                tk.Label(box, text=f'{self.name(k)}  {locked[k]}', anchor='w', bg=bg, fg=DIM, font=F['base'],
                         padx=12, pady=5).pack(fill='x')
                continue
            row = tk.Label(box, text=self.name(k), anchor='w', bg=bg, fg=TEXT, font=F['base'], padx=12, pady=5,
                           cursor='hand2')
            row.pack(fill='x')
            row.bind('<Enter>', lambda _, r=row: r.configure(bg=BTN_HI))
            row.bind('<Leave>', lambda _, r=row, c=bg: r.configure(bg=c))
            row.bind('<ButtonRelease-1>', lambda _, k=k: self.pick(k))
        top.update_idletasks()
        w = max(self.winfo_width(), top.winfo_reqwidth())
        x, y = self.winfo_rootx(), self.winfo_rooty() + self.winfo_height() + 2
        if y + top.winfo_reqheight() > self.winfo_screenheight() - 40:          # sem espaço embaixo: abre pra cima
            y = self.winfo_rooty() - top.winfo_reqheight() - 2
        top.geometry(f'{w}x{top.winfo_reqheight()}+{x}+{y}')
        top.deiconify()
        top.bind('<ButtonPress>', self.outside)
        top.bind('<Escape>', lambda _: self.close())
        top.focus_set()
        top.grab_set()                          # clique fora da lista chega aqui (outside) e fecha
        self.draw()

    def outside(self, e):
        p = self.pop
        if not (p.winfo_rootx() <= e.x_root < p.winfo_rootx() + p.winfo_width()
                and p.winfo_rooty() <= e.y_root < p.winfo_rooty() + p.winfo_height()):
            self.close()
            return 'break'

    def pick(self, k):
        self.close()
        if k != self.value:
            self.value = k
            self.draw()
            self.on_change(k)

    def close(self):
        if self.pop:
            self.pop.grab_release()
            self.pop.destroy()
            self.pop = None
            self.draw()


class Slider(tk.Canvas):
    """Controle deslizante de lo a hi no estilo da barra de dificuldade: caixa com o número + trilho com a parte
    cheia em ciano e uma bolinha; clique ou arraste. on_change recebe o valor."""

    def __init__(self, master, value, on_change, lo=0, hi=100):
        super().__init__(master, bg=CARD, highlightthickness=0, cursor='hand2', width=1)
        self.value, self.on_change, self.lo, self.hi = value, on_change, lo, hi
        self.bind('<Button-1>', self.click)
        self.bind('<B1-Motion>', self.click)
        self.bind('<Configure>', lambda _: self.draw())
        self.rescale()

    def rescale(self):
        self.configure(height=F['num'].metrics('linespace') + 12)
        self.draw()

    def geom(self):
        w, h = max(self.winfo_width(), 120), max(self.winfo_height(), 20)
        box = F['num'].measure('100') + 20
        return w, h, box, box + 16, w - 16

    def set(self, v):
        self.value = v
        self.draw()

    def click(self, e):
        w, h, box, x0, x1 = self.geom()
        v = round(self.lo + (self.hi - self.lo) * min(1, max(0, (e.x - x0) / max(1, x1 - x0))))
        if v != self.value:
            self.value = v
            self.draw()
            self.on_change(v)

    def draw(self):
        self.delete('all')
        w, h, box, x0, x1 = self.geom()
        round_rect(self, 1, 1, w - 2, h - 2, 8, fill=FIELD, outline=FIELD_LINE)
        round_rect(self, 1, 1, box, h - 2, 8, fill=SEL, outline=ACCENT)
        self.create_text(box // 2, h // 2, text=str(self.value), fill=TEXT, font=F['num'])
        x = x0 + (x1 - x0) * (self.value - self.lo) / (self.hi - self.lo)
        cy, t = h // 2, max(2, h // 12)
        self.create_rectangle(x0, cy - t, x1, cy + t, width=0, fill='#1e2a4d')
        self.create_rectangle(x0, cy - t, x, cy + t, width=0, fill=CYAN)
        d = max(10, round(h * 0.42)) | 1
        self.create_image(x, cy, image=aa_radio(d, TEXT, FIELD, None, d / 2))


class TabBar(tk.Canvas):
    """Guias (Simples / Avançado): a escolhida acesa com um traço ciano embaixo; uma linha azul passa por baixo de
    todas. name(k) = texto (segue o idioma); on_pick recebe a guia."""

    def __init__(self, master, keys, name, value, on_pick):
        super().__init__(master, bg=CARD, highlightthickness=0, cursor='hand2', width=1)
        self.keys, self.name, self.value, self.on_pick = list(keys), name, value, on_pick
        self.over = None
        self.bind('<Configure>', lambda _: self.draw())
        self.bind('<Button-1>', lambda e: self.hit(e.x) and self.pick(self.hit(e.x)))
        self.bind('<Motion>', lambda e: self.hover(self.hit(e.x)))
        self.bind('<Leave>', lambda _: self.hover(None))
        self.rescale()

    def rescale(self):
        self.configure(height=F['label'].metrics('linespace') + 20)
        self.draw()

    def spans(self):
        x, out = 10, []
        for k in self.keys:
            tw = max(F['label'].measure(self.name(k)) + 60, round(F['label'].metrics('linespace') * 6))
            out.append((k, x, x + tw))
            x += tw + 4
        return out

    def hit(self, x):
        return next((k for k, a, b in self.spans() if a <= x <= b), None)

    def hover(self, k):
        if k != self.over:
            self.over = k
            self.draw()

    def pick(self, k):
        if k != self.value:
            self.value = k
            self.draw()
            self.on_pick(k)

    def draw(self):
        self.delete('all')
        w, h = max(self.winfo_width(), 60), max(self.winfo_height(), 20)
        for k, a, b in self.spans():
            on = k == self.value
            fill = SEL if on else (BTN_HI if k == self.over else BTN)
            round_rect(self, a, 1, b, h + 12, 8, fill=fill, outline=ACCENT_HI if on else CARD_LINE)
            if on:
                self.create_rectangle(a + 1, h - 5, b - 1, h - 2, width=0, fill=CYAN)
            self.create_text((a + b) // 2, (h - 4) // 2, text=self.name(k), fill=TEXT if on else MUTED,
                             font=F['label'])
        self.create_rectangle(0, h - 2, w, h, width=0, fill=ACCENT)


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


def write_seed(text, van, mode, diff, go='vellum', anti=False, home=None, skip=False):
    """Gera e grava Seed/DemonRando - Nome.sfc e Spoiler/DemonRando - Nome.txt (mode = índice em MODE_KEYS, go = chave
    de GO_KEYS, anti = Anti-Softlock, skip = Skip Somulo). Devolve o nome do arquivo. O spoiler sai sempre em inglês (29/09)."""
    name, seed = seed_from_name(text)
    head = (f"DCOR {VERSION} - {tr('modes', 'en')[mode]}, difficulty {diff}, Goal: {go_name(go, 'en')}, "
            f"{tr('anti', 'en')}: {'yes' if anti else 'no'}, Skip Somulo: {'yes' if skip else 'no'} "
            f"(internal seed {seed})")
    return save_seed(name, seed, R.build_seed(seed, van, R.Logic(diff, MODE_KEYS[mode], go, anti, skipsomulo=skip)),
                     head, home)


def write_seed_adv(text, van, adv, home=None):
    """Guia Avançado: como write_seed, com as opções de adv (adv_resolve). O cabeçalho do spoiler diz o que saiu."""
    name, seed = seed_from_name(text)
    for attempt in range(20 if adv['pool_rando'] else 1):   # Pool Rando: pool que não fecha -> sorteia outra
        logic, got = adv_resolve(adv, seed, attempt)
        res = R.build_seed(seed, van, logic)
        if res is not None:
            break
    pools = ', '.join(tr('pool_names', 'en')[k] for k in got['pool'])
    rem = {'none': 'none', 'rando': '2-4'}.get(adv['removal'], adv['removal'])
    head = (f"DCOR {VERSION} - Advanced: logic level {adv['level']}, density {adv['density']}, item pool: {pools}, "
            f"available HP: {got['hp']}/{HP_TOTAL}, item removal: {rem}, Goal: {go_name(got['goal'], 'en')}, "
            f"Anti-Softlock: {'yes' if got['anti'] else 'no'}, Skip Somulo: {adv['somulo']} (internal seed {seed})")
    if res is None:
        raise RuntimeError(tr('no_fill_adv', n=name))
    return save_seed(name, seed, res, head, home)


def save_seed(name, seed, res, head, home=None):
    """Grava o resultado de build_seed: Seed/DemonRando - Nome.sfc e Spoiler/DemonRando - Nome.txt (em inglês)."""
    home = home or HOME
    if res is None:
        raise RuntimeError(tr('no_fill', n=name))
    data, lines, _ = res
    lines[0] = f'{PREFIX} - {name}' + lines[0][lines[0].index(':'):]
    base = f'{PREFIX} - {name}'
    make_dirs(home)
    open(os.path.join(home, SEED_DIR, base + '.sfc'), 'wb').write(data)
    with open(os.path.join(home, SPOILER_DIR, base + '.txt'), 'w', encoding='utf-8') as f:
        f.write(head + '\n' + '\n'.join(lines) + '\n')
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
        self.about_win = None
        self.busy = False
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

        # --- cartão da lógica (30/09, modelo do Neitan): título | bandeiras + Sobre; guias; opções | descrição
        logic = self.logic_card = Card(body)
        logic.grid(row=0, column=0, sticky='nsew', padx=pad, pady=(pad, 8))
        body.rowconfigure(0, weight=1)
        L = self.logic_inner = logic.inner
        L.columnconfigure(0, weight=1, uniform='l')    # descrição com metade do cartão (3:2 no Avançado, set_tab)
        L.columnconfigure(1, weight=1, uniform='l')
        L.rowconfigure(2, weight=1)
        head = tk.Frame(L, bg=CARD)
        head.grid(row=0, column=0, columnspan=2, sticky='ew')
        head.columnconfigure(0, weight=1)
        self.text(label(head, '', F['title']), 'logic').grid(row=0, column=0, sticky='w')
        self.flags = FlagPicker(head, LANG, self.set_lang)
        self.flags.grid(row=0, column=1, padx=(0, 10))
        Tip(self.flags, lambda: f"{tr('lang_tip', 'pt')} / {tr('lang_tip', 'en')}")
        self.scalables.append(self.flags)
        self.about_btn = RButton(head, tr('about'), self.about, F['base'])
        self.about_btn.grid(row=0, column=2)
        Tip(self.about_btn, lambda: tr('about_tip'))
        self.scalables.append(self.about_btn)
        self.tab = self.cfg.get('tab') if self.cfg.get('tab') in ('simple', 'adv') else 'simple'
        self.tabs = TabBar(L, ('simple', 'adv'), lambda k: tr('tab_' + k), self.tab, self.set_tab)
        self.tabs.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(8, 14))
        self.scalables.append(self.tabs)
        pages = tk.Frame(L, bg=CARD)
        pages.grid(row=2, column=0, sticky='nsew', padx=(0, 12))
        pages.columnconfigure(0, weight=1)
        info = tk.Frame(L, bg='#0c1430', highlightthickness=1, highlightbackground=CARD_LINE)
        info.grid(row=2, column=1, sticky='nsew')
        # width=1: o texto que quebra linha não pede largura (senão a quebra muda o layout, que muda a quebra... e a
        # janela travava num laço ao redimensionar, 28/09)
        self.info = tk.Label(info, text='', justify='left', anchor='nw', bg='#0c1430', fg='#d6ddf7', font=F['desc'],
                             padx=14, pady=12, width=1)
        self.info.pack(fill='both', expand=True)
        self.info.bind('<Configure>', self.info_wrap)
        self.page = {'simple': self.build_simple(pages), 'adv': self.build_adv(pages)}

        # --- seed | Gerar
        bottom = tk.Frame(body, bg=BG)
        bottom.grid(row=1, column=0, sticky='ew', padx=pad, pady=(8, pad))
        bottom.columnconfigure(0, weight=1)
        sc = Card(bottom)
        sc.grid(row=0, column=0, sticky='nsew')
        t = sc.inner
        t.columnconfigure(0, weight=1)
        self.text(label(t, '', F['label']), 'seed').grid(row=0, column=0, columnspan=2, sticky='w')
        self.seed = Field(t, tr('seed_ph'))
        self.seed.grid(row=1, column=0, sticky='nsew', pady=(6, 0), padx=(0, 10))
        Tip(self.seed.e, lambda: tr('seed_tip'))
        self.roll = RButton(t, tr('roll'), self.roll_seed, F['base'])
        self.roll.grid(row=1, column=1, pady=(6, 0))
        Tip(self.roll, lambda: tr('roll_tip'))
        self.scalables.append(self.roll)
        self.go = RButton(bottom, tr('generate'), self.generate, F['big'], bg=BG, fill=ACCENT, hover=ACCENT_HI,
                          line=ACCENT_HI, padx=48, pady=14, r=10)
        self.go.grid(row=0, column=1, padx=(12, 0))
        self.scalables.append(self.go)
        self.cards = [logic, sc]

        self.retext()
        self.set_go(self.gomode)
        self.anti_row.select(self.anti)
        self.skip_row.select(self.skip)
        self.set_mode(self.mode)
        self.refresh_adv()
        self.set_tab(self.tab)
        self.apply_scale(1.0)
        root.update_idletasks()
        self.refit()
        dark_title_bar(root)

    # --- guia Simples: o que o gerador usa hoje
    def build_simple(self, master):
        S = tk.Frame(master, bg=CARD)
        S.columnconfigure(0, weight=1)
        self.text(label(S, '', F['label']), 'diff').grid(row=0, column=0, sticky='w')
        self.diff = DiffBar(S, self.cfg.get('diff', DEFAULT_DIFF), self.set_diff)
        self.diff.grid(row=1, column=0, sticky='ew', pady=(6, 10))
        Tip(self.diff, lambda: tr('diff_tip', v=self.diff.value, d=diff_desc(self.diff.value)))
        self.scalables.append(self.diff)
        self.text(label(S, '', F['label']), 'mode').grid(row=2, column=0, sticky='w', pady=(0, 4))
        self.mode = self.cfg.get('mode', DEFAULT_MODE)
        self.rows = []
        for i in range(len(MODE_KEYS)):
            r = OptRow(S, '', i, self.set_mode)
            r.set_enabled(mode_ok(i))
            r.grid(row=3 + i, column=0, sticky='ew', pady=1)
            Tip(r, lambda i=i: self.mode_text(i))
            self.rows.append(r)
            self.scalables.append(r)
        n = 3 + len(MODE_KEYS)
        self.text(label(S, '', F['title']), 'go').grid(row=n, column=0, sticky='w', pady=(14, 4))
        self.gomode = self.cfg.get('go', DEFAULT_GO)
        if self.gomode not in GO_KEYS:
            self.gomode = DEFAULT_GO
        self.go_rows = {}
        for i, k in enumerate(GO_KEYS):
            r = OptRow(S, '', k, self.set_go)
            r.grid(row=n + 1 + i, column=0, sticky='ew', pady=1)
            Tip(r, lambda k=k: tr('go_desc')[k])
            self.go_rows[k] = r
            self.scalables.append(r)
        n += 1 + len(GO_KEYS)
        self.text(label(S, '', F['title']), 'extras').grid(row=n, column=0, sticky='w', pady=(14, 4))
        self.anti = bool(self.cfg.get('antisoftlock', False))
        self.anti_row = OptRow(S, '', 'anti', self.toggle_anti, box=True)
        self.anti_row.grid(row=n + 1, column=0, sticky='ew', pady=1)
        Tip(self.anti_row, lambda: tr('anti_desc'))
        self.scalables.append(self.anti_row)
        self.skip = bool(self.cfg.get('skipsomulo', False))           # Skip Somulo (Asvel/Neitan, 01/10)
        self.skip_row = OptRow(S, '', 'skip', self.toggle_skip, box=True)
        self.skip_row.grid(row=n + 2, column=0, sticky='ew', pady=1)
        Tip(self.skip_row, lambda: tr('skip_desc'))
        self.scalables.append(self.skip_row)
        # extras do handoff de 29/09 (Fire Crest / crest inicial / cabeçada): na janela, mas travados até a ROM ter
        self.soon_rows = []
        for i, k in enumerate(('x_crest', 'x_head')):
            r = OptRow(S, '', k, None, box=True)
            r.set_enabled(False)
            r.grid(row=n + 3 + i, column=0, sticky='ew', pady=1)
            Tip(r, lambda k=k: tr(k + '_desc') + '\n\n' + tr('not_yet'))
            self.soon_rows.append((r, k))
            self.scalables.append(r)
        return S

    # --- guia Avançado (30/09): só interface por enquanto; as opções ficam salvas na config
    def build_adv(self, master):
        A = tk.Frame(master, bg=CARD)
        A.columnconfigure(1, weight=1)
        self.adv = adv_clean(self.cfg.get('adv'))
        self.presets = [p for p in self.cfg.get('presets', []) if isinstance(p, dict) and p.get('name')
                        and p.get('path')]
        self.adv_focus = None
        self.adv_w = {}
        row = 0

        def name_label(key, r, **grid):
            lb = self.text(label(A, '', F['label']), ('adv_names', key))
            lb.grid(row=r, column=0, sticky='w', padx=(0, 12), **grid)
            lb.bind('<Enter>', lambda _: self.adv_hover(key), add='+')
            return lb

        for key in ADV_FIELDS:
            if key == 'pool':
                name_label(key, row, pady=(6, 2), columnspan=2)
                box = tk.Frame(A, bg=CARD)
                box.grid(row=row + 1, column=0, columnspan=2, sticky='ew')
                box.columnconfigure(0, weight=1, uniform='p')
                box.columnconfigure(1, weight=1, uniform='p')
                self.pool_rows = {}
                for i, k in enumerate(POOL_KEYS + ('rando',)):
                    r = OptRow(box, '', k, self.adv_pool, box=True)
                    r.grid(row=i // 2, column=i % 2, sticky='ew', pady=1, padx=(0, 4) if i % 2 == 0 else (4, 0))
                    r.bind('<Enter>', lambda _: self.adv_hover('pool'), add='+')
                    self.pool_rows[k] = r
                    self.scalables.append(r)
                row += 2
                continue
            name_label(key, row, pady=2)
            if key == 'preset':
                f = tk.Frame(A, bg=CARD)
                f.grid(row=row, column=1, sticky='ew', pady=2)
                f.columnconfigure(0, weight=1)
                w = Dropdown(f, self.preset_keys(), self.preset_name, self.adv['preset'], self.adv_pick_preset)
                w.grid(row=0, column=0, sticky='ew')
                self.load_btn = RButton(f, tr('load'), self.load_preset, F['base'], padx=12, pady=6)
                self.load_btn.grid(row=0, column=1, padx=(8, 0))
                Tip(self.load_btn, lambda: tr('load_tip'))
                self.load_btn.bind('<Enter>', lambda _: self.adv_hover('preset'), add='+')
                self.scalables.append(self.load_btn)
            elif key == 'density':
                w = Slider(A, self.adv['density'], lambda v: self.adv_set('density', v))
                w.grid(row=row, column=1, sticky='ew', pady=2)
            else:
                w = Dropdown(A, ADV_CHOICES[key], lambda k, f=key: adv_value(f, k), self.adv[key],
                             (self.adv_pick_diff if key == 'diff' else lambda v, f=key: self.adv_set(f, v)),
                             locked=lambda f=key: self.adv_locked(f))
                w.grid(row=row, column=1, sticky='ew', pady=2)
            w.bind('<Enter>', lambda _, k=key: self.adv_hover(k), add='+')
            self.adv_w[key] = w
            self.scalables.append(w)
            row += 1
        return A

    def preset_keys(self):
        return ['custom'] + [p['name'] for p in self.presets]

    def preset_name(self, k):
        return tr('adv_values')['custom'] if k == 'custom' else k

    def adv_locked(self, field):
        """Valores travados de cada lista: {valor: nota}. Sem ROM ainda (ADV_SOON); objetivo "4 crests" com remoção;
        crest inicial e remoção sem as Crests na pool."""
        out = {k: tr('soon') for k in ADV_SOON.get(field, ())}
        if field == 'goal' and self.adv['removal'] != 'none':
            out['crests'] = tr('locked_removal')
        no_crests = not self.adv['pool_rando'] and 'crests' not in self.adv['pool']
        if field == 'goal' and no_crests:
            out.update({g: tr('locked_crests') for g in GO_NEEDS_CRESTS})
        if field == 'anti' and self.adv['removal'] == '4':      # os 4 fora = Air e Tornado fora: só com a Claw
            out['no'] = tr('locked_anti')
        if no_crests and field in ('starter', 'removal'):
            out.update({k: tr('locked_crests') for k in ADV_CHOICES[field] if k not in ('vanilla', 'none')})
        return out

    def refresh_adv(self):
        """Controles do Avançado = self.adv."""
        self.adv_w['preset'].set_keys(self.preset_keys())
        if self.adv['preset'] not in self.preset_keys():
            self.adv['preset'] = 'custom'
        for key, w in self.adv_w.items():
            w.set(self.adv[key])
        rando = self.adv['pool_rando']
        for k, r in self.pool_rows.items():
            if k == 'rando':
                r.select(rando)
            elif k in POOL_SOON:
                r.set_enabled(False, tr('soon'))
            else:
                r.set_enabled(not rando)
                r.select(not rando and k in self.adv['pool'])
        fixed = not rando and adv_needs_crests(self.adv)
        self.pool_rows['crests'].set_text(tr('pool_names')['crests'], tr('fixed_crests') if fixed else '')
        self.update_info()

    def adv_changed(self, key):
        self.adv_focus = key
        self.refresh_adv()
        self.save()

    def adv_set(self, key, v):
        """Opção mexida à mão: a dificuldade e o preset viram Custom."""
        self.adv[key] = v
        if key == 'level':                                  # separado da Dificuldade: ela não vira Custom
            self.adv['preset'] = 'custom'
            return self.adv_changed(key)
        if key == 'removal' and v != 'none' and self.adv['goal'] == 'crests':   # "4 crests" não vai com remoção
            self.adv['goal'] = DEFAULT_GO
        if key == 'removal' and v == '4':                  # Air e Tornado sempre fora: Anti-Softlock obrigatório
            self.adv['anti'] = 'yes'
        self.adv['diff'] = self.adv['preset'] = 'custom'
        self.adv_changed(key)

    def adv_pick_diff(self, v):
        self.adv['diff'], self.adv['preset'] = v, 'custom'
        if v != 'custom':
            self.adv.update({k: (list(x) if isinstance(x, list) else x) for k, x in ADV_DIFF[int(v)].items()})
            if v == '5' and self.adv['goal'] == 'crests':      # como na guia Simples: "4 crests" não vai com a 5
                self.adv['goal'] = DEFAULT_GO
        self.adv_changed('diff')

    def adv_pool(self, k):
        if k == 'rando':
            self.adv['pool_rando'] = not self.adv['pool_rando']
        else:
            pool = self.adv['pool']
            if k in pool:
                if len(pool) == 1 or (k == 'crests' and adv_needs_crests(self.adv)):   # pelo menos uma categoria;
                    return                                                          # Crests presas (crest inicial)
                pool.remove(k)
            else:
                pool.append(k)
            self.adv['pool'] = [x for x in POOL_KEYS if x in pool]
        if 'crests' not in self.adv['pool'] and not self.adv['pool_rando'] and self.adv['goal'] in GO_NEEDS_CRESTS:
            self.adv['goal'] = DEFAULT_GO                      # All Bosses / 4 crests precisam das Crests na pool
        self.adv['diff'] = self.adv['preset'] = 'custom'
        self.adv_changed('pool')

    def adv_hover(self, key):
        if key != self.adv_focus:
            self.adv_focus = key
            self.update_info()

    def adv_pick_preset(self, name):
        if name == 'custom':
            self.adv['preset'] = 'custom'
            return self.adv_changed('preset')
        p = next(p for p in self.presets if p['name'] == name)
        try:
            self.apply_preset(p['path'], name)
        except (OSError, ValueError) as e:
            self.presets.remove(p)
            self.adv['preset'] = 'custom'
            self.adv_changed('preset')
            self.dialog(tr('error_title'), tr('preset_bad', e=e), accent=ERR)

    def apply_preset(self, path, name=None):
        d = json.load(open(path, encoding='utf-8'))
        if not isinstance(d, dict):
            raise ValueError('JSON sem opções')
        name = name or str(d.get('name') or os.path.splitext(os.path.basename(path))[0])
        self.adv = adv_clean(d.get('advanced', d))
        self.adv['preset'] = name
        self.presets = [p for p in self.presets if p['name'] != name] + [{'name': name, 'path': path}]
        self.adv_changed('preset')

    def load_preset(self):
        path = filedialog.askopenfilename(parent=self.root, title=tr('load_title'), initialdir=HOME,
                                          filetypes=[('Preset DCOR', '*.json')])
        if not path:
            return
        try:
            self.apply_preset(path)
        except (OSError, ValueError) as e:
            self.dialog(tr('error_title'), tr('preset_bad', e=e), accent=ERR)

    def adv_text(self):
        names = tr('adv_names')
        pool = (tr('adv_values')['rando'] if self.adv['pool_rando'] else
                ', '.join(tr('pool_names')[k] for k in self.adv['pool']))
        lines = []
        for key in ADV_FIELDS:
            v = (self.preset_name(self.adv['preset']) if key == 'preset' else pool if key == 'pool' else
                 str(self.adv['density']) if key == 'density' else adv_value(key, self.adv[key]))
            lines.append(f'{names[key]}: {v}')
        out = ''
        if self.adv_focus:
            out = f"{names[self.adv_focus]}\n{tr('adv_desc')[self.adv_focus]}"
            if self.adv_focus == 'goal' and self.adv['goal'] in GO_KEYS:
                out += '\n\n' + tr('go_desc')[self.adv['goal']]
            out += '\n\n'
        return out + tr('summary') + '\n' + '\n'.join(lines)

    def set_tab(self, tab):
        self.tab = tab
        self.tabs.value = tab
        self.tabs.draw()
        self.logic_inner.columnconfigure(0, weight=3 if tab == 'adv' else 1)    # Avançado: rótulo + controle por
        self.logic_inner.columnconfigure(1, weight=2 if tab == 'adv' else 1)    # linha, precisa de mais largura
        for k, p in self.page.items():
            if k == tab:
                p.grid(row=0, column=0, sticky='nsew')
            else:
                p.grid_remove()
        self.update_info()
        self.save()
        self.root.after_idle(self.refit)

    def save(self):
        self.cfg.update(lang=LANG, tab=self.tab, mode=self.mode, diff=self.diff.value, go=self.gomode,
                        antisoftlock=self.anti, skipsomulo=self.skip, adv=self.adv, presets=self.presets)
        save_config(self.cfg)

    # --- idioma: troca na hora, sem reiniciar
    def text(self, widget, key):
        self.texts.append((widget, key))
        return widget

    def mode_text(self, i):
        d = tr('mode_desc')[i]
        return d if mode_ok(i) else d + '\n\n' + tr('not_yet')

    def retext(self):
        for w, k in self.texts:
            w.configure(text=tr(k[0])[k[1]] if isinstance(k, tuple) else tr(k))
        self.seed.set_placeholder(tr('seed_ph'))
        for b, k in ((self.roll, 'roll'), (self.go, 'busy' if self.busy else 'generate'), (self.about_btn, 'about'),
                     (self.load_btn, 'load')):
            b.set_text(tr(k))
        for i, r in enumerate(self.rows):
            r.set_text(tr('modes')[i], '' if mode_ok(i) else tr('soon'))
        for k, r in self.go_rows.items():
            r.set_text(go_name(k))
        self.anti_row.set_text(tr('anti'))
        self.skip_row.set_text(tr('skip'))
        for r, k in self.soon_rows:
            r.set_text(tr(k), tr('soon'))
        for k, r in self.pool_rows.items():
            r.set_text(tr('pool_names')[k], tr('soon') if k in POOL_SOON else '')
        for w in list(self.adv_w.values()) + [self.tabs]:
            w.draw()
        self.set_diff(self.diff.value, first=True)       # nota do "4 crests" e painel de descrição

    def set_lang(self, lang):
        global LANG
        LANG = lang
        self.save()
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

    # --- opções da guia Simples
    def set_diff(self, v, first=False):
        if v == 5:
            self.go_rows['crests'].set_enabled(False, tr('no_d5'))
            if self.gomode == 'crests':
                self.set_go(DEFAULT_GO)
            if not first and not self.anti:            # a dificuldade 5 liga o anti-softlock sozinha
                self.anti = True
                self.anti_row.select(True)
        else:
            self.go_rows['crests'].set_enabled(True, '')
        self.update_info()
        if not first:
            self.save()

    def set_go(self, k):
        self.gomode = k
        for key, r in self.go_rows.items():
            r.select(key == k)
        self.update_info()
        self.save()

    def toggle_anti(self, _k):
        if self.anti and self.diff.value == 5 and not self.dialog(tr('warn_title'), tr('anti_warn'),
                                                                  (('yes', True), ('no', False)), accent=ERR):
            return
        self.anti = not self.anti
        self.anti_row.select(self.anti)
        self.update_info()
        self.save()

    def toggle_skip(self, _k):
        self.skip = not self.skip
        self.skip_row.select(self.skip)
        self.update_info()
        self.save()

    def set_mode(self, i):
        self.mode = i
        for k, r in enumerate(self.rows):
            r.select(k == i)
        self.update_info()
        self.save()

    def update_info(self):
        if not hasattr(self, 'go') or not hasattr(self, 'pool_rows'):
            return
        if self.tab == 'adv':
            self.info.configure(text=self.adv_text())
            self.go.set_enabled(not self.busy)
            return
        v = self.diff.value
        self.info.configure(text=tr('info', m=self.mode_text(self.mode), v=v, d=diff_desc(v), g=go_name(self.gomode),
                                    a=tr('anti'), s=tr('on') if self.anti else tr('off'), k=tr('skip'),
                                    ks=tr('on') if self.skip else tr('off')))
        self.go.set_enabled(mode_ok(self.mode) and not self.busy)

    def roll_seed(self):
        self.seed.set(seed_name())

    def dialog(self, title, msg, buttons=(('ok', True),), accent=OK):
        """Caixa de mensagem no visual do launcher (a do Windows é clara), modal: devolve o valor do botão clicado
        (Esc/fechar = o do último botão). Como a confirmação do gerador do Metroid Fusion: título, texto e OK."""
        w = tk.Toplevel(self.root, bg=BG)
        w.title(title)
        w.resizable(False, False)
        w.transient(self.root)
        res = [buttons[-1][1]]
        f = tk.Frame(w, bg=BG, padx=24, pady=20)
        f.pack(fill='both', expand=True)
        tk.Frame(f, bg=accent, height=3).pack(fill='x', pady=(0, 14))
        label(f, msg, F['base'], justify='left', wraplength=round(420 * self.scale)).pack(anchor='w')
        row = tk.Frame(f, bg=BG)
        row.pack(anchor='e', pady=(18, 0))

        def close(v):
            res[0] = v
            w.destroy()
        for i, (k, v) in enumerate(buttons):
            b = RButton(row, tr(k), lambda v=v: close(v), F['base'], bg=BG, padx=26,
                        **({'fill': ACCENT, 'hover': ACCENT_HI, 'line': ACCENT_HI} if i == 0 else {}))
            b.pack(side='left', padx=(0 if i == 0 else 10, 0))
        w.bind('<Return>', lambda _: close(buttons[0][1]))
        w.bind('<Escape>', lambda _: close(buttons[-1][1]))
        w.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - w.winfo_reqheight()) // 3
        w.geometry(f'+{max(0, x)}+{max(0, y)}')
        dark_title_bar(w)
        w.focus_set()
        w.grab_set()
        w.wait_window()
        return res[0]

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

    def generate(self):
        if self.busy:
            return
        try:
            van, _ = find_rom()                  # a ROM é conferida a cada Gerar; problema = caixa de erro
        except ValueError as e:
            return self.dialog(tr('error_title'), str(e), accent=ERR)
        text = self.seed.get().strip()
        if not text or text == self.last:  # nome digitado/sorteado é respeitado; o que acabou de sair não se repete
            text = seed_name()
        name, _ = seed_from_name(text)
        self.seed.set(name)
        self.last = name
        self.save()
        self.busy = True
        self.go.set_text(tr('busy'))
        self.update_info()
        self.result = None
        if self.tab == 'adv':
            job = (write_seed_adv, name, van, json.loads(json.dumps(self.adv)))
        else:
            job = (write_seed, name, van, self.mode, self.diff.value, self.gomode, self.anti, None, self.skip)
        threading.Thread(target=self.work, args=job, daemon=True).start()
        self.root.after(100, self.poll)

    def work(self, fn, *args):
        try:
            self.result = True, fn(*args)
        except Exception as e:                                          # mostra qualquer falha na janela
            self.result = False, str(e)              # a janela só é mexida pela thread principal (poll)

    def poll(self):
        if self.result is None:
            self.root.after(100, self.poll)
            return
        self.busy = False
        self.go.set_text(tr('generate'))
        self.update_info()
        ok, v = self.result
        if ok:
            self.dialog(tr('success'), tr('added', b=v, d=SEED_DIR))
        else:
            self.dialog(tr('error_title'), v, accent=ERR)


def main():
    if '--seed' in sys.argv:        # sem janela (conferência):
        # "Demon's Crest Open Randomizer.exe" --seed "Nome Da Seed" [--modo limitado|classico|extra] [--dif 1-5]
        #   [--go vellum|bosses|crests|hp] [--anti 1] [--skip 1] [--home PASTA]
        a = dict(zip(sys.argv[1::2], sys.argv[2::2]))
        home = a.get('--home', HOME)
        mode = MODE_KEYS.index(a.get('--modo', 'extra'))
        write_seed(a['--seed'], find_rom(home)[0], mode, int(a.get('--dif', DEFAULT_DIFF)), a.get('--go', DEFAULT_GO),
                   a.get('--anti', '0') == '1', home, a.get('--skip', '0') == '1')
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
