import hmac
import os
import time
from pathlib import Path

import streamlit as st

MAX_FAILS = 5
LOCK_SECONDS = 60
ASSETS = Path(__file__).parent / "assets"


@st.cache_resource
def _state() -> dict:
    return {"fails": 0, "locked_until": 0.0}


def _password() -> str:
    pw = os.getenv("DASHBOARD_PASSWORD", "")
    if not pw:
        try:
            pw = str(st.secrets.get("dashboard_password", ""))
        except Exception:
            pw = ""
    return pw


def require_login() -> bool:
    pw = _password()
    if not pw:
        return False
    if st.session_state.get("auth_ok"):
        return True

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.image(str(ASSETS / "logo_large.png"), width=110)
        st.title("EnergyGuard")
        st.caption("Acesso restrito. Digite a senha para continuar.")
        state = _state()
        with st.form("login"):
            typed = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary")

        wait = state["locked_until"] - time.time()
        if wait > 0:
            st.error(f"Muitas tentativas. Aguarde {int(wait) + 1} s.")
        elif submitted:
            if hmac.compare_digest(typed.encode(), pw.encode()):
                state["fails"] = 0
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                state["fails"] += 1
                if state["fails"] >= MAX_FAILS:
                    state["fails"] = 0
                    state["locked_until"] = time.time() + LOCK_SECONDS
                st.error("Senha incorreta.")
    st.stop()


def logout_button() -> None:
    if st.button("Sair"):
        st.session_state["auth_ok"] = False
        st.rerun()
