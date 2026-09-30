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
- `pages/dna_expansion.py`: agregacao municipal e classes taticas do mapa de expansao.
- `pages/dna_distribution.py`: grafico de rosca e filtros da distribuicao demografica do eleitorado.
- `pages/shared_header.py`: componente compartilhado de cabecalho, fundo, foto do candidato, seletor entre paginas e helpers visuais comuns.
- `pages/dna_geo_reference.py`: carrega dos parquets a malha, os contornos e os codigos municipais de MG para os mapas do Raio X e do DNA Eleitoral.
- As malhas dos mapas são GeoParquet lidos com `geopandas.read_parquet`. Os cinco mapas do dashboard usam PyDeck/Deck.gl. O mapa detalhado usa apenas setores censitários do IBGE.
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
  - alimenta o mapa de votos por bairro e os filtros encadeados de mesorregiao e municipio.

### Referencia geografica de MG

- `IBGE/MG/dadosterritorio/MG_municipios_2022.parquet`: geometria dos 853 municipios.
- `IBGE/MG/dadosterritorio/MG_mesorregioes_2022.parquet`: contornos das mesorregioes e do estado.
- `IBGE/MG/dadosterritorio/MG_AreaPonderada_CD2022.parquet`: 1.814 areas ponderadas.
- `IBGE/MG/dadosterritorio/MG_bairros_CD2022.parquet`: 2.066 bairros.
- `IBGE/MG/dadosterritorio/MG_setores_CD2022.parquet`: 51.387 setores censitarios distintos (102.774 registros duplicados no arquivo); malha do mapa detalhado da votação.
- `IBGE/MG/dadosterritorio/setor_bairro_lookup.parquet`: índice leve de setores, com código e nome de bairro informados pelo IBGE.
- `IBGE/MG/dadosterritorio/MG_setores_mapa_CD2022.parquet`: setores únicos com geometria simplificada, organizados para leitura por município.
- `IBGE/MG/dadosterritorio/municipios_mg_mesorregioes.parquet`: correspondencia entre codigos TSE e IBGE e classificacao por mesorregiao.

`load_geo_layer()` lê a geometria e o CRS dos GeoParquets com GeoPandas e transforma as coordenadas para EPSG:4326, usado pelos mapas Deck.gl. O mapa detalhado associa votos diretamente ao setor censitário. O tooltip mostra os nomes de bairro informados pelo IBGE e pelos registros eleitorais associados ao setor. Quando não há nome em nenhuma fonte, informa a ausência. Ao selecionar um setor, o perfil demográfico é filtrado pelos bairros eleitorais vinculados a ele. O parquet otimizado dos setores é lido por município. Se a referência remota falhar, o app informa a indisponibilidade.

### Demografia

Na seção **Votação por Setor Censitário e Perfil Demográfico**, a malha é lida por município:

- O mapa usa setores censitários em todos os municípios. A cor azul é relativa à maior votação de um setor no município selecionado, e os limites entre setores aparecem em branco.
- Ao selecionar um setor, o perfil demográfico considera os registros dos bairros eleitorais ligados a ele. Votos sem setor correspondente são informados abaixo do mapa.

- `demografico/stage02_genero.parquet`
- `demografico/stage02_idade.parquet`
- `demografico/stage02_escolaridade.parquet`
- `demografico/stage02_estado_civil.parquet`

Esses arquivos alimentam o grafico de perfil demografico do Raio X, recortado por mesorregiao, municipio e pela selecao ativa do mapa de bairros, e a rosca de distribuicao demografica do DNA Eleitoral.

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

### Potencial demografico

- `potencial_demografico/stage07c_potencial_demografico_icp_geral.parquet`
- `potencial_demografico/stage07c_potencial_demografico_icp_clusters.parquet`

Os arquivos guardam a diferenca em pontos percentuais entre o perfil ICP e a populacao do Censo, por area ponderada e dimensao. A secao de expansao combina esse sinal com a populacao local, os votos da base territorial e os parquets Censo de genero, idade e escolaridade para classificar os municipios.

### Gastos e atuacao parlamentar

- `gastos/gastos_territoriais.parquet`
  - usado em `gastos_territoriais`;
  - alimenta o custo por voto municipal e por mesorregiao no painel de despesas;

- `gastos/despesas_campanha.parquet`
  - usado em `despesas_campanha`;
  - alimenta o treemap da participação de cada tipo de despesa nos gastos totais.

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
- filtro de municipio abaixo do filtro de mesorregiao; a mesorregiao inicial e a de maior votacao total do candidato, e o municipio inicial e o mais votado dentro dela;
- mapa do municipio selecionado com setores censitarios do IBGE;
- dois indicadores compactos no canto superior direito do card: votos do municipio e, quando houver selecao, votos do setor;
- setores coloridos por uma escala azul relativa ao municipio; o total aparece no hover e setores sem votos permanecem visiveis com zero;
- selecao interativa de setor no mapa para recortar o perfil demografico;
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

- faixa compacta com percentual e votos acumulados dos Top 1, Top 5, Top 15 e Top 20 municipios;
- nome do municipio lider no Top 1 e incremento em pontos percentuais dos demais grupos;
- barras que representam a participacao acumulada na votacao total e destacam o incremento de cada grupo;
- frase de leitura com o municipio lider e a concentracao do Top 15;
- listas expansiveis de municipios dos Top 5, Top 15 e Top 20;
- curva acumulada fixa nos Top 50, ou em todos quando houver menos de 50 municipios.

### 5. Mapa da atuacao parlamentar de acordo com os votos

Cruza votacao municipal e volume de emendas destinadas pelo parlamentar.

Esta secao traz:

- mapa coropletico municipal com uma categoria de coerencia politica territorial por municipio;
- seis cores: azul para reduto atendido, verde para investimento, amarelo para reduto desassistido, laranja para baixa expressao, cinza para municipios com votos e sem emendas e branco para municipios sem votos nem emendas;
- KPIs de reciprocidade nos tres principais redutos, municipio mais beneficiado e valor medio de emendas por voto;
- tooltip com municipio, votos, emendas, retorno por voto e explicacao da cor.

O valor principal de emendas vem de `valor_pago_atualizado`, com fallback para `valor_empenhado_ano` e `valor_indicado`.
O parquet de emendas fica na pasta `gastos` de cada candidato. O mapa usa uma unica camada GeoJSON para todas as categorias, evitando repetir a malha municipal no navegador.

### 6. Eficiencia por Custo do Voto

Mostra a participação de cada tipo de despesa nos gastos totais da campanha.

Esta secao traz:

- custo por voto (total geral);
- total gasto na campanha;
- tipo de despesa lider em gasto;
- os tres cards respondem ao tipo clicado no treemap: custo por voto e gasto do tipo, com identificacao da despesa; sem selecao, mostram os totais gerais e a despesa lider;
- treemap por `tipo_despesa`, com área proporcional ao valor gasto;
- percentual do gasto em cada quadrante e detalhes de valor e custo por voto no hover;
- card direito com custo por voto municipal ou por mesorregiao;
- clique em um tipo de despesa no treemap para filtrar o painel direito; o padrao mostra o gasto total;
- o parquet territorial rateia o gasto total proporcionalmente aos votos e nao informa o tipo por local. Para o filtro, aplica-se a participacao estadual do tipo ao rateio territorial. O custo por voto resultante e uniforme entre territorios e deve ser lido como estimativa, nao como despesa local observada.

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
- Quatro atributos em colunas compactas, separados por divisorias sutis: categoria dominante e seu respectivo `pct_*_principal`.
- O card nao exibe a confianca do modelo nem a antiga legenda explicativa dos percentuais.

`_icp_general_row()` identifica persona e categorias dominantes pelo volume de `votos_candidato`. `_demographic_percent()` calcula a media ponderada dos percentuais da categoria escolhida, usando os votos como peso. Nos parquets inspecionados, os percentuais gerais se repetem entre territorios; nao devem ser somados. A confianca ainda e calculada internamente, mas nao aparece no card porque pode ser confundida com confianca estatistica.

#### 2.2 BASE ELEITORAL DO CANDIDATO

Fonte: `perfil/stage04_icp_clusters_geo.parquet`.

`_cluster_profiles()` agrupa por `perfil_eleitor`. `cluster_cards_html()` apresenta:

- resumo por **Base eleitoral**, **Eleitor consolidado** e **Eleitor emergente**;
- cabecalho destacado com a pergunta sobre o peso de cada perfil na votacao;
- uma linha expansivel por ICP, com classificacao, identificador, persona, votos absolutos e participacao sempre visiveis;
- ao abrir cada perfil, quatro barras demograficas independentes e a justificativa em `cluster_strategy_reason`.

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

Os campos percentuais ja usam 0-100: `0.5` significa 0,5%. Percentuais demograficos ausentes ou fora de 0-100 nao sao inventados: os cards informam a ausencia.

Os quatro atributos sao dimensoes independentes, nao parcelas de uma soma de 100%. Os parquets descrevem categorias dominantes; nao permitem reconstruir a distribuicao completa de todas as categorias.

### 3. Demais secoes estruturadas

A pagina possui quatro secoes em `pages/dna_eleitor.py`. A estrutura e o status atual de cada uma sao:

- **Identidade da Base Eleitoral**: implementada com Eleitor ideal do candidato e cards da base eleitoral.
  - subtitulo: `Quem e o eleitor-chave e quais atributos definem o perfil do seu eleitor.`

- **Distribuicao do Perfil do Eleitorado**: grafico de rosca da distribuicao demografica estimada, com total de votos no centro, legenda e filtros de municipio e dimensao (genero, faixa etaria, escolaridade e estado civil).
  - usa os parquets `demografico/stage02_*.parquet` e os votos municipais;
  - agrega os percentuais das categorias com peso em `QT_VOTOS_TOTAL` ou `qt_votos`;
  - apresenta uma dimensao por vez; os arquivos nao permitem contar cruzamentos individuais entre genero, idade e escolaridade;
  - subtitulo: `Distribuicao demografica estimada dos votos, com recorte por municipio e perfil.`

- **Matriz de Potencial Demografico**: mapa coropletico municipal comparando genero, idade e escolaridade do ICP com o Censo.
  - mapa coropletico municipal de MG;
  - seletor para **ELEITOR IDEAL** ou classificacao estrategica do ICP clusters;
  - aderencia demografica calculada pela proximidade, em pontos percentuais, nas tres dimensoes;
  - compatibilidade final e a media da aderencia demografica nas tres dimensoes, em escala de cor logaritmica;
  - municipios sem votos recebem zero de compatibilidade;
  - municipios sem votos ou sem dados completos continuam preenchidos com o verde mais claro.
  - subtitulo: `Comparativo entre o perfil do eleitor do candidato e a populacao local. Identificacao de sobre-representacao e frentes de expansao.`

- **Expansao & Oportunidades para 2030**: mapa municipal de protecao de base e expansao.
  - mapa municipal com quatro classes: verde (oportunidade alta e perfil aderente), azul (bases com muitos votos), amarelo (oportunidade com aderencia menor) e cinza (baixa similaridade, sem oportunidade relevante ou sem dados completos);
  - seletor para Eleitor Ideal ou classificacao do ICP clusters;
  - os cortes de potencial, similaridade e votos sao relativos ao ICP escolhido;
  - subtitulo: `Mapeamento em nivel de bairro e area ponderada. Localizacao dos clusters taticos e visualizacao de manchas de potencial de crescimento.`

### 4. Helpers visuais e renderizacao

A pagina 2 usa:

- `apply_shared_visual_model()`: aplica fundo, variaveis visuais, hero e estilos compartilhados;
- `render_page_header("dna")`: renderiza o cabecalho com texto da pagina 2;
- `major_section_header(...)`: renderiza os blocos de titulo/subtitulo no padrao da pagina 1;
- `render_electorate_distribution()`: monta o grafico de rosca e seus filtros.

Os componentes HTML compartilhados, o card geral e os cards de clusters sao renderizados com `st.html`.

## Cache e performance

O projeto usa cache do Streamlit nos pontos de maior custo:

- `hf_filesystem`: `@st.cache_resource`;
- `remote_data_files`: `@st.cache_data(ttl=600)`;
- `load_tables`: `@st.cache_data`;
- `load_parquet`: `@st.cache_data`;
- `load_geo_reference`: `@st.cache_data`.

As transformacoes visuais sao recalculadas em reruns, mas a leitura remota dos arquivos e das referencias geograficas fica cacheada.

## Estado interativo

O recorte territorial selecionado no mapa de bairros e persistido apenas na secao de demografia em:

```python
st.session_state["pagina1_demographic_territorial_context"]
```

Esse contexto e usado para recalcular apenas:

- grafico demografico;
- legenda do recorte ativo.

Os filtros de mesorregiao e municipio limitam o mapa de bairros e o grafico demografico. Alterar qualquer um deles limpa a selecao anterior de bairro.

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
python -m py_compile app.py hf_sync.py pages\shared_header.py pages\raio_x_do_voto.py pages\dna_eleitor.py pages\dna_distribution.py pages\cluster_cards.py pages\demographic_comparison.py pages\dna_copy.py
```

### Validacao da secao DNA

Foram verificadas as somas de votos e participacoes e os percentuais demograficos com os parquets de Beatriz Cerqueira e Joao Vitor Xavier. O comparativo foi exercitado com `streamlit.testing.v1.AppTest`, incluindo as quatro dimensoes e fontes parciais. Essas verificacoes foram executadas durante o desenvolvimento, sem suite persistida no repositorio. A inspecao visual em navegador continua necessaria para validar layout desktop e mobile.
