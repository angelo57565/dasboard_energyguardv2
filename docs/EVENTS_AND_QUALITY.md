# EnergyGuard v2 — Ocorrências, diagnósticos e qualidade de energia

## Escopo e propósito
A nova aba **Ocorrências** agrega seis análises de telemetria a partir de
`/api/readings` sem dependência de alertas, regras, modelo de ML ou notificações:
1. **Histórico de possíveis quedas de tensão:** episódios com tensão abaixo de 20 V.
2. **Picos elétricos:** sobretensão, sobrecorrente e potência excepcionalmente alta.
3. **Linha do tempo:** eventos classificados ordenados por início, com CSV.
4. **Saúde do ESP32:** tempo sem leituras, lacunas de transmissão e campos inválidos.
5. **Comparação do consumo habitual:** potência mediana da primeira e segunda metade
   das leituras do período, com variação percentual.
6. **Relatório de qualidade:** tensão/frequência mínima, média, máxima e totais por evento.

## Premissas e limites metrológicos
- São **indícios de triagem**. O painel não prova danos, interrupção da concessionária,
  fraude/desvio de energia nem conformidade normativa.
- Os limiares de tensão configurados são 117–133 V para rede nominal de 127 V,
  202–231 V para 220 V, ou ±8%/5% para nominal alternativo. Frequência 59,5–60,5 Hz
  e FP menor que 0,7 sob carga são critérios de apresentação, não atestados.
- Picos de corrente/potência dependem de pelo menos 12 amostras válidas anteriores
  e são relativos à mediana local. Um pico em janela com histórico insuficiente
  pode não ser identificado.
- Duração exibida é **intervalo entre primeira e última amostra fora de faixa**.
  Uma única amostra tem duração observada zero; isso não indica duração física zero.
- Lacuna de transmissão (>3× intervalo de envio, mínimo 10 segundos) é listada
  separadamente como **Intervalo sem telemetria**. Não é considerada queda de energia.
  Uma lacuna impede a continuidade de episódios; histórico e duração real ficam
  desconhecidos durante a ausência de leituras.
- Os dados vêm da janela selecionada no menu lateral e estão limitados pela API
  (até 20.000 leituras atualmente). Mudanças de janela e ausência de históricos
  completos limitam os totais apresentados. Não é armazenamento permanente.
- Comparação de consumo é mediana **de potência** em duas metades por contagem
  de amostras, não consumo de energia em kWh, comparação sazonal ou estimativa
  de faturamento. A linha de base pode ser enviesada por amostragem irregular.
- O relatório cobre apenas tensão/frequência coletadas, sem certificado de qualidade
  da rede elétrica nem assinaturas técnicas. O CSV é exportação tabular, não PDF.

## Arquitetura
- `event_analysis.py`: transformações puras de listas de leituras em episódios e
  estatísticas. Não depende de Streamlit nem acessa a rede.
- `tabs.events_tab()`: interface, filtros não aplicados, tabelas, indicadores e downloads.
- `app.py`: acrescenta a aba **Ocorrências**, preservando as anteriores.
- `tests/test_event_analysis.py`: regressões de eventos e durações.
- Leitura somente; nenhuma chamada de POST/PUT/DELETE introduzida.

## Critérios de aceite
- Com alertas e ML desligados, a aba funciona com dados de leituras disponíveis.
- Amostra de tensão fora de faixa cria evento; lacuna sem amostra não cria queda.
- Episódios não atravessam grandes lacunas.
- Data inicial, última amostra, valores extremos, número de amostras e
  duração observada disponíveis no relatório tabular.
- Dispositivo sem leituras exibe diagnóstico indisponível.
- Temas claro/escuro, tamanho da fonte, tabelas completas, exportações e abas
  anteriores continuam disponíveis.
- Para produção: testar com dados reais, relógios sincronizados, perdas de conexão,
  desligamento de sensor e instâncias com histórico longo.
