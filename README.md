# Fabrica de Videos — Backend 1.4.0

## O que esta versao entrega

- Preserva o motor Classico e o motor Broadcast News.
- Broadcast News gera roteiros com conhecimento consolidado do Gemini, sem Google Search, grounding ou cota de busca. Assuntos atuais ou mutaveis exigem conferencia manual antes da publicacao.
- Interface `ui/index.html` integrada aos catalogos reais de motores, categorias e thumbnails.
- Categorias com perfis editoriais detalhados: objetivo, tom, estrutura, politica factual, itens a evitar, direcao visual e pergunta final.
- Seletor compacto de motores com icones; motores nao implementados continuam marcados como em desenvolvimento.
- Entregas 16:9 e 9:16 geradas como jobs independentes, com duracoes, roteiros, narracoes e pastas proprias.
- Longo 16:9 configurado para 5–10 min; curto 9:16 para 1–2 min.
- Pergunta final de comentario contextual, adaptada a categoria e ao tom do canal.
- Identidade por canal: nome exibido, logo/marca d'agua, intro opcional e configuracao para logo em miniaturas.
- Fila SQLite persistente, identificacao de interrupcoes e recuperacao de trabalhos.
- Fallback de modelos Gemini apenas para erros de indisponibilidade 5xx/UNAVAILABLE; erros de chave e cota permanecem explicitos.

## Executar

1. Extraia/aplique o patch na pasta que contem `app.py`, `criar_video.py`, `iniciar.bat` e `ui/`.
2. Preserve o `config.json`, `.env`, `iniciar.bat`, `data/fabrica.sqlite3`, canais, projetos, modelos e arquivos gerados.
3. Configure as credenciais locais em `.env` ou `config.json` conforme `docs/SEGREDOS_E_CONFIG.md`.
4. Execute seu `iniciar.bat`. No Windows em que `python app.py` nao foi reconhecido, use `py app.py` dentro do batch.
5. Abra `http://127.0.0.1:8765/` e pressione Ctrl+F5.

## Rotas de diagnostico

- `/api/saude`
- `/api/motores`
- `/api/categorias`
- `/api/thumbnails`
- `/api/projetos`

## Identidade do canal

O nome exibido no topo vem de `canal.json` ou de `identidade.nome_exibicao`. Coloque sua logo em `canais/<slug>/identidade/logo.png` e, se quiser intro, em `canais/<slug>/identidade/intro.mp4`. As opcoes sao documentadas em `docs/BROADCAST_NEWS.md` e no exemplo `canais/exemplo/canal.json`; o patch nao sobrescreve o `canal.json` dos seus canais ativos.

## Motores

- Classico: ativo; imagens/videos de apoio, Kokoro e FFmpeg.
- Broadcast News: ativo; motion graphics jornalisticos locais.
- Personagem 2.5D (M1): ativo; cenas em camadas com biblioteca SVG/JSON, direção de arte Gemini/MyHub Bridge e fallback local.
- Isometric, Blueprint e Stickman: catalogados, mas ainda em desenvolvimento.

Os motores planejados podem receber briefings em `projetos/_planejamento`, mas nao entram na fila de renderizacao ate que o respectivo motor seja implementado e testado.

## Limites factuais

O Broadcast News nao consulta a web nesta versao. Nao publique como atuais leis, aliquotas, cronogramas, cargos, resultados ou numeros recentes sem conferir fontes oficiais. Para conteudos que dependem de atualizacao, o Gemini deve tratar o funcionamento geral e sinalizar verificacao manual.


## Integração MyHub Bridge no M1

O motor **Personagem ilustrado 2.5D (M1)** pode usar o MyHub Bridge local como provedor de direção de arte (JSON) e criação de recursos visuais (SVG + sidecar JSON). Configure `m1_diretor_padrao: "myhub"` no `config.json` e `MYHUB_BRIDGE_DIR` no `.env` local da Fábrica (por exemplo `C:\myhub-bridge`). A Fábrica executa o `main.py` do Bridge com o Python do ambiente `.venv` dele, reutiliza os chats `fabrica_m1__direcao_arte` e `fabrica_m1__recursos_svg`, e lê os resultados organizados pelo Bridge.

O Bridge v0.2 deve estar instalado, autenticado e testado previamente. O M1 continua validando SVG/JSON e mantendo fallback local/procedural. Nenhum código Python retornado pela IA é executado. Consulte [docs/MYHUB_M1.md](docs/MYHUB_M1.md) para instalação, configuração e teste.


## MyHub Bridge para roteiro e M1

A integração agora encaminha planejamento narrativo, geração do roteiro, checagem,
otimização, refino e direção de arte/recursos SVG+JSON do M1 ao MyHub Bridge.
Os provedores podem ser escolhidos separadamente na seção **Provedores de IA**
da interface local. As escolhas valem para novas produções.

A configuração também pode ser feita em `config.json`:

- `provedor_planejamento_narrativa`: `myhub` ou `gemini`
- `provedor_geracao_roteiro`: `myhub` ou `gemini`
- `provedor_refino_roteiro`: `myhub` ou `gemini`
- `m1_diretor_padrao`: `myhub`, `gemini`, `auto` ou `local`

Chats do MyHub são separados por etapa para preservar histórico sem misturar
prompts de planejamento, roteiro, revisão e arte. Configure `myhub_bridge_dir`
para a pasta local do Bridge e mantenha a sessão do Chromium autenticada.
Consulte `docs/MYHUB_TEXTO_E_M1.md`.

## Provedores MyHub Bridge — texto e M1

A interface permite escolher separadamente MyHub Bridge ou Gemini para planejamento narrativo, criação do roteiro e checagem/otimização/refino. A direção de arte do M1 tem uma escolha adicional entre MyHub, Gemini, diretor local e automático. O botão **Salvar provedores de IA** cria um backup do `config.json` e atualiza apenas essas opções.

A integração cobre o pipeline textual compartilhado `criar_video.py` usado pelo Clássico e pelo M1, além de artes vetoriais SVG/JSON do M1. Não substitui os provedores de imagens rasterizadas do Clássico nem altera os geradores editoriais independentes de `criar_animado.py` ou Broadcast News. Instalação e diagnóstico: `INSTALAR_MYHUB_M1.md` e `docs/MYHUB_M1.md`.
