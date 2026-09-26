# Visualizacao Eleitoral

Aplicacao Streamlit para leitura territorial, demografica, financeira e parlamentar da votacao de candidatos.

O app consome arquivos remotos do Hugging Face, configurados pelo `.env`, e apresenta a pagina principal **Raio X do voto**.

## Estrutura do projeto

- `app.py`: ponto de entrada Streamlit, configuracao de pagina e navegacao.
- `pages/raio_x_do_voto.py`: pagina principal da visualizacao.
- `pages/pagina_2.py`: pagina auxiliar ainda sem fluxo consolidado.
- `hf_sync.py`: leitura de `.env`, listagem remota no Hugging Face, cache e mapeamento dos parquets por tipo.
- `assets/background.png`: imagem de fundo usada no modelo visual.
- `Visual.md`: briefing visual do produto, separado da documentacao tecnica.

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
- foto do candidato, quando encontrada entre os arquivos remotos;
- nome, cargo e partido do candidato analisado.

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
python -m py_compile app.py hf_sync.py pages\raio_x_do_voto.py pages\pagina_2.py
```
