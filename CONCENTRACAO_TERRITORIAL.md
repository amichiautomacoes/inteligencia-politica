# Concentracao Territorial

Este documento explica como funciona a secao **Concentracao Territorial** da Pagina 1 (`Raio X do voto`), incluindo origem dos dados, calculos e visualizacao atual.

## Objetivo

A secao mede quanto da votacao total do candidato esta concentrada nos municipios onde ele recebeu mais votos.

Ela responde perguntas como:

- qual percentual dos votos esta no municipio principal;
- quanto os Top 5, Top 10 e Top 20 municipios acumulam;
- quantos votos absolutos estao acumulados em cada faixa;
- como a curva de acumulacao evolui nos municipios mais fortes;
- se a votacao e concentrada em poucos redutos ou mais distribuida.

## Posicao na pagina

A secao e renderizada como a ultima secao da Pagina 1, abaixo de:

**Votacao por Bairro de cada municipio e Perfil demografico**

A chamada fica no final de `pages/raio_x_do_voto.py`:

```python
_render_accumulated_concentration_section(votos_municipio_df)
```

## Dados de entrada

A secao usa o dataframe `votos_municipio_df`, carregado por:

```python
votos_municipio_df = _read_selected_parquet("votos_municipio")
```

Esse tipo e resolvido em `hf_sync.py` para o parquet:

```text
territorio/stage01a_municipios.parquet
```

As colunas obrigatorias sao:

- `nm_municipio`: nome do municipio;
- `qt_votos`: quantidade de votos do candidato no municipio.

A coluna `qt_secoes_com_voto` e opcional. Se existir, ela e agregada junto, mas nao aparece diretamente na visualizacao atual.

## Preparacao dos dados

A preparacao acontece em:

```python
_municipal_concentration_frame(df)
```

Fluxo:

1. Valida se o dataframe existe, se nao esta vazio e se contem `nm_municipio` e `qt_votos`.
2. Se existir a coluna `nivel_territorial`, prioriza linhas com valor `municipio`.
3. Normaliza `nm_municipio`, removendo nulos e espacos extras.
4. Converte `qt_votos` para numero e troca valores invalidos por zero.
5. Remove municipios sem nome e municipios com zero voto.
6. Agrupa por municipio, somando votos.
7. Ordena do municipio mais votado para o menos votado.
8. Calcula o total de votos validos.

Se nao houver dados validos, a secao mostra um aviso e nao renderiza os cards/grafico.

## Calculos

Depois da agregacao municipal, sao criadas quatro colunas principais.

### Ranking

```python
rank_municipio = 1, 2, 3, ...
```

O municipio com mais votos recebe `1`, o segundo recebe `2`, e assim por diante.

### Percentual individual

```python
pct_votos = qt_votos / votos_total
```

Representa a participacao individual de cada municipio na votacao total.

### Votos acumulados

```python
votos_acumulados = qt_votos.cumsum()
```

Soma os votos seguindo a ordem do ranking.

Exemplo:

```text
Rank 1: 1.000 votos -> acumulado 1.000
Rank 2:   700 votos -> acumulado 1.700
Rank 3:   300 votos -> acumulado 2.000
```

### Percentual acumulado

```python
pct_acumulado = votos_acumulados / votos_total
```

Este e o indicador central da secao.

Exemplo:

```text
Top 10 municipios = 7.950 votos acumulados
Total = 10.000 votos
pct_acumulado = 7.950 / 10.000 = 79,5%
```

## Layout atual

A secao foi reorganizada em duas colunas.

### Coluna esquerda: resumo politico e metricas

A coluna esquerda contem:

- texto descritivo em destaque;
- mencao ao municipio principal;
- leitura do acumulado dos Top 10 municipios;
- grid 2x2 com os cards:
  - Top 1;
  - Top 5;
  - Top 10;
  - Top 20.

Cada card mostra:

- percentual acumulado;
- municipio de referencia;
- total de votos acumulados.

No `Top 1`, o municipio exibido e o principal municipio do candidato.

Nos demais cards, o texto mostra o municipio que fecha aquela faixa. Por exemplo, no `Top 10`, o municipio exibido e o decimo municipio do ranking, ou o ultimo disponivel se houver menos de 10 municipios.

### Coluna direita: grafico de concentracao

A coluna direita contem:

- toggle para expandir a visualizacao;
- legenda de foco quando o grafico esta limitado aos Top 50;
- grafico de curva acumulada.

O grafico tem altura reduzida para ficar mais proporcional dentro da coluna direita.

## Regra de Pareto / zoom inteligente

Por padrao, o grafico mostra apenas os **Top 50 municipios**.

Motivo:

- em bases grandes, como 526 municipios, a curva geralmente se aproxima de 100% cedo;
- depois do Top 50 ou Top 100, a linha tende a ficar quase plana;
- limitar a visualizacao inicial ajuda a enxergar a dinamica real de concentracao.

A funcao do grafico recebe o parametro:

```python
_accumulated_concentration_chart(concentration_df, max_rank=max_rank)
```

Quando `max_rank` e informado, o grafico filtra:

```python
chart_df = chart_df[chart_df["rank_municipio"].le(max_rank)]
```

Na interface:

- toggle desligado: mostra Top 50;
- toggle ligado: mostra todos os municipios.

O toggle usado e:

```python
st.toggle("Mostrar todos os municipios")
```

Quando o modo Top 50 esta ativo e existem mais de 50 municipios, a pagina mostra uma legenda:

```text
Visualizacao focada nos Top 50 de N municipios.
```

Importante: o zoom afeta apenas o grafico. Os calculos dos cards continuam usando a base completa.

## Grafico de curva acumulada

O grafico e gerado por:

```python
_accumulated_concentration_chart(concentration_df, max_rank=None)
```

### Eixo X

```python
x = rank_municipio
```

Representa a quantidade de municipios acumulados.

### Eixo Y

```python
y = pct_acumulado * 100
```

Representa o percentual acumulado da votacao total, de 0% a 100%.

## Estilo do grafico

O grafico usa Plotly com:

- linha principal azul clara;
- area preenchida em azul com baixa opacidade;
- fundo transparente para combinar com o layout escuro;
- pontos de referencia maiores, brancos, com borda azul;
- rotulos dos pontos em branco/brilhante;
- hover escuro com borda azul clara.

### Linhas de referencia

Foram adicionadas linhas horizontais sutis em:

- 25%;
- 50%;
- 75%;
- 90%.

Essas linhas sao adicionadas via `shapes` no layout do Plotly.

Tambem existem pequenas anotacoes no canto direito do grafico com os textos:

```text
25%, 50%, 75%, 90%
```

Isso facilita a leitura da curva sem depender apenas do eixo Y.

## Pontos de referencia

A funcao:

```python
_concentration_reference_rows(concentration_df)
```

marca os seguintes pontos, quando disponiveis:

- Top 1;
- Top 5;
- Top 10;
- Top 20;
- Top 50;
- Todos.

Se a base visivel tiver menos municipios do que algum ponto, esse ponto nao aparece.

Exemplo:

- no modo Top 50, os pontos podem ir ate Top 50;
- no modo completo, tambem pode aparecer o ponto Todos, quando diferente dos pontos padrao.

## Hover

Ao passar o mouse sobre a curva, o grafico mostra:

- Top N municipios;
- votos acumulados ate aquele ponto;
- percentual acumulado da votacao total;
- municipio localizado naquela posicao do ranking.

## Formatacao

Percentuais sao formatados por:

```python
_format_percent(value)
```

Ela recebe valores em escala decimal.

Exemplo:

```text
0.795 -> 79,5%
```

Numeros absolutos sao formatados por:

```python
_format_number(value)
```

Exemplo:

```text
49781 -> 49.781
```

## Interpretacao politica

Leitura sugerida:

- `Top 1` alto: dependencia forte de um municipio principal;
- `Top 5` alto: existencia de poucos redutos dominantes;
- `Top 10` alto: base muito concentrada nos principais municipios;
- curva muito inclinada no inicio: alta concentracao territorial;
- curva mais suave: votacao mais distribuida;
- necessidade de muitos municipios para chegar a 80% ou 90%: base mais espalhada territorialmente.

A interface nao usa o termo "capilaridade territorial". A metrica exibida mede concentracao territorial por votos acumulados.

## Fallbacks

Se os dados municipais nao estiverem disponiveis, a secao mostra:

```text
Nao encontrei dados municipais validos para calcular a concentracao territorial.
```

Se o dataframe do grafico estiver vazio, a figura exibe:

```text
Dados municipais indisponiveis.
```

## Funcoes envolvidas

- `_municipal_concentration_frame`: prepara ranking, votos e percentuais acumulados;
- `_concentration_reference_rows`: escolhe os pontos de referencia da curva;
- `_accumulated_concentration_chart`: monta o grafico acumulado e aplica zoom Top 50/todos;
- `_render_accumulated_concentration_section`: renderiza layout em duas colunas, cards, texto, toggle e grafico;
- `_format_percent`: formata percentuais;
- `_format_number`: formata numeros absolutos.
