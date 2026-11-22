"""Step 7: Streamlit UI (chat + sources + feedback, drawing upload, voice input, usage dashboard)."""
import os
import httpx
import pandas as pd
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Parts Assistant", page_icon="🔧", layout="wide")

if "token" not in st.session_state:
    st.title("🔧 Parts Assistant")
    u, p = st.text_input("Benutzer"), st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        r = httpx.post(f"{API}/login", json={"username": u, "password": p})
        if r.status_code == 200:
            st.session_state.token = r.json()["access_token"]; st.rerun()
        else:
            st.error("Login fehlgeschlagen")
    st.stop()

H = {"Authorization": f"Bearer {st.session_state.token}"}
tab_chat, tab_draw, tab_dash = st.tabs(["💬 Chat", "📐 Zeichnung", "📊 Dashboard"])
st.session_state.setdefault("msgs", [])


def ask(q):
    r = httpx.post(f"{API}/chat", json={"question": q}, headers=H, timeout=120)
    if r.status_code == 429:
        return {"answer": "Zu viele Anfragen, bitte kurz warten.", "route": "limit"}
    return r.json()


with tab_chat:
    for i, m in enumerate(st.session_state.msgs):
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("rows"):
                st.dataframe(pd.DataFrame(m["rows"], columns=m["columns"])); st.code(m["sql"], language="sql")
            for s in m.get("sources", []):
                st.caption(f"📄 {s['source']} S.{s['page']}")
            if m["role"] == "assistant" and m.get("route") in ("rag", "sql"):
                c1, c2, _ = st.columns([1, 1, 10])
                for col, icon, val in ((c1, "👍", 1), (c2, "👎", -1)):
                    if col.button(icon, key=f"fb{i}{val}"):
                        httpx.post(f"{API}/feedback", headers=H, json={"question": st.session_state.msgs[i - 1]["content"],
                                   "answer": m["content"], "rating": val}); st.toast("Danke für das Feedback!")
    audio = st.audio_input("🎙️ Spracheingabe")
    if audio and st.session_state.get("last_audio") != audio.size:
        st.session_state.last_audio = audio.size
        t = httpx.post(f"{API}/transcribe", headers=H, files={"file": ("a.wav", audio.getvalue(), "audio/wav")}).json()["text"]
        st.session_state.voice_q = t
    q = st.chat_input("Frage zu Ersatzteilen …") or st.session_state.pop("voice_q", None)
    if q:
        st.session_state.msgs.append({"role": "user", "content": q})
        a = ask(q)
        st.session_state.msgs.append({"role": "assistant", "content": a["answer"], **{k: a.get(k) for k in ("route", "sources", "rows", "columns", "sql")}})
        st.rerun()

with tab_draw:
    f = st.file_uploader("Zeichnung oder Teilefoto", type=["png", "jpg", "jpeg"])
    if f and st.button("Analysieren"):
        r = httpx.post(f"{API}/upload-drawing", headers=H, files={"file": (f.name, f.getvalue(), f.type)}, timeout=120).json()
        st.json(r["extracted"]); st.subheader("Passende Teile in der Datenbank"); st.write(r["db_matches"])

with tab_dash:
    u = httpx.get(f"{API}/usage", headers=H).json()
    n, cost, lat, blocked = u["total"]
    a, b, c, d = st.columns(4)
    a.metric("Anfragen", n); b.metric("Kosten (USD)", f"{cost:.4f}"); c.metric("Ø Latenz (ms)", f"{lat:.0f}"); d.metric("Blockiert", blocked)
    st.subheader("Kosten pro Tag"); st.bar_chart(pd.DataFrame(u["per_day"], columns=["Tag", "Anfragen", "Kosten"]).set_index("Tag")["Kosten"])
    st.subheader("Pro Nutzer"); st.dataframe(pd.DataFrame(u["per_user"], columns=["Nutzer", "Anfragen", "Kosten"]))
    st.subheader("Pro Modell"); st.dataframe(pd.DataFrame(u["per_model"], columns=["Modell", "Anfragen", "Kosten", "Ø Latenz"]))
    st.caption(f"Feedback 👍 {u['feedback'][0] or 0} / 👎 {u['feedback'][1] or 0}")
