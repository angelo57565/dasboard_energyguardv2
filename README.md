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
