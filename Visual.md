# Direcao Visual do Projeto

Este documento descreve o projeto pelo vies visual, narrativo e de experiencia. Ele serve como briefing para evoluir a apresentacao das visualizacoes eleitorais, sem substituir o README tecnico.

## Objetivo Visual

O app deve parecer um painel politico-territorial premium: escuro, analitico, geografico e confiavel. A experiencia tem duas frentes principais:

- **Raio X Eleitoral**: leitura descritiva do desempenho do candidato.
- **DNA Eleitoral**: leitura estrategica do eleitor determinante, segmentos e oportunidades.

Na pagina **Raio X Eleitoral**, a narrativa precisa conduzir o usuario por:

- quem e o candidato;
- onde estao os votos;
- quanto a votacao esta concentrada;
- quem compoe o perfil demografico dos territorios;
- quanto custou conquistar votos em cada area;
- onde houve retorno parlamentar por meio de emendas.

Na pagina **DNA Eleitoral**, a narrativa deve conduzir o usuario por:

- quem e o eleitor-chave da candidatura;
- quais atributos definem a base eleitoral;
- onde ha frentes de conversao, consolidacao e expansao;
- onde o eleitor do candidato esta sobre ou sub-representado;
- quais bairros, areas ponderadas e clusters indicam oportunidade para 2030.

O resultado visual desejado e uma central de inteligencia eleitoral, nao uma pagina decorativa. O design deve ajudar a interpretar o territorio.

## Linguagem Visual Atual

### Paleta

A linguagem usa tom sobre tom em azul:

- fundo geral: azul muito escuro, quase noite;
- cards: azul petroleo profundo, translucido;
- bordas: azul claro sutil e luminosa;
- textos principais: branco frio;
- textos secundarios: azul acinzentado claro;
- graficos eleitorais: escala branco-azul;
- destaques pontuais: azul claro, ciano, verde e amarelo em visualizacoes especificas.

Cores de referencia:

- `#eaf2ff`: texto geral claro;
- `#f8fbff`: titulos, numeros e labels fortes;
- `#b7c7e6`: legendas e textos secundarios;
- `#60A5FA`, `#2563EB`, `#0B1F4D`: escala de intensidade territorial;
- `rgba(59, 130, 246, 0.20/0.24)`: bordas sutis dos cards;
- `rgba(11, 31, 77, 0.76)` e `rgba(7, 24, 54, 0.68)`: base dos cards.

### Cards

Todos os blocos visuais devem seguir o modelo monocromatico azul dos KPIs territoriais:

- fundo em azul profundo, nunca preto puro;
- borda fina azul-clara;
- leve sombra e blur;
- cantos arredondados moderados;
- conteudo com alta legibilidade;
- graficos transparentes integrados ao card.

Esse modelo vale para:

- KPIs;
- mapa principal;
- ranking lateral;
- treemap;
- demografia;
- curva acumulada;
- matriz de custo;
- mapa de emendas.
- secoes e cards da pagina DNA Eleitoral.

### Tipografia

A hierarquia atual e forte:

- hero com titulo grande e peso alto;
- titulos de secao grandes e claros;
- labels de KPI pequenos, em caixa alta;
- valores numericos grandes;
- legendas menores, azuladas e discretas.

Evitar textos longos dentro de cards pequenos. Municipios, mesorregioes e categorias demograficas podem ter nomes extensos.

## Estrutura da Experiencia

### 1. Hero do candidato

Funcao visual:

Apresentar imediatamente o candidato analisado e criar contexto editorial.

Composicao:

- bloco horizontal amplo;
- imagem de fundo escurecida;
- titulo conforme pagina ativa;
- subtitulo curto;
- foto do candidato;
- nome, cargo e partido em destaque.
- controle segmentado para alternar entre **Raio X Eleitoral** e **DNA Eleitoral**.

Direcao:

O hero deve parecer uma capa de analise politica. Foto e dados do candidato precisam ser reconhecidos sem competir com os graficos abaixo.

Comportamento por pagina:

- **Raio X Eleitoral**
  - titulo: **RAIO X da votacao 2022**;
  - subtitulo: **Analises descritivas geograficas e do perfil do eleitor na ultima eleicao.**

- **DNA Eleitoral**
  - titulo: **DNA do Eleitor**;
  - subtitulo: **Quem e, onde esta e como se comporta o eleitor determinante da candidatura.**

O controle segmentado deve parecer parte do hero, nao um elemento solto. Ele deve ocupar o espaco vazio superior direito do cabecalho e indicar claramente a pagina ativa.

### 2. Mapa Territorial da Votacao

Funcao visual:

Mostrar a distribuicao geografica dos votos em Minas Gerais.

Elementos:

- KPIs de resumo;
- filtro Mesorregiao/Municipio;
- mapa coropletico de Minas Gerais;
- ranking lateral de concentracao territorial.

Mapa:

- base municipal de MG;
- cor por quantidade de votos;
- escala logaritmica;
- municipios com mais votos ficam em azul mais intenso;
- municipios com poucos votos ficam claros;
- no modo mesorregiao, aparecem fronteiras regionais mais fortes e labels percentuais.

Ranking:

- barras horizontais Top 10;
- complementa o mapa com uma leitura ordinal;
- deve mostrar rapidamente os territorios mais relevantes.

Direcao:

Essa e a primeira grande visualizacao analitica. Mapa e ranking devem parecer um conjunto unico: um mostra geografia, o outro mostra hierarquia.

### 3. Votacao por Bairro e Perfil Demografico

Funcao visual:

Permitir mergulho territorial e leitura do perfil estimado dos eleitores.

Treemap:

- hierarquia municipio > bairro;
- area proporcional a votos;
- selecao interativa;
- recorte ativo persistente.

Demografia:

- barras horizontais;
- filtros por genero, idade, escolaridade e estado civil;
- leitura percentual;
- responde ao recorte selecionado no treemap.

Direcao:

Essa secao deve comunicar exploracao. O usuario escolhe um territorio e imediatamente entende como o perfil demografico muda.

Ponto visual importante:

O recorte ativo precisa ser visivel. A legenda "Recorte territorial ativo" deve evoluir para um badge ou chip mais evidente se o design for refinado.

### 4. Concentracao Territorial

Funcao visual:

Explicar se a votacao depende de poucos redutos ou se e mais espalhada.

Elementos:

- texto interpretativo;
- cards Top 1, Top 5, Top 10 e Top 20;
- curva acumulada;
- toggle para Top 50 ou todos os municipios.

Curva:

- linha azul clara;
- area preenchida translucida;
- marcadores de referencia;
- linhas guias em 25%, 50%, 75% e 90%.

Direcao:

Essa secao e mais interpretativa do que exploratoria. Ela deve ajudar o usuario a ler concentracao como um comportamento politico.

### 5. Eficiencia por Custo do Voto

Funcao visual:

Mostrar quanto cada tipo de despesa custou por voto no resultado geral da campanha.

Tipo:

Ranking horizontal com leitura de Pareto.

Codificacao visual:

- eixo X: custo por voto em R$/voto;
- eixo Y: tipo de despesa;
- cor da barra: valor total gasto no tipo de despesa;
- linha superior: percentual acumulado do gasto.

Direcao:

A visualizacao deve indicar rapidamente quais tipos de despesa mais pesaram no custo de cada voto, sem sugerir vinculo territorial quando a base nao traz esse relacionamento.

Cuidados visuais:

- manter os nomes longos de tipos de despesa legiveis;
- destacar o custo por voto em cada barra;
- diferenciar valor total gasto e custo por voto;
- usar a linha acumulada como apoio analitico, nao como elemento dominante.

### 6. Mapa da Atuacao Parlamentar de Acordo com os Votos

Funcao visual:

Mostrar se ha relacao territorial entre votos recebidos e emendas destinadas pelo parlamentar.

Tipo:

Camada de sobreposicao no mapa.

Codificacao visual:

- base do mapa: cor do municipio conforme votacao;
- bolha sobreposta: volume de emendas destinadas;
- tamanho da bolha: valor de emendas;
- cor da bolha: intensidade do valor de emendas;
- hover: municipio, votos e valor de emendas.

Direcao:

Esse mapa deve comunicar retorno politico territorial. A pergunta visual e: onde o parlamentar teve votos e onde destinou recursos depois?

Cuidados visuais:

- bolhas precisam aparecer sem esconder totalmente o coropletico;
- a legenda de votos e a legenda de emendas devem ser distinguiveis;
- municipios com muitos votos e muitas emendas devem saltar aos olhos;
- municipios com votos altos e poucas emendas tambem precisam continuar interpretaveis.

## Pagina 2: DNA Eleitoral

Funcao visual:

Transformar a leitura descritiva da pagina 1 em leitura estrategica do eleitor. A pagina deve responder quem sustenta a candidatura hoje, onde esse eleitor esta, como ele se comporta e quais territorios podem orientar acao ate 2030.

Direcao geral:

- manter o mesmo sistema visual premium da pagina 1;
- usar os mesmos blocos de titulo/subtitulo para secoes;
- reservar cards para visualizacoes densas e comparativas;
- evitar linguagem decorativa ou excessivamente publicitaria;
- priorizar leitura de segmentos, potenciais e oportunidades territoriais.

### 1. Identidade da Base Eleitoral

Funcao visual:

Definir quem e o eleitor-chave e quais atributos mais caracterizam a base do candidato.

Subtitulo:

**Quem e o eleitor-chave e quais atributos definem o perfil do seu eleitor.**

A secao organiza a leitura em dois cards de subsecao: identidade geral e perfis estrategicos. Sunburst, Heatmap e a composição demográfica por pontos não fazem mais parte da composição atual.

#### 1.1 Eleitor ideal do candidato

Pergunta: **Quem caracteriza a base eleitoral do candidato?**

- Titulo fixo: **Eleitor ideal do candidato**.
- Subtitulo: **Síntese do perfil demográfico predominante na base eleitoral do candidato.**
- Persona abaixo do titulo, com peso e tamanho equilibrados, sem obrigar caixa alta.
- Emoji de pessoa preservado; resumo com emoji de fala quando acrescenta informacao.
- Ocultar o resumo quando ele apenas repete a persona.
- Badges de confianca numerica e qualitativa, identificados como confianca do modelo.
- Quatro KPIs: genero, faixa etaria, escolaridade e estado civil.
- Manter os emojis coloridos dos atributos; eles identificam dimensoes, nao magnitude.
- Categorias com inicial maiuscula, valores legiveis e percentuais em azul claro.

Legenda: **Os percentuais indicam a participação de cada categoria dominante no perfil geral. As quatro dimensões são independentes e não somam 100%.**

O titulo da subsecao deve ser visualmente superior ao nome da persona. Em telas amplas, os quatro KPIs ficam alinhados; em telas menores, passam para duas colunas e depois uma.

#### 1.2 BASE ELEITORAL DO CANDIDATO

Pergunta: **Quais perfis sustentam a candidatura e qual o peso de cada um?**

Titulo solicitado: **BASE ELEITORAL DO CANDIDATO**.

Subtitulo: **Classificações estratégicas, participação na votação e identidade demográfica de cada ICP.**

Composicao:

- card externo azul profundo, borda discreta e cantos arredondados;
- resumo superior para Base eleitoral, Eleitor consolidado e Eleitor emergente;
- participacao de cada classificacao na votacao do candidato;
- grade com um card por ICP, agrupada por classificacao;
- classificacao e identificador do ICP, seguidos pela persona;
- destaque para participacao na votacao e votos absolutos;
- quatro barras independentes com categoria demografica e percentual;
- bloco **Leitura estrategica** visivel, sem exigir clique ou hover.

Dois ICPs com a mesma classificacao devem continuar em cards separados. Classificacao ausente exibe traco e mensagem de ausencia, sem simular um perfil.

Os cards usam duas colunas em telas amplas e uma abaixo de 1000 px. Abaixo de 600 px, resumo de classificacoes e atributos internos tambem empilham.

#### Padrao editorial da secao 1

- Separar titulo, frase de contexto, conteudo e legenda de interpretacao.
- Usar inicial maiuscula em categorias e classificacoes; preservar siglas como ICP.
- Manter o titulo em caixa alta da segunda subsecao conforme solicitado.
- Preservar emojis existentes com funcao de identificacao.
- Identificar o denominador: **da votacao do candidato** para participacao eleitoral; **no perfil** para percentuais demograficos.
- A confianca do modelo e uma terceira medida, distinta dessas participacoes.
- Usar virgula decimal e simbolo de percentual. Valores abaixo de 1% continuam abaixo de 1%.
- Nao repetir a persona no resumo nem preencher recomendacoes ausentes com texto inventado.
- As barras de genero, idade, escolaridade e estado civil nao devem ser empilhadas em uma soma de 100%.
- Mostrar categorias dominantes; nao sugerir que os dados contem a distribuicao completa da populacao.

### 2. Matriz de Potencial Demografico

Funcao visual:

Comparar o perfil do eleitor do candidato com a populacao local para identificar sobre-representacao, sub-representacao e oportunidades.

Subtitulo:

**Comparativo entre o perfil do eleitor do candidato e a populacao local. Identificacao de sobre-representacao e frentes de expansao.**

Direcao:

Essa secao deve ser comparativa. A visualizacao precisa deixar claro quando um grupo aparece acima do esperado na base do candidato e quando ha espaco de crescimento frente ao peso demografico local.

Composicao atual:

- mapa coropletico municipal proprio de Minas Gerais, com a linguagem visual dos mapas da pagina 1;
- seletor no canto superior direito com **ELEITOR IDEAL** e as classificacoes existentes em `cluster_strategy_label`;
- cruzamento conjunto de genero, faixa etaria e escolaridade, sem estado civil;
- referencia populacional dos parquets `IBGE/censo/genero_apond.parquet`, `idade_apond.parquet` e `escolaridade_apond.parquet`;
- genero e idade agregados pelas contagens populacionais das areas ponderadas; escolaridade usa nivel de instrucao para 25 anos ou mais, com percentuais ponderados pela populacao total da area, obtida nos parquets de genero ou idade (`qt_votos_demografico` fica como fallback);
- aderencia por dimensao: `100 - diferenca absoluta em pontos percentuais` entre a categoria e percentual do ICP e o percentual municipal do Censo;
- aderencia demografica e compatibilidade final: media da semelhanca nas tres dimensoes, com escala de cor logaritmica;
- municipios sem votos do candidato ou sem os tres cruzamentos completos ficam no valor minimo da escala;
- escala continua verde: maior compatibilidade em verde escuro, menor compatibilidade em verde claro;
- todos os municipios da malha continuam preenchidos. Sem votos ou sem os tres cruzamentos completos, o municipio recebe o valor minimo (verde mais claro), com detalhes no hover.

A cor representa a semelhanca demografica entre o ICP e a populacao municipal, condicionada a haver votos do candidato naquele municipio. O volume de votos aparece no hover e nao altera a cor.

### 3. Segmentacao & Acao Tatica

Funcao visual:

Identificar frentes de conversao, consolidacao e expansao do eleitorado.

Subtitulo:

**Identificacao de frentes de conversao, consolidacao e expansao do eleitorado.**

Direcao:

Essa secao deve ter aparencia mais operacional. As visualizacoes devem ajudar a separar onde a candidatura defende base consolidada, onde pode converter eleitores semelhantes e onde pode expandir para segmentos ainda pouco explorados.

### 4. Expansao & Oportunidades para 2030

Funcao visual:

Mapear bairros, areas ponderadas e clusters taticos com potencial de crescimento eleitoral.

Subtitulo:

**Mapeamento em nivel de bairro e area ponderada. Localizacao dos clusters taticos e visualizacao de manchas de potencial de crescimento.**

Direcao:

Essa e a secao mais prospectiva. O mapa volta a ser protagonista, mas com foco em oportunidade futura. As manchas de potencial devem comunicar prioridade territorial sem confundir potencial demografico com voto ja conquistado.

## Estados Interativos

### Recorte territorial ativo

O treemap alimenta um contexto persistente local a secao demografica. A legenda deve deixar claro o alcance desse recorte.

Hoje ele afeta:

- grafico demografico;
- legenda do recorte ativo.

Direcao futura:

- transformar a legenda em badge;
- permitir que o mapa tambem alimente o mesmo recorte;
- destacar visualmente o territorio selecionado nos mapas.

### Filtros

Filtros que mudam a interpretacao principal deveriam ter tratamento visual mais forte que um select comum.

Possiveis evolucoes:

- segmented control para alternar entre Raio X Eleitoral e DNA Eleitoral no hero;
- segmented control para Mesorregiao/Municipio;
- chips ou tabs para perfil demografico;
- controles compactos para nivel territorial da matriz de custo.

## Responsividade

Pontos que exigem atencao:

- mapa e ranking podem ficar apertados em telas medias;
- nomes longos podem quebrar cards;
- treemap e demografia devem empilhar no mobile;
- matriz scatter precisa manter eixos legiveis;
- mapa com bolhas precisa preservar espaco para legendas.
- controle segmentado do hero deve quebrar bem no mobile sem competir com titulo e foto.
- secoes da pagina DNA Eleitoral devem manter cards empilhados com altura suficiente para visualizacoes futuras.

## Estados Sem Dados

O app possui estados vazios para dados ausentes. Visualmente, eles devem parecer informativos, nao dados reais.

Direcao:

- evitar graficos ficticios muito parecidos com informacao valida;
- explicar qual arquivo ou fonte esta ausente;
- usar empty states discretos dentro do mesmo modelo de card.

## Principios de Design

1. O mapa e o protagonista.

A leitura geografica deve continuar sendo o centro da experiencia.

2. Cards devem formar um sistema unico.

Todos os blocos devem usar a mesma familia visual: azul profundo, borda clara, sombra sutil e graficos integrados.

3. Cor precisa ter significado.

Azul comunica intensidade territorial. Verde, amarelo e cinza devem aparecer apenas quando carregarem significado analitico, como nos quadrantes de custo.

4. A interface deve parecer analitica.

Evitar enfeites sem funcao. A sofisticacao deve vir de hierarquia, clareza e consistencia.

5. Selecao deve ser persistente e visivel.

Quando o usuario seleciona um territorio, o sistema deve deixar claro que os graficos passaram a responder a esse recorte.

6. Diferenciar zero, baixo e alto.

Municipios sem votos, com poucos votos e com muitos votos precisam ser visualmente distintos.

7. Legendas devem ser claras.

Mapas com multiplas camadas, especialmente votos + emendas, precisam de legendas que nao confundam as escalas.

## Resumo das Visualizacoes

| Visualizacao | Forma atual | Pergunta que responde |
| --- | --- | --- |
| Hero do candidato | Foto + dados em capa escura | Quem esta sendo analisado? |
| KPIs territoriais | Cards numericos | Qual o volume e o principal reduto? |
| Mapa de MG | Coropletico branco-azul | Onde estao os votos? |
| Ranking territorial | Barras horizontais Top 10 | Quais territorios concentram mais votos? |
| Treemap municipio/bairro | Retangulos proporcionais | Como os votos se distribuem dentro dos municipios e bairros? |
| Barras demograficas | Barras horizontais percentuais | Qual o perfil estimado do eleitor no recorte? |
| Curva acumulada | Linha/area com marcadores | Quanta votacao se concentra nos top municipios? |
| Matriz de custo do voto | Ranking/Pareto por tipo de despesa | Quais despesas mais pesaram no custo por voto? |
| Mapa de atuacao parlamentar | Coropletico + bolhas de emendas | Onde votos e emendas se cruzam? |
| Eleitor ideal do candidato | Card geral com persona, confianca e quatro KPIs demograficos | Quem caracteriza a base eleitoral? |
| BASE ELEITORAL DO CANDIDATO | Resumo por classificacao e cards por ICP com barras demograficas | Quais perfis sustentam a candidatura e qual o peso de cada um? |
| Matriz de Potencial Demografico | Mapa municipal verde de compatibilidade demografica e presenca de votos | Quais municipios combinam perfil populacional compativel e votos do candidato? |
| Segmentacao & Acao Tatica | Secao estruturada com card reservado | Quais frentes exigem conversao, consolidacao e expansao? |
| Expansao & Oportunidades 2030 | Secao estruturada com card reservado | Onde estao os clusters e manchas de crescimento? |

## Briefing Curto

Construir uma experiencia de inteligencia eleitoral escura, sofisticada e objetiva. O usuario deve percorrer uma narrativa completa: identidade do candidato, distribuicao dos votos, concentracao territorial, perfil demografico, eficiencia financeira, retorno parlamentar e leitura estrategica do eleitor determinante.

O visual deve ser denso o suficiente para analise, mas limpo o bastante para leitura rapida. Cada grafico precisa responder uma pergunta politica clara.
