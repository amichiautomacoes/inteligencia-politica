# Inteligência Política

Dashboard Streamlit para análise territorial, demográfica, financeira e parlamentar da votação de deputados.

## Páginas

A aplicação possui duas páginas navegáveis:

- **Raio X do voto** — distribuição territorial dos votos, concentração, perfil demográfico, gastos e atuação parlamentar.
- **DNA Eleitor** — perfil estratégico da base eleitoral, ICP, distribuição demográfica, potencial e expansão.

As páginas são as únicas entradas do Streamlit e ficam em `pages/`:

```text
pages/
├── raio_x_do_voto.py
└── dna_eleitor.py
```

## Estrutura do projeto

```text
.
├── app.py                         # Entrada, configuração e navegação
├── hf_sync.py                     # Leitura do Hugging Face e seleção dos parquets
├── pages/                         # Somente as duas páginas Streamlit
├── src/eleitoral/
│   ├── common/                    # Cabeçalho, estilo e textos editoriais
│   ├── maps/                      # GeoParquet, GeoJSON e Plotly
│   └── dna/                       # Componentes e cálculos do DNA Eleitor
├── assets/                        # Imagens usadas pela interface
├── Dockerfile                     # Imagem de produção
└── requirements.txt
```

Os módulos de `src/eleitoral` são importados pelas páginas. As malhas GeoParquet são lidas com pandas, convertidas para GeoJSON e entregues a `plotly.express.choropleth`.

## Dados do Hugging Face

Configure as variáveis no ambiente de execução. O token não deve ser versionado:

```env
HF_BUCKET_URL="hf://buckets/amichianalista/mkt-politico"
HF_VISUALIZACAO_PREFIX="deputados"
HF_GEOGRAPHY_PREFIX="IBGE/MG/dadosterritorio"
HF_TOKEN="seu_token"
```

`HF_VISUALIZACAO_PREFIX` aponta para os dados eleitorais dos candidatos. `HF_GEOGRAPHY_PREFIX` aponta para os GeoParquets e tabelas de referência territorial.

As principais malhas são:

- `MG_municipios_2022.parquet`
- `MG_mesorregioes_2022.parquet`
- `MG_AreaPonderada_CD2022.parquet`
- `MG_bairros_CD2022.parquet`
- `MG_setores_CD2022.parquet`
- `MG_setores_mapa_CD2022.parquet`
- `municipios_mg_mesorregioes.parquet`
- `setor_bairro_lookup.parquet`

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

Os mapas usam `plotly.express.choropleth`. O fluxo é:

```text
GeoParquet → pandas → geometria WKB → GeoJSON → Plotly
```

As geometrias são convertidas para `EPSG:4326`, e os carregamentos são armazenados em cache pelo Streamlit. Se uma malha não puder ser lida, a interface informa o prefixo configurado e o erro original.

Os scripts auxiliares em `scripts/` usam GeoPandas e têm a dependência separada em `scripts/requirements.txt`.

## Organização e manutenção

- Não coloque módulos auxiliares dentro de `pages`; isso evita que o Streamlit os trate como páginas.
- Não versione `.env`, tokens ou credenciais.
- Remova `__pycache__` antes de empacotar manualmente; o `.dockerignore` já os exclui da imagem.
- Depois de alterar os módulos, compile o projeto e teste o carregamento das duas rotas antes do deploy.
