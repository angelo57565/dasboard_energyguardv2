import pandas as pd
import requests
import streamlit as st

from telemetry import plot_sample

import charts
from anomaly_insights import CATALOG, category, codes_for, detail_rows, overview_by_type
from helpers import (
    COLUMNS_PT, NO_TYPE, QUANTITY_PT, TYPE_PT, anomalies_table, daily_consumption, fmt_pct,
    hourly_dataframe, human_age, median_interval_s, month_projection, primary_type, readings_csv,
    reasons_text, rssi_label, today_vs_yesterday, type_label, type_summary, types_text,
    validation_csv, validation_dataframe, validation_summary, validation_table,
)
from ui import banner, cards, hero, plot, progress, rerun, section, simple_help, stale_data_note, table

METRICS_PT = {
    "voltage": ("Tensão", "V"), "current": ("Corrente", "A"), "power": ("Potência", "W"),
    "power_factor": ("Fator de potência", ""), "frequency": ("Frequência", "Hz"),
    "apparent_power": ("Potência aparente", "VA"), "reactive_power": ("Potência reativa", "var"),
}
VOLTAGE_RANGES = {127: (117.0, 133.0), 220: (202.0, 231.0)}
SP = "America/Sao_Paulo"


def _voltage_range(nominal: int) -> tuple[float, float]:
    return VOLTAGE_RANGES.get(nominal, (round(nominal * 0.92, 1), round(nominal * 1.05, 1)))


def _guard(fn) -> bool:
    try:
        fn()
        return True
    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        banner("danger", f"Erro: {detail}")
    except requests.RequestException as exc:
        banner("danger", f"Erro de conexão: {exc}")
    return False


def overview(ctx, d):
    latest, summary, df = d["latest"], d["summary"], d["df"]
    hours_int = d["hours_int"]

    if not d["online"]:
        state = d["connection"]
        status = ("warn" if state.code == "delayed" else "danger",
                  state.label, f"Última leitura há {human_age(d['age'])}." if pd.notna(d["age"]) and d["age"] != float("inf")
                  else "Sem horário válido para a última leitura.")
        stale_data_note()
    elif latest["voltage"] < 20 and latest["current"] > 0.15:
        status = ("warn", "Sem tensão detectada",
                  "O ZMPT101B está sem rede ou desligado. Potência, fator de potência e frequência "
                  "aparecem zerados; a corrente é medida normalmente.")
    elif latest["is_anomaly"]:
        status = ("warn", f"Anomalia: {types_text(latest)}",
                  f"Score {latest['anomaly_score']:.3f}. Veja a aba Anomalias.")
    else:
        status = ("ok", "Leituras dentro do esperado", f"{summary['anomalies']} ocorrência(s) fora do padrão no período.")

    tail = df.tail(60) if not df.empty else df

    def spark(col):
        return tail[col].tolist() if not tail.empty else []

    hero(status, [
        dict(label="Potência", value=f"{latest['power']:.0f}", unit="W", icon="bolt", tone="c2", spark=spark("power")),
        dict(label="Corrente", value=f"{latest['current']:.2f}", unit="A", icon="pulse", tone="c1", spark=spark("current")),
        dict(label="Tensão", value=f"{latest['voltage']:.1f}", unit="V", icon="wave", tone="c3", spark=spark("voltage")),
    ])

    s_va = latest["voltage"] * latest["current"]
    q_var = max(s_va ** 2 - latest["power"] ** 2, 0) ** 0.5
    simple_help("Potência (W) indica o uso instantâneo. Consumo (kWh) é a energia acumulada no período. "
                "Leituras fora do padrão precisam de análise; não são diagnóstico definitivo.")
    section("Detalhes da medição", "gauge")
    cards([
        ("Potência aparente", f"{s_va:.0f} VA", "gauge"),
        ("Potência reativa", f"{q_var:.0f} var", "gauge"),
        ("Fator de potência", f"{latest['power_factor']:.2f}", "target"),
        ("Frequência", f"{latest['frequency']:.2f} Hz", "wave"),
        ("Energia total", f"{latest['energy']:.3f} kWh", "database"),
    ])

    section("Resumo dos últimos 15 minutos" if d["short_window"] else f"Resumo das últimas {hours_int} h", "bars")
    kwh = summary["energy_kwh"] or 0.0
    cards([
        ("Consumo", f"{kwh:.3f} kWh", "bars"),
        ("Custo estimado", f"R$ {kwh * ctx.tariff:.2f}", "dollar"),
        ("Potência média", f"{summary['power_avg'] or 0:.0f} W", "gauge"),
        ("Pico de potência", f"{summary['power_max'] or 0:.0f} W", "bolt"),
        ("Anomalias", str(summary["anomalies"]), "alert"),
    ])
    st.caption("Custo estimado: consumo × tarifa configurada. O valor não substitui sua conta de energia.")
    section("Últimas leituras", "database")
    if df.empty:
        banner("info", "Ainda não há leituras disponíveis nesse período.")
    else:
        recent = df.tail(25).iloc[::-1].copy().rename(columns={
            **COLUMNS_PT, "apparent": "Potência aparente (VA)", "reactive": "Potência reativa (var)"
        })
        table(recent)


def charts_tab(ctx, d):
    rows, df = d["rows"], d["df"]
    section("Medições ao longo do tempo", "chart")
    st.caption("As linhas mostram valores registrados pelo sensor. Marcas em X indicam leituras incomuns.")
    c1, c2 = st.columns([3, 2])
    which = c1.radio("Mostrar", ["Tudo", *charts.SERIES], horizontal=True, key="serie")
    mark = c2.checkbox("Marcar anomalias", value=True, key="marcar")
    if df.empty:
        banner("info", "Sem leituras neste período.")
        return
    plot(charts.timeseries(plot_sample(df), which, mark, ctx.theme, ctx.font_scale), "grafico")
    section("Tabela de medições do período", "database")
    table(df.iloc[::-1].rename(columns={
        **COLUMNS_PT, "apparent": "Potência aparente (VA)", "reactive": "Potência reativa (var)"
    }))
    st.download_button("Baixar leituras (CSV)", readings_csv(rows),
                       file_name=f"leituras_{ctx.device}.csv", mime="text/csv", key="dl_leituras")


def consumption(ctx, d):
    try:
        raw = ctx.api.cached_get("/api/consumption/hourly", device_id=ctx.device, hours=24 * 31)
    except requests.RequestException as exc:
        banner("danger", f"Erro ao consultar o consumo: {exc}")
        return
    hourly = hourly_dataframe(raw)
    if hourly.empty:
        banner("info", "Ainda não há consumo registrado.")
        return

    now = pd.Timestamp.now(tz=SP)
    today, y_same, y_total = today_vs_yesterday(hourly, now)
    so_far, projected, _days = month_projection(hourly, now)
    projection_ready = pd.notna(projected)

    delta = f"{(today - y_same) / y_same * 100:+.0f}% vs ontem" if y_same > 0.001 else "—"
    section("Hoje", "clock")
    st.caption("Consumo em kWh é energia acumulada, diferente da potência instantânea (W).")
    cards([
        ("Hoje até agora", f"{today:.2f} kWh", "bolt"),
        ("Ontem até a mesma hora", f"{y_same:.2f} kWh", "clock"),
        ("Diferença", delta, "chart"),
        ("Ontem inteiro", f"{y_total:.2f} kWh", "bars"),
    ])

    section("Mês", "bars")
    cards([
        ("Consumo no mês", f"{so_far:.2f} kWh", "bars"),
        ("Projeção do mês", f"{projected:.1f} kWh" if projection_ready else "Dados insuficientes", "chart"),
        ("Custo até agora", f"R$ {so_far * ctx.tariff:.2f}", "dollar"),
        ("Custo projetado", f"R$ {projected * ctx.tariff:.2f}" if projection_ready else "—", "dollar"),
    ])
    if ctx.goal > 0:
        frac = so_far / ctx.goal
        progress(frac, f"Meta de {ctx.goal:.0f} kWh: {so_far:.1f} kWh usados ({frac * 100:.0f}%)")
        if not projection_ready:
            banner("warn", "Histórico insuficiente no início do mês para projetar o consumo.")
        elif projected > ctx.goal:
            banner("warn", f"Nesse ritmo você chega a {projected:.1f} kWh e passa da meta de {ctx.goal:.0f} kWh.")
        else:
            banner("ok", f"Nesse ritmo você fecha o mês com {projected:.1f} kWh, dentro da meta.")
    else:
        st.caption("Defina uma meta mensal em Configurações para ver a barra de progresso.")

    last24 = hourly[hourly["period"] >= now - pd.Timedelta(hours=24)]
    plot(charts.bars(last24["period"], last24["kwh"], ctx.theme,
                     "Consumo por hora (últimas 24 h)", font_scale=ctx.font_scale), "barras_hora")
    daily = daily_consumption(hourly).tail(14)
    plot(charts.bars(daily["day"].dt.strftime("%d/%m"), daily["kwh"], ctx.theme,
                     "Consumo por dia (últimos 14 dias)", font_scale=ctx.font_scale), "barras_dia")
    section("Histórico de consumo por hora", "database")
    table(hourly.iloc[::-1].rename(columns={"period": "Horário", "kwh": "Consumo (kWh)"}))
    section("Consumo por dia", "database")
    table(daily.iloc[::-1].rename(columns={"day": "Dia", "kwh": "Consumo (kWh)"}))


def anomalies_tab(ctx, d):
    df, anomalies = d["df"], d["anomalies"]
    st.caption("Anomalia significa uma leitura incomum segundo regras ou modelo, não uma falha confirmada.")
    if not d["model"]["ready"]:
        banner("warn", "O modelo ainda não foi treinado, então nada foi classificado. Veja Sistema, aba Modelo.")
    if not df.empty and "anomaly_score" in df and df["anomaly_score"].notna().any():
        plot(charts.score_chart(plot_sample(df), ctx.theme, ctx.font_scale), "grafico_score")

    if not anomalies:
        banner("info", "Nenhuma anomalia registrada.")
    else:
        summary = type_summary(anomalies)
        section("Anomalias por tipo", "bars")
        plot(charts.bars(summary["Tipo"], summary["Total"], ctx.theme,
                         "Ocorrências por tipo (últimas 200 anomalias)", ytitle="ocorrências",
                         font_scale=ctx.font_scale), "barras_tipo")
        table(summary)

        options = ["Todos os tipos", *summary["Tipo"]]
        chosen = st.selectbox("Filtrar por tipo", options, key="filtro_tipo")
        shown = anomalies if chosen == options[0] else [
            a for a in anomalies
            if (type_label(primary_type(a)) if primary_type(a) else NO_TYPE) == chosen
        ]

        section("Últimas anomalias", "alert")
        table(anomalies_table(shown).head(30))
        st.download_button("Baixar anomalias (CSV)", readings_csv(shown),
                           file_name=f"anomalias_{ctx.device}.csv", mime="text/csv", key="dl_anomalias")

        with st.expander("Como cada tipo é identificado"):
            for label, desc in TYPE_PT.values():
                st.markdown(f"**{label}**: {desc}")
            st.caption("O Isolation Forest detecta que algo é estranho; as regras acima dizem o que parece estar errado. "
                       "Uma anomalia pode ter mais de um tipo.")

        pending = [a for a in shown if not a.get("feedback")][:8]
        section("Avalie as anomalias", "check")
        st.caption("Suas respostas calculam a precisão do modelo (Sistema, aba Modelo) e as anomalias reais saem do próximo treino.")
        if not pending:
            banner("ok", "Todas as anomalias deste filtro já foram avaliadas.")
        for a in pending:
            local = pd.to_datetime(a["created_at"], utc=True).tz_convert(SP)
            st.markdown(f"**#{a['id']}** · {types_text(a)} · {local:%d/%m %H:%M:%S} · {a['voltage']:.0f} V · "
                        f"{a['current']:.2f} A · {a['power']:.0f} W")
            why = reasons_text(a.get("reasons"))
            if why:
                st.caption(why)
            b1, b2 = st.columns(2)
            if b1.button("Confirmar como real", key=f"real_{a['id']}"):
                if _guard(lambda: ctx.api.put(f"/api/readings/{a['id']}/feedback", json={"label": "real"})):
                    rerun(ctx.auto)
            if b2.button("Falso alarme", key=f"false_{a['id']}"):
                if _guard(lambda: ctx.api.put(f"/api/readings/{a['id']}/feedback", json={"label": "false"})):
                    rerun(ctx.auto)

    with st.expander("Rotular qualquer leitura (inclusive as que o modelo deixou passar)"):
        with st.form("form_rotulo", clear_on_submit=False):
            rid = st.number_input("ID da leitura", min_value=1, step=1, value=1)
            choice = st.selectbox("Rótulo", ["Anomalia real (o modelo perdeu)", "Normal (não é anomalia)",
                                             "Remover rótulo"])
            if st.form_submit_button("Salvar rótulo", type="primary"):
                label = {"Anomalia real (o modelo perdeu)": "real", "Normal (não é anomalia)": "false",
                         "Remover rótulo": None}[choice]
                if _guard(lambda: ctx.api.put(f"/api/readings/{int(rid)}/feedback", json={"label": label})):
                    banner("ok", f"Leitura #{int(rid)} atualizada.")



def anomaly_types_tab(ctx, d):
    """Readable differential classification for anomalies already detected by the backend."""
    section("Tipos de anomalia identificados", "alert")
    st.caption("Classificação indicativa baseada nas leituras e nos tipos informados pela API. "
               "Uma mesma ocorrência pode ter mais de um tipo. Isso não comprova a causa da falha.")
    anomalies = d["anomalies"]
    if not anomalies:
        banner("info", "Nenhuma anomalia disponível nas últimas 200 ocorrências consultadas.")
        return

    summary = overview_by_type(anomalies)
    high = int(sum(1 for row in anomalies if any(
        category(code)[1] == "Alta" for code in (codes_for(row) or [""])
    )))
    cards([
        ("Ocorrências consultadas", str(len(anomalies)), "database"),
        ("Para revisar com prioridade", str(high), "alert"),
        ("Tipos encontrados", str(len(summary)), "bars"),
    ])
    st.caption("A prioridade é para triagem das leituras; não é uma avaliação automática do risco de dano "
               "ou perigo elétrico. Consulta limitada às últimas 200 anomalias da API, "
               "independentemente do período selecionado na barra lateral.")

    section("Distribuição por tipo", "bars")
    plot(charts.bars(summary["Tipo"], summary["Ocorrências"], ctx.theme,
                     "Ocorrências classificadas", ytitle="ocorrências",
                     font_scale=ctx.font_scale), "grafico_tipos_diagnostico")
    table(summary.rename(columns={"Código da API": "Classificação técnica"}))

    section("Investigar uma ocorrência", "target")
    found_codes = summary["Código da API"].tolist()
    choices = ["Todos os tipos", *found_codes]
    selected = st.selectbox(
        "Filtrar classificação", choices, key="diagnostico_tipo",
        format_func=lambda code: "Todos os tipos" if code == "Todos os tipos"
        else category("" if code == "sem_tipo" else code)[0]
    )
    selected_code = None if selected == "Todos os tipos" else (
        "" if selected == "sem_tipo" else selected
    )
    details = detail_rows(anomalies, selected_code)
    if details.empty:
        banner("info", "Nenhuma ocorrência encontrada para esse filtro.")
        return

    table(details)
    st.download_button(
        "Baixar diagnóstico de anomalias (CSV)",
        data=details.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"diagnostico_anomalias_{ctx.device}.csv", mime="text/csv",
        key="download_diagnostico_anomalias"
    )

    records = [row for row in anomalies if selected_code is None or
               selected_code in (codes_for(row) or [""])]
    chosen_id = st.selectbox(
        "Ver detalhes da leitura", range(len(records)), key="diagnostico_leitura",
        format_func=lambda i: f"Leitura #{records[i].get('id', '—')} · "
        f"{records[i].get('created_at', 'sem horário')}"
    )
    chosen = records[chosen_id]
    labels = [category(code) for code in (codes_for(chosen) or [""])]
    st.markdown("**Classificações registradas pela API**")
    for label, priority, explanation, action in labels:
        with st.expander(f"{label} · Prioridade: {priority}", expanded=True):
            st.write(f"**O que indica:** {explanation}")
            st.write(f"**O que verificar:** {action}")
    why = reasons_text(chosen.get("reasons"))
    if why:
        st.write("**Indícios numéricos informados pelo modelo:**")
        st.caption(why)
    else:
        st.caption("A API não informou motivos numéricos detalhados para essa leitura.")

    banner("warn", "Consumo inesperado não comprova furto, desvio de energia nem defeito. "
           "É necessária verificação técnica e, se aplicável, da concessionária.")
    with st.expander("Quais classificações o sistema reconhece?"):
        for code, (label, priority, explanation, action) in CATALOG.items():
            st.markdown(f"**{label}** ({code}) · Triagem: {priority}")
            st.caption(f"{explanation} {action}")
        st.caption("Se a API enviar um código desconhecido, ele aparecerá como "
                   "'Anomalia sem classificação técnica', preservando o código original.")


def alerts_tab(ctx, d):
    try:
        channels = ctx.api.get("/api/alerts/channels")
        rules = ctx.api.get("/api/alerts/rules")
        events = ctx.api.get("/api/alerts/events", device_id=ctx.device, limit=50)
    except requests.RequestException as exc:
        banner("danger", f"Erro ao consultar alertas: {exc}")
        return

    on = [n for n, v in (("Telegram", channels["telegram"]), ("E-mail", channels["email"])) if v]
    if on:
        banner("ok", "Avisos enviados por: " + ", ".join(on))
        if st.button("Enviar mensagem de teste", key="teste_notif"):
            _guard(lambda: banner("info", "Teste enviado." if ctx.api.post("/api/alerts/test")["sent"]
                                  else "Nenhum canal conseguiu enviar."))
    else:
        banner("warn", "Telegram e e-mail não configurados: os alertas só aparecem aqui. "
                       "Preencha o .env do backend para receber no celular.")

    section("Regras", "sliders")
    st.caption("Regras enviam avisos quando uma medição ultrapassa o limite configurado.")
    if not rules:
        banner("info", "Nenhuma regra ainda. Crie uma abaixo ou use as sugeridas.")
    for rule in rules:
        label, unit = METRICS_PT[rule["metric"]]
        scope = rule["device_id"] or "todos os dispositivos"
        state = "" if rule["enabled"] else " (desligada)"
        st.markdown(f"**{rule['name']}**{state}  \n{label} {rule['operator']} {rule['threshold']:g} {unit} · "
                    f"aviso a cada {rule['cooldown_s'] // 60} min · {scope}")
        b1, b2 = st.columns(2)
        if b1.button("Desligar" if rule["enabled"] else "Ligar", key=f"tog_{rule['id']}"):
            body = {k: rule[k] for k in ("name", "metric", "operator", "threshold", "cooldown_s", "device_id")}
            body["enabled"] = not rule["enabled"]
            if _guard(lambda: ctx.api.put(f"/api/alerts/rules/{rule['id']}", json=body)):
                rerun(ctx.auto)
        if b2.button("Excluir", key=f"del_{rule['id']}"):
            if _guard(lambda: ctx.api.delete(f"/api/alerts/rules/{rule['id']}")):
                rerun(ctx.auto)

    vmin, vmax = _voltage_range(ctx.nominal)
    if st.button(f"Criar regras sugeridas ({ctx.nominal} V)", key="sugeridas", type="primary"):
        base = {"cooldown_s": 600, "enabled": True, "device_id": None}
        suggested = [
            {"name": "Tensão baixa", "metric": "voltage", "operator": "<", "threshold": vmin},
            {"name": "Tensão alta", "metric": "voltage", "operator": ">", "threshold": vmax},
            {"name": "Frequência baixa", "metric": "frequency", "operator": "<", "threshold": 59.5},
            {"name": "Frequência alta", "metric": "frequency", "operator": ">", "threshold": 60.5},
        ]
        existing = {(r["metric"], r["operator"], float(r["threshold"]), r.get("device_id")) for r in rules}
        pending = [r for r in suggested if (r["metric"], r["operator"], float(r["threshold"]), None) not in existing]
        created = 0
        for rule in pending:
            if not _guard(lambda rule=rule: ctx.api.post("/api/alerts/rules", json={**base, **rule})):
                banner("warn", f"{created} regras criadas antes da falha. Confira as regras antes de tentar novamente.")
                break
            created += 1
        else:
            banner("ok", f"{created} regras criadas; {len(suggested) - created} já existentes.")
            rerun(ctx.auto)

    with st.expander("Nova regra"):
        with st.form("form_regra", clear_on_submit=True):
            name = st.text_input("Nome", "Corrente alta")
            metric = st.selectbox("Grandeza", list(METRICS_PT),
                                  format_func=lambda m: f"{METRICS_PT[m][0]} ({METRICS_PT[m][1]})".replace(" ()", ""))
            op = st.radio("Dispara quando for", [">", "<"], horizontal=True,
                          format_func=lambda o: "maior que" if o == ">" else "menor que")
            thr = st.number_input("Limite", value=30.0, step=1.0)
            cool = st.number_input("Intervalo mínimo entre avisos (min)", min_value=0, value=10, step=1)
            only = st.checkbox(f"Só para {ctx.device}", value=False)
            if st.form_submit_button("Criar regra", type="primary"):
                body = {"name": name, "metric": metric, "operator": op, "threshold": float(thr),
                        "cooldown_s": int(cool) * 60, "enabled": True, "device_id": ctx.device if only else None}
                if _guard(lambda: ctx.api.post("/api/alerts/rules", json=body)):
                    rerun(ctx.auto)

    section("Histórico", "clock")
    if not events:
        banner("info", "Nenhum alerta disparado ainda.")
        return
    kinds = {"rule": "Regra", "anomaly": "Anomalia", "offline": "Offline"}
    ev = pd.DataFrame(events)
    ev["created_at"] = pd.to_datetime(ev["created_at"], utc=True).dt.tz_convert(SP).dt.strftime("%d/%m %H:%M")
    table(pd.DataFrame({
        "Horário": ev["created_at"], "Tipo": ev["kind"].map(kinds), "Mensagem": ev["message"],
        "Enviado": ev["notified"].map({True: "sim", False: "não"}),
    }))


def quality_health(ctx, d):
    latest, df, hours_int = d["latest"], d["df"], d["hours_int"]
    vmin, vmax = _voltage_range(ctx.nominal)

    section(f"Qualidade da energia · últimas {hours_int} h", "wave")
    try:
        q = None if d["short_window"] else ctx.api.cached_get("/api/quality", device_id=ctx.device, hours=hours_int, vmin=vmin, vmax=vmax)
    except requests.RequestException as exc:
        banner("danger", f"Erro ao consultar a qualidade: {exc}")
        q = None
    if q and q["readings_with_mains"]:
        v, f = q["voltage"], q["frequency"]
        cards([
            ("Tensão mínima", f"{v['min']:.1f} V", "wave"),
            ("Tensão média", f"{v['avg']:.1f} V", "wave"),
            ("Tensão máxima", f"{v['max']:.1f} V", "wave"),
            (f"Abaixo de {vmin:g} V", fmt_pct(v["low_pct"]), "alert"),
            (f"Acima de {vmax:g} V", fmt_pct(v["high_pct"]), "alert"),
            ("Frequência mín–máx", f"{f['min']:.2f}–{f['max']:.2f} Hz" if f["min"] is not None else "—", "pulse"),
            ("Frequência fora de 59,5–60,5 Hz", fmt_pct(f["out_pct"]), "alert"),
        ])
        st.caption(f"Faixa adequada para {ctx.nominal} V: {vmin:g} a {vmax:g} V. Mude a tensão nominal em Configurações.")
    elif d["short_window"]:
        banner("info", "Indicadores de qualidade da API disponíveis para períodos a partir de 1 hora.")
    elif q:
        banner("info", "Sem leituras com a rede ligada neste período.")

    section("Saúde do ESP32", "cpu")
    st.caption("A conexão é estimada pelas leituras recebidas na API; não é teste direto do cabo ou do Wi-Fi.")
    rssi = latest.get("rssi")
    avail = d["coverage"]
    interval = median_interval_s(df)
    cards([
        ("Sinal Wi-Fi", f"{rssi} dBm ({rssi_label(rssi)})" if rssi is not None else "—", "wifi"),
        ("Ligado há", human_age(latest["uptime_s"]) if latest.get("uptime_s") is not None else "—", "clock"),
        ("Falhas de envio", str(latest["send_failures"]) if latest.get("send_failures") is not None else "—", "alert"),
        ("Cobertura de leituras", f"{avail:.0f}%", "check"),
        ("Intervalo entre leituras", f"{interval:.1f} s" if interval else "—", "clock"),
    ])
    if latest.get("uptime_s") is not None and latest["uptime_s"] < 120:
        banner("info", "O ESP32 reiniciou há pouco tempo.")
    if rssi is not None and rssi < -80:
        banner("warn", "Sinal Wi-Fi ruim: aproxime o ESP32 do roteador para evitar falhas de envio.")
    if not df.empty and "rssi" in df and df["rssi"].notna().any():
        plot(charts.rssi_chart(df, ctx.theme, ctx.font_scale), "grafico_rssi")


def validation(ctx, d):
    section("Validação com instrumento", "target")
    st.caption("Meça a mesma grandeza com multímetro (tensão) ou alicate amperímetro (corrente) e digite o valor. "
               "O sistema guarda a média das últimas 6 leituras do ESP32 para comparar.")
    with st.form("form_validacao", clear_on_submit=True):
        c1, c2 = st.columns(2)
        quantity = c1.selectbox("Grandeza", list(QUANTITY_PT),
                                format_func=lambda q: f"{QUANTITY_PT[q][0]} ({QUANTITY_PT[q][1]})")
        ref = c2.number_input("Valor do instrumento", min_value=0.0, value=0.0, step=0.1, format="%.3f")
        note = st.text_input("Observação (carga, instrumento...)", "")
        if st.form_submit_button("Registrar comparação", type="primary"):
            if ref <= 0:
                banner("warn", "Digite o valor medido pelo instrumento.")
            else:
                body = {"device_id": ctx.device, "quantity": quantity, "reference": float(ref), "note": note or None}
                if _guard(lambda: ctx.api.post("/api/validations", json=body)):
                    rerun(ctx.auto)

    try:
        rows = ctx.api.get("/api/validations", device_id=ctx.device)
    except requests.RequestException as exc:
        banner("danger", f"Erro ao consultar validações: {exc}")
        return
    df = validation_dataframe(rows)
    if df.empty:
        banner("info", "Nenhuma comparação registrada ainda.")
        return

    items = []
    for _, r in validation_summary(df).iterrows():
        name = QUANTITY_PT[r["quantity"]][0]
        items.append((f"{name}: erro médio absoluto", f"{r['mape_pct']:.2f}% ({int(r['n'])} medidas)", "target"))
        items.append((f"{name}: viés", f"{r['vies_pct']:+.2f}%", "chart"))
    cards(items)

    present = [q for q in QUANTITY_PT if q in set(df["quantity"])]
    q_sel = st.radio("Gráfico de", present, horizontal=True, key="val_q", format_func=lambda q: QUANTITY_PT[q][0])
    plot(charts.validation_scatter(df, q_sel, ctx.theme, ctx.font_scale), "val_scatter")
    table(validation_table(df).head(30))
    st.download_button("Baixar validação (CSV)", validation_csv(df), file_name=f"validacao_{ctx.device}.csv",
                       mime="text/csv", key="dl_val")

    with st.expander("Apagar um registro"):
        rid = st.selectbox("ID", list(df["id"]), key="val_del_id")
        if st.button("Apagar", key="val_del"):
            if _guard(lambda: ctx.api.delete(f"/api/validations/{int(rid)}")):
                rerun(ctx.auto)


def model_tab(ctx, d):
    model = d["model"]
    section("Detecção inteligente (Isolation Forest)", "network")
    st.caption("O score do modelo sinaliza leituras incomuns; não representa probabilidade de defeito.")
    if model["ready"]:
        cards([
            ("Estado", "Treinado", "check"),
            ("Leituras no treino", str(model["n_samples"]), "database"),
            ("Contaminação", str(model["contamination"]), "target"),
        ])
        st.caption(f"Último treino: {model['trained_at']} (UTC). Leituras marcadas como anomalia real ficam fora do treino.")
    else:
        banner("warn", "Ainda não treinado. Treina sozinho ao juntar leituras suficientes, ou clique abaixo.")
    if st.button("Treinar agora", key="treinar", type="primary"):
        try:
            info = ctx.api.post("/api/model/train")
            banner("ok", f"Modelo treinado com {info['n_samples']} leituras.")
        except requests.HTTPError as exc:
            banner("danger", exc.response.json().get("detail", str(exc)))
        except requests.RequestException as exc:
            banner("danger", str(exc))

    section("Avaliação pelos seus rótulos", "target")
    try:
        ev = ctx.api.get("/api/model/evaluation", device_id=ctx.device)
    except requests.RequestException as exc:
        banner("danger", f"Erro ao consultar a avaliação: {exc}")
        return
    if not ev["labeled"]:
        banner("info", "Marque anomalias como reais ou falsos alarmes na aba Anomalias para ver a precisão.")
        return

    def pct(x):
        return "—" if x is None else f"{x * 100:.0f}%"

    cards([
        ("Precisão", pct(ev["precision"]), "target"),
        ("Recall", pct(ev["recall"]), "target"),
        ("F1", pct(ev["f1"]), "target"),
        ("Leituras rotuladas", str(ev["labeled"]), "database"),
    ])
    st.caption("Precisão = das que o modelo marcou, quantas eram anomalia de verdade. "
               "Recall = das anomalias reais que você rotulou, quantas o modelo pegou "
               "(só é confiável se você rotular também as que ele deixou passar).")
    matrix = pd.DataFrame(
        {"Modelo marcou anomalia": [ev["tp"], ev["fp"]], "Modelo não marcou": [ev["fn"], ev["tn"]]},
        index=["Era anomalia real", "Era normal"],
    ).reset_index().rename(columns={"index": ""})
    table(matrix)


def system_tab(ctx, d):
    t_quality, t_validation, t_model = st.tabs(["Qualidade e saúde", "Validação", "Modelo"])
    with t_quality:
        quality_health(ctx, d)
    with t_validation:
        validation(ctx, d)
    with t_model:
        model_tab(ctx, d)
