# M1 - Acabamento visual para TikTok (Etapa 11)

> **Versao mesclada (Fabrica + acabamento)**. Base: o codigo da Fabrica de Videos (contador gigante com extrusao, kit de widgets
> animados, chip "TEMPO · LUGAR", prompt didatico, entrada pop/esq/dir/subir). Sobre ele entram: exposicao automatica, remocao de fundo
> dos SVGs da IA (`rig.descaixar`), halo do heroi, camera com parallax, particulas, titulo-gancho, legenda TikTok, barra de progresso,
> flash de corte, selos presos dentro da tela e regras de heroi/acentuacao/cenario vertical nos prompts.
> Onde os dois faziam a mesma coisa (leitura presa ao heroi, luz de recorte) ficou a versao da Fabrica / o halo do motor.
> Cena 1: titulo-gancho primeiro (0-3,6 s); o numero gigante entra logo depois (se a cena for curta, fica so o titulo).


## O que mudou e por que
Comparando o video gerado ("O que aconteceria se um pais tentasse invadir o Brasil") com a cena de referencia (geladeira/apagao):

| Problema no video gerado | Causa no codigo | Correcao |
|---|---|---|
| Cena escura, tudo "afundado" no preto | paleta dos SVGs da IA + vinheta 0.60 + sem exposicao | `polimento.exposicao_auto` (gamma medido 1x por cena), bloom 1.25, saturacao 1.14, vinheta 0.42 |
| Objetos pequenos dentro de "caixas" retangulares | a IA desenha um retangulo de fundo; caixa do recurso nao encolhia; heroi 0.30 da altura | `rig.descaixar` remove o fundo e encolhe a caixa; `polimento.suavizar_caixa` derrete "paisagens-quadro"; heroi 0.35-0.42 da altura, ate 94% da largura |
| Sem ponto focal | nenhum heroi marcado, sem luz propria | heroi marcado (`hero`), halo de luz na cor de acento atras dele, "pop" de entrada + flutuacao |
| Cena estatica | camera so dava zoom 1.06 | camera alterna aproximar/afastar + pan (parallax), particulas flutuantes |
| Cada corte escurecia o quadro | fade-in 0.30 s + fade-out 0.20 s em TODA cena | corte seco com flash curto de luz (0.16 s); fade so no fim do video |
| Sem gancho nos 3 primeiros segundos | 1a cena igual as outras | titulo grande palavra-por-palavra na cena 1 |
| Sem dado concreto | numeros ficavam em selo estatico | (Fabrica) `contadores`: numero gigante que CONTA de 0 ate o valor; `chamadas` presas ao heroi |
| Selos sem acento ("INVASAO") | o prompt da direcao de arte estava sem acentos e o Gemini copiava | prompt reescrito com acentos + regra de acentuacao; regex de numeros aceita "milhoes/quilometros" |
| Legenda pequena, 4 palavras, cor unica | `legendas.desenhar` classico | estilo `tiktok`: contorno preto, palavra ativa na cor de acento, palavras-chave em amarelo, 3 palavras por trecho, mais alta (fora da UI) |
| Heroi abstrato ("soberania", "imensidao") e paisagem como objeto | prompt pedia "hero" sem criterio | regras de heroi concreto/isolado; SVG de objeto proibe fundo/moldura; cenario pensado para a faixa central do 9:16 |
| Sem retencao visual | - | barra de progresso fina no topo (desligar: `"barra_progresso": false` no canal.json) |

## Arquivos
- NOVO `estudio/estudio/cenas2d/polimento.py` - exposicao, particulas, contador, titulo-gancho, barra, flash, chamada de dado.
- `cena_generica.py` - `quadro()` proprio (acabamento), entrada/flutuacao, halo do heroi, chamadas, titulo.
- `rig.py` / `biblioteca.py` - `descaixar` (so objetos com `origem: ia`).
- `legendas.py` - estilo `tiktok` (o classico continua padrao para os outros modelos).
- `diretor_m1.py` - layout, camera, titulo, dado, prompt de arte, fallback sem cena vazia, regex de numeros.
- `recursos_ia.py` - prompts de SVG (objeto isolado, objeto mais claro que o fundo, cenario com luminosidade e foco central).
- `recursos_ativos.py` - mais palavras-chave (invasor, quilometros, litoral, contingente...).
- `criar_cenas2d.py` - progresso global, `VERSAO_RENDER = "3"` (invalida o cache de segmentos antigos), 3 palavras por trecho.

## Ajustes finos (campos opcionais da cena / canal)
`acento` (#hex), `exposicao` (alvo de luminancia, padrao 64), `bloom_ganho`, `vinheta`, `saturacao`, `particulas`, `flash` (false desliga), por elemento: `halo`, `flutuar`, `entrada`.

## Custo
~0,31 -> ~0,47 s por quadro 1080x1920 (+50%) em 1 CPU. `render_processos` no canal continua dividindo por cena.

## Nao testado aqui (sem rede/GPU/Kokoro)
Gemini (direcao de arte e SVGs novos com os prompts novos) e voz real. Os SVGs ja existentes na biblioteca foram corrigidos em tempo de render, sem regravar arquivos.
