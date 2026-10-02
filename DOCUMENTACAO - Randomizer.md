# Demon's Crest — nosso randomizer (documentação)

Documentação própria do Neitan + Claude. Começou em 25/09/2026. **Separada dos relatórios pro Fred, que não
recebem mais nada.** Detalhes de engenharia reversa do motor ficam no `CONTEXTO.md` e em
`DemonsCrest Editor\DOCUMENTACAO.md`. Este arquivo registra o que o NOSSO código faz, as decisões e o histórico.

Regras do projeto:
- Nada do código do Fred: ele não tem licença. Ler pra entender pode; copiar não.
- Placement nunca é restrito por bug técnico, só por lógica de progressão.
- Tudo é medido. Hipótese vem marcada como hipótese.
- Termo: **"HP" e "Energia" são a mesma coisa (recarga)**.

---

## 1. Partes

- **Patch "item com gráfico próprio" (conserta sprite/paleta de qualquer seed)** — Estado: pronto, validado no jogo; Onde: `tools\patch_items.py` (referência), `rust\dc_rando_gfx` (porte, ROM byte a byte igual)
- **Ferramentas de medição (Lua)** — Estado: pronto; Onde: `lua\`
- **Insanity Randomizer (do zero)** — Estado: mapeamento na ROM em andamento (25/09); Onde: seção 3, `tools\insanity_map.py`

## 2. Patch de gráficos (estado em 25/09)

Entrada: uma ROM do rando. Saída: `<rom> - items.sfc` (2 MB).
- Restaura as tabelas gráficas originais: `[0xAE11,0xB2EB)`, `[0x1E9953,0x1EA383)` e os bytes do banco $80.
- Por localização, planeja onde cada item fica na VRAM e qual slot de paleta ele usa.
- Na hora em que o item nasce, o código em `BF:D600` decodifica o gráfico e a paleta dele. Os ganchos ficam em
  `82:E086`, `82:E09B` e `82:EA0F`.
- A caixa de texto ganhou 4 ganchos (`BE:DC77`, `BE:DC88`, `BE:DC8D`, `BE:DE92`). Com eles a água não quebra e
  a caixa não fica preta.
- Código: 847 B. Bloco `BF:D600-DF2F`: 2120 B para código e dados, quase cheio.
- Quando o bloco lota, o patch degrada em ordem:
  1. tira o brilho do item;
  2. se ainda não couber, devolve a localização ao comportamento original.

  Todas as degradações saem no relatório.

Casos especiais em vigor:
- **Área 25 (Stage5Hp3)**: a VRAM está 100% cheia. O item usa a unidade do único pote da sala
  (`POT_SPOT = {25: 0x0AE}`), só com o desenho parado. Exclusivo da área 25, por decisão do Neitan.
- **Earth Crest em espaço de 1 unidade**: os 4 tiles do desenho parado são juntados numa unidade e comprimidos no
  formato `80:C300`. A regra é genérica: vale para qualquer desenho parado com até 4 peças 8x8.
- **Aqua demon (empréstimo de VRAM)**: implementado e desligado (`BORROW_ON = False`). Quebrava o item ao ir até
  o aqua demon e voltar, e custa 274 B que o bloco não tem.

Pendente:
- **Stage2Hp2 (área 9, Belth)**: o item sai com a paleta do slot 0 (as cores do HP). Falta medir os slots da
  área 9 com retratos para decidir.
- **Espaço**: em 201 seeds, 34 itens perdem o brilho e 6 localizações voltam ao comportamento original.
  Caminhos possíveis:
  - 4 MB: a causa é a antipirataria, com conserto de 2 bytes em `82:9B3A` e `BE:E35D`, `$40→$80`. Não aplicado.
  - Enxugar os dados do bloco.

## 3. Insanity Randomizer

Ideia: um randomizer escrito do zero. A pool de itens inclui também:
- potes;
- estátuas quebráveis com soco;
- quebráveis com Earth Crest;
- orbes de recarga de HP.

Fonte do mapeamento: `mapeameno de itens.txt` (Neitan, 25/09). A numeração de área é a do jogo (`$8D/2`):
conferida na ROM em 25/09 (§3.2). Única diferença: o HP do Somulo sai na área 17.

- **1 Coliseu** — Área: 0; Conteúdo: drop da cabeça do Somulo: HP *(conferir: o CONTEXTO dá a luta do Somulo na área 17)*
- **Área 1** — Conteúdo: 1 pote com recarga, 3 potes, 6 estátuas de gárgula (1 com Vellum), Hippogriff (HP)
- **Área 2** — Conteúdo: 2 potes, Potion no chão
- **Área 3** — Conteúdo: HP no chão, 1 pote com recarga, Arma (Earth Crest)
- **Fase 2** — Área: 4; Conteúdo: 6 potes, 1 caveira quebrável com soco (as janelas ficaram de fora, por decisão do Neitan)
- **Área 5** — Conteúdo: 5 potes, Potion e talismã Hand no chão
- **Área 6** — Conteúdo: 2 blocos de Earth Crest, 1 pote com Vellum, 3 potes
- **Área 7** — Conteúdo: 1 pote com HP, 3 blocos de Earth Crest, 1 pote com recarga
- **Área 8** — Conteúdo: 1 pote com recarga, Ovnunu (Buster)
- **Área 9** — Conteúdo: 6 lápides, 5 pilhas de ossos (1 com HP), Belth (HP), 2 potes
- **Fase 3** — Área: 10; Conteúdo: 4 potes, Potion no chão
- **Área 11** — Conteúdo: 1 pote com recarga, 1 pote com Vellum (trancado por Buster ou Time Crest)
- **Área 13** — Conteúdo: 5 potes, Skulla (HP)
- **Área 14** — Conteúdo: 1 pote com recarga, HP no ar (evento: Flame Lord derrotado ou morte pra ele), Flame Lord (Tornado)
- **Área 15** — Conteúdo: 1 pote com HP
- **Área 16** — Conteúdo: talismã Skull
- **Fase 4** — Área: 18; Conteúdo: 1 pote, HP no chão (trancado por Buster ou Time Crest)
- **Área 19** — Conteúdo: 1 pote com recarga, Flier (Claw)
- **Área 20** — Conteúdo: Hippogriff (recarga)
- **Área 21** — Conteúdo: 4 potes
- **Área 22** — Conteúdo: 3 estátuas de gárgula (1 com o talismã Crown)
- **Área 23** — Conteúdo: Vellum no ar, Arma 2 (Air Crest)
- **Fase 5** — Área: 24; Conteúdo: 10 potes
- **Área 25** — Conteúdo: 1 pote com HP
- **Área 26** — Conteúdo: Holothurion (HP)
- **Área 27** — Conteúdo: 7 estátuas (1 com HP), 3 potes, Crawler (Water Crest)
- **Área 28** — Conteúdo: 4 potes, 1 estátua com HP
- **6 Degelo** — Área: 29; Conteúdo: Potion numa plataforma no céu, 5 pilhas de ossos de Earth Crest
- **Área 30** — Conteúdo: 2 potes, 5 pilhas de ossos (1 com Vellum), Grewon (Demon Fire)
- **Área 32** — Conteúdo: 1 pote com HP
- **Área 33** — Conteúdo: 3 estátuas de gelo de Earth Crest
- **Área 34** — Conteúdo: Flier (recarga)
- **Área 35** — Conteúdo: 1 estátua quebrável com o talismã Armor
- **Área 36** — Conteúdo: Arma 3 (Time Crest)
- **Castelo do Phalanx** — Área: ?; Conteúdo: HP e talismã Fang. **Só esses 2**, por decisão do Neitan
- **Área 53** — Conteúdo: **Trio the Pago (HP)**. Faltava no arquivo; confirmado 25/09

Notas do Neitan:
- Área 14 tem 2 eventos: o teto pegando fogo, e o item liberado quando o Flame Lord morre ou quando ele mata o
  Firebrand.
- Área 18: o HP que o Neitan lembrava ali era de uma seed do rando. No jogo original, a Potion da área 18 fica
  no mesmo lugar.

### 3.1 Como o jogo guarda cada tipo de localização (medido na ROM US, 25/09)

Ferramenta: `tools\insanity_map.py` (código nosso) → `logs\insanity_map.txt`, com cada localização e o endereço
de onde ela sai.

**Lista de objetos por área** (chamada na carga da área e ao rolar a tela, `82:8B2B` → `82:8BDB`):
- `$81:C874 + área*3` = ponteiro de 24 bits para `[n]` + n registros de 6 B `[id u16][X u16][Y u16]`.
- Id = tipo (byte baixo) + subtipo (byte alto). O bit 7 do subtipo é flag do spawner (`82:8CE1`); o objeto
  recebe o id sem ele.
- `$81:C9D0 + área*3` = **versão da área já limpa** (sem inimigos, só potes e itens), usada quando `$1E58` bit 0
  está ligado e a área é menor que 80. **Tabela válida só para as áreas 0-63.** Um item tem que ser trocado nas duas.
- Só o carregador `82:8BDB` lê `$C874`/`$C9D0` (com DB `$81`) e usa o ponteiro como longo (`LDA [$10],Y`): a lista
  pode ficar em qualquer banco (o editor de fases muda listas maiores pra `$C0+` na ROM de 4 MB). O objeto nasce
  quando entra na janela da câmera (`82:8C32`); "já nasceu" = bit do índice na lista em `$09C0-$09DF` (256 bits,
  zerado na carga em `84:EAAE`) → no máximo 255 por lista.
- As vagas de objeto ficam em `$1080-$1D4F` (42 × `$50` B), com o tipo em +2 e o subtipo em +3. O laço é
  `82:8600`, e a tabela de rotinas é `$82:8000/8180/8300/8480 + tipo*2`.

**Ids de item** (subtipo & `$3F` = índice; bit `$40` = não quica):

- **Tipo `2D`** — Item: vellum/potion; Índices: `00-08` vellum (5), `0A-12` potion (5)
- **Tipo `2E`** — Item: talismã; Índices: `00` Crown, `02` Skull, `04` Armor, `06` Fang *(área 39, confirmar)*, `08` Hand
- **Tipo `48`** — Item: crest; Índices: `00` Buster, `02` Tornado, `04` Claw, `06` Demon Fire (fire, sprite 4F); `08-0E` elementais (sprite 4D), `0C` = Water
- **Tipo `49`** — Item: HP; Índices: subtipo & `$1F` = bit da flag em `$1E54` (tabela `$82:F4CA`); `1F` = sem flag
- **Tipo `23`** — Item: drop pequeno (efeito em `82:C996`); Índices: `00` **20G**, `02` 5G, `04` 1G, `06` **recarga total**, `08` +2 HP, `0A` +1 HP (dinheiro em `$1063`, máx. 999)

Uma crest com `$1E51` bit 8 ligado vira `1F49` (`82:E9EE`).

**Pote (tipo `57`)**, quebrado em `84:C4BF`:
- Subtipo 0 = pote comum: sorteia 1 de 16 em `$81:D1D1` (6 nada, 6 × 1G, 2 × 5G, 1 × 20G, 1 × +1 HP).
- Subtipo ≠ 0: o id sai de `$81:D85C + subtipo`:
  - `02` = **20G fixo**: áreas 1, 4, 6, 9, 10 (3), 13 (5), 18;
  - `04` = recarga total;
  - `06`/`0A` = vellum 02/04;
  - `08`/`0C`/`0E`/`10` = HP 08/0B/0D/0F.

**Cenário quebrável, 2 sistemas** (o atributo do bloco vem de `80:946B`):
- **`$A0`** (`80:F30E`):
  - A lista por área `$81:B513` define o bloco que entra no lugar (12 bits) e a rotina (4 bits):
    0 = troca e sorteia drop, 1 e 2 = bloco grande, 3 = só troca. Índice = atributo & `$1F`; valor v: rotina
    v>>12 (`JMP ($F3DE,X)`), bloco novo v & `$FFF`. Medido: as gárgulas (áreas 1, 22, 37...) são rotina 2; rotina 0
    são paredes de blocos (área 32: 96 blocos, área 4: 56).
  - O item escondido é casado **por posição** em `$81:B477 + área*2` → `[X][Y][id]` até X = 0.
  - Só 2 itens usam isso: o Vellum 00 (área 1) e a Crown (área 22).
- **`$E0`** (`80:F5D0`):
  - `$81:B5C3 + área*2` → registros `[X u16][Y u16][bloco][i]`. **Qual registro:** atributo do bloco & `$1F` =
    índice na lista (`80:F609`), não a posição; todos os blocos de uma estátua têm o mesmo índice e X,Y é onde o
    drop nasce. Atributo do bloco = `$98:8000 + (conjunto<<12) + bloco` (`80:94D3`).
  - Com i ≠ 0, o id sai de `$81:B507 + i`: `02` HP 09, `04` HP 05, `06` HP 0E, `08` Vellum 08, `0A` Armor.
  - Com i = 0, sorteia um drop (`80:F56F`, tabela `$81:D1B1`).
  - As listas são compartilhadas entre áreas (ex.: `B6B5` = áreas 15-28). O mapa da área escolhe quais blocos
    existem.
  - Os blocos de Earth Crest do mapeamento estão aqui: 2 na área 6, 3 na 7, 5 ossos na 29 e 3 estátuas de gelo
    na 33.

**Drops por código** (chefes): `LDA #id` + `JSL 82:877B` (cria) ou `82:87E9` (o objeto vira o item). Trocar o
item = trocar o operando.

### 3.2 Localizações de item do jogo original (conferidas contra o mapeamento do Neitan)

- **Área 1** — Localização: estátua de gárgula; Id: vellum 00; De onde sai: `$A0`, `$81:B4F9`
- **Área 1** — Localização: Hippogriff; Id: HP 02; De onde sai: código `82:9999` (tipo 09; em outra condição o mesmo código solta `0623` recarga, `82:99A7`: área 20)
- **Área 2** — Localização: chão; Id: potion 0A (`4A2D`); De onde sai: objeto
- **Área 3** — Localização: chão; Id: HP 07 (`4749`); De onde sai: objeto
- **Área 3** — Localização: Arma; Id: Earth Crest; De onde sai: **não achado** (suspeita: objeto `4F` → `4E48` em `82:F009`)
- **Área 5** — Localização: chão; Id: potion 0C, talismã Hand (`482E`); De onde sai: objeto
- **Área 6** — Localização: pote; Id: vellum 02; De onde sai: pote sub `06`
- **Área 7** — Localização: pote; Id: HP 08; De onde sai: pote sub `08`
- **Área 8** — Localização: Ovnunu; Id: Buster (`4048`); De onde sai: código `83:C6D4` (tipo 6B)
- **Área 9** — Localização: pilha de ossos; Id: HP 09; De onde sai: `$E0`, lista `B667`, em 536,192
- **Área 9** — Localização: Belth; Id: HP 03; De onde sai: código `83:E8D8` (tipo 74)
- **Área 10** — Localização: chão; Id: potion 0E; De onde sai: objeto
- **Área 11** — Localização: pote; Id: vellum 04; De onde sai: pote sub `0A`
- **Área 13** — Localização: Skulla; Id: HP 04; De onde sai: código `BD:85AD`/`BD:8B99` (tipo 7B)
- **14 → 50** — Localização: Flame Lord; Id: Tornado (`4248`); De onde sai: código `82:CCFD` (tipo 28)
- **Área 50** — Localização: HP no ar; Id: HP 0A (`4A49`); De onde sai: objeto da **área 50** (a 14 depois do evento; 51 = outra variante)
- **Área 15** — Localização: pote; Id: HP 0B; De onde sai: pote sub `0C`
- **Área 16** — Localização: chão; Id: talismã Skull (`422E`); De onde sai: objeto
- **Área 17** — Localização: cabeça do Somulo; Id: HP 01; De onde sai: código `83:96D3` (tipo 52). **Área 17, não 0** (a 0 é a luta inteira)
- **Área 18** — Localização: chão; Id: potion 10; De onde sai: objeto
- **Área 19** — Localização: Flier; Id: Claw (`0448`); De onde sai: código `85:DBA0`/`85:EF1F` (tipo 82, subtipo 0)
- **Área 22** — Localização: estátua de gárgula; Id: Crown; De onde sai: `$A0`, `$81:B501`
- **Área 23** — Localização: no ar; Id: vellum 06; De onde sai: objeto
- **Área 23** — Localização: Arma 2; Id: Air Crest; De onde sai: **não achado**
- **Área 25** — Localização: pote; Id: HP 0D; De onde sai: pote sub `0E`
- **Área 26** — Localização: Holothurion; Id: HP 06; De onde sai: código `83:D7B7` (tipo 6F)
- **Área 27** — Localização: Crawler; Id: Water (`0C48`); De onde sai: código `82:BA12` (tipo 1A)
- **Área 27/28** — Localização: estátuas; Id: HP 05 e HP 0E; De onde sai: `$E0`, lista `B6B5` (436,136 e 644,456) — falta ver no mapa qual é de qual área
- **Área 29** — Localização: plataforma no céu; Id: potion 12; De onde sai: objeto
- **Área 30** — Localização: pilha de ossos; Id: vellum 08; De onde sai: `$E0`, lista `B703`, em 1480,168
- **Área 30** — Localização: Grewon; Id: Demon Fire (`0648`); De onde sai: código `BE:9E23` (tipo 13, subtipo 0; na área 41 o mesmo solta `0623`)
- **Área 32** — Localização: pote; Id: HP 0F; De onde sai: pote sub `10`
- **Área 34** — Localização: Flier; Id: `1F49` (HP sem flag = recarga); De onde sai: código `85:DBA7` (tipo 82, subtipo 1)
- **Área 35** — Localização: estátua; Id: talismã Armor; De onde sai: `$E0`, lista `B733`
- **Área 36** — Localização: Arma 3; Id: Time Crest; De onde sai: **não achado**
- **Área 39** — Localização: chão; Id: talismã `462E` (Fang?); De onde sai: objeto
- **Área 52-54** — Localização: Trio the Pago; Id: HP 0C (`4C49`); De onde sai: código `BC:A13E` (tipo 96)
- **Área 38** — Localização: sino (bater para cair); Id: HP 10; De onde sai: código `BE:FA01` (tipo `AE`): o sino cria o **pote `1257`**, que tem o HP 10 (`$81:D85C+12`). Nas outras áreas (40) é o pote `0457` = recarga total (`BE:F9F3`). Achado pelo Neitan

Flags de HP: a tabela `$81:F4CA` vai de **01 a 10** (bits 0-15 de `$1E54`; não existe flag 00). As 16 estão
localizadas.

### 3.4 Lógica e gerador (25/09)

Lógica atual (desde 29/09, versão 0.2 do DCOR): `lógica_demonRando_V3.txt` (Neitan). É a V2 com a dificuldade de
cada alternativa entre parênteses:
- `(5)`, `(4 e 5)`, `(1 a 3)`: o **menor** número é o piso. A alternativa vale daquela dificuldade pra cima, nunca
  abaixo. A faixa diz onde ela é o caminho **principal** ("principalmente, não obrigatório").
- Sem parênteses: vale em qualquer dificuldade.
- No código (`insanity_rando.parse`): cada alternativa vira (termos, piso, principal); `Logic` usa só as de piso
  menor ou igual à dificuldade da seed. O "principal" fica guardado em `Logic.alts` para o trabalho das esferas (0.3).
- A V3 substitui o ajuste de 25/09 do Potion 0C e da Hand (6+/10+ HP e Time Crest com 5+).

Lógica anterior: `lógica_demonRando_V2.txt` (Neitan). Regras decididas por ele:
- **Sintaxe:** `,`, `+` e ` e ` = E; `/` e ` ou ` = OU; `n/a` = sem requisito.
- **`X+ HP`** = barra de vida total = 4 (início, `84:8906`) + nº de HPs pegos (`84:C17A` recalcula assim).
- **Go mode:** o castelo do Phalanx só aparece com os **5 vellum** (regra herdada do rando do Fred). Todas as
  fases ficam abertas desde o início.
- **Shock Spell:** comprada na loja. Na lógica basta ter 1 vellum; dinheiro não entra.
- **Pool:** só localizações que soltam algo no original, inclusive chefes, 20G e recarga total. Quebráveis sem
  item ficam de fora até o algoritmo ser validado.

Gerador: `tools\insanity_rando.py`:
- 58 checks. Pool: 16 HP, 5 vellum, 5 potion, 5 talismãs, 8 crests, 11 × 20G e 8 × recarga.
- Preenchimento "assumed fill". Cada item de progressão vai para um check alcançável sem ele. Se cair num beco,
  a mesma seed tenta de novo.
- Conferência: joga a seed do zero, em esferas.
- `-s SEED` imprime o spoiler; `--lote N` testa N seeds.
- 5000 seeds: 0 falhas, 0 check inalcançável, de 2 a 5 esferas.

### 3.5 Gravação da ROM (25/09) — `tools\insanity_rom.py`

`python tools\insanity_rando.py -s SEED --rom` grava `Demon's Crest Insanity - seed N.sfc` + `log Insanity - seed N.txt`
na pasta do projeto (`-o PASTA` muda o destino). Mesma seed = mesma ROM (conferido com `PYTHONHASHSEED` diferente).

- **4 MB**:
  - A ferramenta `DemonsCrest Editor/ferramentas/rom_expand` (validada) conserta os 2 bytes da antipirataria.
  - A metade nova guarda a tabela de potes em `$C0:8000` e 3 desvios em `$C0:8100`.
  - **Savestate de ROM 2 MB não serve.**
- **Toda escrita confere o valor original antes** (AssertionError se a ROM não for a esperada).
- **Como cada check é gravado:**

- **item no chão/no ar** — Como: id do registro nas duas listas de objetos (normal e área limpa); mantém o bit `$40` do lugar
- **pote** — Como: cada pote da pool ganha subtipo próprio (a partir de `$14`) numa cópia da `$81:D85C` em `$C0:8000`; `84:C4E2` vira `JSL $C0:8100` (`LDA $C08000,X`)
- **sino (área 38)** — Como: `LDX #$1257` em `BE:FA01` → pote com subtipo próprio
- **cenário `$A0`** — Como: id em `$81:B4FD` (Vellum 00) e `$81:B505` (Crown)
- **cenário `$E0`** — Como: ids em `$81:B509-B512`
- **Arma 1/2** — Como: `$81:F0A2` / `$81:F0A4`; Arma 3 = `82:F009` (o `4F` vira esse id)
- **chefes** — Como: operando `LDA #id` (Skulla e Flier têm 2 cópias do código: as duas recebem o item)
- **Crawler** — Como: `LDA #sub / XBA / LDA #tipo` em `82:BA12` / `82:BA15`
- **Hippogriff 2** — Como: `82:99A0` → desvio: subtipo 2 (`$1DD8`, área 20) solta o item; o da área 37 continua recarga
- **Grewon** — Como: `BE:9E22` → desvio: subtipo 0 (área 30) solta o item; o da área 41 continua recarga

- Verificado offline (seed 1):
  - 92 trechos alterados, todos esperados;
  - o código dos desvios foi desmontado e confere;
  - 300 seeds gravadas sem nenhuma conferência falhar.
- **Sem o patch de gráficos ainda**: item fora do lugar original pode sair com sprite/paleta errados. O objetivo
  deste passo é validar que cada check solta o item certo.
- **Fim de área depois do chefe** (1º teste do Neitan, seed 1):
  - O que o teste mostrou:
    - a crest do pote da área 1 levou para a sala seguinte;
    - o HP 01 no lugar da Potion 0A levou de volta ao Somulo;
    - o Arma 1 soltou recarga e o jogo travou (softlock).
  - Causa: no original **quem encerra a área é o item**.
    - HP com subtipo 0-4 ou 6 vai para o estado 2 (`82:EB28`). Toda crest também vai para ele (`82:EA93`).
    - O estado 2 (`82:EB7C`) segura o jogador, espera a fanfarra e a mensagem (`$0EDB`) e pula para `80:BB58`.
    - `80:BB58` é a saída de área. A próxima área sai da tabela `$81:97DA[área atual]` e a troca é feita pela
      mudança de thread `80:829B`.
  - Conserto (gravado junto com a ROM):
    - HP de chefe = HP comum (`82:EB28` → NOP).
    - A crest, depois da mensagem, só some (`82:EB86`: `LDA $0EDB / BEQ / STZ $0E5C / JMP $8752`).
    - Os 13 pontos de drop que encerravam a área **marcam o objeto do drop**: `$7F:6F00` = objeto, `6F02` = id,
      `6F04` = contador. Esses pontos são Somulo, Hippogriff 1, Belth, Skulla ×2, Holothurion, Ovnunu, Flame Lord,
      Crawler, Arma 1/2, Arma 3, os dois Flier (19 e 34; corrigido 26/09) e, só com subtipo 0, o Grewon.
    - O vigia (`82:86A7` → `$C0`) funciona assim: quando o drop marcado some (pego ou expirado) e não há caixa de
      mensagem (objeto tipo `8B`), conta 40 quadros e chama `80:BB58`.
    - O marcador zera a cada carga de área (`82:8B4D`).
    - O Hippogriff da 20/37, o Flier da 34 e o Grewon da 41 não encerravam a área e continuam sem encerrar.
  - Verificado offline: código desmontado; 200 seeds gravadas; a seed 1 tem o mesmo spoiler. **Falta testar no jogo.**
- **Progresso deduzido dos itens** (teste da seed 2):
  - O que o teste mostrou: Belth e Skulla sumiram, o Grewon não estava lá, o castelo apareceu de cara, e as fases
    não estavam todas abertas.
  - Causa:
    - O cartucho **não tem SRAM** (cabeçalho: SRAM 0). O progresso só existe na senha, então o jogo deduz fase
      feita, chefe vencido e fase liberada **dos bits de item**.
    - O roteiro do mapa-múndi (`BE:83E4-8467`, tabela de saltos `BE:8397`, contador `$0EBA`) revela as fases em
      cadeia pelos itens de chefe. A **Time Crest revela o castelo**.
  - Bits:
    - crests `$1E51` (tabela `$81:D730`): Buster `01`, Tornado `02`, Claw `04`, Demon Fire `08`, Earth `10`,
      Air `20`, Water `40`, Time `80`;
    - HPs `$1E54-55` (16 bits);
    - talismãs `$1E53` bits 3-7;
    - `$1E56`;
    - `$1E58` bit 0 = "fase limpa" (usa a lista `$81:C9D0`).
  - **Senha** (encoder `84:BAB8`):
    - 8 bytes (`$10-$17`) embaralhados bit a bit viram 16 caracteres de 4 bits (buffer `$1E59`, caracteres
      `$1E61`).
    - `$10` = crests; `$11` = `$1E51` bit 8 + `$1E56`×2; `$12` = talismãs (**bits 0-2 livres**); `$13-14` = HPs;
      `$15` = `$1E58` & `0F` (**bits 4-7 livres**); `$16` = chave aleatória (nibble alto ≠ 0/F) + checksum;
      `$17` = checksum.
    - **Sobram 7 bits para 14 chefes**, então estender exige mais caracteres na senha.
  - Decisão do Neitan: ~~estender a senha~~ → **26/09: senha fora do escopo** ("não precisa fazer o password
    funcionar"). As flags de lugar ficam só na RAM.
  - Base (vale para qualquer forma de guardar): uma flag de "lugar feito" por chefe, independente do item, e os
    testes do jogo trocados para ela.
  - Medição (`lua\progress_reads.lua`):
    - Precisa de gatilho de **execução**, porque o de leitura não dispara pelos bancos `$80`/`$81`.
    - 45 instruções vigiadas; com 98 o jogo caía para 45 fps.
  - **Portão de chefe = `80:A45F`**:
    - roda ao chegar no chefe e ao sair da fase;
    - usa `$81:80A1[área]` → `[índice][máscara]`; se `$1E51+índice` tem a máscara, grava `TSB $0EAA` e
      `$09F8 = $14`, e o chefe é pulado.
    - Portões:

      | Área | Chefe | Bit |
      |---|---|---|
      | 1 | Hippogriff | HP 02 |
      | 3 | Arma 1 | Earth |
      | 9 | Belth | HP 03 |
      | 13 | Skulla | HP 04 |
      | 14/50/51 | Flame Lord | Tornado |
      | 19 | Flier | Claw |
      | 23 | Arma 2 | Air |
      | 26 | Holothurion | HP 06 |
      | 27 | Crawler | Water |
      | 30 | Grewon | Demon Fire |
      | 36 | Arma 3 | Time |

  - **Mapa-múndi = `85:A1EE`**, chamado pelo controlador do mapa (objeto `6A`, `85:AEE7`):
    - 5 grupos (`$81:8D61`/`8D6B`, crest **ou** HP de chefe):
      - Buster ou HP 03;
      - Tornado ou HP 04;
      - Claw ou Air;
      - Water ou HP 06;
      - Demon Fire ou Time.
    - Resultado Y → `$81:E1D2[Y]` = máscara de fases visíveis (`$37`):
      - padrão `0F`;
      - 3 grupos `4F`;
      - crests `37` → `3F`;
      - os 5 grupos `7F`;
      - crest de bit 8 → `FF`.
    - Isso explica as fases 5, 6 e o castelo aparecerem juntos ao pegar o HP 04.
  - Flags de vellum/potion em `$1E56` (vellum bits 0-4, potion 5-9, tabela `$81:F4CC`). Por isso `$12` bits 0-2
    **não** estão livres na senha: sobram só os bits 4-7 de `$15`.
  - **Conserto (base, antes da senha estendida)**:
    - `LOC` (`$7F:6F10`) = 1 bit por chefe, tabela por área `LOCBIT` em `$C0:8400`;
    - o vigia liga o bit da área ao encerrar;
    - o portão `80:A47D` testa `LOC` (a máscara do `TSB $0EAA` continua a original);
    - o mapa `85:A1EE` dá sempre `3F` (fases 1-6) e `7F` com os 5 vellums (**hipótese: castelo = bit 6**,
      conferir no jogo); a crest de bit 8 continua `FF`;
    - `LOC` zera no jogo novo (`84:8906`) e ao carregar senha (`84:C17F`).
  - Teste de 26/09 (seed 2): fases todas abertas e o Belth apareceu, mas a Skulla e o Arma 1 não. Outros testes
    de "tem o item", também trocados pela flag do lugar:
    - `BE:E3E1` (código do Arma): **com a Time Crest, todo Arma se apagava**. Agora cada Arma olha o próprio lugar
      (subtipo 0/2/4 → Arma 1/2/3).
    - Roteiro de entrada das fases `BE:8326-845B`, 14 testes (Buster, HP 03, Tornado, **HP 04 = Skulla**, Claw,
      HP 06, Water, Demon Fire, Time). Suspeita para a Skulla; **confirmar no jogo**.
    - `84:9902`: evento de entrada da área 1 (intro do Hippogriff, HP 02).
    - `BC:AAEC`: Trio the Pago (HP 0C).
    - Troca de área por item (`84:8949` → `JSR ($8950,X)` por área):
      - área 8 com Buster → área 60 (arena sem Ovnunu), `84:89F7`;
      - área 27 com Water → área 59 (sem Crawler), `84:8A18`;
      - as áreas 14/51 → 64/66 dependem de flags de evento `$7F:E000/E001`, não de item, e ficam como estão.
    - `84:8564`: áreas 0-3 e 17 **sem Earth Crest** (= Arma 1 não vencido) seguem outro fluxo. Agora usa a flag do
      Arma 1.
  - **Classificação das 98 instruções que leem `$1E51-$1E58`** (26/09). As que ficam olhando o item são de propósito:
    - progresso por lugar (trocadas): portão `80:A47D`, mapa `85:A1EE`, roteiro `BE:8326-845B`, `84:9902`,
      `BC:AAEC`, `BE:E3E1`, `84:89F7`, `84:8A18`, `84:8564`;
    - habilidade do item: `84:996F` (Water em área de água), `BC:9F4D` (Buster no Trio);
    - código do próprio item (não duplicar item já pego): `82:E0xx-EBxx`;
    - senha: `84:BACB-BAE6` e `84:C10C-C1EF`; jogo novo: `84:88E8-88FA`;
    - final/segredo (todas as crests e talismãs): `83:80C0-80D5`, `BE:D82B-D850`, e o bit 8 da crest em `BE:84A9`;
    - menu de crests e inventário/loja: `84:9012-9093`, `84:9381-93B1`, `85:C2FD`, `BC:9D65`, `BC:A5C0`, `BC:AAB5`;
    - `$1E58` (fase limpa): `80:AAB3`, `82:8BF9`.
  - **26/09: `$7F:6F00-6F1F` NÃO é livre.**
    - O savestate da seed 2 (jogo do Neitan, área 1) tinha `LOC = FF26`: lixo, com o bit do Arma 1 ligado. Por
      isso o Arma 1 não aparece.
    - A suposição de "páginas 60-7F nunca tocadas" vinha de medição em só 3 áreas.
    - Marcador (`6F00`) e `LOC` (`6F10`) precisam mudar para RAM medida como livre.
    - Medição passiva: `lua\wram_free.lua` enquanto ele joga; saída em `logs\wram_free.txt`.
    - Teste automático descartado: gravar dano na RAM não mata o Firebrand, e o Start só pausava o jogo.
  - **Regra do Neitan (26/09): nenhuma seed nova sem eu conferir antes no emulador.**
  - **RAM nova** (medida pelo `wram_free.lua` passivo: 46 min, 40 áreas, `$7E:1E58-1FFF` nunca mudou; a pilha
    começa em `$023F`): marcador `$7E:1F80`, `LOC` `$7E:1F90`.
  - **Teste automático** `lua\boss_test.lua` (26/09):
    - Como funciona: marca um drop falso no vigia, força o caminho "próxima área" da saída e troca `$8D` em
      `80:BB7F`. O jogo carrega a área pelo caminho normal. Entra pela entrada escolhida (`$09F7`), e dá para
      segurar um botão.
    - Resultado, com `LOC` zerado: Arma 1 (também com a Time na mão, andando a partir do savestate do Neitan),
      Ovnunu, Belth e Skulla **aparecem**; o portão nunca deu chefe como feito.
    - Não verificados: Hippogriff e Flame Lord (o teste não chegou perto), e Somulo, Flier, Arma 2, Holothurion,
      Crawler, Grewon, Arma 3 e Trio.
    - Andar sozinho esbarra em parede e inimigo, então o teste é limitado.
  - **Comparação com a ROM gerada pelo rando do Fred** (só a saída, não o código), para conferir a cobertura:
    - ele mexeu nos mesmos pontos: tabela do portão `$81:8123`, mapa `85:A1EE` (castelo = 5 vellums → `7F`, senão
      `3F`, **igual ao nosso**), Arma `BE:E3E1`, troca de área `84:89F7`, Trio `BC:AAEC`, e uma tabela de "HP que
      encerra a área" em `82:EB20`;
    - a estratégia dele é outra: o chefe testa o bit do item sorteado. Isso funciona porque o pool dele só tem
      itens únicos, e no Insanity não serve (20G e recarga não têm bit);
    - ele não mexeu no roteiro `BE:83xx`, em `84:9902` nem em `84:8564`. Nós trocamos os três pela flag do lugar,
      que é equivalente ao original com o item no lugar original.
  - Limite da varredura: pega só acesso direto ou longo a `$1E51-$1E58`. Um teste por ponteiro ou por outra
    variável derivada escapa dela. Por isso vale rodar o `progress_reads.lua` nos testes.
- Pendente no jogo: testar cada tipo de check (chão, pote, sino, cenário, chefe, Arma, Hippogriff/Grewon).

### 3.6 Gráficos dos itens no Insanity (26/09)

**Etapa 1**: `tools\insanity_gfx.py`, chamado pelo gravador.
- Reaproveita o `patch_items.py`: planejamento, registro de 22 B, código 65816 em `BF:D600`, ganchos `82:E086`,
  `82:E09B` e `82:EA0F`, e os 4 ganchos da caixa de mensagem. O caminho do Fred não muda.
- "Que item em qual lugar" vem de `GFX_INFO`: por check, a área onde o item nasce, se o item original era da lista
  principal ou da lista do meio (chefe), o item original, e se é chefe. Itens originais 20G/recarga contam como
  "Hp" (precisam de VRAM própria).
- **Não restaura o banco `$80`.** No Fred, a restauração desfaria o portão `80:A47D`.
- VRAM planejada **em sequência** por área, para dois itens não caírem no mesmo lugar.
- **No máximo 2 por área.** O código só tem buffers para as entradas `$1C`/`$1E`: o deslocamento é
  `(E - $1C) × $40` em `$7F:7C00-7FFF`. Passando de 2, ficam os de progressão (crest > Armor > vellum > talismã >
  potion).

**Conferência**: `tools\insanity_gfx_check.py SEED PASTA SAVESTATE` com `lua\gfx_test.lua`.
- Entra em cada área e cria o item parado (bit `$40`) ao lado do Firebrand, com as flags de "já tem" zeradas e a
  vida cheia.
- Compara:
  - tiles na VRAM × tile set decodificado;
  - paleta no slot × paletas de item;
  - pedaços do OAM em cima do item (tile e paleta).
- Seed 2: 22/23 ok. O Crawler tem o slot 5 com paleta de item só depois da lista do meio (a luta); o pedaço na
  tela já está certo.
- Limites do teste:
  - entra pela entrada 0, antes da lista do meio (item de chefe usa VRAM que os inimigos ocupam antes da luta);
  - sair da área 13 atrasa pelo evento da água (ela vai por último).

**200 seeds** (planejamento fora do emulador):

- **3º item na área (sem gráfico próprio)** — Itens: 267
- **Sem slot de paleta livre (cores erradas)** — Itens: 154
- **Bloco cheio, perde o brilho** — Itens: 38
- **Bloco cheio, comportamento original** — Itens: 23
- **Sem VRAM** — Itens: 9

**Etapa 2** (26/09, "faz tudo já"):
- **Código e dados no banco `$C1`** (tabela por área em `$C1:8000`), sem limite de espaço: acabaram as
  degradações por bloco cheio.
- **Até 6 itens com gráfico próprio por área** (`K = 6`):
  - entradas de sprite contadas de `$1E` para baixo, só as que a área não usa (usadas = 2 do Firebrand + fixos
    + lista);
  - `build_code(LAY)`: `OFF = ($1E - E) × $40`;
  - buffers em `$7F:E100-EE7F` (trabalho `E100`, quadros `E700`, animação `EA00`, paleta guardada `ED00`), região
    medida intocada.
- **Itens com o mesmo desenho na área dividem VRAM e paleta.**
- **Área apertada**: se algum item ficaria sem VRAM, a área é replanejada com todos só no desenho parado.
- **Sem slot de paleta livre** (decisão: o item fica com a cor certa):
  - o item pega o slot de menos donos (1-5);
  - ao gravar a paleta, a original é guardada (`ED00 + OFF/2`: 32 B + slot + marca `A5` + área);
  - `pal_restore` no `82:8752` (o "apagar objeto" de todo objeto) devolve a paleta quando o item some.
- O caminho do Fred continua igual byte a byte: `build_code()` padrão = mesmos 847 B, conferido.
- 200 seeds: 4.574 itens com gráfico próprio; 22 ainda sem VRAM (quase todos na área 13 com mais de 4 itens
  diferentes); 157 pegam slot emprestado; 113 dividem VRAM.
- **Conferido no emulador**:

  | Seed | Resultado |
  |---|---|
  | 2 | 22/23 (o Crawler tem a paleta só na luta) |
  | 24 | 21/22 (idem; 3 itens na área 13 e 2 paletas emprestadas devolvidas) |
  | 13 | 22/22 (2 crests com paleta emprestada, devolvida depois de pegar) |

- O teste recarrega o savestate antes de cada item. Sem isso, um teste contaminava o seguinte: na área 13 o OAM
  ficava vazio.

**Aviso**: a medição `wram_free` mostrou que o jogo também escreve em `$7F:7C00-7FFF`, onde o patch guarda quadros
e animação do item. O mais provável é que aconteça só na carga da área (o item nasce depois), mas isso não está
medido.

### 3.3 Falta

1. Crests do Arma 1/2/3 (Earth, Air, Time): quem as cria. A pista é o objeto `4F`, criado em `BE:E61D`, que vira
   `4E48`. É mais rápido medir no emulador (logar escrita de tipo nas vagas de objeto ao matar o Arma).
2. Confirmar que o `462E` (área 39) é a Fang, e que o "1 HP do castelo" do mapeamento é o sino da área 38.
3. Hippogriff: qual condição escolhe entre HP 02 (área 1) e recarga (área 20). Grewon/Flier: o subtipo decide.
4. ~~HP 05 × HP 0E~~ **resolvido 25/09** pelo índice no atributo: área 27 usa os registros 0-6 da lista `B6B5`
   (HP 0E = registro 1, 644,456), área 28 usa o registro 7 (HP 05, 436,136). A 59 (mapa gêmeo da 27) repete o HP 0E.
5. Quebráveis **sem item**, para a pool do Insanity:
   - potes: contados em `insanity_map.txt`;
   - estátuas/lápides/ossos `$E0`: contados por lista;
   - `$A0` e `$E0`: contados no mapa pelo editor (`DemonsCrest Editor/objects.py`; no visualizador, "quebráveis").
     `$E0` por área (quebráveis, não blocos): 4:1, 6:2, 7:3, 9:11, 27:7, 28:1, 29:5, 30:5, 33:3, 35:1, 44:3.
     `$A0` rotina 2 (estátuas, em blocos): 1:7, 4:7, 10:1, 14:1, 21:3, 22:3, 24:2, 31:2, 37:6, 41:3, 44:1, 50/51:1.

Depois disso, o desenho do rando:
- como um quebrável sem item passa a ter um;
- como os orbes de recarga entram na pool;
- a lógica de progressão, porque locais trancados por Buster/Time/Earth Crest e voo são requisito.

### 3.4.1 Dificuldade 1-5 e esferas (26/09, proposta do Neitan)

**Esfera** (`Logic.sweep`): a esfera 1 é o que dá para pegar sem nenhum item. A esfera N é o que abre com todos os
itens das esferas anteriores. A seed fecha quando uma rodada não abre mais nada e todos os checks foram pegos.

Com `-d 1..5` o gerador usa `fill_spheres`. Sem `-d`, usa o preenchimento antigo, que dá a seed 2 igual. O
`fill_spheres` monta esfera por esfera:
- cada rodada preenche **todas** as vagas que acabaram de abrir, então a rodada é a esfera do spoiler;
- a rodada coloca poucos itens-chave (`pick_keys`). A ordem de tentativa é 1 item, depois N HPs, depois pares. A
  preferência é pelos que abrem menos checks, para dar profundidade;
- o resto das vagas recebe itens sorteados com peso por dificuldade;
- a seed é refeita se não tiver **5 esferas ou mais** (`MIN_SPHERES`).

Itens fortes: Time Crest, Demon Fire, Fang, Armor, Air Crest.

- **Dif. 1** — Itens fortes: esferas 1-2; HP: mais nas esferas 1-2; HP removidos: 0; Go mode (castelo): vencer Flame Lord, Flier 1 e Belth
- **Dif. 2** — Itens fortes: esferas 2-3; HP: mais nas esferas 1-2; HP removidos: 0; Go mode (castelo): 5 vellum
- **Dif. 3** — Itens fortes: sem viés (moderada); HP: sem viés; HP removidos: 0; Go mode (castelo): 5 vellum
- **Dif. 4** — Itens fortes: só a partir da esfera 4; HP: menos nas esferas 1-3; HP removidos: 5 (vira 3×20G + 2×Recarga); Go mode (castelo): 5 vellum + 5 potion
- **Dif. 5** — Itens fortes: o mais tarde possível; HP: sem viés; HP removidos: 10 (vira 5×20G + 5×Recarga); Go mode (castelo): todos os itens de verdade fora do castelo (20G e recarga não contam)

Lote de 200 seeds por dificuldade: todas completáveis, todas com 5 esferas ou mais.

- **Dif. 1** — Esferas (seeds): 5: 200; Itens fortes, média por esfera: 4,9 na esfera 1; HP, média por esfera: 10 na 1, 5,8 na 2
- **Dif. 2** — Esferas (seeds): 5: 123, 6: 77; Itens fortes, média por esfera: 4,8 na esfera 2; HP, média por esfera: 11,9 na 1, 3,1 na 2
- **Dif. 3** — Esferas (seeds): 5-8; Itens fortes, média por esfera: espalhados, com mais nas esferas 1-3; HP, média por esfera: espalhados
- **Dif. 4** — Esferas (seeds): 5-9; Itens fortes, média por esfera: 3,9 na esfera 4, nenhum antes; HP, média por esfera: cerca de 2 por esfera
- **Dif. 5** — Esferas (seeds): 5-11; Itens fortes, média por esfera: 2 no castelo (a última esfera) e 3 entre as esferas 4 e 8; HP, média por esfera: poucos

Limite da dificuldade 5: o castelo só tem 2 checks, então só 2 dos 5 fortes cabem na última esfera. Os outros 3
ficam nas esferas anteriores mais tardias.

**Ajustes do Neitan, 26/09**. O código fica em `strong_targets` e `accept`, e as regras valem para a seed pronta:
- **dif. 1**: cada item forte ganha uma esfera-alvo sorteada entre 1 e 3.
  - Nenhum passa da esfera 3.
  - Média por esfera: 1,4 / 1,8 / 1,8.
  - A Time Crest cai menos na esfera 1, com 18% das seeds contra cerca de 40% na 2 e na 3. Com ela na esfera 1,
    a seed abre demais e perde as 5 esferas.
- **dif. 3** (até 02/10): exatamente 5 esferas, 1 item forte em cada, Time Crest nunca nas esferas 1 e 2. Trocada em
  02/10 (ver o histórico): o "exatamente 5" era interpretação minha (5 fortes, 1 por esfera), não pedido do Neitan.
- **dif. 5**: Time Crest e Fang sempre no castelo (`CASTLE_FIXED`). Os outros 3 fortes ficam o mais tarde possível.
- **Regra dura, todas as dificuldades e também o preenchimento antigo**: Water Crest nunca no Holothurion
  (`FORBIDDEN`). O requisito dele já exige Water, então isso nunca aconteceu; a regra fica explícita.
- Conferido em 1000 seeds de cada modo:
  - 0 casos de Water no Holothurion;
  - 0 casos de item preso atrás de si mesmo. Treze checks exigem a Earth em todas as alternativas, e a Earth nunca
    caiu em nenhum deles. O Buster sempre tem a Time como alternativa, e a lógica de alcance impede os dois
    trancados um pelo outro.

Os spoilers de exemplo (seed 1 de cada dificuldade) estão em `logs\dificuldades\`.

**Modos (27/09)**. Ficam em `MODES` e `shuffled()`, com `-m limitado|classico|extra`. Um local fora do sorteio
do modo fica com o item original e entra na lógica normalmente. No spoiler ele aparece como `[fora do sorteio]`.
- **Limitado**: sorteia crests, potions, vellums e talismãs (23 locais). Os 16 HPs, os 11 potes de 20G e as 8
  recargas ficam no lugar.
- **Clássico**: + HP (39 locais).
- **Clássico Extra**: os 58 locais.
- **Insano**: não liga. Precisa das localizações novas (quebráveis sem item, "segurados" pelo Neitan) e da lógica
  delas, que é o Neitan quem monta.
- **HP removido (dif. 4/5)**: no modo em que o HP não é sorteado (Limitado), o HP removido vira 20G/Recarga num
  local de HP sorteado.
- **Dif. 5 no Limitado**: o Sino HP 10 fica fora do sorteio, então o castelo só tem uma vaga sorteável, a da Fang.
  A Time Crest vai nela, e a Fang fica o mais tarde possível.
- **Lote**: 100 seeds em cada uma das 15 combinações (3 modos × 5 dificuldades). Todas completáveis, todas com 5
  esferas ou mais.

**Go Mode escolhido pelo jogador (27/09, substitui o go mode por dificuldade)**. Fica em `GO_MODES` e `GO_ITEMS`,
com `-g` na linha de comando e a sessão Go Mode na janela. As colunas "Go mode" das tabelas acima valem só até
esta data.
- **5 Vellums** (padrão): o código original validado (`85:A1EE`, `$1E56 & 1F`).
- **All Bosses**: os 15 chefes (`BOSSES`). O Trio the Pago fica de fora, porque é minigame (decisão do Neitan).
  - Na ROM: `LOC & DFFF`. Dois bits novos: `4000` Flier 2 (área 34, ligado pelo vigia) e `8000`
    Hippogriff 2.
  - A área do Hippogriff 2 não encerra, então o bit dele é ligado no desvio `82:99A0`, quando o drop da área 20
    nasce.
- **All 4 Main Crests** (as de transformação: Earth, Air, Water, Time): `$1E51 & F0`.
- **All HP**: a flag de cada HP fora do castelo (`$1E54`). Nas dificuldades 4 e 5 contam só os que sobraram.
- **Regras**:
  - Item exigido pelo Go Mode nunca vai para o castelo.
  - O preenchimento reserva itens que não são do Go Mode para as vagas do castelo que ainda vão abrir.
  - Na dif. 5, a Time/Fang no castelo cede ao Go Mode. Com "4 crests", a Time não vai; com "All HP", o Sino HP
    10 fica fora da conta.
- **Dificuldade** agora cuida só de esferas, itens fortes, HP por esfera e HP removido. A Potion deixou de ser
  progressão (era só pelo go mode da dif. 4).
- **Lote**: 30 seeds × 60 combinações (4 Go Modes × 3 modos × 5 dificuldades). Todas completáveis, com 5 esferas
  ou mais e nenhum item do Go Mode no castelo.
- **Emulador** (`tools\castle_check.py` por Go Mode, 27/09): vellum, bosses (`LOC & DFFF`), crests e hp. Com tudo ligado dá `7F`; faltando 1 bit, `3F`. Resultado 8/8. O bit `8000` do Hippogriff 2 (desvio `82:99A0`) foi conferido só no código, não em luta.
- **Janela**: a sessão Go Mode (4 opções, descrição no mouse). Nos "Extras", **Objetivos** e **Anti-Softlock
  prevent** aparecem travados (em breve).

**Castelo na ROM (27/09)**. Fica em `insanity_rom.castle_req` e `progress(castle=...)`.
- Dif. 2/3 (e o preenchimento antigo): continua o código validado, com os 5 vellums.
- Dif. 1/4/5: o `85:A1EE` chama uma rotina em `$C0` que confere uma lista (endereço, máscara) e devolve Y = 0
  (`7F`, com castelo) ou 1 (`3F`):
  - dif. 1: `LOC & 0034` (Belth, Flame Lord, Flier 1);
  - dif. 4: `$1E56 & 03FF`;
  - dif. 5: a flag de cada item de verdade fora do castelo. As tabelas do jogo foram conferidas na ROM:
    - vellum/potion: `$81:F4CC` → `$1E56`;
    - talismã: `$81:F4D2` → `$1E53`, bits 3-7 (Crown `08` … Hand `80`);
    - crest: `$81:D730` → `$1E51`;
    - HP de flag n → `$1E54`, bit n-1.
- **Conferido no emulador** (`tools\castle_check.py` + `lua\castle_test.lua`):
  - o teste força o fim da área 3 (`$81:97DA[3] = F0` → mapa) a partir do savestate da seed 2;
  - lê a máscara no `STA $37` de `85:AEF5`. O `$37` é da página direta do objeto do mapa, não `$0037`;
  - resultado: dif. 1/3/4/5, com "tudo ligado" = `7F` e "falta 1 bit" = `3F`, 13/13 ok. A dif. 5 também passou
    em uma 2ª seed.
  - Um bug achado pelo teste: o salto da rotina com várias máscaras contava 11 bytes por conferência em vez de 12.
    O jogo travava (tela preta). Corrigido.

### 3.4.3 Dificuldade 5 nova e Anti-Softlock (28/09, Neitan)

- **Dif. 5**: não tira mais os 10 HP. Sorteia de **2 a 4** entre Air Crest, Time Crest, Tornado e Demon Fire para
  sair da pool, e eles viram 20G/Recarga (`REMOVABLE`, `pick_removed`, sorteio a cada tentativa de preenchimento).
  - O objetivo "All 4 Main Crests" é **bloqueado** com a dif. 5: na janela ele fica cinza, e na linha de comando dá
    erro.
  - Time/Fang no castelo só quando estão no jogo.
- **Anti-Softlock** (opção dos Extras). Os patches de mapa vêm do editor do Neitan, em `DCOR\patch\area_0NN.dcmapa.json`:
  - **27**: entra sempre que a opção está ligada. Tela 135 (áreas 27, 59 e 70): quem entra sem a Earth Crest pode
    morrer para sair.
  - **29** (telas 39 e 48) e **38** (telas 162 e 163): só entram com a opção ligada **e** Air + Tornado fora da
    pool. Aí, na lógica, a **Claw vale onde o requisito pede Air Crest ou Tornado** (`CLAW_SUB`,
    `Logic.term_ok`), inclusive o castelo do Phalanx.
  - A janela liga a opção sozinha ao escolher a dif. 5. Desligar com a dif. 5 mostra o aviso do Neitan ("pode
    tornar a seed impossível… por conta e risco") e deixa desligar.
  - Com a opção desligada o gerador nunca tira Air e Tornado juntos, porque a seed não fecharia sem os mapas.
- **Gravação** (`insanity_rom.apply_map_patches`):
  - Cada arquivo do editor traz também as outras áreas que estavam abertas nele, então só a área pedida entra.
  - Entra só o desenho (telas e blocos novos). Objetos, eventos, gráficos, colisão e animação do arquivo ficam de
    fora.
  - Os patches entram antes do rando, na ROM de 4 MB.
  - O aplicador é uma cópia de `DemonsCrest Editor/mapa.py` + `chefes.py` na `data`.
- **Conferido**:
  - 40 seeds × 18 combinações da dif. 5 (com e sem o anti-softlock, 3 modos, objetivos vellum/bosses/hp): 0 falhas.
  - Com o anti-softlock, 2/3/4 removidos. Air + Tornado juntos em cerca de metade, sempre com os patches 29/38.
  - Sem ele, nunca juntos.
  - Emulador (`lua\area_shot.lua`): áreas 27, 29 e 38 carregam com e sem patch.
  - As 5 telas gravadas batem com os arquivos, bloco a bloco.

### 3.4.2 Vida dos chefes (pesquisa, 27/09; para a dif. 5 trocar "10 HP a menos" por chefe mais forte)

**Mecanismo (medido no Somulo 1)**:
- A vida é o byte `$36` do objeto. `FF` funciona como "não apanha"; o Somulo 1 fica em `FF` fora da fase
  vulnerável.
- Em `82:8901` o jogo faz `vida -= $81:[$2E + índice do tiro]`: cada chefe tem uma tabela de dano, e o dano depende
  do tipo de tiro. O dano dobra quando `$0014` está ligado (forma `$1066 = 2E`).
- A luta do Somulo acaba quando a vida chega a **1**, então tiros = vida − 1.

**Estático (padrão `LDA #n / STA $36` perto do código do objeto; não confirmado em luta)**:

- **Somulo 1 (área 0, obj. `33`)** — Onde: `83:8A3C`; Vida: 7, agora 4 (**medido**); Tabela de dano: `D959`, tudo 1
- **Somulo 2, cabeça (área 17, obj. `53`)** — Onde: `83:97BD`; Vida: 4; Tabela de dano: `D959`, tudo 1
- **Grewon (obj. `13`)** — Onde: `BE:980B`; Vida: 64; Tabela de dano: `CF81`: 4,1,0,1,6,2,1,0,2,1,10,10
- **Hippogriff (obj. `09`)** — Onde: `82:9983`; Vida: 64; Tabela de dano: não achada
- **Holothurion (obj. `6F`)** — Onde: `83:D37C`; Vida: 128; Tabela de dano: `E439` (zeros nos 12 primeiros: índice diferente?)
- **Flame Lord? (obj. `25`/`28`)** — Onde: `82:CBFA` / `82:CC72`; Vida: 26 / 148; Tabela de dano: não achada
- **Castelo (obj. `5C`, área 43; obj. `AE`, áreas 38/40)** — Onde: `BE:B3C0` / `BE:FB84`; Vida: 100 / 100; Tabela de dano: não achada

Belth, Ovnunu, Skulla, Flier, Crawler e Arma não apareceram nesse padrão. Eles usam outra forma de gravar a vida
(tabela, 16 bits ou valor calculado).

**Medição de verdade**: `lua\boss_hp_log.lua` é passivo; o Neitan joga normalmente. A cada acerto ele grava:
- área, alvo (tipo/subtipo), estado;
- vida antes e dano;
- a tabela `$2E` e o índice do tiro, e qual tiro acertou;
- as crests e a forma.

Também anota a **fase** (vida que muda sem tiro, em área de chefe) e quando o alvo sai da lista.
- Ao sair de uma área de chefe, grava um **resumo** por alvo: vidas de fase, maior vida, nº de acertos e dano por tiro (`tipo:sub/índice`).
- Na tela do jogo mostra o nome do chefe, a vida (antes → depois), o dano, o tiro e os acertos.
- Saídas: `logs\boss_hp.txt` (tudo) e `logs\boss_hp_resumo.txt` (só os resumos). As duas acrescentam, nunca apagam.
- Conferido no emulador (jogo novo, Somulo 1): 3 acertos com dano 1, tiro `40:00` índice 0; fases `FF`; SAIU e resumo certos. O HUD não dá para conferir por print, porque o print do BizHawk não pega o desenho da Lua.

**Cuidados para a dif. 5**:
- Vida é 1 byte, e `FF` é "não apanha", então o teto é `FE`.
- Alguns chefes têm várias fases, cada uma com a sua vida.
- O limiar de morte (0 ou 1) pode mudar por chefe.

**Medido pelo Neitan jogando (27/09, `boss_hp_log.lua`) × tópico "Boss Stats" do GameFAQs (The_Admiral, 2009;
gamefaqs.gamespot.com/boards/588275-demons-crest/48868077)**. A vida é a inicial de cada forma.

- **Somulo 1** — Objeto (área): `33` (0); Vida medida: 7 → 4 no DCOR; GameFAQs: —
- **Somulo 2, cabeça** — Objeto (área): `53` (17); Vida medida: 4; GameFAQs: —
- **Hippogriff 1 / 2 / 3** — Objeto (área): `09` (1 / 20 / 37); Vida medida: 16 / 24 / 64; GameFAQs: 16 / 24 / 64
- **Arma 1 / 2 / 3** — Objeto (área): `A5:00/02/04` (3 / 23 / 36); Vida medida: 16 / 32 / 72; GameFAQs: 16 / 32 / 72
- **Chefe Belth** — Objeto (área): `74` (9); Vida medida: 32; GameFAQs: 32
- **Ovnunu** — Objeto (área): ? (8/60); Vida medida: não pego; GameFAQs: olhos 3, corpo 10
- **Flame Lord** — Objeto (área): `28` (14/50); Vida medida: 26 no chão, 20 voando; GameFAQs: 26 / 20
- **Skulla ("Scula")** — Objeto (área): `7B` + `7F` (13); Vida medida: 24 (lançando), 10 (rolando); GameFAQs: 24 / 10
- **Flier 1 / 2** — Objeto (área): `82:00/01` (19 / 34); Vida medida: 24 / 48; GameFAQs: 24 / 48
- **Crawler** — Objeto (área): `18:05` (59); Vida medida: 36; GameFAQs: 36
- **Holothurion** — Objeto (área): `92` (26); Vida medida: 72; GameFAQs: 72
- **Grewon 1 / 2** — Objeto (área): `13:00/02` (30 / 41); Vida medida: 64 / 64; GameFAQs: 64 / 64
- **Phalanx 1 / 2 / 3** — Objeto (área): castelo; Vida medida: não pego; GameFAQs: 50 / 127 (Spherix: 128) / 128
- **Dark Demon** — Objeto (área): secreto; Vida medida: não pego; GameFAQs: 200

Onde a medição e o tópico se cruzam, 17 de 17 valores batem.

- **Dano por arma** (tópico, por chefe): Fire 1 (Grewon 4, Arma 3 3, Phalanx 2), Buster 1, Claw 1, Demon Fire 3
  (Grewon, Arma 3 e Phalanx 6), Earth chão 2 / ar 1, Aerial 2-4, Tidal 1-3, Legendary e Ultimate 5 (Grewon e
  Arma 3 10).
- **Tiros no log**: `40` = Fire (índice 0), `4A` = Demon Fire (4), `4B` = Earth (8 chão / 9 ar), `4C` = Tidal (5),
  `4D` = Aerial (7), `4E` = Legendary (10).
- **Bit `$80` da vida** = piscando depois de apanhar. O acerto nesse estado não desconta (`82:88EC`). Por isso o
  Hippogriff 2 levou uns 50 acertos para perder 24 de vida. Depois de 27/09 o `boss_hp_log.lua` separa esse bit.
- **Fang equipada dobra o dano**: com ela o `$0014` fica em `FF`. No Flier 1 e na Skulla caiu 2 por tiro com a
  tabela dizendo 1; no Grewon, 12 com a tabela em 6. Só ter a Fang no inventário não dobra: no Hippogriff 2 ela
  estava no inventário e o `$0014` ficou em `00`.
- **Fonte oficial (Neitan, 28/09)**: os dados do tópico estão corretos e são a referência de vida e de dano por
  crest de cada chefe. Não precisa medir Ovnunu, Phalanx e Dark Demon.
- **Falta, para a dif. 5**: o endereço na ROM de cada vida inicial. Os conhecidos estão na tabela estática acima;
  o resto vem pelo objeto e pelo estado da medição.

### 3.9 Pesquisa: spells (29/09, pedido do Asvel)
Medido no BizHawk (`lua\dce_medir_spells.lua` área 1, `dce_medir_spells28.lua` área 28 com 4 potes; logs em
`DemonsCrest Editor\logs\spells*.txt` + prints `spell*_*.png`). O Lua cria o spell no slot `$1D00` como o jogo.

- **Onde fica:** vellums `$1E30-$1E34` e poções `$1E35-$1E39` guardam o id (a loja grava em `BC:A618` a partir de
  `$81:E68D`). Usar = `80:DD20`: tipo do objeto = `$81:B458[id]` no slot fixo `$1D00` (`$1D00 = $11`, posição do
  Firebrand); ids `$10`/`$12` (Mercury/Sulfur) não funcionam nas áreas 42, 43 e 45.
- **Mapa id → spell** (ordem das mensagens da loja, conferida pelo comportamento e pelas tabelas de dano):
  `02` Hold = objeto `A0` (`BE:A795`), `04` Death = `A1` (`BE:A92C`), `06` Shock = `A2` (`BE:AC20`), `08` Imp = `A3`
  (`BE:ACE4`), `0A` Shadow = `A4` (`BE:B011`). Poções: `0C` Herb, `0E` Ginseng, `10` Mercury, `12` Sulfur, `14`
  Elixir (sem objeto).
- **Como o spell acerta:** na colisão de todo inimigo (`82:884A`/`82:8A74`), depois dos tiros: spell vivo, caixa de
  dano ligada (`$1D37 ≠ 0`) e `$37 do inimigo & $1D2E` (máscara do spell) → `82:8958`. Dano = `$81:[tabela do
  inimigo ($2E) + $1D36]` (índice do spell; 0 = dano 1). Com `$1D07` ligado, cada inimigo só leva 1 vez por spell.
- **`$37` do inimigo = de quais spells ele leva dano** (1 bit por spell): `01` Hold, `02` Death, `04` Shock, `08` Imp,
  `10` Shadow. Máscara e índice de cada spell: Death `02`/`0E`, Shock `04`/0 (dano 1), Imp `08`/`0C`, Shadow `10`/`0D`.
  Colunas nas tabelas de chefe: `0C` Imp = 1 ou 0, `0D` Shadow = 2 ou 4, `0E` Death = 7 (Phalanx 3 = 3).
- **Todo spell congela o jogo** enquanto anima: `BE:B17F` liga `$FF` e marca os objetos que já existiam
  (`$2C++`); `80:DAD1` (Firebrand) e `82:8611` (objetos) param com `$FF`. Medido (quadros com `$FF`): Hold 30, Shock
  79, Imp 167, Shadow 278, Death 343.
- **Imp:** tira 1 de gold a cada 32 quadros (`BE:AD31`: `$73 & 1F = 0` → `DEC $1063`; ~1,9 G/s), medido (50 → 37 em
  ~400 quadros). Com gold 0 ele vai embora (estado `0E`; também se chegar com 0). A cada 64 quadros procura o
  inimigo mais próximo **na tela da câmera** e com `$37 & 08` (`BE:AE3F`). Dura enquanto houver gold.
- **Death:** caixa de dano ligada 1 quadro (medido); caixa `$81:D816` = ±256 px. Ovnunu não leva dano porque grava
  `$37 = $18` (`83:C33B`, `83:C98E`: só Imp e Shadow), mas a tabela dele tem **12** na coluna do Death →
  provável descuido; trocar pra `$1A` liga.
- **Shock:** depois de cair solta o congelamento e treme 255 quadros; caixa ligada a cada 8 quadros (31 vezes,
  medido), ±256 px (a tela). **Já quebra potes no original:** o pote (`57`, `84:C3EA`) nasce com `$37 = 04` e vida 1
  — medido na área 28: 4 potes → 0. Death e Shadow não quebram (pote sem o bit deles).
- **Shadow:** cai do alto, segue o Firebrand por 3 ciclos com o jogo congelado, solta e liga a caixa de dano 1
  quadro (2 ou 4 de dano), some. **Não existe redução de dano** (nenhuma leitura do slot do spell no dano do
  Firebrand). Código morto `BE:B0CA` (nenhuma chamada): paralisa por 240 quadros (bit `$20` no estado, `$2C = F0`)
  os inimigos com `$37 & 10` a ±64 px (X) / ±80 px (Y) — escrito como estado do Shadow (termina avançando `$05`),
  fora da tabela `BE:B063` [`B070`, `B096`, `B069`]. É a "proteção" da descrição que não entrou. Ligar = gancho
  antes do `B069` (fim).
- **Hold:** 480 quadros, 5 orbes (`000C`) girando em volta do Firebrand, tela escurecida; no fim (`BE:A8FB`) marca
  os inimigos com `$37 & 01` (bit `$20`, `$2C = 2`). Falta medir com inimigo na tela.
- **No editor (29/09):** aba Spells do DemonsCrest Editor edita tudo isso (parâmetros, paralisia do Shadow,
  máscara `$37` e dano por tipo, com aviso do Ovnunu); detalhes na DOCUMENTACAO do editor, seção Spells. Correção:
  o Hold chama `BE:A8FB` todo quadro (estado 4) — os inimigos com `$37 & 01` ficam parados enquanto ele dura (480).

### 3.8 Pesquisa: Fire Crest sem uso, crest inicial e soco como item (29/09, não implementado)
Pedido do Neitan: pôr na pool o asset da Fire Crest que o jogo nunca usa, começar o jogo com uma crest qualquer e ver se
o soco pode virar item. Medido no BizHawk (`lua\dce_medir_tiro_soco.lua`, `_soco2.lua`, `dce_medir_tiro3.lua`; logs em
`DemonsCrest Editor\logs\tiro_soco*.txt`, `tiro3.txt`).

- **Asset sem uso:** crest = objeto `48`; `$81:D744` + subtipo×2 = [sprite][deslocamento de animação]. Fire Crest =
  sprite `4F` com +02/+04/+06/+08 (Buster/Tornado/Claw/Demon Fire); a animação **+00 do sprite `4F` existe e nenhum
  subtipo usa**. O menu de crests (`84:9012`) mostra a Fire Crest inteira quando `$1E51 & 0F = 0F`.
  Tabelas coladas: `$81:D730` (bit do item, 9 entradas até `0100`), `$81:D744` (8 × 2 B) e logo depois `$81:D754`
  (ponteiros das mensagens, banco `$BE`) — subtipo novo não cabe no lugar, precisa de gancho em `82:EA02`.
- **Tiro:** botão Y. `80:EFD6-EFDE`: tipo = `$81:B446[$1054]` (`$1054` = arma escolhida: 0 = Fire `40`, 2 Buster
  `43`, 4 Tornado `44`, 6 Claw `45`, 8 Demon Fire `4A`; depois Earth `4B`, Aerial `4D`, Tidal `4C`) → `80:F222` cria
  nos slots fixos `$1080-$12B0` (7 tiros). O objeto `40` é o próprio tiro (`82:E3C8`; ele cria o rastro `0240`).
  Tiro básico como item = gancho em `80:EFD6`: com `$1054 = 0` e sem o item, não atira.
- **Soco = Head Butt** (nome do jogo, fala da loja do Trio the Pago; usado a partir de 29/09): botão A, no chão. `80:F181`: `$5E` (botão) e `$03 & 4` (no chão) → `JMP 80:E157` → estado `$0A`,
  animação `$10` (medido: A grava o estado em `80:E15B`, vindo de `80:F1BB`). No estado `$0A`, com o contador da
  animação em `$10`, `80:E54A` chama `80:F30E` = quebra os quebráveis `$A0` (estátuas). Também entra no estado
  `$0A` por `80:E517` (estado `$12`). Soco como item = gancho de 4 bytes em `80:F1B3` (`LDA $03 / AND #$04` → JSL
  que também testa o item) + o mesmo em `80:E504`. A quebra da estátua não apareceu no teste (Firebrand parado em
  X=72, a estátua em 80-95): falta conferir a distância.
- **Crest inicial:** jogo novo zera os itens em `84:88E8-88FA` (`STZ $1E51`…); trocar por `LDA #crest / STA $1E51`
  e, se a crest for arma de fogo, `$1054` = índice dela (senão o tiro sai como Fire).
- **Onde guardar os itens novos:** NÃO usar `$1E52` bits 1-7: o final secreto (`83:80C7`) exige `$1E52 = FE`. Usar RAM
  medida como livre (`$7E:1F80+`, onde já ficam marcador e `LOC`). A senha não guarda (fora do escopo, 26/09).
- **Falta decidir:** o que a Fire Crest dá (o tiro básico, ou as 4 peças juntas), a mensagem dela (texto no banco
  `$BE`, ponteiro de 16 bits), gráfico do soco (não existe; reusar outro), lógica (sem tiro e sem soco o jogador pode
  ficar sem ataque; estátuas `$A0` passam a exigir o soco).

### 3.7 DCOR — executável com janela (26/09)

Nome: **DCOR - Demon's Crest Open Randomizer**. A pasta de entrega é `DCOR - Demons Crest Open Randomizer\`. A fonte fica em
`tools\dcor_gui.py` (Tkinter) e gera a ROM por `insanity_rando.build_seed(seed, rom_original)`, a mesma função da
linha de comando. A seed 2 sai byte a byte igual à da linha de comando.

A janela tem:
- **Seed**: o nome de 4 palavras do jogo, como no "MFOR - Adam Arachnus Dachora Space".
  - As palavras vêm de `WORDS`: chefes, crests, itens, talismãs, Firebrand, lugares.
  - Em branco (ou pelo botão do dado), o nome é sorteado.
  - O número interno da seed é o hash SHA-1 do nome. Maiúsculas e espaços extras não mudam o resultado, e o mesmo
    nome com as mesmas opções refaz a mesma ROM.
- **Dificuldade 1-5** (barra, padrão 3): afeta todos os modos. A descrição do nível aparece no mouse e no painel de info.
- **modos**, com a descrição no mouse e no painel de info. Os nomes são provisórios:
  - Limitado: só crests, potion, vellums e talismãs; HP ficam vanilla;
  - Clássico: + HP;
  - Clássico Extra: + recarga de HP em chefes e potes, + potes de 20G;
  - Insano: + todos os potes, gárgulas, quebráveis de Earth Crest, janelas da fase 2 e blocos da fase 6.
  - Limitado, Clássico e Clássico Extra funcionam desde 27/09. No Insano o botão Gerar fica travado (§3.4.1).

**Pastas fixas ao lado do exe (26/09)**. Não há mais escolha de ROM nem de pasta de saída:
- `ROM\`: o gerador usa a primeira `.sfc`/`.smc` dali que seja a `Demon's Crest (USA)` (SHA-1 `743d60ee…`,
  aceita cabeçalho de copiadora). A janela mostra qual ROM achou;
- `Seed\DemonRando - Nome.sfc`;
- `Spoiler\DemonRando - Nome.txt`, com o mesmo nome. A 1ª linha traz o modo, a dificuldade e a seed interna.

O exe cria as 3 pastas se faltarem. O modo e a dificuldade escolhidos ficam em `dcor_config.json`.

- **Visual (26/09, modelo do Neitan, sem a imagem de fundo)**:
  - tema escuro, com cartões arredondados desenhados em Canvas (Tkinter puro, sem dependência);
  - ícones desenhados: documento, pasta, dado;
  - barra de dificuldade segmentada;
  - modos em linhas selecionáveis, e o painel de info mostra a descrição do modo escolhido;
  - botão de sortear a seed;
  - barra de título escura (DWM).
- **Ícone**: vem do `icone.png` da pasta do DCOR. O `tools\make_dcor_icon.py` gera o `tools\dcor.ico` em pixel art
  nítido, que vai no exe e na janela.
- **Código fora do exe (27/09, pedido do Neitan; ele pretende abrir o código no git)**:
  - O executável (`Demon's Crest Open Randomizer.exe`, nome do Neitan desde 27/09; antes `DCOR.exe`) é só o lançador (`data\dcor_launcher.py`, com o Python embutido). Ele põe `data\` no caminho
    e abre o `dcor_gui` de lá.
  - **Todo o código do rando fica em `DCOR - Demons Crest Open Randomizer\data\`**, que é a fonte oficial:
    `dcor_gui`, `insanity_rando`, `insanity_rom`, `insanity_gfx`, `item_gfx`, `rom_tables`,
    `palettes`, `graphics`, `asm65816`, `rom_expand` (cópia de `DemonsCrest Editor/ferramentas/rom_expand`),
    `mapa`/`chefes` (cópias do editor) e `dcor.ico`. Desde 28/09 sem nada do rando do Fred (ver histórico).
  - Mexer num `.py` da `data` vale na próxima vez que o exe abrir, sem compilar. Conferido: mudei a versão só
    no `.py` e a ROM gerada pelo exe veio com ela.
  - Só precisa compilar de novo se mudar o lançador, ou se o código passar a usar um módulo da biblioteca padrão
    que o lançador ainda não importa (a lista fica no lançador).
  - Se der erro ao abrir, ele aparece numa janela e em `dcor_erro.txt`.
- **Sem o exe**: `python data\dcor_gui.py`. Linha de comando: `python data\insanity_rando.py -m MODO -d DIF -s N --rom`.
  Sem caminho, o `--rom` usa a pasta `ROM` do DCOR.
- **Build**: `data\build_dcor.ps1` (PyInstaller num venv `.venv_dcor`, instalado com a autorização do Neitan;
  outro venv pela variável `DCOR_VENV`). O ícone vem de `data\make_dcor_icon.py`.
- `tools\` ficou só com o que é de desenvolvimento, e tudo ali importa de `data`: conferências no emulador
  (`castle_check`, `insanity_gfx_check`), `insanity_map`, `dis65816` e o caminho antigo do Fred
  (`fix_rom`, `fix_duplicate_sprite`).
- **Sem janela**: `DCOR.exe --seed "Nome Da Seed" [--modo limitado|classico|extra] [--dif 1-5] [--home PASTA]`,
  para conferência. Grava em `Seed`/`Spoiler` da pasta.

---

## 4. Histórico

### 03/10 (0.3.1)

- **Spoiler mais limpo** (Neitan: quem só joga não conhece o número das áreas): cada check mostra a fase (`Stage 1` a `Stage 6`, `Castle` = castelo do Phalanx, `Minigame` = Trio the Pago; `STAGE_AREAS`/`stage` em `insanity_rando.py`, fases como na lógica V4, área 50 = Fase 3) no lugar de "area N", e sai o id do item. A linha do Skip Somulo diz "Stage 1". As seeds não mudam. Pendente: nomes dos potes que ainda têm "area N" no nome (17 checks).
- **Nível da lógica independente da Dificuldade** (guia Avançado, Neitan): a Dificuldade 1-5 não mexe mais no Nível da lógica, e mudar o Nível não troca a Dificuldade pra Custom (só o preset .json). Dá pra Dificuldade 1 com Nível 5.

### 02/10

- **Versão 0.3** (Neitan): o que vinha sendo a 0.2.3 sai como 0.3 (VERSION, README, exe e zip).
- **Lógica V4** (Neitan, `lógica_demonRando_V4.md`): os requisitos citam capacidades (`CAN` em `insanity_rando.py`: canFly, canBreakeSatue, canHeadbutt, canSwim, canBreakeblocks, canBreakgroundpot, canVerticalClimb, canLight, canSpikegrabe, canWaterRun1, canWaterRun2, canHeavyWaterRun), que o `parse` expande em itens/HP; o resto da lógica não muda. `/` = ou, `,` = e. Piso numérico mantido: as capacidades de correr na água têm piso próprio (`CAN_FLOOR`: canWaterRun1 desde a 1, canWaterRun2 a partir da 3, canHeavyWaterRun a partir da 4); as outras valem em toda dificuldade. canFly e canHeadbutt sem Claw de propósito (não conflitar com canVerticalClimb). Sem crest inicial, a Fire Crest conta como tida (`base_have`). Os locais novos do modo Insano da V4 ficam de fora por enquanto.
  - Mudanças nos checks atuais: Water Crest passa a quebrar bloco (HP 07, Potion 10, Pote Vellum 02, Pote HP 08); Claw entra no Sino HP 10 e no Fang; Arma 2, Flier 2 e Arma 3 sem 10+ HP; Hippogriff 1 pede canHeadbutt; Crawler só Earth (sem 8+ HP); água sem Water Crest só com Armor, 10 HP + Armor, Time Crest ou 15 HP + Armor + Time (saem as alternativas só com HP e as de Time + poucos HP).
  - 60 seeds por dificuldade, com e sem crest inicial: 0 falhas e 0 checks inalcançáveis nas 5 (`testes\v4_check.py`). V3 guardada em `testes\backup\insanity_rando_V3.py`.
- **Dificuldade 3 sem teto de esferas** (Neitan): era "exatamente 5 esferas, 1 item forte em cada" (minha leitura de "pelo menos 1 item forte em cada esfera" com 5 itens fortes). Agora: no mínimo 5 esferas e nenhum item forte nas esferas 1 e 2; da 3 em diante eles caem com o peso de qualquer item, sem esfera-alvo (`strong_weight`, `accept`). 1700 seeds (V4, Clássico Extra, 5 Vellums): de 5 a 11 esferas, média 7,0 (antes sempre 5); itens fortes na esfera 3: 25%, 4: 27%, 5: 24%, 6: 14%, 7: 7%, 8 ou mais: 3,5%. A Time Crest puxa mais pra 3 e 4. Com crest inicial também fecha (0 falhas). Dif. 1: 5 a 7 esferas (média 6,0); dif. 2: 5 a 8 (média 6,1) (`testes\esferas.py`, `testes\fortes_d3.py`).
- **Guia Avançado gerando** (Neitan). Gerador (`insanity_rando.py`): o modo pode ser um conjunto de itens originais (`POOL_CATS`, `pool_mode`); `Logic` ganhou `level` (piso da lógica, separado da dificuldade), `hp_removed`, `remove_span` (faixa da remoção), crest inicial fixa (`startcrest` = nome), `soft_cap` (o teto da 1ª esfera cede quando não sobra enchimento) e `min_spheres`; as regras de itens fortes e o castelo fixo da dif. 5 olham só os itens que estão na pool. A guia Simples gera exatamente as mesmas seeds de antes (513 combinações conferidas pelo hash do spoiler, `testes\simples_ref.py`).
  - Janela (`dcor_gui.py`, `adv_resolve`): Densidade 0-100 vira a "dificuldade" 1-5 dos itens fortes/HP (0-19 = 1 ... 80-100 = 5); campo novo Nível da lógica (o piso, Neitan); Anti-Softlock Sim/Não (novo, Neitan); HP Sparse 6-10, Medium 11-15, Full 16 (Neitan); remoção Nenhuma/2/3/4/Rando (2-4). "Rando" é sorteado pela seed (mesmo nome, mesmo resultado); Pool Rando que não fecha sorteia outra pool (até 20). Spoiler com cabeçalho do que saiu.
  - Ainda sem ROM, travados "(em breve)" na lista: Acessibilidade Vanilla/Rando (hoje o mapa já abre as 6 fases = All Stages) e Head Butt Sim/Rando.
  - Travas: crest inicial, remoção e objetivos All Bosses / All 4 Main Crests prendem as Crests na pool (sem as crests sorteadas o castelo abriria na 3ª esfera); remoção trava o objetivo 4 crests; remoção de 4 exige Anti-Softlock (Air e Tornado sempre fora: só a Claw nas áreas 29/38).
  - Mínimo de esferas no Avançado: 4 (Neitan: com pool pequena o jogo fica perto do original, que tem 4; menos que 4 nunca). Testei antes contar o castelo como esfera própria: resolve as pools com Crests, mas sem Crests o castelo já é a 4ª sozinho.
  - Teste (`testes\adv_matrix.py`): as 127 pools x 3 níveis/densidades + 1500 configurações sorteadas + 12 ROMs gravadas: 1893/1893 fecham. Janela (`testes\gui_func.py`): 25/25, incluindo gerar pelo Avançado e as travas.
- **Vaso de recarga da sala do Ovnunu** (área 8, Neitan): o vaso ficava num nicho da parede esquerda do poço (64,408) e se perdia fácil. Agora fica em (56,656) (posição do Neitan), ao lado da porta que vem da área 7 (P0, escada embaixo à esquerda): cai ao carregar a sala e quebra na frente do Firebrand assim que ele entra. Conferido no jogo pelo Neitan (02/10). As duas listas de objetos da área têm o registro. Patch de fase, sempre ligado (`OVNUNU_POT`). Posição escolhida no desenho da área pelo motor do DemonsCrest Editor (`testes\area8_render.py`).

### 01/10

- **Skip Somulo** (ideia do Asvel, pedido do Neitan): a abertura (área 0 = luta no Coliseu, área 17 = a cabeça solta o item, depois a área 1) vira só o resultado. Opção nas duas guias da janela (na Simples gera; no Avançado é só interface, como o resto da guia), `-k` na linha de comando, linha no spoiler. A lógica não muda: o check do Somulo não tem requisito.
  - Jogo novo (`84:8906`, o gancho do LOC): `$8D = 2` (área 1, como a saída da área 17 grava em `80:BB75`; o jogo zera `$8D` e a entrada `$09F7` em `84:88E2`/`84:8903`), `$0E56 = 22` (veio da 17), `LOC 0800` (Somulo vencido, conta no All Bosses) e FLAGS (`$7E:1F92`) bit 2 = item do Somulo pendente. A senha limpa o bit 2.
  - Item: no começo do vigia (fim do laço de objetos), na área 1 com o Firebrand em cena há 60 quadros (`$7E:1F94`), cria o item da cabeça do Somulo (id lido de `83:96D3`, o mesmo do spoiler) com a rotina do jogo `82:877B` (A = id, D = `$1000`, o Firebrand: nasce na posição dele) e limpa o bit 2. Coleta e mensagem são as do jogo; não marca drop de chefe, então pegar não encerra a área.
  - Conferido no BizHawk (`lua\somulo_skip_test.lua`, jogo novo de verdade): seed 7 (Demon Fire no Somulo) começa na área 1, `LOC = 0800`, o item nasce em cima do Firebrand, "YOU GOT THE PIECE OF THE FIRE CREST CALLED DEMON FIRE" e `$1E51 = 08`. Seed 6 com crest inicial Earth + Skip: começa transformado, o HP do Somulo é pego (5 corações), FLAGS certo. Sem a opção, o código do jogo novo é o mesmo de antes (conferido nos bytes da ROM). As 5 dificuldades geram com a opção (com e sem crest inicial).

- **Janela com guias Simples e Avançado** (modelo do Neitan). Cartão da Lógica com título, bandeiras lado a lado e Sobre em cima; guias; opções à esquerda e descrição à direita. Embaixo o cartão da Seed e o Gerar. A linha da ROM e o status saíram: erro (sem ROM, ROM errada, lógica que não fecha) e sucesso ("DemonRando - Nome foi adicionada à pasta Seed.", como no gerador do Metroid Fusion) vêm numa caixa no visual do launcher. O aviso do Anti-Softlock na dificuldade 5 também usa essa caixa.
  - Guia Simples: o que já existia (dificuldade, modo, objetivo, extras). É a única que gera.
  - Guia Avançado: só interface por enquanto; Gerar nela avisa que ainda não gera. Opções: Preset (lista + Carregar .json), Dificuldade (1 a 5 ou Custom), Acessibilidade (All Stages, Vanilla, Rando), Pool de Itens (Crests, Vellum, Potion, Talismã, HP, Refil HP, Moedas 20G, Insanity "em breve", Rando), Densidade (0 a 100), Remoção de itens (Nenhuma, 2, 3, 4, Rando), HP disponível (Sparse, Medium, Full, Rando), Objetivo (os 4 + Rando), Starter Crest (Vanilla, Earth, Buster, Claw, Rando) e Randomizar Head Butt (Não, Sim, Rando). "Rando" = o gerador escolhe ao gerar.
  - Dificuldade 1 a 5 no Avançado marca as opções como a da guia Simples no Clássico Extra: densidade 0/25/50/75/100; remoção Nenhuma, e Rando na 5 (2 a 4); HP Full, e Medium na 4 (ela tira 5 dos 16 HP, sobram 11, que fica entre o Sparse e o Medium). Pool com as 7 categorias, Vanilla, Starter Crest Vanilla e Head Butt Não. O objetivo fica como está (a 5 troca "4 crests" por 5 Vellums). Mexer em qualquer opção troca a dificuldade e o preset pra Custom.
  - Pool: nunca fica vazia; Rando trava as outras caixas.
  - Últimas opções salvas (como o Archipelago guarda o último yaml): guia aberta, opções das duas guias e presets carregados vão pro `dcor_config.json` a cada mudança e voltam ao abrir. Preset `.json`: as chaves do Avançado soltas ou dentro de `{"name": ..., "advanced": {...}}`; o que faltar ou vier errado fica no padrão.
  - Teste (`testes\gui_func.py`, pasta de teste com cópia da ROM): 18/18, incluindo gerar pela Simples, caixa de sucesso, caixa de erro sem ROM, carregar preset e reabrir com as últimas opções.

### 30/09

- **Crest inicial: Fire Crest (= jogo original), Claw, Earth ou Buster** (Neitan). Demon Fire e Time fora. Earth, Air e Water não dão head butt.
  - Earth inicial começa JÁ transformado (arma `0A`, forma `06`, como o menu grava): menu mostra "GROUND GARGOYLE", HUD mostra a Earth.
  - Menu sem a Fire Crest: o código 0 (Fire) deixa de ser "sempre tem" (`84:938A`) e o ícone dela é coberto por quadro vazio antes do desenho dos ícones (`84:8FEF`, fila de VRAM do jogo; mapa de tiles `$4800`, célula `$4883`; vazio = `1C34/1C35/1C44/1C45`). Conferido no print do menu.
  - Hippogriff 1 com Earth inicial: pula a luta (sem ligar o LOC) enquanto não houver crest de head butt (Fire Crest, Buster, Tornado, Claw, Demon Fire, Time). O Hippogriff é decidido em dois lugares, ambos com a mesma condição: `84:9902` (cena de abertura) e o portão de chefe da área 1 (entrada `$81:8123` = HP 02), que é quem faz ele nascer; "vencido" no portão = evento 14 = sai pra área 2. Conferido (jogo novo da ROM de teste, Neitan jogando junto): só Earth e Earth+Water → sem Hippogriff (Earth+Water saiu pra área 2); Earth+Buster, Earth+Fire Crest e Earth+Time → Hippogriff nasce. Lógica: com Earth inicial o check do Hippogriff 1 exige uma crest de head butt.
  - Corrigido no gerador: o preenchimento por esferas começava com o inventário vazio, sem a crest inicial (só a conferência final contava). Era isso que fazia Earth/Air/Water "não fecharem" (29/09). Agora Fire/Claw/Earth/Buster fecham 10/10 nas 5 dificuldades.

- **Pesquisa: pular o Hippogriff 1 (ideia do Neitan pra crest inicial Earth / Head Butt)** — quem decide se o Hippogriff 1 aparece é só o teste de entrada da área 1 (`84:9902`, já trocado pela flag de lugar `LOC 0001` em 26/09); o portão geral (`80:A45F`) nem roda na área 1 e a lista de objetos não muda. Medido (`lua\hippo1_test.lua`, entrada 0 da área 1, andando pra direita): com `LOC 0001 = 0` a cena de abertura roda e o Hippogriff (objeto `09`) nasce; com `LOC 0001 = 1` não há cena nem Hippogriff, a área segue normal (itens no lugar) e a saída leva pra área 2. Então o pulo é viável: o gancho de `84:9902` passa a responder "vencido" também quando a condição de pulo vale, SEM ligar o `LOC` — voltando depois com a condição desfeita, o teste responde "não vencido" e a luta acontece

- **Fire Crest e crest inicial funcionando na ROM (0.2.3, ainda travado na janela)** — `data/fire_crest.py`, código em `$C2:8000`. Conferido no BizHawk (`lua\fire_test.lua`, seed de teste com Claw inicial e Fire Crest no Belth): jogo novo passa pelo gancho `84:88E8` e começa com `$1E51 = 04` (Claw), arma `$1054 = 06` já escolhida; sem a Fire Crest, arma Fire não cria tiro (0 quadros com tiro `40` apertando Y), a Claw atira; o item `1048` nasce, é pego, a mensagem sai do banco `$C2` ("YOU GOT "FIRE CREST". / NOW YOU CAN / LIGHT TORCHES / AND DEAL BASIC DAMAGE"), FLAGS `$7E:1F92` bit 0 liga e aí o Fire atira. Na área 9 (onde a seed pôs o item) ele aparece com o desenho sem uso do sprite `4F` (quadro 1, orbe com a chama) e paleta certa, entrada de sprite `$1E` do patch de gráficos. Corrigido um erro de tipo no `apply` (bytes + tupla) que impedia gravar a ROM com a opção. Pendente: lógica (Earth/Air/Water como crest inicial não fecham nas dif. 1-3) e ligar a opção na janela

Mais novo primeiro. Cada data junta as mudanças daquele dia.

### 29/09

- **Patch anti-softlock da área 59** (Neitan, `patch/area_059.dcmapa.json`): entra junto com o 27 (`Logic.patches` → 27, 59). As áreas 27, 59 e 70 dividem a tela 135 do conjunto 1, então é uma tela só na ROM: `merge_shared_screens` (`insanity_rom.py`) junta as mudanças dos patches bloco a bloco e só dá erro se dois mudam o mesmo bloco para valores diferentes. O da 59 = o da 27 (pedras das linhas 8-10) + a linha 11. Conferido: seeds com dif. 3 e 5 gravam a tela juntada, e as áreas 27, 59 e 70 carregam no emulador (`lua\area_shot.lua`)

- **Crawler sumia com Water Crest** (seed "Castle Grewon Realm Hippogriff Holothurion", achado pelo Neitan: entrou na área 27, subiu sem vencer o Crawler, voltou e foi mandado pro mapa). Causa: o evento da arena (`84:996F`, Firebrand em X ≥ `0270`) liga `$0EAA` bit 40 ("chefe já vencido") se `$1E51` tem a Water Crest — no original ela só vinha do Crawler. Faltava na lista de testes trocados pela flag de lugar. Agora é `LOC 0100` (Crawler vencido = o drop dele sumiu). Seed refeita: só mudam o checksum, o gancho e 20 bytes de código no `$C0`. Medido no emulador (`lua\event_map.lua`, `lua\crawler59_test.lua`): a área 27 roda o evento `0C` (`84:9839`), que liga `$7FE002` quando o Crawler aparece; com `$7FE002` a 27 passa a carregar como área 59 (`84:8A18`), e é a 59 que roda o evento `10` (`84:9942`, o teste da Water). Com o gatilho forçado na 59 e a Water ligada: ROM antiga marca chefe vencido mesmo sem LOC; ROM nova só marca com LOC 0100. Por isso o patch anti-softlock da área 27 também precisa existir pra área 59 (Neitan vai fazer). Varredura de todos os chefes: só `80:A488` (portão, já por LOC desde 26/09) e `84:997C` (este) ligam `$0EAA`; Flame Lord (áreas 14/51, `84:8A03`) troca de área por flags que o próprio chefe liga (`82:DAE2`, `82:CC26`), não por item. Ainda sobra um teste parecido em `84:C1D1`/`C1E0` (Tornado → `$7FE000/01`, Water → `$7FE002`), que roda ao carregar senha; senha está fora do escopo

- **Softlock no Ovnunu com recarga** (seed "Firebrand Crest Crown Tornado Buster", achado pelo Neitan): o Ovnunu cria o item dentro da areia (`82:877B`) e o sobe mexendo na posição dele a cada quadro (`83:C6E7`: X = 80, Y −7F até < B0). Crest/talismã/vellum/HP ficam parados e sobem junto; 20G e recarga (objeto `23`) têm física própria e não apareciam, e sem o item o fim de área não vem. Pedido do Neitan: Ovnunu nunca recebe 20G nem recarga (`FORBIDDEN`, aplicado também no sorteio, não só na conferência). 960 seeds: 0 falhas. Não conferido no emulador; os outros chefes que usam `82:877B` (Holothurion, Flame Lord, Skulla, Arma 1/2) não mexem no item do mesmo jeito até onde li, mas não foram testados com recarga

- **Janela 0.2.1** (pedido do Neitan: leitura ruim, sem rolagem, círculos pixelados): conteúdo num Canvas que rola, com barras escuras desenhadas (`ScrollBar`; a do Windows é clara e o `ttk` não está no exe); tamanho mínimo 320×240, abaixo da largura base × 0,8 aparece a barra horizontal em vez de espremer; roda do mouse rola (Shift = horizontal). Escala das letras só pela largura. Bolinhas de seleção lisas (`aa_radio`: imagem com 4×4 amostras por pixel). Letras maiores (base 11) e contraste maior. Carregador de fonte privada (`load_fonts`, `data/fonts`, `AddFontResourceEx`): Roboto 2.138 (Regular/Medium/Bold/Italic, sem hinting, Apache 2.0, licença em `data/fonts/LICENSE-Roboto.txt`) baixada do repositório oficial `googlefonts/roboto` com autorização do Neitan; sem os arquivos, Segoe UI. Cartão de Objetivo/Extras meio a meio

- **Pesquisa dos spells (§3.9)** pedida pelo Asvel: `$37` do inimigo = máscara de spells; congelamento `$FF`; Imp 1 G
  a cada 32 quadros; Ovnunu sem o bit do Death; Shock já quebra pote; Shadow sem redução de dano, com a paralisia
  sem uso em `BE:B0CA`. Medido no BizHawk.

- **Spoiler em inglês** (padrão do Neitan): cabeçalho, esferas e nomes dos locais/itens saem em inglês (`insanity_rando.en()` traduz os nomes internos, que continuam em PT no código). README com a parte em inglês completa. Sobre: "Natan Anile" + colaboração do Asvel (lógica e ideias)

- **Extras novos na janela, travados "(em breve)"** (handoff Fire Crest / crest inicial / soco): "Randomizar Crest inicial" e "Randomizar Head Butt" (a descrição diz que sem ele não se quebram estátuas nem janelas). PT/EN. Ficam desativados até a ROM ter os ganchos

- **Pesquisa (§3.8)**: Fire Crest sem uso (animação +00 do sprite `4F`), tiro (`$81:B446[$1054]` → `80:F222`), soco
  (botão A → estado `$0A`, `80:F181`; quebra `$A0` em `80:E54A`), crest inicial (`84:88E8`). Medido no BizHawk.
  Nada implementado.

- **1ª esfera controlada (0.3, escolha do Neitan)**: ~22 checks abrem sem nada e recebiam muito HP (7 a 12 dos 16), que abre os caminhos "X+ HP". Agora `SPHERE1_MAX` (`insanity_rando.py`) limita o que cai ali: chave (crests + Armor) 3/2/2/1/1 nas dif. 1 a 5; HP 5/2/3 nas dif. 3/4/5 (dif. 1 e 2 sem limite de HP: "mais HP no começo" é a proposta delas). O item que o gerador precisa pra abrir a 2ª esfera entra mesmo acima do limite. Resultado em 200 seeds por dificuldade: dif. 5 foi de 7,2 HP na 1ª esfera pra 3,0, a 2ª esfera de 15,6 checks pra 5,7 e a média de esferas de 5,7 pra 6,6; dif. 4 de 6,7 pra 7,8 esferas. 4560 seeds no lote largo: 0 falhas. Reserva, se as seeds ainda abrirem demais: preferir o caminho "principal" da V3 na escolha das chaves

- **Lógica V3 ligada (DCOR 0.2)** (§3.4): dificuldade por alternativa, piso = menor número dos parênteses. Mudou de verdade: Potion 0C, Hand, recarga da área 11, os 5 potes 20G da área 13, HP 0B, HP 0D e Flier 2 (Tornado só da dif. 4 pra cima). 4560 seeds (3 modos × 4 objetivos × anti on/off × 5 dificuldades × 40): 0 falhas, 0 check inalcançável

### 28/09

- **Janela travava ao redimensionar** (visto pelo Neitan): os textos que quebram linha (descrição e status) recalculavam a quebra a cada redimensionamento, e isso mudava a largura que eles pediam, que mudava o layout... e em certas larguras virava um laço infinito do Tk. Agora `width=1` nesses rótulos. Teste por script: 786 tamanhos de 1 em 1 px, arraste de 160 passos, maximizar/restaurar, sem travar. A opção passou a se chamar **Prevenção Anti-Softlock**
- **Gerar sempre dá seed nova** (pedido do Neitan): se o campo ainda tem o nome da última seed gerada, Gerar sorteia outro nome. Nome digitado ou vindo do Sortear é respeitado (serve pra repetir/compartilhar seed). Conferido por script: 3 cliques = 3 nomes; nome digitado mantido e trocado no clique seguinte
- **Seed com 5 palavras** (eram 4): 37 palavras = ~45 milhões de nomes sorteáveis (antes ~1,6 milhão). Botão **Sobre** (canto de baixo): versão + créditos do Neitan + referência do FredYeye (valores dele usados só pra conferir; nenhum código). Link abre com `os.startfile` (o `webbrowser` não está embutido no exe; assim não precisa recompilar)
- **Idioma PT/EN** (pedido do Neitan): cartão "Idioma" ao lado da seed com as bandeiras desenhadas no Canvas (Brasil em cima, EUA embaixo; a escolhida fica acesa). Troca todos os textos na hora, sem reiniciar (`TEXTS`/`tr()` no `dcor_gui.py`), inclusive status, erros da ROM, dicas e a janela Sobre; lembra o idioma no `dcor_config.json`. Spoiler continua em PT. **Descrição**: fonte Segoe UI Semibold 10 (antes itálico 9) e painel com metade do cartão (antes 2/5). Como a descrição quebra linha, a escala agora recua se o texto passar do cartão (`fit_info`). Teste por script: 144 combinações (idioma × modo × dificuldade × tamanho) sem texto cortado, arraste sem travar, seed gerada em EN
- `data/location_gfx.txt` apagado (Lixeira; pedido do Neitan: nada do rando do Fred no DCOR). Só a `main()` do `patch_items.py` (ferramenta antiga que remendava a ROM do rando do Fred) lia esse arquivo; o DCOR usa só as funções do `patch_items`. Conferido: 9 seeds (3 modos × 3 combinações) geradas sem ele
- **DCOR sem nada do rando do Fred** (pedido do Neitan: só código nosso). Na `data`, `check_rom.py`, `fix_palette.py` e `patch_items.py` foram para a Lixeira e deram lugar a `rom_tables.py` (leitura da ROM + tabelas gráficas + alocador), `palettes.py` (paletas por área) e `item_gfx.py` (peças do item com gráfico próprio). Saiu tudo que só servia pra ROM do Fred: verificador e conserto de paleta da ROM dele, restauração das tabelas/banco $80 que o rando dele mexia, lista de localizações dele, o empréstimo de VRAM do homem-peixe (só existia no caminho do Fred e estava desligado), o layout antigo em BF:D600 e as referências a ele nos comentários. `build_code` ficou só com o layout do DCOR (banco $C1, entradas contadas de $1E). `tools\insanity_gfx_check.py` passou a importar os módulos novos. **Conferido: 90 seeds (3 modos × 5 dificuldades × 3 objetivos × anti on/off) saem byte a byte iguais às de antes da limpeza**
- **Dif. 5 nova, Anti-Softlock e janela nova** (§3.4.3, §3.7). A dif. 5 tira de 2 a 4 entre Air, Time, Tornado e Demon Fire (não tira mais os 10 HP). O anti-softlock aplica os mapas 27 (sempre) e 29/38 (só sem Air + Tornado, e aí a Claw vale na lógica). O objetivo 4 crests fica bloqueado na dif. 5. Janela: "Go Mode" virou **Objetivo**, sem ícones, e é **redimensionável**: cartões, linhas e barra esticam, as letras acompanham (escala pelo espaço que o conteúdo ocupa; mínimo 480×678). O Extras "Objetivos (em breve)" saiu, porque a sessão Objetivo é ele

### 27/09

- **Somulo, 1ª luta (área 0): cabeça com 3 tiros** (pedido do Neitan). A cabeça é o objeto `33`. A vida fica em `$36`: `FF` fora da fase vulnerável, e `83:8A3C LDA #$07 / STA $36` ao entrar no estado `1A`. O dano por tiro é 1 (tabela `$81:[$2E + índice do tiro]`), e a luta acaba quando a vida chega a 1, então tiros = vida − 1. Original: 7 (6 tiros). Agora: `SOMULO_HEAD_HP = 4` (3 tiros). Medido no emulador com `lua\somulo_test.lua`: jogo novo, sem savestate e sem crest (a luta tem que ser sem Time Crest). Antes, 6 tiros; depois, 3, e a luta termina e vai para a área 17. A área 17 (objeto `52`/`53`) não mudou. Existe outro `LDA #$07 / STA $36` em `82:F1CB`, que não é o Somulo e ficou como estava
- **Crest: controle volta na hora em que a caixa fecha.** O estado 2 esperava o temporizador `$3A = F0` (240 quadros desde a coleta) antes de conferir. Com a caixa fechada antes do fim, o Firebrand ficava parado o resto do tempo, e sem caixa ficava 4 s. Agora `82:EB7F` confere todo quadro e solta assim que não há objeto `8B` vivo. O `$0EDB` saiu da condição, porque um roteiro de chefe pode ligá-lo com a caixa aberta. No emulador (`control_test.lua` mede o quadro em que a caixa some e o quadro em que `$0E5C` zera): antes, caixa 226 e controle 244; depois, 226 e 226; sem caixa, antes 244 e depois 4. O vigia continua 6/6
- **Go Mode na janela** (§3.4.1): 5 Vellums / All Bosses (15, sem o Trio) / 4 crests de transformação / All HP, no lugar do go mode por dificuldade. Extras Objetivos e Anti-Softlock prevent travados. Castelo conferido no emulador (8/8)
- **Código fora do exe** (§3.7): `DCOR.exe` virou só o lançador; o código do rando mora em `DCOR\data` e vale sem compilar (conferido). `tools` importa de lá
- **Controle preso com crest e item perdido no Arma 3** (achados pelo Neitan jogando). (1) A crest pega fica no estado 2 esperando `$0EDB`, que só a caixa de mensagem dela liga ao terminar (`BE:DE9B`). Se a caixa não nasce, o `$0E5C = 8B` segura o Firebrand para sempre. Agora `82:EB86` solta com `$0EDB` **ou** sem objeto `8B` vivo. (2) A crest apaga o bit `$4000` do próprio subtipo ao nascer (`82:EA84`), e o vigia comparava o id inteiro (`4648` contra `0648`). Ele achava que o item tinha sumido e encerrava a área sem o item: foi o Arma 3 com a Demon Fire no ar, e vale para todo drop com esse bit. Agora a marca e a comparação ignoram `$4000`. Conferido no emulador (`lua\control_test.lua`, `lua\mark_test.lua`): a ROM antiga reproduz os dois; a corrigida passa em 10/10 e 6/6. Mensagem de crest muda de página com Y/Start (`$95 & $50`)
- **Modos e dificuldades ligados** (§3.4.1, §3.7): Limitado/Clássico/Clássico Extra no gerador e na janela; castelo novo na ROM para as dif. 1/4/5, conferido no emulador (13/13, depois de corrigir o salto da rotina). O Insano continua travado

### 26/09

- Ajustes das dificuldades 1, 3 e 5 e regra da Water Crest fora do Holothurion (§3.4.1). 1000 seeds por modo, 0 violações
- **Dificuldade 1-5** (§3.4.1): `fill_spheres`, mínimo de 5 esferas, itens fortes e HP por esfera, HP removido, go mode por dificuldade (na lógica). 200 seeds por dificuldade, todas ok. A ROM ainda não tem o castelo novo das dificuldades 1, 4 e 5
- **DCOR, a janela** (§3.7): `tools\dcor_gui.py`, uma barra de dificuldade (1-5) e 4 modos com descrição no mouse; só o Clássico Extra gera. `build_seed()` foi separado do `main()` do `insanity_rando.py` (a seed 2 continua idêntica)
- **Gráficos, etapa 2** (§3.6): banco `$C1`, até 6 itens por área, divisão de VRAM, área apertada sem brilho, paleta emprestada com devolução (`82:8752`). Conferido nas seeds 2, 24 e 13. Seed 2 regenerada
- **Gráficos, etapa 1** (`tools\insanity_gfx.py`, §3.6): patch de gráficos ligado ao Insanity. Seed 2: 23 itens conferidos no emulador (`tools\insanity_gfx_check.py` + `lua\gfx_test.lua`), 22 ok de ponta a ponta e o Crawler com a paleta chegando só na luta. Seed 2 regenerada
- **Chefes validados no jogo pelo Neitan** (seed 2, jogando até o Arma 3): todos aparecem e a progressão por lugar funciona
- Flier 2 (área 34) não mudava de área: o `1F49` dele também vai para o estado 2 (`82:EB2A`), então encerrava no original. Agora os dois Flier são marcados. Regressão no emulador: Arma 1 (andando), Ovnunu e Belth aparecem. Seed 2 regenerada
- Flags e marcador para `$7E:1F80/1F90` (RAM medida livre). Teste automático de chefes (`lua\boss_test.lua`): Arma 1, Ovnunu, Belth e Skulla aparecem. Cobertura conferida contra a ROM gerada pelo Fred. Seed 2 regenerada
- Classificação das 98 leituras de progresso. Trocados pela flag de lugar também: Arma (Time apagava todos), roteiro de entrada das fases, intro do Hippogriff, Trio, troca de área do Ovnunu (60) e do Crawler (59), fluxo da fase 1 (Earth). Seed 2 regenerada (mesmo spoiler)

### 25/09

- Mapeamento do Insanity recebido e conferido. Esta documentação criada; os relatórios pro Fred foram encerrados
- Insanity, fase de mapeamento: lista de objetos por área (normal + área limpa), pote, 2 sistemas de cenário quebrável, drops de chefe. `tools\insanity_map.py`. Faltam as crests do Arma. Drops: 20G/5G/1G/recarga total/+2/+1 HP. HP do sino (área 38) = flag 10; as 16 flags de HP localizadas
- Medição achou o portão de chefe (`80:A45F`) e o mapa (`85:A1EE`). Flag por lugar (`LOC`) no portão; mapa com todas as fases e castelo com 5 vellums. Seed 2 regenerada (mesmo spoiler)
- Teste da seed 2: progresso (chefe vencido, fases, castelo) deduzido dos bits de item; sem SRAM, senha de 64 bits com 7 livres. Decisão: estender a senha. Medição `lua\progress_reads.lua`
- 1º teste da seed 1: item encerrava a área (crest no pote, HP 01) e chefe com outro drop travava (Arma 1). Conserto: fim de área decidido pelo lugar (marcador + vigia), §3.5
- Gravação da ROM (§3.5): 4 MB, tabela nova de potes, desvios do Hippogriff e do Grewon. Crests do Arma achadas (`$81:F0A2`, objeto `4F` → `82:F009`). Lógica: Potion 0C e Hand ajustadas pelo Neitan. Seed 1 gerada para teste
- Lógica V2 + gerador `tools\insanity_rando.py` (ainda sem gravar ROM). Detalhes na §3.4. 5000 seeds: 0 falhas, 0 check inalcançável
- Lógica V1 do Neitan: `lógica_demonRando_V1.txt`. Formato: `,` = E dentro do requisito, `/` = OU entre requisitos, qualquer requisito completo libera o check. Conferida contra o mapa; dúvidas enviadas a ele

### 24-25/09

- Caixa de texto preta: agora lê o CGADSUB salvo. Área 25: item no pote. Earth Crest reempacotada. Aqua demon testado e desligado

### 23/09

- Porte pra Rust (ROM byte a byte igual). Firebrand bugado ao cair: restauração estendida até `B2EB`

### 22/09

- Patch de gráficos: restauração das tabelas, planejamento por localização, regras de slot, conserto da água sob a caixa de texto
