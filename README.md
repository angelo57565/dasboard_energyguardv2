# EnergyGuard – Dashboard (Streamlit) v2

Lê tudo pela API FastAPI (não acessa o MySQL direto). Precisa do backend v2.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export API_URL=http://localhost:8000   # Windows (cmd): set API_URL=http://localhost:8000
export API_KEY=a-mesma-chave-do-backend
streamlit run app.py
```

Abre em http://localhost:8501.

## Barra lateral

Logo · Tema (escuro / claro de alto contraste) · Dispositivo · Período · Atualização automática + "Atualizar agora" ·
Configurações (tarifa, tensão nominal 127/220 V, meta mensal em kWh, intervalo de envio; ficam salvas no backend) ·
Conexão com a API (URL e chave).

## Abas

| Aba | O que tem |
|---|---|
| Início | Status geral, potência/corrente/tensão com mini-gráficos, detalhes (VA, var, FP, frequência) e resumo do período |
| Gráficos | Tensão, corrente, potência, aparente e reativa; anomalias marcadas; CSV |
| Consumo | kWh por hora e por dia, hoje × ontem, projeção do mês, custo e barra da meta mensal |
| Anomalias | Score do modelo, tipo e motivo de cada anomalia, gráfico por tipo, filtro, avaliação (real / falso alarme) |
| Alertas | Regras por limite, regras sugeridas, histórico, teste de Telegram/e-mail |
| Sistema | Qualidade da energia e saúde do ESP32 · Validação com multímetro/alicate · Modelo (treino, precisão, recall, F1) |

## Visual

Interface sem emoji: ícones geométricos em SVG (`icons.py`), logo em `assets/`, cores e espaçamentos em `theme.py`.
Atualização automática sem piscar a tela, layout responsivo (celular, tablet e computador) e animações
desligadas quando o sistema pede "reduzir movimento".

## Tema

O tema escolhido fica no endereço (`?tema=claro`). As cores vêm de `theme.py`.

## Arquivos

`app.py` (layout e dados) · `tabs.py` (conteúdo das abas) · `ui.py` (componentes) · `icons.py` · `theme.py` · `charts.py` · `client.py` · `helpers.py` · `auth.py` · `assets/`

## Abrir para a internet (apresentação) com senha

Deixe tudo rodando no seu PC (MySQL, backend, dashboard) e exponha **só o dashboard**, porta 8501.
A API (porta 8000) continua acessível apenas no seu PC e na sua rede.

1. Defina a senha antes de abrir o dashboard:
   - Windows (cmd): `set DASHBOARD_PASSWORD=sua-senha`   ·   Linux/Mac: `export DASHBOARD_PASSWORD=sua-senha`
   - ou copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e edite.
2. `streamlit run app.py`
3. Em outro terminal, instale o `cloudflared` (developers.cloudflare.com → Cloudflare One → Connect networks → Downloads) e rode:
   `cloudflared tunnel --url http://localhost:8501`
4. Ele mostra um link `https://....trycloudflare.com`: é o endereço público (muda a cada vez que o túnel é reiniciado).

Sem `DASHBOARD_PASSWORD` o dashboard abre sem senha, então **nunca abra o túnel sem definir a senha**.
Depois de 5 senhas erradas o login trava por 1 minuto.


## Correções de confiabilidade

- O resumo de 15 minutos é estimado pela integração das amostras; intervalos grandes não são interpolados.
- Cobertura de leituras mede intervalos de reporte observados, não uptime físico.
- Projeção mensal é omitida quando faltam dados do começo do mês.
- Consultas incrementais exigem IDs estáveis e timestamps ISO consistentes na API.
- Regras sugeridas evitam duplicação sequencial; idempotência concorrente exige suporte do backend.
- Qualidade da API agregada por hora não é exibida na janela de 15 minutos.
- Testes: `pip install -r requirements-dev.txt && pytest -q && ruff check .`.


## Redesign UX/UI e acessibilidade

A especificação por tela, os estados de conexão, as regras de tabelas e os critérios de aceitação estão em [docs/UX_UI_SPEC.md](docs/UX_UI_SPEC.md).

Na barra lateral em **Aparência**, alterne **Escuro/Claro**, escolha a letra **Normal/Grande/Extra grande** e selecione tabelas **Resumidas/Completas**. O modo completo preserva todas as colunas exibidas pelo backend. A visualização é por sessão, e tema/fonte também podem ser compartilhados por URL (`?tema=claro&fonte=18`).

O cabeçalho informa **ESP32 enviando leituras**, **com atraso** ou **sem novas leituras**, com base no horário da última leitura registrada na API. Isso não é uma medição física direta do estado do ESP32. Quando a API falha, o estado é indeterminado, não offline confirmado.

O redesign preserva as seis abas, operações de alertas, avaliações de anomalias, validações, treinamento e os downloads CSV. A **Visão geral** e **Medições** ganharam tabelas nativas; **Consumo** possui tabelas horárias e diárias. Testes de regressão de apresentação em `tests/test_presentation.py`.


## Tipos de anomalia e diagnóstico explicativo

A aba **Tipos de anomalia** apresenta as classificações recebidas da API,
com prioridade de triagem, tabela de ocorrências, filtros, valores elétricos,
orientações de conferência e download CSV. Consulte a [especificação de tipos](docs/ANOMALY_TYPES.md).

O dashboard **não diagnostica desvio/furto de energia nem calcula energia perdida**:
consumo incomum é sinal de investigação, não prova de causa. A classificação
se limita às últimas 200 ocorrências consultadas. A aba original de Anomalias,
regras de Alertas e formulários permanecem preservados.
