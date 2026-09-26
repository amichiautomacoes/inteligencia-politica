# Direcao Visual do Projeto

Este documento descreve o projeto pelo vies visual, narrativo e de experiencia. A ideia e servir como briefing para evoluir a apresentacao das visualizacoes eleitorais, sem focar na arquitetura tecnica do app.

## Visao geral

O app e uma visualizacao eleitoral em Streamlit com linguagem de dashboard politico-territorial. A tela principal se chama **Raio X do voto** e apresenta uma leitura visual da votacao de um candidato em Minas Gerais.

A experiencia deve comunicar tres ideias ao mesmo tempo:

- onde o candidato foi mais votado;
- o quanto essa votacao esta concentrada ou espalhada;
- qual e o perfil demografico estimado dos eleitores nos territorios selecionados.

Visualmente, o app tem atmosfera escura, institucional e analitica. Ele usa fundo com imagem, sobreposicoes azuladas translucidas, textos claros e graficos com escala branco-azul. A sensacao desejada e de painel estrategico: algo que parece uma sala de analise eleitoral, com mapas, rankings e sinais de concentracao territorial.

## Linguagem visual atual

### Paleta

A paleta dominante e azul escuro com branco e azul claro:

- fundo principal: azul muito escuro, quase marinho;
- paineis e cards: gradientes entre azul profundo e azul petroleo escuro;
- texto principal: branco frio;
- texto secundario: azul acinzentado claro;
- realces: azul claro, azul medio e branco;
- graficos: escala de votos indo de branco para azul escuro.

Cores recorrentes:

- `#eaf2ff`: texto claro geral;
- `#f8fbff`: titulos e numeros em destaque;
- `#b7c7e6`: legendas e textos secundarios;
- `#d1def7`: subtitulos de secao;
- `#7DD3FC`: linha de destaque da curva acumulada;
- `#60A5FA`, `#2563EB`, `#0B1F4D`: escala azul de intensidade;
- fundos translucidos como `rgba(11, 31, 77, 0.76)` e `rgba(7, 24, 54, 0.68)`.

A escala cromatica comunica densidade: territorios com poucos ou nenhum voto ficam claros, quase brancos; territorios mais fortes ficam cada vez mais azuis, chegando ao azul escuro.

### Fundo e profundidade

O app usa `assets/background.png` como imagem de fundo fixa. Essa imagem aparece:

- no container geral da aplicacao;
- no hero inicial;
- no card largo de territorio lider.

Sobre a imagem ha camadas de gradiente escuro para garantir leitura. A interface usa bordas finas azuladas, sombras profundas e leve blur nos paineis, criando efeito de vidro escuro. Os elementos parecem flutuar acima do fundo, mas ainda com cara de dashboard.

### Tipografia e hierarquia

A tipografia visual e pesada nos titulos e numeros:

- titulo do hero: grande, branco, muito pesado, com leve brilho azul;
- textos de candidato: caixa alta, negrito, forte;
- titulos de secao: grandes, claros, com peso alto;
- labels de KPI: pequenos, caixa alta, espacamento de letras;
- valores de KPI: grandes, brancos, densos;
- legendas e captions: menores, azuladas, menos contraste.

A hierarquia atual e bastante clara: primeiro vem o nome da experiencia, depois o candidato, depois os blocos de leitura territorial.

## Estrutura visual da pagina

### 1. Hero / Cabecalho do candidato

Primeira area visual da tela. Funciona como capa da analise.

Composicao:

- bloco horizontal largo, com altura minima de aproximadamente 22rem;
- fundo com imagem e overlay escuro em gradiente da esquerda para a direita;
- titulo grande: **RAIO X da votacao 2022**;
- subtitulo: analises descritivas geograficas e do perfil do eleitor;
- abaixo, uma linha com foto do candidato a esquerda e informacoes textuais a direita.

Foto:

- proporcao vertical, aproximadamente 1:1,35;
- largura desktop de 10,5rem;
- borda levemente arredondada;
- fundo claro caso a imagem nao carregue;
- sombra forte para destacar do fundo.

Informacoes do candidato:

- tres linhas em caixa alta:
  - nome;
  - cargo;
  - partido.
- texto grande, branco, negrito, com leve brilho.

Intencao visual:

O hero deve estabelecer imediatamente o personagem analisado. Ele nao e apenas uma barra de titulo; ele e a abertura editorial do painel. Deve parecer uma ficha eleitoral premium, com a foto e os dados do candidato ganhando protagonismo.

Possiveis melhorias visuais:

- diferenciar melhor o nome do candidato dos campos "Cargo" e "Partido";
- adicionar uma faixa discreta ou selo do ano eleitoral;
- reduzir repeticao de caixa alta se a leitura estiver pesada;
- criar uma area mais limpa para a foto quando o fundo estiver muito complexo;
- tornar o hero mais responsivo para celular, garantindo que foto e texto nao disputem espaco.

### 2. Header de secao principal

O bloco **Mapa Territorial da Votacao** abre a parte analitica.

Composicao:

- card largo arredondado;
- fundo azul escuro translucido;
- borda azul fina;
- sombra externa;
- barra vertical luminosa na lateral esquerda;
- titulo grande;
- subtitulo explicativo curto.

Intencao visual:

Esse componente separa grandes capitulos da pagina. Ele deve funcionar como divisor editorial, nao como card de dado. A barra lateral azul ajuda a criar sensacao de marco visual.

### 3. KPIs territoriais

Logo abaixo do header principal, aparecem tres cards pequenos e um card largo.

Cards pequenos:

- **Total de votos**;
- **Municipio mais votado**;
- **Municipios com votos**.

Composicao:

- grid com tres colunas no desktop;
- cards azulados translucidos;
- label pequena em caixa alta;
- valor grande em branco;
- legenda menor abaixo.

Card largo:

- **Territorio lider**;
- possui tag no canto superior direito: "Maior concentracao";
- usa a imagem de fundo com overlay escuro;
- valor principal e o nome da mesorregiao lider;
- abaixo aparece o total de votos.

Intencao visual:

Esses KPIs criam uma leitura imediata antes dos graficos. Eles devem responder rapidamente: qual foi o volume, qual foi o principal reduto, qual foi a amplitude municipal e qual territorio concentra mais.

Possiveis melhorias visuais:

- usar icones discretos para cada KPI;
- destacar mais o card de territorio lider como insight principal;
- criar microbarras ou sparklines para dar mais vida aos cards;
- melhorar quebra de texto em nomes longos de municipios/mesorregioes.

### 4. Filtro territorial

Antes do mapa ha um filtro que alterna a visualizacao entre:

- **Mesorregiao**;
- **Municipio**.

Visual atual:

- selectbox do Streamlit posicionado na coluna direita;
- ao lado esquerdo fica o titulo da subsecao **Sua votacao no territorio de Minas Gerais**.

Intencao visual:

O filtro muda a granularidade da leitura territorial. Visualmente, ele deveria parecer um controle de modo, quase como uma chave de visualizacao, porque altera a interpretacao principal do mapa e do ranking.

Possiveis melhorias visuais:

- trocar selectbox por segmented control;
- deixar "Mesorregiao" e "Municipio" como botoes lado a lado;
- mostrar um pequeno texto de contexto quando o modo muda;
- reforcar visualmente que mapa e ranking lateral respondem ao mesmo filtro.

## Visualizacoes principais

### 5. Mapa coropletico de Minas Gerais

Esta e a visualizacao central da pagina.

Tipo:

- mapa coropletico de Minas Gerais;
- construido sobre malha municipal;
- coloracao por quantidade de votos;
- escala logaritmica para evitar que grandes redutos escondam todos os demais municipios.

Layout:

- ocupa cerca de 68% da largura no desktop;
- altura aproximada de 560px;
- margem interna pequena;
- fundo transparente para integrar com o tema escuro;
- titulo interno do Plotly:
  - **Concentracao de votos por mesorregiao (MG)** quando o filtro esta em mesorregiao;
  - **Concentracao de votos por municipio (MG)** quando o filtro esta em municipio.

Escala de cor:

- votos zero ou muito baixos: branco;
- poucos votos: azul muito claro;
- faixa intermediaria: azul claro e azul medio;
- alta votacao: azul forte;
- maxima concentracao: azul escuro profundo.

Colorbar:

- fica a direita do mapa;
- titulo "Votos";
- ticks formatados em numeros reais, apesar da escala logaritmica;
- texto azul claro.

Hover:

Ao passar o mouse, aparece tooltip escuro com:

- nome do municipio;
- quantidade de votos;
- codigo de municipio TSE;
- latitude e longitude.

O tooltip usa fundo quase preto, texto claro e borda azulada.

Modo mesorregiao:

- os municipios sao coloridos de acordo com o total da mesorregiao;
- linhas internas municipais quase desaparecem;
- ha linhas brancas mais fortes marcando fronteiras de mesorregioes;
- ha uma linha branca ainda mais forte no limite externo de Minas Gerais;
- aparecem labels percentuais sobre as mesorregioes, indicando participacao relativa.

Modo municipio:

- cada municipio aparece com sua propria intensidade de votos;
- as divisoes municipais ficam mais visiveis com linhas claras;
- a leitura e mais granular, mostrando redutos locais e dispersao.

Intencao visual:

O mapa deve ser o "centro de gravidade" da pagina. Ele mostra rapidamente se a votacao tem base regional, se se espalha pelo estado ou se se concentra em poucos polos. O usuario precisa conseguir bater o olho e identificar manchas de forca eleitoral.

Possiveis melhorias visuais:

- reduzir o branco puro nos municipios sem voto, pois pode parecer destaque indevido;
- considerar cinza frio para ausencia de votos e azul para votos reais;
- adicionar legenda textual explicando que a escala e logaritmica;
- criar destaque visual para o municipio mais votado;
- incluir labels somente quando nao poluirem o mapa;
- melhorar contraste entre limites municipais e preenchimento em areas muito claras.

### 6. Grafico lateral de concentracao territorial

Ao lado direito do mapa existe um ranking horizontal.

Tipo:

- grafico de barras horizontais;
- mostra Top 10 mesorregioes ou Top 10 municipios, conforme o filtro territorial;
- ordenado visualmente para que a maior barra fique no topo ou ao final do eixo, dependendo da ordenacao Plotly.

Layout:

- fica em container com borda;
- titulo externo: **Concentracao territorial**;
- titulo interno do grafico:
  - **Top 10 mesorregioes**;
  - **Top 10 municipios**.
- altura igual ao mapa, cerca de 560px;
- margem esquerda larga para caber nomes de territorios.

Barras:

- horizontais;
- coloridas pela quantidade de votos usando escala Blues;
- borda fina clara;
- texto dentro ou proximo da barra com:
  - quantidade de votos;
  - percentual dos votos.

Hover:

- mostra territorio;
- votos;
- participacao percentual.

Intencao visual:

Esse grafico complementa o mapa com uma leitura ordinal. Enquanto o mapa mostra geografia, o ranking mostra hierarquia. O usuario deve entender rapidamente quais territorios explicam a maior parte da votacao.

Possiveis melhorias visuais:

- alinhar melhor ranking e mapa como um conjunto unico;
- destacar o primeiro colocado com cor ou marcador diferente;
- reduzir texto dentro das barras se houver sobreposicao;
- padronizar o sentido da ordenacao para que o maior valor fique sempre em posicao intuitiva;
- adicionar divisores sutis ou grid minimo para comparar comprimentos.

### 7. Treemap de votacao por municipio e bairro

Depois do mapa, a pagina traz uma leitura mais granular por bairro.

Tipo:

- treemap hierarquico;
- primeiro nivel: municipio;
- segundo nivel: bairro;
- tamanho dos retangulos proporcional a quantidade de votos;
- limitado aos 500 maiores agrupamentos para preservar performance e legibilidade.

Layout:

- fica em coluna esquerda, ocupando metade da largura;
- container com borda;
- titulo centralizado: **Votacao por Municipio e Bairro**;
- altura aproximada de 500px;
- fundo transparente;
- texto claro.

Interacao:

- o usuario pode clicar em um bloco do treemap;
- a selecao dispara recarregamento da pagina;
- o contexto selecionado e usado para recortar o grafico demografico ao lado;
- se selecionar um bairro, a demografia passa a representar esse bairro;
- se selecionar um municipio, a demografia passa a representar esse municipio.

Hover:

- mostra nome do bloco;
- mostra total de votos.

Estado vazio:

- quando nao ha dados, aparece um treemap ficticio com "Parquet pendente" e recortes A/B/C.

Intencao visual:

O treemap deve comunicar concentracao intraurbana. Ele mostra se os votos estao espalhados em muitos bairros ou se poucos bairros dominam a votacao dentro dos municipios.

Possiveis melhorias visuais:

- definir uma paleta customizada alinhada ao restante do app;
- diferenciar visualmente municipio e bairro;
- adicionar breadcrumb visual do nivel selecionado;
- indicar explicitamente que o treemap e clicavel;
- destacar o bloco selecionado apos o clique;
- evitar que labels pequenos fiquem ilegiveis em blocos muito pequenos.

### 8. Grafico de barras demografico

Ao lado do treemap existe o painel de perfil demografico.

Tipo:

- grafico de barras horizontais;
- mostra distribuicao percentual do perfil estimado dos eleitores;
- a dimensao exibida muda por filtro.

Filtro de perfil:

- Genero;
- Idade;
- Escolaridade;
- Estado civil.

Layout:

- fica em coluna direita, ocupando metade da largura;
- container com borda;
- titulo centralizado: **Distribuicao por perfil demografico**;
- selectbox pequeno alinhado a direita;
- grafico com altura aproximada de 430px;
- margem esquerda larga para caber categorias.

Barras:

- horizontais;
- eixo X em percentual;
- eixo Y com categorias;
- cor varia conforme percentual usando escala Blues;
- valor percentual aparece fora da barra;
- grid horizontal/vertical sutil em branco translucido.

Hover:

- mostra categoria;
- mostra participacao percentual.

Contexto selecionado:

- se houver clique no treemap, aparece uma legenda abaixo:
  - "Recorte do treemap: [bairro ou municipio]".

Intencao visual:

Esse grafico traduz o territorio selecionado em perfil de eleitor. Ele deve funcionar como painel comparativo: depois de escolher um territorio no treemap, o usuario entende quem compoe aquele recorte em termos demograficos.

Possiveis melhorias visuais:

- substituir o selectbox por abas ou chips de categoria;
- mostrar o recorte ativo em um badge mais visivel;
- usar cores complementares para demografia, evitando tudo em azul;
- adicionar subtitulo dinamico: "Perfil em [municipio/bairro]";
- melhorar legibilidade de categorias longas de escolaridade;
- manter escala percentual consistente quando trocar o filtro.

### 9. Secao de Concentracao Territorial acumulada

No fim da pagina ha uma segunda grande secao chamada **Concentracao Territorial**.

Objetivo:

Mostrar quanto da votacao total esta concentrada nos municipios onde o candidato mais recebeu votos.

Composicao geral:

- header de secao principal com barra lateral azul;
- container com duas colunas:
  - esquerda: resumo textual e cards de marcos;
  - direita: curva acumulada.

Coluna esquerda:

- frase de destaque:
  - "[Municipio principal] abre a curva com X% da votacao."
- texto contextual:
  - "Os 10 principais municipios acumulam X% dos votos..."
  - explica que quanto mais rapido a curva sobe, mais concentrada esta a base.
- grid 2x2 de cards:
  - Top 1;
  - Top 5;
  - Top 10;
  - Top 20.

Cards de concentracao:

- fundo azul escuro;
- borda fina azul;
- label pequena em caixa alta;
- percentual acumulado em destaque;
- nome do municipio limite;
- votos acumulados em legenda.

Coluna direita:

- toggle: **Mostrar todos os municipios**;
- se desligado, grafico foca no Top 50;
- se ligado, exibe todos os municipios;
- quando ha mais de 50 municipios e o toggle esta desligado, aparece caption explicativa.

Grafico de curva acumulada:

- linha azul clara;
- area preenchida abaixo da linha em azul translucido;
- eixo X: municipios acumulados;
- eixo Y: percentual da votacao total;
- eixo Y vai de 0% a 100%;
- linhas horizontais pontilhadas em 25%, 50%, 75% e 90%;
- labels desses percentuais aparecem no canto direito;
- marcadores brancos com borda azul nos pontos de referencia:
  - Top 1;
  - Top 5;
  - Top 10;
  - Top 20;
  - Top 50;
  - Todos, quando aplicavel.

Hover:

- mostra Top N municipios;
- votos acumulados;
- percentual da votacao total;
- municipio na posicao.

Intencao visual:

Essa secao e mais analitica e interpretativa. Ela ajuda a responder se o candidato depende de poucos redutos ou se tem base dispersa. Uma curva que sobe muito rapido indica concentracao forte; uma curva mais gradual indica distribuicao territorial mais ampla.

Possiveis melhorias visuais:

- destacar visualmente as faixas 50%, 75% e 90%;
- adicionar uma linha vertical no ponto em que atinge 50% dos votos;
- transformar os cards Top 1/5/10/20 em mini indicadores clicaveis;
- incluir interpretacao automatica do tipo "votacao altamente concentrada";
- reforcar o contraste entre area preenchida e fundo.

## Responsividade atual

Ha ajustes para telas menores:

- hero reduz padding;
- titulo do hero diminui;
- foto do candidato reduz de 10,5rem para 7,5rem;
- informacoes do candidato ficam menores;
- grids de KPI viram uma coluna;
- cards de concentracao preservam duas colunas;
- titulo de secao principal reduz.

Pontos de atencao:

- mapa e ranking lado a lado podem ficar comprimidos em telas medias;
- nomes longos de municipios podem quebrar mal;
- cards de KPI com valores grandes podem estourar;
- treemap e barras demograficas em duas colunas podem precisar empilhar no mobile;
- o selectbox de filtro pode ocupar espaco demais se o layout estiver estreito.

## Estados sem dados

O app possui estados alternativos quando dados ou arquivos nao carregam:

- mapa vazio com marcadores ficticios e texto "Parquet pendente";
- treemap vazio com recortes ficticios;
- grafico demografico com categoria "Parquet pendente";
- curva acumulada com anotacao de dados indisponiveis;
- KPIs mostram "--".

Visualmente, esses estados ainda parecem parte do painel, mas poderiam ser mais explicativos e menos parecidos com dados reais.

Possiveis melhorias:

- criar empty states com texto direto e discreto;
- usar icone de arquivo/dados ausentes;
- evitar graficos ficticios que possam ser confundidos com informacao real;
- indicar qual parquet ou fonte esta ausente.

## Principios para evoluir o visual

1. O mapa deve continuar sendo o protagonista.

Ele e a visualizacao mais importante da pagina. Qualquer melhoria deve preservar a leitura geografica e evitar excesso de elementos concorrentes.

2. A interface deve parecer analitica, nao decorativa.

O publico provavelmente quer interpretar desempenho eleitoral. O visual pode ser sofisticado, mas precisa continuar objetivo, legivel e confiavel.

3. Diferenciar ausencia de voto de baixa votacao.

Hoje o branco pode comunicar tanto "sem voto" quanto "baixo voto". Seria melhor separar claramente zero, baixo, medio e alto.

4. Usar cor como semantica, nao so estetica.

Azul ja representa intensidade territorial. Outros tipos de informacao, como demografia, selecao ou alertas, poderiam usar acentos diferentes com parcimonia.

5. Mostrar selecoes de forma persistente.

Quando o usuario clica no treemap, o recorte ativo deveria ficar muito claro visualmente, nao apenas como caption pequena.

6. Reduzir ambiguidade dos filtros.

Filtros que mudam o sentido dos graficos devem parecer controles principais. "Mesorregiao/Municipio" e "Genero/Idade/Escolaridade/Estado civil" poderiam ter tratamento visual mais forte.

7. Evitar que textos longos quebrem a composicao.

Municipios, mesorregioes e categorias demograficas podem ter nomes grandes. Cards, eixos e labels devem prever isso.

8. Manter consistencia entre os graficos.

Mapa, ranking, treemap, barras e curva devem parecer partes de um mesmo sistema visual, com mesma tipografia, contraste, hover e estilo de container.

## Resumo das visualizacoes

| Visualizacao | Forma atual | Pergunta que responde |
| --- | --- | --- |
| Hero do candidato | Foto + dados em capa escura | Quem esta sendo analisado? |
| KPIs territoriais | Cards numericos | Qual o volume e o principal reduto? |
| Mapa de MG | Coropletico branco-azul | Onde estao os votos? |
| Ranking territorial | Barras horizontais Top 10 | Quais territorios concentram mais votos? |
| Treemap municipio/bairro | Retangulos proporcionais | Como os votos se distribuem dentro dos municipios e bairros? |
| Barras demograficas | Barras horizontais percentuais | Qual o perfil estimado do eleitor no recorte? |
| Curva acumulada | Linha/area com marcadores | Quanta votacao se concentra nos top municipios? |

## Briefing curto para redesign

Criar uma experiencia visual de dashboard eleitoral premium, escura, geografica e analitica. O usuario deve sentir que esta vendo um raio X territorial da votacao: primeiro identifica o candidato, depois enxerga as manchas de voto em Minas Gerais, compara os territorios mais fortes, mergulha em municipios e bairros, e finalmente entende a concentracao territorial e o perfil demografico.

O visual deve priorizar legibilidade, hierarquia e interpretacao rapida. A estetica pode ser sofisticada, com profundidade e atmosfera, mas os graficos precisam continuar claros, comparaveis e confiaveis.
