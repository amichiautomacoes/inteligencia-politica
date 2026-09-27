# Visualizacao Eleitoral

Aplicacao Streamlit para leitura territorial, demografica, financeira, parlamentar e demografica-estrategica da votacao de candidatos.

O app consome arquivos remotos do Hugging Face, configurados pelo `.env`, e apresenta duas paginas:

- **Raio X do voto**: leitura descritiva territorial, financeira e parlamentar.
- **DNA Eleitor**: leitura estrategica do eleitor determinante, com ICP geral da base e secoes de segmentacao, potencial e expansao.

## Estrutura do projeto

- `app.py`: ponto de entrada Streamlit, configuracao de pagina e navegacao.
- `pages/raio_x_do_voto.py`: pagina principal da visualizacao.
- `pages/dna_eleitor.py`: pagina do DNA Eleitor, com secoes estruturadas para as visualizacoes da segunda experiencia.
- `pages/cluster_cards.py`: HTML e estilos dos cards de classificacao e dos ICPs.
- `pages/dna_copy.py`: padronizacao editorial de categorias e personas.
- `pages/shared_header.py`: componente compartilhado de cabecalho, fundo, foto do candidato, seletor entre paginas e helpers visuais comuns.
- `pages/geo_reference.py`: referencia compartilhada de malha e codigos municipais de MG.
- `hf_sync.py`: leitura de `.env`, listagem remota no Hugging Face, cache e mapeamento dos parquets por tipo.
- `assets/background.png`: imagem de fundo usada no modelo visual.
- `Visual.md`: briefing visual do produto, separado da documentacao tecnica.

## Navegacao

A navegacao e configurada em `app.py` por `st.navigation`, com duas rotas:

- `/raio-x-eleitoral`: pagina **Raio X do voto**;
- `/dna-eleitoral`: pagina **DNA Eleitor**.

O cabecalho possui um controle segmentado estilizado com as opcoes **Raio X Eleitoral** e **DNA Eleitoral**. A selecao navega entre as rotas mantendo o mesmo deputado selecionado na barra lateral.

## Fonte de dados

Os dados sao carregados de um bucket Hugging Face definido por:

```env
HF_BUCKET_URL="hf://buckets/..."
HF_VISUALIZACAO_PREFIX="deputados/estaduais/2022"
HF_TOKEN="..."
```

O app localiza as pastas dos candidatos a partir do prefixo geral da eleicao, lista os deputados na barra lateral e usa aliases em `hf_sync.py` para selecionar cada parquet dentro da pasta escolhida.

## Parquets utilizados

### Territorio

- `territorio/stage01a_municipios.parquet`
  - usado em `votos_municipio`;
  - usado tambem em `votos_mesorregiao`, com agregacao por mesorregiao;
  - alimenta KPIs, mapa coropletico, ranking territorial e curva de concentracao.

- `territorio/stage01b_bairros.parquet`
  - usado em `votos_bairro`;
  - alimenta o treemap de municipio/bairro e o filtro de mesorregiao.

### Demografia

- `demografico/stage02_genero.parquet`
- `demografico/stage02_idade.parquet`
- `demografico/stage02_escolaridade.parquet`
- `demografico/stage02_estado_civil.parquet`

Esses arquivos alimentam o grafico de perfil demografico, recortado por mesorregiao e pela selecao ativa do treemap.

### Censo para a Matriz de Potencial Demografico

- `IBGE/censo/genero_apond.parquet`
- `IBGE/censo/idade_apond.parquet`
- `IBGE/censo/escolaridade_apond.parquet`

Esses arquivos sao cruzados com os ICPs no nivel municipal. Genero e idade usam as contagens populacionais por area ponderada, agregadas pelo prefixo municipal do codigo da area. Escolaridade usa `nivel_instrucao` para pessoas com 25 anos ou mais e agrega os percentuais das areas ponderados pela populacao total da area, obtida dos parquets de genero ou idade. `qt_votos_demografico` e usado apenas como fallback se essa populacao nao estiver disponivel.

### Perfil estrategico

- `perfil/stage04_icp_geral_geo.parquet`
  - alias `icp_geral` em `hf_sync.py`;
  - alimenta **Eleitor ideal do candidato**;
  - contem persona, resumo, confianca do modelo e atributos demograficos principais por territorio;
  - usa `votos_candidato` como peso na consolidacao do perfil geral.

- `perfil/stage04_icp_clusters_geo.parquet`
  - alias `icp_clusters` em `hf_sync.py`;
  - alimenta **BASE ELEITORAL DO CANDIDATO**;
  - contem `perfil_eleitor`, `cluster_strategy_label`, `persona_executiva`, `cluster_strategy_reason` e os atributos demograficos dos clusters;
  - preserva cada `perfil_eleitor`, mesmo quando dois perfis possuem a mesma classificacao estrategica.

### Gastos e atuacao parlamentar

- `gastos/gastos_territoriais.parquet`
  - usado em `gastos_territoriais`;

- `gastos/despesas_campanha.parquet`
  - usado em `despesas_campanha`;
  - alimenta o ranking de custo por voto por tipo de despesa.

- `gastos/emendas_legislativa.parquet`
  - usado em `emendas_legislativa`;
  - alimenta o **Mapa da atuacao parlamentar de acordo com os votos**.

## Pagina 1: Raio X do voto

### 1. Cabecalho do candidato

Apresenta o contexto geral da analise:

- titulo da visualizacao: `RAIO X da votacao 2022`;
- subtitulo: `Analises descritivas geograficas e do perfil do eleitor na ultima eleicao.`;
- foto do candidato, quando encontrada entre os arquivos remotos;
- nome, cargo e partido do candidato analisado.
- controle segmentado para alternar entre **Raio X Eleitoral** e **DNA Eleitoral**.

### 2. Mapa Territorial da Votacao

Mostra a distribuicao geografica dos votos em Minas Gerais.

Esta secao traz:

- total de votos no recorte ativo;
- municipio mais votado;
- quantidade de municipios com votos;
- territorio lider por mesorregiao;
- filtro para alternar entre visualizacao por mesorregiao e por municipio;
- mapa coropletico de Minas Gerais com intensidade de votos;
- grafico lateral com top 10 de concentracao territorial.

### 3. Votacao por Bairro e Perfil Demografico

Cruza o territorio selecionado com o perfil demografico estimado dos eleitores.

Esta secao traz:

- filtro de mesorregiao;
- treemap de votacao por municipio e bairro;
- selecao interativa no treemap;
- persistencia do recorte da secao em `st.session_state["pagina1_demographic_territorial_context"]`;
- botao para limpar o recorte territorial ativo;
- grafico de barras do perfil demografico, com filtros por:
  - genero;
  - idade;
  - escolaridade;
  - estado civil.

### 4. Concentracao Territorial

Resume o quanto a votacao esta concentrada nos principais municipios.

Esta secao traz:

- percentual acumulado de votos no Top 1, Top 5, Top 10 e Top 20 municipios;
- destaque textual para a concentracao dos 10 principais municipios;
- toggle para mostrar Top 50 ou todos os municipios;
- curva acumulada mostrando quantos municipios concentram determinada parcela da votacao total.

### 5. Eficiencia por Custo do Voto

Mostra quanto cada tipo de despesa custou por voto no resultado geral da campanha.

Esta secao traz:

- custo medio geral por voto;
- total gasto na campanha;
- tipo de despesa lider em gasto;
- ranking horizontal por `tipo_despesa`;
- eixo X: custo por voto em R$/voto;
- cor da barra: valor total gasto no tipo de despesa;
- linha de Pareto com percentual acumulado do gasto.

### 6. Mapa da atuacao parlamentar de acordo com os votos

Cruza votacao municipal e volume de emendas destinadas pelo parlamentar.

Esta secao traz:

- mapa coropletico com base na votacao municipal;
- camada de bolhas sobreposta;
- tamanho e cor das bolhas proporcionais ao valor de emendas;
- tooltip com municipio, votos e valor de emendas.

O valor principal de emendas vem de `valor_pago_atualizado`, com fallback para `valor_empenhado_ano` e `valor_indicado`.

## Pagina 2: DNA Eleitor

### 1. Cabecalho do candidato

Usa o mesmo componente visual da pagina 1, com alteracao apenas do titulo e subtitulo:

- titulo da visualizacao: `DNA do Eleitor`;
- subtitulo: `Quem e, onde esta e como se comporta o eleitor determinante da candidatura.`;
- foto, nome e cargo do deputado selecionado;
- controle segmentado para alternar entre **Raio X Eleitoral** e **DNA Eleitoral**.

### 2. Identidade da Base Eleitoral

A secao possui duas subsecoes, nesta ordem. Os antigos Sunburst, Heatmap e a composição demográfica por pontos não fazem parte da experiência atual.

#### 2.1 Eleitor ideal do candidato

Fonte: `perfil/stage04_icp_geral_geo.parquet`.

- Titulo: **Eleitor ideal do candidato**.
- Subtitulo: `Síntese do perfil demográfico predominante na base eleitoral do candidato.`
- Persona: `persona_executiva`, com capitalizacao editorial e emoji preservado.
- Resumo: `perfil_resumo`, ocultado se apenas repetir a persona, ignorando caixa, espacos e ponto final.
- Badges: confianca numerica do modelo e classificacao qualitativa.
- Quatro KPIs: categoria dominante e seu respectivo `pct_*_principal`.

`_icp_general_row()` identifica persona e categorias dominantes pelo volume de `votos_candidato`. `_demographic_percent()` calcula a media ponderada dos percentuais da categoria escolhida, usando os votos como peso. Nos parquets inspecionados, os percentuais gerais se repetem entre territorios; nao devem ser somados. A confianca tambem usa media ponderada, com valores validos e pesos positivos.

#### 2.2 BASE ELEITORAL DO CANDIDATO

Fonte: `perfil/stage04_icp_clusters_geo.parquet`.

`_cluster_profiles()` agrupa por `perfil_eleitor`. `cluster_cards_html()` apresenta:

- resumo por **Base eleitoral**, **Eleitor consolidado** e **Eleitor emergente**;
- card independente para cada ICP, com classificacao, identificador e persona;
- votos absolutos e participacao na votacao do candidato;
- quatro barras demograficas independentes, com categoria e percentual;
- justificativa em `cluster_strategy_reason`, visivel sem selecao.

A participacao soma `pct_market_share` por ICP e depois por classificacao. Se o campo estiver ausente ou nulo, o fallback e `votos_candidato / total_votos_candidato * 100`. Na ausencia do total do candidato, usa-se a soma de votos do nivel territorial selecionado. `total_votos_candidato` e um denominador repetido, nunca uma coluna a somar.

Uma classificacao sem perfis exibe traco e mensagem explicita, sem criar um ICP ficticio. Perfis distintos com o mesmo rotulo estrategico permanecem separados.

#### Regras de granularidade e percentuais

`_territorial_rows()` usa apenas `nivel_territorial = municipio`; se nao houver municipios, usa bairros. Nunca combina os dois niveis na mesma soma. Sem a coluna de nivel, preserva as linhas recebidas; com niveis desconhecidos, retorna vazio.

| Campo do parquet | Significado | Uso na pagina |
| --- | --- | --- |
| `votos_candidato` | Votos do registro territorial/perfil | Volumes e pesos |
| `total_votos_candidato` | Votacao geral do candidato | Denominador, sem soma |
| `pct_market_share` | Participacao do registro na votacao geral, em 0-100 | Soma por ICP, em um unico nivel territorial |
| `pct_votos` | Participacao no `total_votos_territorio`, em 0-100 | Nao usado para participacao geral |
| `pct_genero_principal` | Percentual do genero dominante | KPI e barra de genero |
| `pct_idade_principal` | Percentual da faixa etaria dominante | KPI e barra de idade |
| `pct_escolaridade_principal` | Percentual da escolaridade dominante | KPI e barra de escolaridade |
| `pct_estado_civil_principal` | Percentual do estado civil dominante | KPI e barra de estado civil |

Os campos percentuais ja usam 0-100: `0.5` significa 0,5%. Apenas a confianca aceita explicitamente a conversao de fracao para percentual. Percentuais demograficos ausentes ou fora de 0-100 nao sao inventados: os cards informam a ausencia.

Os quatro atributos sao dimensoes independentes, nao parcelas de uma soma de 100%. Os parquets descrevem categorias dominantes; nao permitem reconstruir a distribuicao completa de todas as categorias.

### 3. Demais secoes estruturadas

A pagina possui quatro secoes em `pages/dna_eleitor.py`. A estrutura e o status atual de cada uma sao:

- **Identidade da Base Eleitoral**: implementada com Eleitor ideal do candidato e cards da base eleitoral.
  - subtitulo: `Quem e o eleitor-chave e quais atributos definem o perfil do seu eleitor.`

- **Matriz de Potencial Demografico**: mapa coropletico municipal comparando genero, idade e escolaridade do ICP com o Censo.
  - mapa coropletico municipal de MG;
  - seletor para **ELEITOR IDEAL** ou classificacao estrategica do ICP clusters;
  - aderencia demografica calculada pela proximidade, em pontos percentuais, nas tres dimensoes;
  - compatibilidade final e a media da aderencia demografica nas tres dimensoes, em escala de cor logaritmica;
  - municipios sem votos recebem zero de compatibilidade;
  - municipios sem votos ou sem dados completos continuam preenchidos com o verde mais claro.
  - subtitulo: `Comparativo entre o perfil do eleitor do candidato e a populacao local. Identificacao de sobre-representacao e frentes de expansao.`

- **Segmentacao & Acao Tatica**: card reservado para visualizacao futura.
  - subtitulo: `Identificacao de frentes de conversao, consolidacao e expansao do eleitorado.`

- **Expansao & Oportunidades para 2030**: card reservado para visualizacao futura.
  - subtitulo: `Mapeamento em nivel de bairro e area ponderada. Localizacao dos clusters taticos e visualizacao de manchas de potencial de crescimento.`

### 4. Helpers visuais e renderizacao

A pagina 2 usa:

- `apply_shared_visual_model()`: aplica fundo, variaveis visuais, hero e estilos compartilhados;
- `render_page_header("dna")`: renderiza o cabecalho com texto da pagina 2;
- `major_section_header(...)`: renderiza os blocos de titulo/subtitulo no padrao da pagina 1;
- `visualization_placeholder()`: cria card reservado para cada visualizacao futura.

Os componentes HTML compartilhados, o card geral e os cards de clusters sao renderizados com `st.html`.

## Cache e performance

O projeto usa cache do Streamlit nos pontos de maior custo:

- `hf_filesystem`: `@st.cache_resource`;
- `remote_data_files`: `@st.cache_data(ttl=600)`;
- `load_tables`: `@st.cache_data`;
- `load_parquet`: `@st.cache_data`;
- `_load_geo_reference`: `@st.cache_data`.

As transformacoes visuais sao recalculadas em reruns, mas a leitura remota dos arquivos e das referencias geograficas fica cacheada.

## Estado interativo

O recorte territorial selecionado no treemap e persistido apenas na secao de demografia em:

```python
st.session_state["pagina1_demographic_territorial_context"]
```

Esse contexto e usado para recalcular apenas:

- grafico demografico;
- legenda do recorte ativo.

Os demais filtros e selecoes ficam restritos as suas proprias secoes.

## Configuracao

Crie um arquivo `.env` com as variaveis necessarias:

```env
HF_BUCKET_URL="hf://buckets/..."
HF_VISUALIZACAO_PREFIX="deputados/estaduais/2022"
HF_TOKEN="..."
```

Opcionalmente, para operacoes de Git automatizadas no ambiente local:

```env
GIT_URL="https://github.com/usuario/repositorio.git"
GIT_TOKEN="..."
```

## Rodar localmente

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Verificacao rapida

```powershell
python -m py_compile app.py hf_sync.py pages\shared_header.py pages\raio_x_do_voto.py pages\dna_eleitor.py pages\cluster_cards.py pages\demographic_comparison.py pages\dna_copy.py
```

### Validacao da secao DNA

Foram verificadas as somas de votos e participacoes e os percentuais demograficos com os parquets de Beatriz Cerqueira e Joao Vitor Xavier. O comparativo foi exercitado com `streamlit.testing.v1.AppTest`, incluindo as quatro dimensoes e fontes parciais. Essas verificacoes foram executadas durante o desenvolvimento, sem suite persistida no repositorio. A inspecao visual em navegador continua necessaria para validar layout desktop e mobile.
