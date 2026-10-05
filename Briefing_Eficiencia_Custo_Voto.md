# Briefing tecnico e visual - Eficiencia por Custo do Voto

Este documento descreve a secao **Eficiência por Custo do Voto** da pagina **Raio X Eleitoral**. Ele consolida a experiencia visual, o contrato de dados, os calculos, os estados de tela e os pontos de manutencao observados na implementacao atual.

Arquivo principal: `pages/raio_x_do_voto.py`

## 1. Objetivo analitico

A secao responde a duas perguntas:

- quais tipos de despesa concentraram o orcamento de campanha;
- qual e o custo estimado por voto quando o gasto total, ou um tipo de despesa selecionado, e comparado aos votos dos territorios.

A leitura correta e **eficiencia de referencia**, nao auditoria de gasto local observado. Quando existe `gastos_territoriais_por_tipo.parquet`, o valor do tipo de despesa e tratado como total de campanha repetido nas linhas municipais; por isso o dashboard divide esse total pelos votos do territorio. Quando esse arquivo nao existe, a secao usa o fallback `gastos_territoriais.parquet`, com rateio proporcional.

## 2. Posicao na pagina

A secao aparece na rota `/raio-x-eleitoral`, depois de:

1. Mapa de Força Eleitoral;
2. Votação por Bairros dentro dos municípios;
3. Força da política local;
4. Concentração territorial dos votos;
5. Mapa da atuação parlamentar de acordo com os votos.

Ela fecha a pagina Raio X, funcionando como leitura financeira complementar as leituras territoriais e parlamentares anteriores.

## 3. Estrutura visual

A secao abre com a faixa principal padrao do projeto:

- titulo: `Eficiência por Custo do Voto`;
- subtitulo: `Participação de cada tipo de despesa nos gastos totais da campanha.`;
- mesma linguagem visual das demais faixas principais: fundo azul profundo, borda fina, brilho discreto e barra vertical clara a esquerda.

Logo abaixo vem uma linha de **tres KPIs**, antes dos graficos:

- **Custo por voto (total geral)** ou **Custo por voto**, quando ha filtro;
- **Total gasto** ou **Gasto no tipo selecionado**;
- **Despesa líder** ou **Tipo de despesa selecionado**.

Os KPIs usam a familia visual `.raiox-heatmap-kpi`: tres colunas, borda clara, fundo transparente, label pequeno em caixa alta, valor branco em destaque e caption discreta quando aplicavel.

Abaixo dos KPIs, o conteudo principal se divide em **dois cards lado a lado** por `st.columns(2, gap="large")`:

- card esquerdo: treemap `Gastos por tipo de despesa`;
- card direito: dispersao `Matriz de eficiencia territorial · Gasto total` ou `Matriz de eficiencia territorial · {tipo selecionado}`.

Em telas estreitas, o empilhamento segue o comportamento padrao do Streamlit.

## 4. Card esquerdo - Gastos por tipo de despesa

O card esquerdo mostra um treemap Plotly de aproximadamente **600 px** de altura.

### Aparencia

- cada retangulo representa um tipo de despesa;
- a area do retangulo corresponde a `valor_total_despesa`;
- a paleta varia de azul profundo `#0b1f4d` a ciano `#60a5fa`;
- quanto maior o valor da despesa, mais clara tende a ser a cor;
- as bordas internas usam linha clara fina `rgba(191,219,254,0.55)`;
- o fundo do grafico e transparente;
- a margem interna do Plotly e pequena (`8 px` em todos os lados);
- a fonte segue `Segoe UI, Inter, sans-serif`.

O texto dentro de cada bloco usa:

```text
TIPO DE DESPESA
{percentual} do orçamento • {valor em reais}
```

Os nomes longos sao encurtados para caber melhor no treemap. Ha dois mapas de rotulos:

- `EXPENSE_TYPE_SHORT_LABELS`, para rotulos curtos de apoio;
- `EXPENSE_TREEMAP_LABELS`, para nomes em caixa alta exibidos no treemap.

Quando nao ha mapeamento explicito, o nome e normalizado, convertido para caixa alta e truncado acima de 30 caracteres.

Despesas pequenas que representam menos de 1,5% do orcamento cada sao agrupadas visualmente, depois dos quatro maiores tipos, no bloco **OUTRAS DESPESAS**. O agrupamento reduz a malha de micro-retangulos do treemap. Esse bloco mostra no hover quantos tipos foram agrupados e nao atua como filtro individual.

### Hover

O hover do treemap mostra:

- tipo de despesa completo;
- total gasto;
- participacao no orcamento;
- custo por voto daquele tipo.

### Selecao

O clique em um bloco do treemap seleciona aquele tipo de despesa como filtro mestre da secao.

Quando existe selecao:

- o titulo do card esquerdo muda para `Gastos por tipo de despesa · filtrando {tipo}`;
- o tipo selecionado fica em `#60a5fa`;
- os demais tipos ficam atenuados em `#1e3a5f`;
- os tres KPIs passam a refletir apenas o tipo selecionado;
- a matriz territorial a direita passa a usar o mesmo filtro e mostra uma tag com o nome do tipo selecionado.

O clique no mesmo item selecionado nao limpa o filtro. A limpeza acontece pelo botao **Mostrar gasto total**, exibido no card direito.

## 5. Card direito - Matriz de eficiencia territorial

O card direito mostra um grafico de dispersao Plotly com aproximadamente **560 px** de altura. Ele cruza participacao territorial na votacao com custo por voto e usa o tamanho da bolha para representar volume de votos.

### Controles

Quando ha um tipo de despesa selecionado, aparece o botao:

```text
Mostrar gasto total
```

Esse botao remove `pagina1_tipo_despesa_selecionado`, incrementa a revisao do treemap e força novo render.

Abaixo, ha um radio horizontal:

```text
Agrupar por: Municípios / Mesorregiões
```

O controle usa a chave `pagina1_custo_territorio`.

### Aparencia

- bolhas em escala azul/ciano, com borda clara discreta;
- eixo X com titulo `% da votacao do deputado`;
- eixo Y com titulo `Custo por voto (R$/voto)`;
- tamanho da bolha proporcional a `qt_votos`;
- grade discreta em branco translucido nos dois eixos;
- fundo transparente;
- sem legenda;
- rotula os principais territorios por votos para evitar excesso de texto;
- linhas pontilhadas indicam as medianas de participacao e custo;
- anotacoes ajudam a ler bases eficientes e redutos dispersos.

O quadrante inferior direito concentra bases eficientes: maior participacao na votacao e menor custo por voto. O superior esquerdo evidencia redutos dispersos: pouca participacao e custo teorico maior.

### Hover

O hover mostra:

- territorio;
- participacao nos votos do deputado;
- custo por voto;
- total usado no calculo;
- votos.

O label do total muda conforme a origem dos dados:

- com `gastos_territoriais_por_tipo.parquet`: `Total da campanha`;
- com fallback `gastos_territoriais.parquet`: `Gasto atribuído`.

### Nota explicativa

Quando existe `gastos_territoriais_por_tipo.parquet`, a legenda informa que o valor exibido e **custo de referencia**: o total da campanha para o tipo selecionado, ou todos os tipos, dividido pelos votos do territorio. A nota tambem explica que o parquet repete o total da campanha em cada municipio e nao registra gasto realizado em cada local.

Quando o app cai no fallback `gastos_territoriais.parquet`, a legenda informa que o gasto e atribuido proporcionalmente aos votos em cada territorio e que o parquet nao identifica o tipo de despesa por local.

## 6. Contrato de dados

### Entradas carregadas na pagina

No fim de `pages/raio_x_do_voto.py`, a secao recebe:

```python
despesas_campanha_df = _read_selected_parquet("despesas_campanha")
gastos_territoriais_df = _read_selected_parquet("gastos_territoriais")
gastos_territoriais_por_tipo_df = _read_selected_parquet("gastos_territoriais_por_tipo")
_render_cost_efficiency_section(
    votos_municipio_df,
    despesas_campanha_df,
    gastos_territoriais_df,
    gastos_territoriais_por_tipo_df,
)
```

Esses nomes sao resolvidos em `hf_sync.file_by_kind()`:

| Kind | Arquivo esperado | Uso |
| --- | --- | --- |
| `despesas_campanha` | `gastos/despesas_campanha.parquet` | Treemap e KPIs |
| `gastos_territoriais_por_tipo` | `gastos/gastos_territoriais_por_tipo.parquet` | Custo territorial de referencia por tipo |
| `gastos_territoriais` | `gastos/gastos_territoriais.parquet` | Fallback territorial com rateio |
| votos municipais | `territorio/stage01a_municipios.parquet` | Total de votos da campanha e denominador territorial |

### Colunas exigidas para o treemap

`_expense_cost_by_type_frame()` exige:

| Coluna | Uso |
| --- | --- |
| `tipo_despesa` | Agrupamento da despesa |
| `valor_despesa` | Valor monetario somado por tipo |

Tambem exige votos totais maiores que zero. Se nao houver `qt_votos` valido em `votos_df`, a tabela do treemap fica vazia.

### Colunas exigidas para custo territorial por tipo

`_territorial_expense_cost_by_type_frame()` exige:

| Coluna | Uso |
| --- | --- |
| `cd_municipio` | Deduplicacao municipal |
| `nm_municipio` | Rotulo e agrupamento municipal |
| `nm_mesorregiao` | Agrupamento mesorregional |
| `tipo_despesa` | Filtro por tipo selecionado |
| `valor_total_tipo_despesa` | Total de campanha daquele tipo |
| `qt_votos_municipio` | Denominador de votos |

### Colunas exigidas para fallback territorial

`_territorial_expense_cost_frame()` exige:

| Coluna | Uso |
| --- | --- |
| `qt_votos` | Denominador de votos |
| `valor_despesas_rateado` | Valor territorial ja rateado |
| `nm_municipio` | Agrupamento municipal |
| `nm_mesorregiao` | Agrupamento mesorregional |
| `nivel_territorial` | Opcional; prioriza `municipio`, depois `bairro` |

## 7. Pipeline tecnico

### 7.1 Total de votos

`_campaign_total_votes(votos_df)` calcula o total usado como denominador geral.

Regras:

- se `votos_df` e vazio ou nao tem `qt_votos`, retorna `0`;
- converte `qt_votos` para numerico;
- se existe `nm_municipio`, agrupa por municipio e soma;
- sem `nm_municipio`, soma todos os votos.

### 7.2 Agregacao de despesas por tipo

`_expense_cost_by_type_frame(despesas_df, total_votes)`:

1. valida `tipo_despesa`, `valor_despesa` e votos totais;
2. normaliza tipo vazio como `Nao informado`;
3. converte `valor_despesa` para numerico;
4. agrupa por `tipo_despesa`;
5. remove valores zerados;
6. calcula:
   - `valor_total_despesa`;
   - `qt_votos`;
   - `custo_por_voto = valor_total_despesa / total_votes`;
   - `pct_gasto = valor_total_despesa / total_spend`;
   - `pct_gasto_acumulado`;
   - rotulos formatados para moeda, percentual e nomes.

### 7.3 KPIs

`_cost_efficiency_kpis(chart_df, selected_expense)`:

Sem selecao:

- custo por voto = soma de todas as despesas / votos totais;
- total gasto = soma de todas as despesas;
- despesa lider = maior `valor_total_despesa`.

Com selecao:

- custo por voto = gasto do tipo selecionado / votos totais;
- total gasto = gasto do tipo selecionado;
- tipo selecionado aparece como terceiro KPI;
- caption mostra valor e percentual do gasto total.

Se `chart_df` estiver vazio:

- custo por voto = `R$ 0,00`;
- total gasto = `R$ 0,00`;
- despesa lider = `Sem dados`.

### 7.4 Treemap

`_expense_cost_by_type_chart(chart_df, selected_expense)`:

- monta `go.Treemap`;
- usa `valor_total_despesa` como `values`;
- usa `tipo_despesa_treemap` como `labels`;
- passa dados completos em `customdata`;
- define texto com percentual e valor inteiro;
- calcula cor interpolada entre `#0b1f4d` e `#60a5fa`;
- calcula cor do texto por luminancia para manter contraste;
- quando filtrado, destaca apenas o selecionado.

Se `chart_df` estiver vazio, retorna figura vazia com anotacao:

```text
Dados de despesas de campanha indisponíveis.
```

### 7.5 Selecao do treemap

`_selected_expense_from_treemap(event, chart_df)` tenta identificar o item clicado por:

1. `customdata[0]`, que carrega o `tipo_despesa` completo;
2. fallback por `label`, comparando com `tipo_despesa_treemap`.

Se encontrar uma despesa valida, grava em:

```python
st.session_state["pagina1_tipo_despesa_selecionado"]
```

Depois chama `st.rerun()`.

### 7.6 Custo territorial com arquivo por tipo

`_territorial_expense_cost_by_type_frame(gastos_por_tipo_df, selected_expense, territory)`:

1. valida as colunas obrigatorias;
2. converte votos e valores para numerico;
3. calcula `type_totals` usando o primeiro `valor_total_tipo_despesa` de cada tipo;
4. se existe filtro, usa apenas o total do tipo selecionado;
5. sem filtro, soma os totais dos tipos;
6. deduplica municipios por `cd_municipio`;
7. agrupa votos por municipio ou mesorregiao;
8. define `gasto_atribuido = campaign_spend` para cada territorio;
9. calcula `custo_por_voto = campaign_spend / qt_votos`;
10. ordena por `qt_votos` decrescente.

Essa regra e intencionalmente uma comparacao de referencia: cada territorio e comparado contra o mesmo total de campanha, variando apenas pelos votos do territorio.

### 7.7 Custo territorial com fallback rateado

`_territorial_expense_cost_frame(gastos_df, expense_share, territory)`:

1. valida as colunas obrigatorias;
2. se houver `nivel_territorial`, prioriza linhas `municipio`; se nao houver, usa `bairro`;
3. converte votos e valor rateado para numerico;
4. agrupa por municipio ou mesorregiao;
5. remove territorios sem votos;
6. calcula `gasto_atribuido = valor_despesas_rateado * expense_share`;
7. calcula `custo_por_voto = gasto_atribuido / qt_votos`;
8. ordena por `qt_votos` decrescente.

Com filtro de tipo, `expense_share` e o percentual daquele tipo no gasto total. Sem filtro, `expense_share = 1.0`.

### 7.8 Grafico territorial

`_territorial_expense_cost_chart(frame, territory, campaign_total)`:

- cria dispersao territorial;
- usa `% da votacao do deputado` no eixo X;
- usa `custo_por_voto` no eixo Y;
- usa `qt_votos` no tamanho da bolha;
- rotula os principais territorios por votos;
- usa `customdata` com territorio, total usado e votos;
- se o frame estiver vazio, mostra anotacao de indisponibilidade.

## 8. Estado e chaves de sessao

As chaves de estado da secao sao:

| Chave | Papel |
| --- | --- |
| `pagina1_tipo_despesa_selecionado` | Tipo de despesa ativo no filtro mestre |
| `pagina1_treemap_despesas` | Prefixo da chave do grafico Plotly |
| `pagina1_treemap_despesas_revisao` | Revisao usada para recriar o treemap ao limpar selecao |
| `pagina1_custo_territorio` | Radio `Municípios` / `Mesorregiões` |

Se o deputado muda, ou se o tipo salvo nao existe no novo `chart_df`, a selecao e descartada:

```python
if chart_df.empty or selected_expense not in chart_df["tipo_despesa"].values:
    selected_expense = None
    st.session_state.pop(EXPENSE_SELECTION_KEY, None)
```

## 9. Estados sem dados

A secao nao deve simular resultado.

Estados previstos:

- sem votos totais validos: o frame de despesas fica vazio;
- sem `despesas_campanha.parquet` valido: KPIs zerados e treemap com anotacao de indisponibilidade;
- sem dados territoriais validos: grafico territorial com anotacao `Dados territoriais de gastos indisponíveis.`;
- sem `gastos_territoriais_por_tipo.parquet`: usa `gastos_territoriais.parquet` como fallback e mostra caption explicando o rateio;
- sem ambos os arquivos territoriais: grafico territorial fica vazio, mantendo a estrutura da secao.

Zero legitimo deve aparecer como valor quando os dados existem; ausencia de dado deve aparecer como mensagem ou caption explicativa.

## 10. Semantica dos indicadores

### Custo por voto total

```text
soma(valor_despesa) / votos totais da campanha
```

### Custo por voto de um tipo

```text
valor_total_despesa_do_tipo / votos totais da campanha
```

### Participacao no orcamento

```text
valor_total_despesa_do_tipo / soma(valor_total_despesa)
```

### Custo territorial com arquivo por tipo

```text
total_de_campanha_do_tipo_ou_total_geral / votos_do_territorio
```

Este numero nao quer dizer que aquele valor foi gasto no territorio. Ele mede quanto o total da campanha representa quando dividido pela base de votos daquele territorio.

### Custo territorial com fallback rateado

```text
(valor_despesas_rateado_do_territorio * participacao_do_tipo) / votos_do_territorio
```

Se nao houver tipo selecionado, a participacao e `1.0`.

## 11. Formatacao numerica

As funcoes de formatacao seguem o padrao brasileiro:

- `_format_number`: milhar com ponto, sem casas decimais;
- `_format_percent`: uma casa decimal, virgula decimal e `%`;
- `_format_currency`: `R$`, milhar com ponto e duas casas decimais;
- `_format_currency_whole`: `R$` sem centavos.

Exemplos:

```text
12.345
18,7%
R$ 45.678,90
R$ 45.679
```

## 12. Criterios visuais de fidelidade

Ao alterar essa secao, preservar:

- faixa principal igual as demais secoes do Raio X;
- KPIs antes dos graficos;
- treemap a esquerda e custo territorial a direita;
- cor azul/ciano para intensidade financeira no treemap;
- destaque claro para o tipo selecionado;
- botao **Mostrar gasto total** apenas quando houver filtro ativo;
- radio horizontal de agrupamento territorial;
- fundo transparente dos graficos;
- notas explicativas proximas ao grafico territorial;
- diferenca textual entre **custo de referencia** e **gasto atribuido**.

## 13. Pontos de manutencao

Ao mudar nomes de arquivos, atualizar:

- `hf_sync.file_by_kind()`;
- `README.md`;
- este briefing.

Ao mudar texto, ordem, altura, cor ou interacao, atualizar:

- `Visual.md`;
- este briefing.

Ao mudar o calculo territorial, verificar explicitamente se o novo comportamento representa:

- gasto local observado;
- gasto rateado;
- ou custo de referencia por total de campanha.

Essa distincao precisa permanecer visivel na interface para evitar leitura financeira incorreta.

## 14. Funcoes relacionadas

Principais funcoes em `pages/raio_x_do_voto.py`:

| Funcao | Responsabilidade |
| --- | --- |
| `_render_cost_efficiency_section()` | Orquestra a secao inteira |
| `_campaign_total_votes()` | Calcula votos totais da campanha |
| `_expense_cost_by_type_frame()` | Agrega despesas por tipo |
| `_cost_efficiency_kpis()` | Calcula textos dos KPIs |
| `_render_cost_efficiency_kpis()` | Renderiza a linha de KPIs |
| `_expense_cost_by_type_chart()` | Monta o treemap |
| `_selected_expense_from_treemap()` | Extrai a despesa clicada |
| `_territorial_expense_cost_by_type_frame()` | Calcula custo territorial com arquivo por tipo |
| `_territorial_expense_cost_frame()` | Calcula fallback territorial rateado |
| `_territorial_expense_cost_chart()` | Monta a matriz territorial de eficiencia |

