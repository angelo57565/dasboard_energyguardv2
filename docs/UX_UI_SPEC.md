# EnergyGuard v2 — Especificação UX/UI
Versão: 1.0 | 23/11/2026 | Escopo: dashboard Streamlit (sem mudanças de API, banco ou firmware)

## Objetivos e princípios
1. **Compreensível:** responder primeiro “o ESP32 está enviando dados?” e “há algo que exige atenção?”.
2. **Sem perda de informação:** preservar as seis abas, formulários, gráficos, tabelas, avaliações, download CSV e operações existentes.
3. **Acessível:** temas claro e escuro com contraste legível, três tamanhos tipográficos e foco visível.
4. **Honesto sobre o estado:** conexão do dashboard à API não é o mesmo que comunicação ESP32→API.
5. **Sem dados fictícios:** jamais simular leituras no produto; valores antigos sempre identificados.
6. **Responsivo:** navegação utilizável entre 360 e 1920 px; tabelas não ocultam colunas permanentemente.

## Arquitetura da informação
Menu lateral: marca EnergyGuard; **Aparência** (Claro/Escuro, Fonte Normal/Grande/Extra grande,
Tabelas Resumidas/Completas), Dispositivo, Período, Atualização, Configurações, Conexão com API.
Navegação principal, nesta ordem: **Visão geral**, **Medições**, **Consumo**, **Anomalias**,
**Alertas**, **Sistema**. Nomes de endpoints e códigos enviados à API permanecem inalterados.
Valores de aparência são preferencias por sessão e opção de URL (?tema=; ?fonte=);
não se gravam no backend.

## Design system
- Tipografia: fonte nativa de sistema, 16px / 18px / 20px (Normal / Grande / Extra grande).
  Proporções em em/rem; KPIs responsivos; tabelas e controles acompanham escala.
- Grid responsivo: 12 colunas desktop, 2–3 cartões em tablet, 1–2 em celular;
  áreas clicáveis de pelo menos 44px, foco visível, sem animação obrigatória.
- Dark: fundo #080D18; superfícies #121C2E, #19253A; texto #EDF3FD; acento #4CA7FF;
  sucesso #36D9A0; atenção #FFD166; erro #FF8797.
- Light: fundo #F5F7FC; superfícies #FFFFFF, #EBF0F8; texto #15243A; acento #175CD3;
  sucesso #096B50; atenção #8C5600; erro #A42237.
- Estados usam **ícone + texto + cor**, nunca somente cor; exibir timestamps e unidade.
- Tabelas padrão nativas `st.dataframe`: scroll horizontal, ordenação por cabeçalho,
  tela cheia, seleção de densidade por opção simplificada ou completa; CSVs existentes preservados.
- Gráficos: mesma semântica de cor em ambos os temas; legenda/eixos aumentam com fonte global;
  anomalias identificadas por símbolo, não somente vermelho.

## Regras de conexão e estados
A conectividade é **inferida pela idade da última leitura recebida na API**, não um
teste direto da conexão física ou do Wi-Fi do ESP32.

- **Recebendo dados**: idade de leitura válida entre -5 s e limite configurado
  `max(30 s, 3 × intervalo de envio)`. Mensagem: “ESP32 enviando leituras”.
- **Com atraso**: idade acima desse limite e até 2× esse limite.
  Mensagem: “ESP32 com atraso no envio”; pode ser rede, dispositivo ou backend.
- **Sem comunicação**: idade acima de 2× o limite, ou timestamp inválido.
  Mensagem: “Sem novas leituras do ESP32”.
- **Sem histórico/dispositivos**: estado vazio; orientar iniciar ESP32 e verificar API.
- **API indisponível**: **não** declarar ESP32 desconectado; mostrar “Não é possível
  verificar o ESP32: API indisponível”.
- Dados em atraso ou sem comunicação: KPIs permanecem visíveis como “última leitura
  recebida”, sem mensagem “ao vivo”. Exibir horário e idade da leitura com status.
- Diagnóstico: verificar energia do ESP32, Wi-Fi, conexão com API e horário do dispositivo.
- Evitar afirmações sobre causa raiz sem telemetria específica.

## Especificação por tela
### 1. Visão geral
Cabeçalho com dispositivo, último recebimento e estado legível; cartão hero:
Potência, Corrente e Tensão (ou último valor conhecido).
Explicar tensão nominal e indicação de comportamento anormal em linguagem simples.
Detalhes técnicos permanecem: VA, var, FP, frequência, energia acumulada.
Resumo de kWh, custo, média, pico e anomalias; **tabela de últimas leituras** com modo
resumido/completo. Sem histórico: mostrar instrução, não zero fictício.

### 2. Medições
Controles de série (Tudo, Tensão, Corrente, Potência, Aparente, Reativa), marcador de
anomalias, gráfico responsivo, informação sobre unidades, tabela de todas as leituras
do período em modo Resumido/Completo e download CSV. Dados ausentes:
mensagem e tabela vazia sem crash.

### 3. Consumo
Hoje / ontem, mês / projeção, custos estimados, meta, série horária, série diária.
Adicionar tabela de consumo por hora e por dia, preservando granularidade e dados
brutos via tabela completa. Projetado somente quando a cobertura permite; sinalizar
quando é estimativa. Nunca equiparar custo estimado a fatura de concessionária.

### 4. Anomalias
Score identificado como “indicador do modelo” e explicado; série, resumo por tipo,
tabela filtrável completa e CSV. Manter rotulação e formulário para qualquer leitura,
incluindo falsos negativos. Não tratar score como probabilidade sem calibração.

### 5. Alertas
Estado dos canais, teste de envio, lista de regras, criação, habilitação/desabilitação,
exclusão, regras sugeridas e histórico tabular. Operações administrativas existentes
não devem ser removidas nem silenciosamente alteradas. Mensagens de operação claras.

### 6. Sistema
Qualidade da energia, saúde do ESP32 (sinal Wi-Fi, uptime, falhas, cobertura),
validação contra instrumento, tabela de validações, CSV, exclusão, treinamento de
modelo, métricas e matriz de confusão. Distinguir “dispositivo sem leituras” de
“API indisponível”; indicadores técnicos têm ajuda contextual.

## Redação, glossário e ajuda
- “Potência (W)” — quanta energia é utilizada a cada instante (taxa de uso).
- “Consumo (kWh)” — energia acumulada no período; diferente de potência instantânea.
- “Tensão (V)” — nível de tensão elétrica medido.
- “Corrente (A)” — corrente elétrica circulando no circuito.
- “Fator de potência (FP)” — relação entre potência ativa e aparente, não
  um medidor universal de eficiência.
- “Potência aparente (VA)” e “reativa (var)” — detalhes avançados; não omitir.
- “Sinal Wi-Fi (dBm)” — quanto mais perto de zero, em geral melhor (valores negativos).
- “Anomalia” — leitura incomum segundo regras/modelo, não diagnóstico definitivo.
- “Score” — indicador numérico do modelo; não probabilidade de falha.

## Critérios de aceitação
1. Trocar Escuro ↔ Claro não altera leituras, filtros ou ações; opção persiste em URL.
2. Normal / Grande / Extra grande afeta controles, títulos, tabelas, gráficos;
   verificar visual a 360px, 768px e 1440px; zoom do navegador 200%.
3. Estado “Sem comunicação” aparece sem leituras novas; valores antigos sinalizados.
4. Falha na API apresenta estado **indeterminado**, nunca “ESP32 desconectado” como fato.
5. Últimas leituras disponíveis em Visão geral e Medições com colunas completas;
   CSV de medições e anomalias existente continua disponível.
6. Formulários de alertas, feedback, configuração, calibração e treino operam como antes.
7. Rótulos e unidades são legíveis sem depender exclusivamente da cor.
8. Nenhuma permissão de escrita no GitHub, senha, URL da API ou credenciais é alterada
   pelo redesign; P0 segurança permanece fora de escopo.
9. Testes unitários para estados de conexão, formato de rótulos, modos de apresentação;
   CI e validação manual com API/ESP32 antes do merge.

## Limitações explícitas
Esta implementação usa componentes nativos Streamlit e CSS complementar. O comportamento
exato de tela cheia, ordenação e acessibilidade dos widgets depende da versão do
Streamlit em execução. A perda de comunicação do ESP32 é **inferida** por timestamps;
não é uma prova de desconexão física. Não há backend de paginação novo.
