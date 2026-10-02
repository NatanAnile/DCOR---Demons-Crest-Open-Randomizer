DEMON'S CREST OPEN RANDOMIZER (DCOR) - versão 0.3
==================================================

(English version below.)


O QUE É
-------
O DCOR é um randomizer de Demon's Crest (Super Nintendo, versão americana). Ele embaralha os itens do jogo
(crests, talismãs, vellums, potions, HPs, recargas e potes de moedas) e garante que a seed sempre pode ser
terminada: cada item fica num lugar que dá pra alcançar com o que você já tem.

O código é todo feito do zero para este projeto, com auxilio de agentes de IA.


O QUE VOCÊ PRECISA
------------------
- A ROM original de Demon's Crest (USA). A ROM não vem junto; use a sua.
  Com ou sem cabeçalho de 512 bytes, as duas funcionam.
- Windows. É só abrir "Demon's Crest Open Randomizer.exe"; não precisa instalar nada.
-  A ROM gerada tem 4 MB, Use um emulador de Super Nintendo (BizHawk, snes9x, bsnes...), Everdrive compatível com ROM de 4MB ou FXPak/Sd2Snes caso jogue no console.


COMO USAR
---------
1. Coloque a ROM original na pasta ROM (ao lado do executável). Se ela faltar ou estiver errada, uma caixa de erro
   avisa ao gerar.
2. Escolha as opções. A guia Simples tem os presets (modo, dificuldade, objetivo, extras); a guia Avançado deixa
   ajustar cada coisa (veja GUIA AVANÇADO). Passe o mouse em cima de cada opção para ver a descrição.
3. Clique em Gerar. Ele usa as opções da guia que estiver aberta.
4. A ROM sai na pasta Seed e o spoiler (onde está cada item) na pasta Spoiler, com o mesmo nome:
   "DemonRando - Nome Da Seed.sfc" e "DemonRando - Nome Da Seed.txt".

As opções escolhidas ficam salvas para a próxima vez.


A SEED
------
- O nome da seed são 5 palavras do jogo, tipo "Hand Flier Crawler Air Belth". O nome É a seed: o mesmo nome com
  as mesmas opções gera sempre a mesma ROM. Dá pra passar o nome pra um amigo e jogar a mesma seed.
- Campo em branco: o gerador sorteia um nome.
- Sortear: sorteia um nome sem gerar.
- Clicar em Gerar de novo sem mexer no nome gera uma seed nova.
- Pode digitar qualquer texto como nome ("Live de Sexta", por exemplo).


MODOS (o que é embaralhado)
---------------------------
- Limitado: crests, potion, vellums e talismãs. Os HPs ficam no lugar original.
- Clássico: crests, potion, vellums, talismãs e HPs.
- Clássico Extra: tudo acima, mais as recargas de HP (de chefes e potes) e os potes de moedas 20G.
- Insano: em breve. Vai embaralhar também potes, estátuas de gárgula, estátuas quebráveis pela Earth Crest,
  janelas da fase 2 e blocos da fase 6.


DIFICULDADE (1 a 5, vale para todos os modos)
---------------------------------------------
O jogo é dividido em "esferas": a esfera 1 é o que dá pra pegar sem nada, a 2 é o que abre com os itens da 1, e
assim por diante. Toda seed tem pelo menos 5 esferas. "Itens fortes" = Time Crest, Demon Fire, Fang, Armor e
Air Crest.

- 1: itens fortes nas esferas 1 a 3, mais HP no começo. No início, no máximo 3 crests/Armor. A lógica aceita a
  Armor no lugar da Water Crest em alguns checks debaixo d'água.
- 2: itens fortes nas esferas 2 e 3, mais HP no começo. No início, no máximo 2 crests/Armor. A lógica aceita a
  Armor no lugar da Water Crest em alguns checks debaixo d'água.
- 3: moderada. No mínimo 5 esferas, e nenhum item forte nas 2 primeiras. No início, no máximo 2 crests/Armor e
  5 HP. Debaixo d'água, a lógica também aceita Time Crest, ou Armor com 10+ HP, no lugar da Water Crest.
- 4: itens fortes só a partir da esfera 4, 5 HPs a menos no jogo. No início, no máximo 1 crest/Armor e 2 HP.
  Debaixo d'água, a lógica também aceita Time Crest + Armor + 15 HP no trecho mais longo.
- 5: itens mais fortes sempre nas últimas esferas, com Time Crest (quando no jogo) e Fang no castelo final. De 2 a
  4 itens, entre Air Crest, Time Crest, Tornado e Demon Fire, ficam fora do jogo. A lógica pode exigir checks
  debaixo d'água sem Water Crest. Prevenção Anti-Softlock obrigatória.

Item tirado do jogo vira pote de 20G ou recarga de HP.


OBJETIVO (o que abre o castelo do Phalanx no mapa)
--------------------------------------------------
- 5 Vellums (padrão).
- All Bosses: vencer os 15 chefes (Somulo, Hippogriff 1 e 2, Arma 1, 2 e 3, Belth, Ovnunu, Flame Lord, Skulla,
  Flier 1 e 2, Holothurion, Crawler e Grewon). O Trio the Pago é minigame e não conta.
- All 4 Main Crests: as 4 crests de transformação (Earth, Air, Water e Time). Não disponível na dificuldade 5.
- All HP: todos os HPs do jogo fora do castelo.

Um item que o objetivo exige nunca fica dentro do castelo.


EXTRAS
------
- Prevenção Anti-Softlock: pequenos ajustes de mapa para o jogador não ficar preso.
  - Área 27: quem entra sem a Earth Crest pode morrer para sair.
  - Dificuldade 5 sem Air Crest e sem Tornado: as áreas 29 e 38 ganham caminho pela Claw, inclusive até o Phalanx.
  A dificuldade 5 liga esta opção sozinha. Dá pra desligar, com um aviso: a seed pode ficar impossível.
- Skip Somulo: pula a luta do Somulo na abertura. O jogo começa na área 1, com o Somulo já vencido, e o item
  que ele soltaria aparece em cima do Firebrand.
- Randomizar Crest inicial: em breve. O Firebrand começa com uma crest sorteada e o tiro básico vira o item Fire
  Crest.
- Randomizar Head Butt: em breve. A cabeçada vira item; sem ela não se quebram estátuas nem janelas.


GUIA AVANÇADO
-------------
Cada parte da seed separada. "Rando" = sorteado pela seed (o mesmo nome dá o mesmo resultado); o cabeçalho do
spoiler diz o que saiu.
- Preset: carrega as opções de um arquivo .json (botão Carregar).
- Dificuldade: 1 a 5 marca tudo abaixo como na guia Simples; mexer em qualquer opção vira Custom.
- Nível da lógica: até onde a lógica pode exigir truques, como correr debaixo d'água sem a Water Crest (1 a 5).
- Acessibilidade: All Stages (as 6 fases abertas). Vanilla: em breve.
- Pool de Itens: o que entra no sorteio (Crests, Vellum, Potion, Talismã, HP, Refil HP, Moedas 20G); o que ficar
  desmarcado fica no lugar original. Rando sorteia de 1 a 7 categorias.
- Densidade: 0 a 100, onde caem os itens fortes e o HP (mais alto = mais tarde e mais difícil).
- Remoção de itens: Nenhuma, 2, 3, 4 ou Rando (2 a 4) entre Air Crest, Time Crest, Tornado e Demon Fire.
- HP disponível: Sparse (6 a 10), Medium (11 a 15), Full (16) ou Rando. Os HP que saem viram 20G ou Refil HP.
- Objetivo, Starter Crest (Vanilla, Earth, Buster, Claw, Rando), Skip Somulo e Anti-Softlock.
- Randomizar Head Butt: em breve.
Travas: sem as Crests na pool não dá pra ter crest inicial, remoção nem os objetivos All Bosses e All 4 Main
Crests; com remoção de itens não dá o objetivo All 4 Main Crests; remoção de 4 exige o Anti-Softlock.
No Avançado a seed tem no mínimo 4 esferas (com pool pequena o jogo fica perto do original, que tem 4).


OUTROS AJUSTES QUE O DCOR FAZ NA ROM
------------------------------------
- Cada item aparece com o próprio gráfico e a própria paleta, esteja onde estiver.
- Pegar uma crest devolve o controle assim que a caixa de mensagem fecha (no original podia prender o Firebrand).
- Somulo, primeira luta: a cabeça morre com 3 tiros (eram 6).
- A caixa de mensagem não estraga mais o efeito da água.
- Inimigos na fase 3, na área do Flame Lord não exibem mais sprites incorretos quando há uma Crest ou Piece of Fire Crest na área.


LIMITAÇÕES CONHECIDAS
---------------------
- A senha (password) do jogo não guarda o progresso do randomizer. Jogue com save state do emulador ou FXpack/SD2SNES.
- A lógica vai mudar conforme o feedback de quem jogar. Achou algo impossível ou estranho? Mande o nome da seed,
  as opções selecionadas e o spoiler.


IDIOMA
------
As bandeiras no canto de cima trocam a janela entre português e inglês na hora. O spoiler sai sempre em inglês.


ARQUIVOS E PASTAS
-----------------
- Demon's Crest Open Randomizer.exe: abre a janela.
- ROM: coloque aqui a ROM original.
- Seed: as ROMs geradas.
- Spoiler: onde está cada item de cada seed.
- patch: mapas da Prevenção Anti-Softlock.
- data: o código do gerador (Python). Mexer aqui vale na próxima vez que abrir o exe.
- dcor_config.json: as últimas opções escolhidas.


CRÉDITOS
--------
Criado por Natan Anile: ideia, direção, visual e ícone; lógica de progressão, dificuldades, modos e objetivos;
mapeamento dos itens do jogo; patches de mapa; testes de tudo no jogo.
Colaboração: Asvel (lógica e ideias).
Referência: FredYeye, Demon's Crest Rando (https://github.com/FredYeye/Demon-s-Crest-Rando). Os valores que ele
mapeou foram usados só para conferir os que coletamos. Nenhum código dele está no DCOR.

Fonte da janela: Roboto (Google, licença Apache 2.0, em data/fonts).

Demon's Crest é da Capcom. Este é um projeto de fã, sem fins lucrativos, e não distribui a ROM do jogo.



==================================================
DEMON'S CREST OPEN RANDOMIZER (DCOR) - version 0.3
==================================================


WHAT IT IS
----------
DCOR is a randomizer for Demon's Crest (Super Nintendo, US version). It shuffles the game's items (crests,
talismans, vellums, potions, HPs, refills and coin pots) and makes sure every seed can be finished: each item is
placed somewhere you can reach with what you already have.

All the code was written from scratch for this project, with the help of AI agents.


WHAT YOU NEED
-------------
- The original Demon's Crest (USA) ROM. The ROM is not included; use your own.
  With or without a 512-byte header, both work.
- Windows. Just open "Demon's Crest Open Randomizer.exe"; nothing to install.
- The generated ROM is 4 MB. Use a Super Nintendo emulator (BizHawk, snes9x, bsnes...), an Everdrive that supports
  4 MB ROMs, or an FXPak/SD2SNES if you play on the console.


HOW TO USE
----------
1. Put the original ROM in the ROM folder (next to the executable). If it is missing or wrong, an error box tells you
   when you generate.
2. Pick the options. The Simple tab has the presets (mode, difficulty, goal, extras); the Advanced tab lets you tune
   each part (see ADVANCED TAB). Hover over each option to read its description.
3. Click Generate. It uses the options of the open tab.
4. The ROM goes to the Seed folder and the spoiler (where each item is) to the Spoiler folder, with the same name:
   "DemonRando - Seed Name.sfc" and "DemonRando - Seed Name.txt".

Your options are saved for next time.


THE SEED
--------
- The seed name is 5 words from the game, like "Hand Flier Crawler Air Belth". The name IS the seed: the same name
  with the same options always makes the same ROM. You can give the name to a friend and play the same seed.
- Blank field: the generator picks a random name.
- Roll: picks a random name without generating.
- Clicking Generate again without changing the name makes a new seed.
- Any text works as a name ("Friday Stream", for example).


MODES (what gets shuffled)
--------------------------
- Limited: crests, potion, vellums and talismans. HPs stay in their original places.
- Classic: crests, potion, vellums, talismans and HPs.
- Classic Extra: all of the above, plus HP refills (from bosses and pots) and the 20G coin pots.
- Insane: coming soon. It will also shuffle pots, gargoyle statues, statues broken by the Earth Crest, the Stage 2
  windows and the Stage 6 wall blocks.


DIFFICULTY (1 to 5, applies to every mode)
------------------------------------------
The game is split into "spheres": sphere 1 is what you can get with nothing, sphere 2 is what the items from
sphere 1 open, and so on. Every seed has at least 5 spheres. "Strong items" = Time Crest, Demon Fire, Fang, Armor
and Air Crest.

- 1: strong items in spheres 1 to 3, more HP early. Early game: at most 3 crests/Armor. The logic accepts the Armor
  instead of the Water Crest for some underwater checks.
- 2: strong items in spheres 2 and 3, more HP early. Early game: at most 2 crests/Armor. The logic accepts the Armor
  instead of the Water Crest for some underwater checks.
- 3: moderate. At least 5 spheres, and no strong items in the first 2. Early game: at most 2 crests/Armor and 5 HP.
  Underwater, the logic also accepts the Time Crest, or the Armor with 10+ HP, instead of the Water Crest.
- 4: strong items only from sphere 4 on, 5 fewer HP in the game. Early game: at most 1 crest/Armor and 2 HP.
  Underwater, the logic also accepts Time Crest + Armor + 15 HP for the longest stretch.
- 5: strongest items always in the last spheres, with Time Crest (when in the game) and Fang in the final castle.
  2 to 4 items among Air Crest, Time Crest, Tornado and Demon Fire are out of the game. The logic may require
  underwater checks without the Water Crest. Anti-Softlock Prevention required.

An item removed from the game becomes a 20G pot or an HP refill.


GOAL (what opens Phalanx's castle on the map)
---------------------------------------------
- 5 Vellums (default).
- All Bosses: beat the 15 bosses (Somulo, Hippogriff 1 and 2, Arma 1, 2 and 3, Belth, Ovnunu, Flame Lord, Skulla,
  Flier 1 and 2, Holothurion, Crawler and Grewon). Trio the Pago is a minigame and does not count.
- All 4 Main Crests: the 4 transformation crests (Earth, Air, Water and Time). Not available on difficulty 5.
- All HP: every HP in the game outside the castle.

An item the goal requires is never placed inside the castle.


EXTRAS
------
- Anti-Softlock Prevention: small map edits so the player never gets stuck.
  - Area 27: entering without the Earth Crest, you can die to get out.
  - Difficulty 5 without Air Crest and without Tornado: areas 29 and 38 get a path with the Claw, including the way
    to Phalanx.
  Difficulty 5 turns this option on by itself. You can turn it off, with a warning: the seed may become impossible.
- Skip Somulo: skips the opening Somulo fight. The game starts in area 1 with Somulo already beaten, and the item
  he would drop appears on top of Firebrand.
- Randomize starting Crest: coming soon. Firebrand starts with a random crest and the basic shot becomes the Fire
  Crest item.
- Randomize Head Butt: coming soon. The head butt becomes an item; without it you cannot break statues or windows.


ADVANCED TAB
------------
Each part of the seed on its own. "Rando" = rolled from the seed (the same name gives the same result); the spoiler
header tells what came out.
- Preset: loads the options from a .json file (Load button).
- Difficulty: 1 to 5 sets everything below like the Simple tab; changing any option makes it Custom.
- Logic level: how far the logic may require tricks, like running underwater without the Water Crest (1 to 5).
- Accessibility: All Stages (all 6 stages open). Vanilla: coming soon.
- Item Pool: what gets shuffled (Crests, Vellum, Potion, Talisman, HP, HP Refill, 20G Coins); anything unchecked
  stays in its original place. Rando picks 1 to 7 categories.
- Density: 0 to 100, where strong items and HP land (higher = later and harder).
- Item removal: None, 2, 3, 4 or Rando (2 to 4) among Air Crest, Time Crest, Tornado and Demon Fire.
- Available HP: Sparse (6 to 10), Medium (11 to 15), Full (16) or Rando. Removed HP become 20G or HP Refill.
- Goal, Starter Crest (Vanilla, Earth, Buster, Claw, Rando), Skip Somulo and Anti-Softlock.
- Randomize Head Butt: coming soon.
Locks: without Crests in the pool there is no starting crest, no removal and no All Bosses / All 4 Main Crests goal;
item removal blocks the All 4 Main Crests goal; removing 4 requires Anti-Softlock.
On the Advanced tab a seed has at least 4 spheres (with a small pool the game stays close to the original, which has 4).


OTHER CHANGES DCOR MAKES TO THE ROM
-----------------------------------
- Every item shows up with its own graphics and its own palette, wherever it is.
- Picking up a crest gives control back as soon as the message box closes (in the original it could lock
  Firebrand in place).
- Somulo, first fight: the head dies in 3 shots (it used to take 6).
- The message box no longer breaks the water effect.
- Enemies in Stage 3, in the Flame Lord area, no longer show wrong sprites when there is a Crest or a Piece of Fire
  Crest in the area.


KNOWN LIMITATIONS
-----------------
- The game's password does not keep randomizer progress. Play with emulator save states or an FXPak/SD2SNES.
- The logic will change with feedback from players. Found something impossible or weird? Send the seed name, the
  selected options and the spoiler.


LANGUAGE
--------
The flags in the top corner switch the window between Portuguese and English instantly. The spoiler is always in
English.


FILES AND FOLDERS
-----------------
- Demon's Crest Open Randomizer.exe: opens the window.
- ROM: put the original ROM here.
- Seed: the generated ROMs.
- Spoiler: where each item is, for every seed.
- patch: the Anti-Softlock Prevention maps.
- data: the generator's code (Python). Changes here take effect the next time you open the exe.
- dcor_config.json: the last options you picked.


CREDITS
-------
Created by Natan Anile: idea, direction, look and icon; progression logic, difficulties, modes and goals; mapping of
the game's items; map patches; testing everything in the game.
Collaboration: Asvel (logic and ideas).
Reference: FredYeye, Demon's Crest Rando (https://github.com/FredYeye/Demon-s-Crest-Rando). The values he mapped
were used only to cross-check the ones we collected. None of his code is in DCOR.

Window font: Roboto (Google, Apache License 2.0, in data/fonts).

Demon's Crest belongs to Capcom. This is a non-profit fan project and does not distribute the game ROM.
