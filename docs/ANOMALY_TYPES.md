# EnergyGuard v2 — Tipos de anomalia

## Propósito
A aba **Tipos de anomalia** traduz em linguagem acessível os códigos de anomalia
já fornecidos pela API FastAPI. Não substitui as abas **Anomalias** ou **Alertas**:
as ações de rotulagem e as regras de alertas continuam onde estavam.

## Categorias da API
| Código da API | Interpretação exibida | Prioridade de triagem |
| --- | --- | --- |
| queda | Possível interrupção de energia | Alta |
| sobretensao | Tensão acima do limite configurado | Alta |
| subtensao | Tensão abaixo do limite configurado | Alta |
| sobrecorrente | Corrente elevada ou pico | Alta |
| consumo_elevado | Potência / consumo acima do habitual | Atenção |
| consumo_baixo | Potência / consumo abaixo do habitual | Atenção |
| frequencia | Frequência fora da faixa | Alta |
| fp_baixo | Fator de potência baixo | Atenção |
| sensor | Possível inconsistência do sensor | Alta |
| incomum | Comportamento incomum sem causa identificada | Analisar |
| ausente/desconhecido | Anomalia sem classificação técnica | Analisar |

A **prioridade** organiza a revisão humana: não é laudo de dano, severidade física
ou previsão de incêndio. Os limites numéricos e os códigos são estabelecidos pelo backend.

## O que cada ocorrência mostra
- Data/hora e ID da leitura, dispositivo, tipo e prioridade;
- Tensão, corrente e potência medidas e score do modelo, se disponíveis;
- Indício da classificação e procedimento sugerido para conferência;
- Avaliação prévia do operador, quando houver;
- Filtro por tipo, tabela completa e exportação CSV.

Uma leitura pode ter múltiplos códigos. Nesse caso, aparece em todas as
categorias correspondentes; portanto, a soma por tipo pode ser superior à
quantidade de leituras únicas. O painel consulta no máximo 200 anomalias;
esse conjunto independe do seletor de período do menu lateral.

## Limites e não conclusões
**Queda de energia:** tensão/corrente ausentes não comprovam corte no
fornecimento; sensor desconectado ou alimentação do dispositivo podem
produzir sinais similares. **Consumo elevado:** não prova desvio, fraude,
furto ou desperdício; comparação de cargas e medição independente são necessárias.
**Picos:** a medida isolada não prova dano aos equipamentos.
**Energia perdida (kWh):** não calculada nesta aba porque uma leitura anômala
não fornece por si só duração do evento, medição antes/depois nem linha de base
para estabelecer quantidade de energia não entregue ou desviada.

Para identificar desvio/furto exigiria novos dados e métodos: medidor
certificado da entrada, medidor a jusante, sincronização, balanço energético,
validade metrológica, inspeção e análise de falhas, todos fora do escopo do
dashboard atual. Nunca atribuir culpa a pessoas.

## Testes e aceite
1. Casos multi-rótulo permanecem visíveis, sem perda de código original.
2. Tipo ausente ou não reconhecido permanece explícito.
3. Valores nulos e horários inválidos não encerram a página.
4. Tabela/CSV incluem medição e orientação, sem alterar APIs.
5. Se a API falhar, o dashboard mantém o tratamento de erro anterior.
6. Rotulagem, treinamento, regras e downloads anteriores continuam funcionando.
7. Não inferir furto, dano, causa física ou energia perdida sem evidência.


## Diagnóstico automático independente de alertas

O modo padrão da aba é **Indícios nas medições (automático)**: usa as leituras
que já alimentam a aba Medições, do período selecionado pelo usuário. Não
exige a existência de regras, notificações, registros em `/api/anomalies`
ou treinamento do modelo. Mesmo se a API de anomalias falhar, a aba continua
funcionando com `/api/readings`, desde que esse endpoint esteja acessível.

O algoritmo `reading_diagnostics.infer_reading_types` usa critérios de triagem,
sem persistir resultados ou emitir notificações: tensão nominal 127 V (faixa
117–133 V) ou 220 V (202–231 V); frequência 59,5–60,5 Hz; FP abaixo de 0,7
quando há carga; queda de tensão após leitura normal; grandeza negativa ou
potência ativa acima da aparente com margem; e variações extremas de potência
ou corrente em relação à mediana de pelo menos 12 amostras anteriores. Esses
valores não são normas de conformidade nem limites de proteção.

Com o seletor de origem, ainda é possível ver **Anomalias classificadas pela
API** como antes. O painel não cria `/api/alerts/*`, não escreve no backend
e não confunde indicativo com diagnóstico. Sem leituras, exibe estado vazio.
