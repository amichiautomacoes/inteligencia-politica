# Visualizacao Eleitoral

Aplicacao Streamlit para leitura territorial e demografica da votacao de candidatos.

O app consome arquivos remotos do Hugging Face, configurados pelo `.env`, e apresenta a pagina principal **Raio X do voto**.

## Pagina 1: Raio X do voto

### 1. Cabecalho do candidato

Apresenta o contexto geral da analise:

- titulo da visualizacao: `RAIO X da votacao 2022`;
- foto do candidato, quando encontrada entre os arquivos remotos;
- nome, cargo e partido do candidato analisado.

### 2. Mapa Territorial da Votacao

Mostra a distribuicao geografica dos votos em Minas Gerais.

Esta secao traz:

- total de votos no recorte municipal;
- municipio mais votado;
- quantidade de municipios com votos;
- territorio lider por mesorregiao;
- filtro para alternar entre visualizacao por mesorregiao e por municipio;
- mapa coropletico de Minas Gerais com intensidade de votos;
- grafico lateral com o top 10 de concentracao territorial.

### 3. Concentracao Territorial

Resume o quanto a votacao esta concentrada nos principais municipios.

Esta secao traz:

- percentual acumulado de votos no Top 1, Top 5, Top 10 e Top 20 municipios;
- destaque textual para a concentracao dos 10 principais municipios;
- curva acumulada mostrando quantos municipios concentram determinada parcela da votacao total.

### 4. Votacao por Bairro e Perfil Demografico

Cruza o territorio selecionado com o perfil demografico estimado dos eleitores.

Esta secao traz:

- filtro de mesorregiao;
- treemap de votacao por municipio e bairro;
- selecao interativa no treemap para recortar os graficos demograficos;
- grafico de barras do perfil demografico, com filtros por:
  - genero;
  - idade;
  - escolaridade;
  - estado civil.

## Configuracao

Crie um arquivo `.env` com as variaveis necessarias:

```env
HF_BUCKET_URL="hf://buckets/..."
HF_VISUALIZACAO_PREFIX="deputados/estaduais/2022/nome_do_candidato"
HF_TOKEN="..."
```

## Rodar localmente

```powershell
pip install -r requirements.txt
streamlit run app.py
```
