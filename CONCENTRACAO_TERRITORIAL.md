# Concentração Territorial

Este documento explica como funciona a seção **Concentração Territorial** da Página 1 (`Raio X do voto`), incluindo origem dos dados, regras de cálculo e visualização.

## Objetivo

A seção mede quanto da votação total do candidato está concentrada nos municípios onde ele recebeu mais votos.

Em termos práticos, ela responde perguntas como:

- qual percentual dos votos está no município mais forte;
- quanto os 5, 10 ou 20 principais municípios concentram;
- quantos municípios são necessários para acumular determinada parcela da votação total.

## Posição na página

Atualmente, a seção é renderizada como a última seção da Página 1, abaixo de:

**Votação por Bairro de cada município e Perfil demográfico**

A chamada fica no final de `pages/raio_x_do_voto.py`:

```python
_render_accumulated_concentration_section(votos_municipio_df)
```

## Dados de entrada

A seção usa o dataframe `votos_municipio_df`, carregado por:

```python
votos_municipio_df = _read_selected_parquet("votos_municipio")
```

Esse tipo é resolvido em `hf_sync.py` para o parquet:

```text
territorio/stage01a_municipios.parquet
```

As colunas obrigatórias para a seção funcionar são:

- `nm_municipio`: nome do município;
- `qt_votos`: quantidade de votos do candidato no município.

A coluna `qt_secoes_com_voto` é opcional. Se existir, ela é agregada junto, mas não é usada diretamente na visualização atual.

## Preparação dos dados

A preparação acontece na função:

```python
_municipal_concentration_frame(df)
```

O processo é:

1. Verifica se o dataframe existe, se não está vazio e se contém `nm_municipio` e `qt_votos`.
2. Se existir a coluna `nivel_territorial`, mantém apenas linhas com valor `municipio`, quando esse recorte estiver disponível.
3. Normaliza o nome do município:

```python
result["nm_municipio"] = result["nm_municipio"].fillna("").astype(str).str.strip()
```

4. Converte `qt_votos` para número e troca valores inválidos por zero.
5. Remove municípios sem nome e municípios com zero voto.
6. Agrupa por município, somando os votos:

```python
result.groupby("nm_municipio", as_index=False).agg({"qt_votos": "sum"})
```

7. Ordena os municípios do maior para o menor número de votos.
8. Calcula o total de votos municipais válidos.

Se não houver votos válidos após esse tratamento, a seção mostra um aviso de dados indisponíveis.

## Cálculos

Depois da agregação municipal, a função cria quatro colunas principais.

### 1. Ranking do município

```python
rank_municipio = 1, 2, 3, ...
```

O município com mais votos recebe rank `1`, o segundo recebe rank `2`, e assim por diante.

### 2. Percentual individual de votos

```python
pct_votos = qt_votos / votos_total
```

Esse percentual representa a participação individual de cada município na votação total do candidato.

Exemplo:

```text
Município A = 1.000 votos
Total = 10.000 votos
pct_votos = 1.000 / 10.000 = 0,10 = 10%
```

### 3. Votos acumulados

```python
votos_acumulados = qt_votos.cumsum()
```

Essa coluna soma os votos em ordem decrescente de força eleitoral.

Exemplo:

```text
Rank 1: 1.000 votos -> acumulado 1.000
Rank 2:   700 votos -> acumulado 1.700
Rank 3:   300 votos -> acumulado 2.000
```

### 4. Percentual acumulado

```python
pct_acumulado = votos_acumulados / votos_total
```

Esse é o principal indicador da seção.

Ele mostra qual parcela da votação total está concentrada nos `N` municípios mais votados.

Exemplo:

```text
Top 10 municípios = 7.950 votos acumulados
Total = 10.000 votos
pct_acumulado = 7.950 / 10.000 = 79,5%
```

## Cards de resumo

A seção mostra quatro cards:

- `Top 1`
- `Top 5`
- `Top 10`
- `Top 20`

Cada card usa a função interna `pct_at(rank)`.

A lógica é:

```python
idx = min(rank, len(concentration_df)) - 1
return concentration_df.iloc[idx]["pct_acumulado"]
```

Isso significa:

- se houver pelo menos 20 municípios, `Top 20` mostra o percentual acumulado até o vigésimo município;
- se houver menos municípios do que o rank solicitado, usa o último município disponível;
- por isso, em uma base com apenas 12 municípios, `Top 20` equivale ao acumulado de todos os 12.

O texto principal da seção usa especificamente o `Top 10`:

```text
Os 10 principais municípios concentram X% da votação total.
```

## Gráfico de curva acumulada

O gráfico é gerado por:

```python
_accumulated_concentration_chart(concentration_df)
```

Ele é um gráfico de linha com área preenchida.

### Eixo X

```python
x = rank_municipio
```

Representa a quantidade de municípios acumulados.

Exemplo:

- `1` = apenas o município mais votado;
- `5` = soma dos 5 municípios mais votados;
- `10` = soma dos 10 municípios mais votados.

### Eixo Y

```python
y = pct_acumulado * 100
```

Representa o percentual acumulado da votação total, em escala de 0 a 100%.

### Linha e preenchimento

A linha mostra a velocidade de acumulação dos votos:

- subida muito rápida no início indica alta concentração territorial;
- subida mais gradual indica votação mais distribuída;
- quando a linha chega perto de 100%, significa que quase toda a votação foi acumulada.

### Hover

Ao passar o mouse, o gráfico mostra:

- Top N municípios;
- votos acumulados até aquele ponto;
- percentual acumulado da votação total;
- município localizado naquela posição do ranking.

## Pontos de referência no gráfico

A função:

```python
_concentration_reference_rows(concentration_df)
```

marca pontos específicos na curva:

- Top 1;
- Top 5;
- Top 10;
- Top 20;
- Top 50;
- Todos.

Um ponto só aparece se existir quantidade suficiente de municípios.

Por exemplo, se houver apenas 18 municípios, o ponto `Top 20` não é criado. Nesse caso, o ponto final será `Todos`.

## Formatação dos números

Percentuais são formatados por:

```python
_format_percent(value)
```

Ela recebe valores em escala decimal e exibe em percentual.

Exemplo:

```text
0.795 -> 79,5%
```

Números absolutos são formatados por:

```python
_format_number(value)
```

Exemplo:

```text
49781 -> 49.781
```

## Interpretação política

A leitura da seção é:

- `Top 1` alto: o candidato depende fortemente de um município principal;
- `Top 5` ou `Top 10` alto: votação concentrada em poucos redutos;
- curva muito inclinada no início: baixa dispersão territorial;
- curva mais suave: votação mais espalhada;
- necessidade de muitos municípios para chegar a 80% ou 90%: base territorial mais capilarizada.

Importante: a seção não usa o termo "capilaridade territorial" na interface. Ela mede concentração territorial por votos acumulados.

## Fallbacks e erros tratados

Se os dados municipais não estiverem disponíveis, a seção mostra:

```text
Nao encontrei dados municipais validos para calcular a concentracao territorial.
```

Se o dataframe de concentração estiver vazio no gráfico, é exibida uma figura vazia com a mensagem:

```text
Dados municipais indisponiveis.
```

## Funções envolvidas

As funções da seção são:

- `_municipal_concentration_frame`: prepara ranking, votos e percentuais acumulados;
- `_concentration_reference_rows`: escolhe os pontos de referência da curva;
- `_accumulated_concentration_chart`: monta o gráfico acumulado;
- `_render_accumulated_concentration_section`: renderiza título, cards, resumo textual e gráfico;
- `_format_percent`: formata percentuais;
- `_format_number`: formata números absolutos.
