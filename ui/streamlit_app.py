"""Step 7: Streamlit UI. Icons are \\U escapes so the file survives any editor/terminal encoding.
Styling lives in ui/style.css and .streamlit/config.toml."""
import html
import os
import re
import time
from pathlib import Path

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
UP, DOWN, MIC, DOC, INFO = "\U0001F44D", "\U0001F44E", "\U0001F399\uFE0F", "\U0001F4C4", "\u2139\uFE0F"
st.set_page_config(page_title="Parts Assistant", page_icon="\U0001F527", layout="wide", initial_sidebar_state="collapsed")
DARK = (":root{color-scheme:dark;--bg-top:#121B23;--bg-bot:#0C1319;--bg-mid:#101920;--panel:#18222B;--panel2:#1F2B36;--hover:#243340;--ink:#E6ECF0;"
        "--muted:#97A7B3;--line:#2D3B47;--red:#EF5350;--red-btn:#D32F2F;--red-d:#B71C1C;--teal:#4DB6C4;--bubble:#2B3B49;--bubble-ink:#EAF0F3;"
        "--disc1:#AEBBC5;--disc2:#5E6E7B;--hub:#51616D;--shadow:rgba(0,0,0,.65)}")


def theme_toggle(key):
    def flip():
        st.session_state.ui_theme = "light" if st.session_state.ui_theme == "dark" else "dark"
        st.query_params["theme"] = st.session_state.ui_theme  # survives page reload
    dark = st.session_state.ui_theme == "dark"
    st.button("\u2600\uFE0F" if dark else "\U0001F319", key=key, on_click=flip, help="Helles Design" if dark else "Dunkles Design")


if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = st.query_params.get("theme", "light") if st.query_params.get("theme") in ("light", "dark") else "light"
css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8") + (DARK if st.session_state.ui_theme == "dark" else "")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def table(cols, rows, num=()):
    """Themed HTML table (st.dataframe is canvas-based and cannot follow the light/dark toggle)."""
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f'<td class="{"num" if j in num else ""}">{html.escape(str(v))}</td>' for j, v in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def bars(items):
    mx = max([v for _, v, _ in items] + [1])
    return '<div class="bars">' + "".join(
        f'<div class="bar"><span>{html.escape(str(l))}</span><div class="track"><i style="width:{max(4, 100 * v / mx):.0f}%"></i></div><b>{html.escape(str(c))}</b></div>'
        for l, v, c in items) + "</div>"


EXAMPLES = ["Woran erkenne ich verschlissene Stoßdämpfer?", "Welche Querlenker passen zum Golf VII?",
            "Preis der günstigsten Bremsscheibe?", "Was ist der Unterschied zwischen Querlenker und Traggelenk?"]
ROUTES = {"rag": ("Aus Dokumenten", ""), "sql": ("Aus Datenbank", "sql"), "blocked": ("Blockiert", "blocked")}


def disc(size=240, cls="", caliper=True):
    """Ventilated brake disc with a red caliper. Only the disc rotates."""
    holes = "".join(f'<circle cx="110" cy="86" r="4" fill="var(--bg-mid)" transform="rotate({72 * i} 110 110)"/>' for i in range(5))
    cal = ('<path d="M146.3 10.4A106 106 0 0 1 212.4 82.6L177.6 91.9A70 70 0 0 0 133.9 44.2Z" fill="#C62828" stroke="#A61E1E" stroke-width="2"/>'
           if caliper else "")
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 220 220" role="img" aria-label="Bremsscheibe">'
            '<defs><linearGradient id="st" x1="0" y1="0" x2="1" y2="1"><stop offset="0" style="stop-color:var(--disc1)"/><stop offset="1" style="stop-color:var(--disc2)"/></linearGradient></defs>'
            f'<g class="spin {cls}"><circle cx="110" cy="110" r="96" fill="url(#st)"/>'
            '<circle cx="110" cy="110" r="66" fill="none" stroke="var(--bg-mid)" stroke-width="20" stroke-dasharray="16 14"/>'
            f'<circle cx="110" cy="110" r="34" fill="var(--hub)"/><circle cx="110" cy="110" r="12" fill="var(--bg-mid)"/>{holes}</g>{cal}</svg>')


def thinking():
    return f'<div class="think">{disc(34, "fast", False)}<span>Durchsuche Dokumente und Datenbank</span></div><div class="sk" style="width:92%"></div><div class="sk" style="width:64%"></div>'


def words(text):
    delay = 0.018 if len(text.split()) < 60 else 0.008
    for w in re.split(r"(\s+)", text):
        yield w
        if w.strip():
            time.sleep(delay)


def online():
    try:
        return httpx.get(f"{API}/health", timeout=1.5).status_code == 200
    except httpx.HTTPError:
        return False


# ------------------------------------------------------------------ login
if "token" not in st.session_state:
    st.markdown(f'<div class="hero"><div><h1>Teile finden. Fragen klären.</h1>'
                '<p>Der Assistent beantwortet Fragen zu Ersatzteilen, Datenblättern und Bestand und nennt zu jeder Antwort die Quelle.</p></div>'
                f'<div class="disc">{disc(260)}</div></div>', unsafe_allow_html=True)
    with st.container(key="loginbar"):
        _, tcol = st.columns([12, 1.4])
        with tcol:
            theme_toggle("themelogin")
    mid = st.container()
    with mid:
        c1, c2 = st.columns(2)
        u, p = c1.text_input("Benutzer"), c2.text_input("Passwort", type="password")
        if st.button("Anmelden", type="primary"):
            try:
                r = httpx.post(f"{API}/login", json={"username": u, "password": p}, timeout=10)
            except httpx.HTTPError:
                st.error("Die API ist nicht erreichbar. Starte sie in einem zweiten Fenster mit: python -m uvicorn app.main:app"); st.stop()
            if r.status_code == 200:
                st.session_state.token = r.json()["access_token"]; st.rerun()
            else:
                st.error("Benutzer oder Passwort stimmt nicht.")
        st.caption("Demo-Zugang: admin / admin123")
    st.stop()

H = {"Authorization": f"Bearer {st.session_state.token}"}
st.session_state.setdefault("msgs", [])

# ------------------------------------------------------------------ top bar
ok = online()
with st.container(key="bar"):
    c_brand, c_theme, c_out = st.columns([5, 1.3, 2.6])
    c_brand.markdown(f'<div class="topbar">{disc(38, "", False)}<b>Parts Assistant</b>'
                     f'<span class="status"><span class="dot {"" if ok else "off"}"></span><span class="txt">{"API verbunden" if ok else "API nicht erreichbar"}</span></span></div>',
                     unsafe_allow_html=True)
    with c_theme:
        theme_toggle("theme")
    if c_out.button("Abmelden"):
        for k in ("token", "msgs", "pending", "last_audio"):
            st.session_state.pop(k, None)
        st.rerun()

tab_chat, tab_draw, tab_dash = st.tabs(["Chat", "Zeichnung", "Dashboard"])


def ask(q):
    try:
        r = httpx.post(f"{API}/chat", json={"question": q}, headers=H, timeout=120)
    except httpx.HTTPError:
        return {"answer": "Die API ist nicht erreichbar.", "route": "error"}
    if r.status_code == 429:
        return {"answer": "Zu viele Anfragen. Warte kurz und frage erneut.", "route": "limit"}
    if r.status_code in (401, 403):
        st.session_state.pop("token", None); st.rerun()
    return r.json()


def render_extras(m, i):
    if m.get("rows"):
        st.markdown(table(m["columns"], m["rows"], num=[j for j, c in enumerate(m["columns"]) if "price" in c or c in ("stock", "artikel", "stueck_gesamt")]), unsafe_allow_html=True)
        with st.expander("SQL-Abfrage"):
            st.markdown(f'<pre class="sql">{html.escape(m["sql"])}</pre>', unsafe_allow_html=True)
    if m.get("sources"):
        with st.expander(f"{DOC} Quellen ({len(m['sources'])})"):
            for s in m["sources"]:
                st.markdown(f"**{s['source']}**, S.{s['page']}  \n_{s['snippet']}_")
    if m.get("model") == "mock":
        st.markdown(f'<div class="meta">{INFO} Demo-Modus: Auszug aus den Dokumenten. Mit API-Key antwortet ein echtes Modell.</div>', unsafe_allow_html=True)
    elif m.get("cost_usd") is not None:
        st.markdown(f'<div class="meta">{m.get("model")} \u00b7 {m.get("latency_ms")} ms \u00b7 ${m["cost_usd"]:.5f}</div>', unsafe_allow_html=True)
    if m.get("route") in ("rag", "sql"):
        with st.container(key=f"fbrow{i}"):
            c1, c2, _ = st.columns([1, 1, 8])
            for col, icon, val in ((c1, UP, 1), (c2, DOWN, -1)):
                if col.button(icon, key=f"fb{i}_{val}", help="Antwort bewerten"):
                    httpx.post(f"{API}/feedback", headers=H, json={"question": st.session_state.msgs[i - 1]["content"],
                               "answer": m["content"], "rating": val}); st.toast("Danke für dein Feedback.")


with tab_chat:
    if not st.session_state.msgs:
        st.markdown("### Was möchtest du wissen?")
        cols = st.columns(2)
        for n, ex in enumerate(EXAMPLES):
            if cols[n % 2].button(ex, key=f"ex{n}", width="stretch"):
                st.session_state.pending = ex; st.rerun()
    for i, m in enumerate(st.session_state.msgs):
        with st.chat_message(m["role"]):
            if m["role"] == "assistant" and m.get("route") in ROUTES:
                label, cls = ROUTES[m["route"]]
                st.markdown(f'<span class="chip {cls}"><i></i>{label}</span>', unsafe_allow_html=True)
            if m.get("fresh"):
                st.write_stream(words(m["content"])); m["fresh"] = False  # stream only the newest answer
            else:
                st.markdown(m["content"])
            if m["role"] == "assistant":
                render_extras(m, i)
    audio = st.audio_input(f"{MIC} Spracheingabe")
    if audio and st.session_state.get("last_audio") != audio.size:
        st.session_state.last_audio = audio.size
        st.session_state.pending = httpx.post(f"{API}/transcribe", headers=H, files={"file": ("a.wav", audio.getvalue(), "audio/wav")}).json()["text"]
    q = st.chat_input("Frage zu Ersatzteilen …") or st.session_state.pop("pending", None)
    if q:
        st.session_state.msgs.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            holder = st.empty(); holder.markdown(thinking(), unsafe_allow_html=True)
            a = ask(q)
        st.session_state.msgs.append({"role": "assistant", "content": a.get("answer", "Fehler"), "fresh": True,
                                      **{k: a.get(k) for k in ("route", "sources", "rows", "columns", "sql", "model", "cost_usd", "latency_ms")}})
        st.rerun()
    if st.session_state.msgs and st.button("Chat leeren"):
        st.session_state.msgs = []; st.rerun()

with tab_draw:
    st.markdown("### Zeichnung oder Teilefoto auswerten")
    f = st.file_uploader("Bild hochladen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if f:
        st.image(f.getvalue(), width=320)
    if f and st.button("Analysieren", type="primary"):
        with st.spinner("Analysiere Bild …"):
            r = httpx.post(f"{API}/upload-drawing", headers=H, files={"file": (f.name, f.getvalue(), f.type)}, timeout=120).json()
        if r["extracted"].get("note"):
            st.info("Demo-Modus: feste Beispielausgabe. Für echte Bildanalyse ANTHROPIC_API_KEY setzen.")
        ex = r["extracted"]
        st.markdown("#### Erkannte Daten")
        st.markdown(table(["Teiletyp", "Sicherheit", "Teilenummern"], [[ex.get("part_type", "-"), ex.get("confidence", "-"), ", ".join(ex.get("part_numbers") or []) or "-"]]), unsafe_allow_html=True)
        if ex.get("dimensions"):
            st.markdown(table(["Maß", "Wert", "Einheit"], [[d.get("name"), d.get("value"), d.get("unit")] for d in ex["dimensions"]], num=[1]), unsafe_allow_html=True)
        st.markdown("#### Passende Teile in der Datenbank")
        if r["db_matches"]:
            st.markdown(table(["Teilenummer", "Name", "Preis EUR", "Bestand"], r["db_matches"], num=[2, 3]), unsafe_allow_html=True)
        else:
            st.write("Keine Treffer.")

with tab_dash:
    u = httpx.get(f"{API}/usage", headers=H).json()
    n, cost, lat, blocked = u["total"]
    with st.container(key="metrics"):
        a, b, c, d = st.columns(4)
        a.metric("Anfragen", n); b.metric("Kosten (USD)", f"{cost:.4f}"); c.metric("Ø Latenz (ms)", f"{lat:.0f}"); d.metric("Blockiert", blocked)
    if u["per_day"]:
        st.markdown("#### Anfragen pro Tag")
        st.markdown(bars([(day, cnt, f"{cnt} \u00b7 ${(cst or 0):.4f}") for day, cnt, cst in u["per_day"]]), unsafe_allow_html=True)
    l, r_ = st.columns(2)
    l.markdown("#### Pro Nutzer"); l.markdown(table(["Nutzer", "Anfragen", "Kosten"], [(a_, b_, f"{(c_ or 0):.4f}") for a_, b_, c_ in u["per_user"]], num=[1, 2]), unsafe_allow_html=True)
    r_.markdown("#### Pro Modell"); r_.markdown(table(["Modell", "Anfragen", "Kosten", "Ø Latenz"], [(a_, b_, f"{(c_ or 0):.4f}", f"{(d_ or 0):.0f}") for a_, b_, c_, d_ in u["per_model"]], num=[1, 2, 3]), unsafe_allow_html=True)
    st.caption(f"Feedback {UP} {u['feedback'][0] or 0} / {DOWN} {u['feedback'][1] or 0}")
