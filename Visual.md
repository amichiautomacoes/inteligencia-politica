# Briefing visual — Visualização Eleitoral

Este documento registra **a interface implementada hoje** nas três páginas do aplicativo. Ele descreve a aparência, a ordem de leitura, os controles, as respostas às interações e os estados sem dados. O [README](README.md) concentra a arquitetura e as fontes; aqui o foco é o que o usuário vê e entende. Textos que mencionam bairros na página Expansão 2030 descrevem rótulos atualmente presentes na interface: o mapa dessa página é municipal.

## 1. Visão geral da experiência

O produto é um painel de inteligência eleitoral para deputados, com três rotas. **Raio X Eleitoral** mostra a votação de 2022, sua distribuição territorial, concentração, atuação parlamentar e custo do voto. **DNA Eleitoral** sintetiza o eleitor predominante, os perfis estratégicos e a distribuição demográfica. **Expansão 2030** mostra oportunidades territoriais. As páginas compartilham candidato selecionado, fundo, hero, tipografia e família de cards.

O percurso é vertical. Uma capa apresenta o candidato; faixas de seção delimitam cada pergunta analítica; os cards abaixo contêm números, mapas ou gráficos. O app usa a barra lateral nativa do Streamlit para escolher o deputado e navegar entre páginas. Um controle segmentado dentro da capa também alterna as três rotas e indica qual está ativa.

### 1.1 Sistema visual compartilhado

| Elemento | Aparência atual | Função |
| --- | --- | --- |
| Fundo da página | Imagem `assets/background.png`, cobrindo a área de conteúdo, centralizada e fixa | Criar profundidade sem disputar atenção com os dados |
| Hero | Retângulo amplo com imagem escurecida, gradiente azul quase preto, borda clara fina e sombra profunda; cantos retos | Abrir a narrativa e identificar o candidato |
| Faixa principal de seção | Card de cantos arredondados, gradiente azul, brilho radial discreto e barra vertical branca/azul à esquerda | Separar os grandes capítulos da análise |
| Cabeçalho interno | Card azul mais leve, com título e subtítulo em duas linhas de hierarquia | Introduzir uma visualização dentro da seção |
| Cards de conteúdo | Azul profundo translúcido, borda azul clara fina, sombra e leve blur | Agrupar informação sem esconder o fundo |
| Gráficos Plotly | Fundo transparente, textos claros e grades discretas | Integrar gráfico e card |
| Mapas | Coropléticos Plotly nas três páginas, sem mapa-base de ruas | Mostrar votos por intensidade, malhas neutras ou oportunidades por classe |
| Mensagens de ausência | Aviso ou informação textual dentro do espaço da visualização | Explicar falta de dados sem simular um resultado |

A base cromática é `#eaf2ff` para texto, `#f8fbff` para títulos e números, `#b7c7e6` para descrição e legendas. Os cards usam gradientes próximos de `rgba(11,31,77,.76)` e `rgba(7,24,54,.68)`, com bordas azuis próximas de `rgba(59,130,246,.24)`. Azul claro (`#60a5fa`), azul médio (`#2563eb`) e azul profundo (`#0b1f4d`) expressam intensidade ou seleção; verde, amarelo, laranja e cinza têm significado específico nos mapas categóricos.

Os preenchimentos dos mapas são opacos e aparecem sobre fundo transparente, sem nomes de ruas sob os polígonos. Os tooltips usam fundo escuro e texto claro. Os 853 municípios de Minas Gerais compõem os mapas estaduais; os polígonos municipais são simplificados com tolerância pequena para preservar a leitura dos limites. O mapa detalhado usa bairros oficiais quando a malha cobre pelo menos 95% do município; caso contrário, tenta áreas ponderadas com ao menos quatro unidades e cobertura equivalente, e recorre à malha completa de setores censitários quando necessário.

### 1.2 Hierarquia de texto e formatação

O hero usa título grande e pesado, subtítulo menor e nome/cargo em maiúsculas. Os títulos principais de seção são largos, brancos e densos; subtítulos ficam em azul claro. Labels de KPI são pequenos; o valor tem protagonismo. Cards e legendas não devem exigir que a cor sozinha explique um resultado: os textos e tooltips dão o nome da categoria, a unidade e o recorte. Números de votos usam separador de milhar; percentuais e valores monetários aparecem com unidade explícita. Onde os dados são estimados ou rateados, a interface informa isso junto à visualização.

### 1.3 Capa comum às três páginas

O hero contém, nesta ordem, o título da página, um subtítulo curto e uma linha com foto à esquerda e dados do deputado à direita. A foto é vertical, com cantos levemente arredondados, borda clara e sombra; quando não há imagem remota, o espaço permanece como um bloco neutro. Os dados aparecem como `NOME:` e `CARGO:` em caixa alta. No Raio X, o card `TOTAL DE VOTOS` aparece logo abaixo do cargo. O ano integra o título do Raio X. **O hero atual não mostra partido.**

No canto superior direito há uma cápsula de três opções: **Raio X Eleitoral**, **DNA Eleitoral** e **Expansão 2030**. A opção ativa recebe fundo azul mais claro e texto branco. A cápsula faz parte do hero e usa links para as rotas da aplicação; o deputado selecionado na barra lateral é preservado na sessão.

| Página | Título do hero | Subtítulo |
| --- | --- | --- |
| Raio X | `RAIO X da votação 2022` (ano conforme o deputado) | `Análises descritivas geográficas e do perfil do eleitor na última eleição.` |
| DNA | `DNA do Eleitor` | `Quem é, onde está e como se comporta o eleitor determinante da candidatura.` |
| Expansão 2030 | `Expansão de votos para 2030` | `Oportunidades territoriais para ampliar a votação em 2030.` |

## 2. Página 1 — Raio X Eleitoral

A página segue a ordem: **Mapa Territorial da Votação → Votação por Bairros dentro dos municípios → Força da política local → Concentração territorial dos votos → Mapa da atuação parlamentar → Eficiência por Custo do Voto**. A primeira parte oferece localização e volume; a segunda aproxima o município; a seção de política local reserva espaço para análise futura; as três seguintes interpretam dependência territorial, emendas e gastos.

### 2.1 Mapa Territorial da Votação

**Pergunta visual:** onde estão os votos e quais localidades lideram?

A faixa **Mapa Territorial da Votação** apresenta o subtítulo `Leitura territorial do desempenho eleitoral no recorte ativo.`. Logo abaixo, antes do mapa e dos cards laterais, o card horizontal de **Território líder** destaca a mesorregião mais votada e seu volume. O total de votos do candidato fica no hero, abaixo do cargo. Os números são brancos, os rótulos menores, e as descrições usam azul acinzentado.

O seletor **Mesorregião / Município** fica sozinho no canto superior direito, dentro do card do mapa. Ele altera o agrupamento do mapa estadual.

O card do mapa ocupa **70% da largura** disponível e tem cerca de 560 px de altura. Os 30% restantes contêm quatro cards empilhados: **Município principal (Top 1)** (nome, participação no total e votos da cidade líder, com alerta acima de 30%), **Dependência do reduto principal** (parcela dos votos no município líder, com alerta acima de 30%), **Penetração territorial** (municípios com votos sobre os municípios do estado) e **Densidade média por município** (votos divididos apenas pelos municípios com voto). No modo municipal, cada município de Minas Gerais é um polígono Plotly; o hover informa nome e votos. A intensidade progride do azul muito claro ao azul profundo, com transformação logarítmica dos votos. No modo mesorregional, cada mesorregião é um único polígono da malha oficial, colorido pelo total de seus votos; o hover informa nome e votos da mesorregião. Áreas sem votos continuam desenhadas na cor mínima. As linhas visíveis correspondem à malha selecionada.

O gráfico de barras aparece em uma janela de detalhamento após o clique no mapa. No modo mesorregional, mostra todos os municípios da mesorregião selecionada. No modo municipal, mostra todos os bairros com registros de votos do município selecionado. A altura cresce conforme a quantidade de linhas, permitindo rolar a janela até o último território sem comprimir as barras. O comprimento expressa votos, a cor também varia em azul e o texto junto à barra traz votos e participação no recorte. O hover repete território, votos e percentual.

Se a malha ou os votos não puderem ser carregados, o mapa cede lugar a uma mensagem de indisponibilidade. O detalhamento também informa quando faltam dados. A interface não preenche municípios ou bairros com valores fictícios.

### 2.2 Votação por Bairros dentro dos municípios

Esta seção apresenta seletores de mesorregião e município e a distribuição de votos por bairro do `stage01b_bairros.parquet`. A mesorregião filtra os municípios disponíveis no segundo seletor. A geometria usa bairros oficiais quando seus polígonos cobrem pelo menos 95% do município. Se a cobertura for menor, usa áreas ponderadas quando existem pelo menos quatro unidades e elas alcançam a mesma cobertura mínima; nos demais casos, usa todos os setores censitários do município, inclusive aqueles sem votos. Um contorno branco mais espesso preserva a silhueta municipal sobre qualquer uma dessas subdivisões. A cor usa os mesmos cinco tons de azul do mapa estadual. Dentro do município selecionado, os votos por polígono usam escala linear relativa ao maior valor local quando o candidato recebeu até 5 mil votos no município; a transformação logarítmica é aplicada somente quando o total municipal ultrapassa 5 mil votos. Nas malhas de bairros e áreas ponderadas, a intensidade também é multiplicada pela raiz quadrada da proporção de polígonos com votos, mantendo a faixa cromática fixa de zero a um. No fallback por setores censitários, a escala local ocupa toda a faixa de zero a um, sem esse fator de cobertura, para que os poucos setores associados aos registros eleitorais permaneçam visíveis. O hover mostra o total e os bairros eleitorais associados; o nome oficial aparece quando a própria malha ou a tabela auxiliar o fornece. Quando um polígono abrange vários bairros do TSE, todos aparecem na lista. Códigos das unidades geométricas não aparecem na visualização.

À direita, cinco cards mostram, nesta ordem, **Total de votos** (total municipal e mesorregião), **Bairro principal (Top 1)**, **Dependência do bairro principal**, **Penetração por bairros** e **Densidade média por bairro**. Os cálculos usam nomes de bairros do `stage01b_bairros.parquet`, agrupados dentro do município selecionado; não usam a contagem de unidades geométricas. Como esse arquivo contém apenas bairros com votos, o card de penetração mostra a quantidade de bairros com voto e informa que o total de bairros do município está indisponível. A proporção será calculada quando houver uma fonte para esse denominador.

### 2.3 Força da política local

A faixa principal usa o título `Força da política local` e o subtítulo `Veja se vereadores e prefeitos das cidades foram decisivos na sua votação`. Logo abaixo há um card vazio de largura total, reservado para conteúdo futuro. A seção ainda não apresenta métricas nem conclusões.

### 2.4 Concentração territorial dos votos

**Pergunta visual:** a candidatura depende de poucos redutos ou distribui votos por muitos municípios?

Uma faixa principal apresenta o título e a frase `Quanto da votação total está concentrada nos municípios onde o candidato mais recebeu votos.`. O conteúdo está em um único card. Na parte superior há **quatro cards**: Top 1, Top 5, Top 15 e Top 20. Cada um mostra votos acumulados e uma rosca Plotly com o percentual acumulado em relação a 100% dos votos. O Top 1 mostra o nome do município líder; os demais mostram a quantidade de municípios. As roscas usam tons de azul da mesma família; o texto de instrução de clique não aparece abaixo delas.

Um clique na rosca abre uma janela com a composição incremental até aquele Top: Top 1, municípios 2 a 5, 6 a 15 e 16 a 20, conforme o card selecionado. Cada etapa mostra sua contribuição percentual e votos absolutos, seguida do total acumulado. Abaixo, uma frase automática nomeia o líder e destaca o peso dos 15 municípios principais. Os nomes completos estão em expansores `Ver municípios do Top 5`, `Top 15` e `Top 20`, com posição numérica.

Ao final, uma curva Plotly mostra a participação acumulada em função da posição do município. A linha azul, a área translúcida, os marcadores e as referências percentuais permitem ver a velocidade da concentração. A curva limita a exibição aos **Top 50** quando a base é maior; uma legenda informa esse corte. Com menos municípios, usa todos. Sem linhas municipais válidas, o card exibe aviso e não fabrica uma curva.

### 2.5 Mapa da atuação parlamentar de acordo com os votos

**Pergunta visual:** onde os votos recebidos encontram as emendas destinadas pelo parlamentar?

A faixa principal traz o título completo e explica o índice de retorno parlamentar. Em seguida há **três KPIs**: **Taxa de Reciprocidade** (parcela das emendas destinada aos três maiores redutos), **Maior Beneficiado (R$)** (município, valor e votos) e **Média R$/Voto** (valor estadual por voto). Os cards seguem a mesma família visual dos KPIs territoriais.

O mapa Plotly ocupa um card de largura total e aproximadamente **610 px** de altura. Cada município recebe uma categoria. A legenda fica à direita, no próprio mapa, com título e explicação breve junto a cada cor: **azul** para reduto atendido, **verde** para investimento, **amarelo** para reduto desassistido, **laranja** para baixa expressão, **cinza** para votos sem emendas e **branco** para ausência de ambos. A cor é **classe**, não escala monetária. O hover traz município, categoria, votos e emendas. O valor financeiro não modifica a intensidade do preenchimento.

O mapa depende de votos e emendas do candidato. Se a combinação não estiver disponível, o card mostra `Mapa parlamentar indisponível.`. Os KPIs também têm rótulos de ausência ou zero quando faltam dados.

Ao clicar em um município no mapa parlamentar, uma janela mostra os votos, a categoria, o total indicado de emendas e uma tabela por finalidade e tipo de indicação. A tabela agrega os valores indicados das emendas registradas para o município; pagamentos podem ser diferentes. O card do mapa não acrescenta preenchimento lateral interno.

### 2.6 Eficiência por Custo do Voto

**Pergunta visual:** que tipos de despesa dominam os gastos e qual o custo estimado por voto nos territórios?

A seção abre com faixa principal e a frase `Participação de cada tipo de despesa nos gastos totais da campanha.`. Antes dos gráficos há **três KPIs**: custo por voto, gasto total e despesa líder. Sem seleção, retratam a campanha inteira. Ao clicar em uma despesa no treemap, os rótulos e valores passam a refletir o tipo escolhido.

Os gráficos ficam em **dois cards lado a lado**, com o treemap à esquerda e o custo territorial à direita. Em telas estreitas, as colunas do Streamlit podem se empilhar. O primeiro, `Gastos por tipo de despesa`, é um **treemap Plotly** de cerca de 600 px de altura. A área de cada retângulo corresponde ao valor gasto no tipo; o texto apresenta tipo e participação no gasto. A borda fina separa os retângulos. O hover detalha total em reais, participação e custo por voto. O clique seleciona uma despesa e atualiza o gráfico territorial ao lado.

O segundo card, `Custo por voto territorial · Gasto total`, muda o sufixo para a despesa selecionada. O botão **Mostrar gasto total** restaura o estado inicial. Um rádio horizontal alterna **Municípios / Mesorregiões**. O gráfico tem cerca de 560 px de altura e mostra até 15 municípios ou todas as mesorregiões, com custo de referência em reais por voto. O novo parquet repete o total da campanha de cada tipo de despesa em todos os municípios; o gráfico conta esse total uma vez e o divide pelos votos do território. O hover mostra o total usado e os votos. O resultado não representa despesa local observada. Na ausência do novo parquet, a interface usa o rateio territorial anterior e informa essa condição.

## 3. Página 2 — DNA Eleitoral

Depois do hero comum, a página apresenta **três faixas principais** nesta ordem: Identidade da Base Eleitoral, Distribuição do Perfil do Eleitorado e Matriz de Potencial Demográfico. O card Eleitor ideal do candidato aparece na primeira faixa. A seção de distribuição vem em seguida, depois o card BASE ELEITORAL DO CANDIDATO; o mapa de potencial fecha a página. Sunburst, heatmap e composição demográfica por pontos não pertencem à interface atual.

### 3.1 Identidade da Base Eleitoral

**Pergunta visual:** quem é o eleitor predominante do candidato?

A faixa principal usa o subtítulo `Quem é o eleitor-chave e quais atributos definem o perfil do seu eleitor.`. Ela é seguida pelo card de eleitor ideal, ocupando a largura do conteúdo.

#### 3.1.1 Eleitor ideal do candidato

O primeiro card tem borda azul clara, fundo profundo e espaçamento amplo. O título `Eleitor ideal do candidato` aparece antes da descrição `Síntese do perfil demográfico predominante na base eleitoral do candidato.`. A persona, precedida do emoji de pessoa, é o ponto central e recebe tamanho e peso maiores. Quando o resumo agrega informação, ele aparece abaixo com emoji de fala; se apenas repete a persona, é ocultado. **A confiança do modelo não aparece no card.**

Na base do card, **quatro colunas compactas** apresentam Gênero, Faixa etária, Escolaridade e Estado civil. Cada coluna contém um emoji colorido de identificação, a categoria dominante e seu percentual em azul claro. Divisórias sutis substituem caixas individuais. Os percentuais das quatro dimensões são independentes; não formam fatias de uma soma de 100%. Se o percentual não é válido ou não existe, o card não inventa o número.

### 3.2 Distribuição do Perfil do Eleitorado

**Pergunta visual:** como se repartem as categorias demográficas e quais perfis sustentam a candidatura?

A faixa principal traz `Distribuição demográfica estimada dos votos, com recorte por município e perfil.`. Primeiro aparece a distribuição; logo abaixo, ainda nesta mesma faixa principal, vem o painel **BASE ELEITORAL DO CANDIDATO**.

#### 3.2.1 Distribuição do eleitorado

O conteúdo está em um card de borda fina. Dentro dele, o título menor `Distribuição do eleitorado` e uma legenda explicam que as parcelas são estimadas.

A composição usa **gráfico à esquerda e filtros à direita** (proporção aproximada 2,3:1). À direita há uma chamada `Refine a distribuição`, um seletor **MUNICÍPIO** com opção `Todos os municípios` e um seletor **PERFIL DEMOGRÁFICO** com Gênero, Faixa etária, Escolaridade e Estado civil. O município altera o universo de votos; a dimensão altera as fatias.

À esquerda, uma badge indica a categoria dominante da dimensão selecionada. A **rosca Plotly** tem centro vazado amplo, total de votos em tipografia forte no miolo e subtítulo menor em azul acinzentado. Os percentuais ficam fora da rosca, ligados às respectivas fatias por linhas. O hover mostra categoria e participação. À direita, abaixo dos seletores, a legenda mostra cor, categoria e percentual, sem votos estimados. Para gênero, feminino usa azul, masculino usa laranja e não informado usa cinza. O gráfico mostra **uma dimensão por vez**. A nota abaixo afirma que os parquets não permitem cruzar diretamente idade, gênero e escolaridade de indivíduos. Dados ausentes geram mensagem no lugar da rosca.

#### 3.2.2 BASE ELEITORAL DO CANDIDATO

O segundo bloco é um painel próprio, com título em caixa alta e pergunta `Quais perfis sustentam a candidatura e qual o peso de cada um na votação?`. Uma **barra de composição** apresenta a participação das classificações na votação do candidato: azul para Base eleitoral, ciano para Eleitor consolidado e verde para Eleitor emergente. A legenda abaixo identifica cada segmento e seu percentual. Uma classificação vazia apresenta travessão; uma parcela sem classificação aparece em cinza azulado.

A lista abaixo contém **uma linha expansível por ICP**, ordenada dentro da classificação pelo peso eleitoral. A linha fechada mostra uma badge de maturidade (`🎯 Base Principal`, `🛡️ Consolidado` ou `🚀 Emergente / Expansão`), identificador ICP, atributos demográficos dominantes em chips, percentual da votação e votos absolutos; uma seta sugere abertura. A linha aberta recebe borda mais clara e revela quatro blocos demográficos em grade de duas colunas. Cada bloco mostra dimensão, categoria dominante, percentual e uma barra azul individual. Uma nota esclarece que os percentuais descrevem categorias dominantes **dentro do perfil**. O bloco final `Leitura estratégica` traz a justificativa textual disponível. Dois ICPs com o mesmo rótulo estratégico continuam separados. Ausência de perfis gera mensagem, não um ICP fictício.

### 3.3 Matriz de Potencial Demográfico

Esta seção está em preparação para receber as métricas de potencial. A faixa principal mantém o subtítulo `Comparativo entre o perfil do eleitor do candidato e a população local. Identificação de sobre-representação e frentes de expansão.`.

Logo após a faixa principal, o card interno **Potencial demográfico municipal** introduz uma estrutura em duas colunas, na proporção aproximada de 70% para o mapa e 30% para os cards laterais. À esquerda, seletores de **Mesorregião** e **Município** controlam a malha exibida. A formação territorial reutiliza exatamente a lógica do mapa detalhado do Raio X: bairros oficiais quando cobrem pelo menos 95% do município, áreas ponderadas com ao menos quatro unidades e cobertura equivalente e, nos demais casos, a malha completa de setores censitários.

Por enquanto, todos os polígonos aparecem no mesmo azul muito claro (`#e8f1ff`), com divisórias azuladas e contorno municipal branco mais espesso, apenas para apresentar a geometria. Não há informação analítica, intensidade de cor, legenda nem tooltip de dados. À direita ficam **quatro cards vazios**, empilhados e reservados para as próximas métricas. Se a malha não puder ser carregada, o card do mapa mostra uma mensagem de indisponibilidade.

## 4. Página 3 — Expansão 2030

### 4.1 Expansão & Oportunidades para 2030

**Pergunta visual:** onde proteger a base existente e onde há oportunidade demográfica relativa ao ICP escolhido?

A faixa principal mantém o texto atual `Mapeamento em nível de bairro e área ponderada. Localização dos clusters táticos e visualização de manchas de potencial de crescimento.`. **A implementação exibida logo abaixo é municipal**: não há mapa de bairros nem de áreas ponderadas nesta seção. Um seletor à direita alterna **ELEITOR IDEAL** e classificações estratégicas.

Antes do mapa há uma **legenda de quatro cards**. Cada um combina amostra de cor, nome da classe e uma explicação curta: **verde** para oportunidade alta com perfil aderente, **azul** para base com muitos votos que pede proteção, **amarelo** para oportunidade com menor aderência e **cinza** para baixa similaridade ou informação insuficiente. A legenda torna o mapa categórico; cores não representam uma sequência contínua.

O mapa municipal é um **coroplético Plotly** de largura total e cerca de **640 px** de altura. Cada município recebe uma das quatro classes e a barra categórica do próprio Plotly permanece visível. O hover informa nome, classe, votos, oportunidade e similaridade. A nota inferior explicita que os limites de votos, similaridade e potencial são relativos ao perfil selecionado e que potencial demográfico **não é previsão de votos**. Se não houver dados completos de Censo/potencial ou a malha municipal falhar, a seção mostra uma informação textual no lugar do mapa.

## 5. Interação, estados e continuidade visual

### 5.1 Escopo dos controles

| Controle | Onde atua | Persistência observável |
| --- | --- | --- |
| Deputado na barra lateral | Três páginas | Mesmo candidato ao trocar de rota |
| Cápsula Raio X / DNA / Expansão 2030 | Navegação | Opção ativa destacada no hero |
| Filtro territorial Mesorregião / Município | Mapa estadual do Raio X e conteúdo da janela aberta por clique | Restrito ao primeiro mapa |
| Mesorregião e município da votação por bairros | Malha intramunicipal e cinco cards laterais | Restrito à seção detalhada do Raio X |
| Tipo de despesa no treemap | KPIs de custo e gráfico territorial | Botão restaura gasto total |
| Município e dimensão da rosca DNA | Rosca e total do recorte | Restrito à seção de distribuição |
| Mesorregião e município da Matriz DNA | Malha neutra exibida na preparação do potencial | Restrito à Matriz de Potencial |
| Perfil para expansão | Classes e métricas do mapa de Expansão 2030 | Restrito à página de expansão |

### 5.2 Estado sem dados

Falta de parquet, malha ou dimensão não deve parecer valor zero. A implementação usa `st.info`, `st.warning`, captions ou cards com texto para explicar o que está ausente. Zero legítimo continua como valor ou cor mínima quando existe malha e a métrica pode ser calculada. Os mapas mantêm municípios ou setores sem votos visíveis onde a fonte geométrica está disponível. As notas analíticas permanecem próximas ao gráfico a que se referem.

### 5.3 Responsividade implementada

No hero, a cápsula de navegação, a foto e os textos se reorganizam em larguras menores por regras CSS próprias. Os KPIs da página 1 passam de linha para uma coluna em telas até cerca de **900 px**. A faixa Top 1/5/15/20 passa para duas colunas; a lista de municípios reduz colunas novamente abaixo de **600 px**. O card do eleitor ideal reduz sua grade de quatro para duas e depois uma coluna. No card dos ICPs, o resumo e as barras demográficas empilham abaixo de **600 px**; o cabeçalho de cada perfil pode quebrar em telas estreitas. A legenda de expansão passa de quatro para duas colunas abaixo de **900 px** e para uma abaixo de **560 px**.

Os pares de mapa e cards laterais da página 1, os gráficos de custos lado a lado e o par rosca/filtros do DNA são montados com `st.columns`; a experiência móvel também depende do empilhamento padrão do Streamlit. Nomes longos de município, persona e despesa podem quebrar linha. Tooltips complementam os rótulos que não cabem nos cards.

## 6. Critérios de fidelidade para futuras alterações

1. Preservar a diferença entre **intensidade** (gradiente azul contínuo) e **classe** (cores da atuação parlamentar e da expansão).
2. Manter a leitura em camadas: hero, faixa principal, cabeçalho interno quando necessário e conteúdo analítico.
3. Não apresentar os cards vazios de política local e potencial como se já contivessem conclusões.
4. Mostrar voto observado, estimativa demográfica, custo de referência, gasto rateado e potencial em seus papéis corretos, com unidades e notas visíveis.
5. Fazer seleção e estado vazio permanecerem compreensíveis sem depender só de cor.
6. Atualizar este briefing quando mudar texto, card, escala, interação, ordem de seção ou granularidade de mapa.
