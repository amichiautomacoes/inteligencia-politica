# Inteligência Política

Dashboard Streamlit para análise territorial, demográfica, financeira e parlamentar da votação de deputados.

## Páginas

A aplicação possui três páginas navegáveis:

- **Raio X Eleitoral** — mapas de votação estadual e municipal, concentração territorial, atuação parlamentar e custo do voto.
- **DNA Eleitoral** — perfil estratégico da base eleitoral, ICP, distribuição demográfica e potencial.
- **Expansão 2030** — oportunidades territoriais para 2030, com mapa municipal por classes.

As páginas são as únicas entradas do Streamlit e ficam em `pages/`:

```text
pages/
├── raio_x_do_voto.py
├── dna_eleitor.py
└── expansao_2030.py
```

## Estrutura do projeto

```text
.
├── app.py                         # Entrada, configuração e navegação
├── hf_sync.py                     # Leitura do Hugging Face e seleção dos parquets
├── pages/                         # As três páginas Streamlit
├── src/eleitoral/
│   ├── common/                    # Cabeçalho, estilo e textos editoriais
│   ├── maps/                      # GeoParquet, GeoJSON e Plotly
│   └── dna/                       # Componentes e cálculos do DNA Eleitor
├── assets/                        # Imagens usadas pela interface
├── Dockerfile                     # Imagem de produção
└── requirements.txt
```

Os módulos de `src/eleitoral` são importados pelas páginas. As malhas GeoParquet são lidas com pandas, convertidas para GeoJSON e entregues a `plotly.express.choropleth`.

No Raio X, o total de votos aparece no cabeçalho. O mapa estadual tem o card **Território líder** acima dele e quatro indicadores laterais. A seção de bairros usa o `stage01b_bairros.parquet` para associar votos à malha do município selecionado e calcular os cards de bairro. A malha detalhada só usa bairros ou áreas ponderadas quando os polígonos cobrem pelo menos 95% do território municipal; caso contrário, recorre à malha completa de setores censitários, incluindo os setores sem votos. A escala de cores é linear nos municípios com até 5 mil votos e logarítmica somente acima desse total. Quando uma unidade da malha abrange vários bairros eleitorais, o hover mostra o total e os votos de cada bairro do TSE, sem expor o identificador geográfico. A taxa de penetração por bairros aguarda uma fonte para o total de bairros do município; o card mostra apenas quantos bairros têm voto. **Força da política local** aparece como seção com card vazio, reservada para análise futura. A seção de concentração reúne as roscas Top 1/5/15/20. O mapa parlamentar traz a explicação das classes na própria legenda. Na seção de custos, treemap e gráfico territorial ocupam cards lado a lado.

## Dados do Hugging Face

Configure as variáveis no ambiente de execução. O token não deve ser versionado:

```env
HF_BUCKET_URL="hf://buckets/amichianalista/mkt-politico"
HF_VISUALIZACAO_PREFIX="deputados"
HF_GEOGRAPHY_PREFIX="IBGE/malha_mapas"
HF_GEOGRAPHY_REFERENCE_PREFIX="IBGE/MG/dadosterritorio"
HF_TOKEN="seu_token"
```

`HF_VISUALIZACAO_PREFIX` aponta para os dados eleitorais dos candidatos. `HF_GEOGRAPHY_PREFIX` aponta para as malhas otimizadas dos mapas. `HF_GEOGRAPHY_REFERENCE_PREFIX` aponta para as tabelas de referência territorial, que permanecem na pasta original.

As principais malhas são:

- `MG_municipios_2022.parquet`
- `MG_mesorregioes_2022.parquet`
- `MG_AreaPonderada_CD2022.parquet`
- `MG_bairros_CD2022.parquet`
- `MG_setores_mapa_CD2022.parquet`

As tabelas `municipios_mg_mesorregioes.parquet` e `setor_bairro_lookup.parquet` continuam em `HF_GEOGRAPHY_REFERENCE_PREFIX`.

## Execução local

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

O endereço padrão local é `http://localhost:8501`.

Para verificar a estrutura e os imports:

```powershell
python -m compileall -q app.py pages src
rg -n "from pages|import pages" -g "*.py" .
```

A segunda busca deve não retornar referências antigas aos módulos auxiliares.

## Docker

A imagem usa Streamlit na porta `8502`:

```powershell
docker build -t inteligencia-politica .
docker run --env-file .env -p 8502:8502 inteligencia-politica
```

O `Dockerfile` copia `pages`, `src`, `assets` e `hf_sync.py` para a imagem e inicia:

```text
streamlit run app.py --server.port=8502 --server.address=0.0.0.0
```

No painel de deploy, use:

- Repositório: `amichiautomacoes/inteligencia-politica`
- Branch: `main`
- Caminho de build: `/`
- Porta: `8502`

## Mapas

Os mapas eleitorais e o mapa parlamentar usam coropléticos Plotly. O fluxo das malhas é:

```text
GeoParquet → pandas → geometria WKB → GeoJSON → Plotly
```

As geometrias são convertidas para `EPSG:4326`, e os carregamentos são armazenados em cache pelo Streamlit. Se uma malha não puder ser lida, a interface informa o prefixo configurado e o erro original.

No mapa parlamentar, as cores representam **classes**, com título e explicação na legenda, e não uma escala de valores monetários.

Os scripts auxiliares em `scripts/` usam GeoPandas e têm a dependência separada em `scripts/requirements.txt`.

## Organização e manutenção

- Não coloque módulos auxiliares dentro de `pages`; isso evita que o Streamlit os trate como páginas.
- Não versione `.env`, tokens ou credenciais.
- Remova `__pycache__` antes de empacotar manualmente; o `.dockerignore` já os exclui da imagem.
- Depois de alterar os módulos, compile o projeto e teste o carregamento das três rotas antes do deploy.
