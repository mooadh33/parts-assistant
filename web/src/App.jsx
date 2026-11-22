import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { chat, feedback, login } from "./api.js";
import { Composer, Disc, Message, Sidebar, Thinking } from "./components.jsx";

const uid = () => Math.random().toString(36).slice(2, 10);
const load = () => { try { return JSON.parse(localStorage.getItem("pa.convs")) || []; } catch { return []; } };
const EXAMPLES = ["Woran erkenne ich verschlissene Stoßdämpfer?", "Welche Querlenker passen zum Golf VII?", "Preis der günstigsten Bremsscheibe?", "Was ist der Unterschied zwischen Querlenker und Traggelenk?"];

function Login({ onToken, theme, toggle }) {
  const [u, setU] = useState(""), [p, setP] = useState(""), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const submit = async (e) => { e.preventDefault(); setBusy(true); setErr(""); try { onToken(await login(u, p)); } catch (x) { setErr(x.message); } setBusy(false); };
  return (
    <main className="login">
      <button className="theme" onClick={toggle} aria-label="Design wechseln">{theme === "dark" ? "☀️" : "🌙"}</button>
      <motion.div className="hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <div><h1>Teile finden. Fragen klären.</h1><p>Antworten zu Ersatzteilen, Datenblättern und Bestand, jeweils mit Quelle.</p></div>
        <Disc size={220} />
      </motion.div>
      <form onSubmit={submit} className="form">
        <label>Benutzer<input value={u} onChange={(e) => setU(e.target.value)} autoComplete="username" required /></label>
        <label>Passwort<input type="password" value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" required /></label>
        <button className="primary" disabled={busy}>{busy ? "Anmelden …" : "Anmelden"}</button>
        {err && <p className="error" role="alert">{err}</p>}
      </form>
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("pa.token"));
  const [theme, setTheme] = useState(document.documentElement.dataset.theme);
  const [convs, setConvs] = useState(() => load().map((c) => ({ ...c, msgs: c.msgs.map((m) => ({ ...m, fresh: false })) })));
  const [activeId, setActive] = useState(null), [query, setQuery] = useState(""), [open, setOpen] = useState(false), [busy, setBusy] = useState(false);
  const inputRef = useRef(), searchRef = useRef(), endRef = useRef();
  const active = convs.find((c) => c.id === activeId);

  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("pa.theme", theme); }, [theme]);
  useEffect(() => { localStorage.setItem("pa.convs", JSON.stringify(convs.map((c) => ({ ...c, msgs: c.msgs.map(({ fresh, ...m }) => m) })))); }, [convs]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [active?.msgs.length, busy]);
  useEffect(() => {
    const k = (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setOpen(true); searchRef.current?.focus(); } if (e.key === "Escape") setOpen(false); };
    addEventListener("keydown", k); return () => removeEventListener("keydown", k);
  }, []);

  const patch = useCallback((id, fn) => setConvs((cs) => cs.map((c) => (c.id === id ? fn(c) : c))), []);
  const logout = () => { sessionStorage.removeItem("pa.token"); setToken(null); };

  const ask = useCallback(async (q, id) => {
    setBusy(true);
    try {
      const a = await chat(token, q);
      patch(id, (c) => ({ ...c, msgs: [...c.msgs, { id: uid(), role: "assistant", content: a.answer || "", route: a.route, sources: a.sources, rows: a.rows, columns: a.columns, sql: a.sql, model: a.model, cost_usd: a.cost_usd, latency_ms: a.latency_ms, fresh: true }] }));
    } catch (e) {
      if (e.auth) return logout();
      patch(id, (c) => ({ ...c, msgs: [...c.msgs, { id: uid(), role: "assistant", error: e.message }] }));
    } finally { setBusy(false); }
  }, [token, patch]);

  const send = (q) => {
    let id = activeId;
    if (!id) { id = uid(); setConvs((cs) => [{ id, title: q.slice(0, 48), ts: Date.now(), msgs: [] }, ...cs]); setActive(id); }
    patch(id, (c) => ({ ...c, msgs: [...c.msgs, { id: uid(), role: "user", content: q }] }));
    ask(q, id);
  };
  const regenerate = (i) => {
    const q = [...active.msgs.slice(0, i)].reverse().find((m) => m.role === "user")?.content; if (!q) return;
    patch(active.id, (c) => ({ ...c, msgs: c.msgs.slice(0, i) })); ask(q, active.id);
  };

  if (!token) return <Login theme={theme} toggle={() => setTheme(theme === "dark" ? "light" : "dark")} onToken={(t) => { sessionStorage.setItem("pa.token", t); setToken(t); }} />;
  const msgs = active?.msgs || [];
  return (
    <div className="app">
      <Sidebar convs={convs} activeId={activeId} query={query} setQuery={setQuery} open={open} onClose={() => setOpen(false)} searchRef={searchRef}
        onSelect={(id) => { setActive(id); setOpen(false); }} onNew={() => { setActive(null); setOpen(false); inputRef.current?.focus(); }}
        onDelete={(id) => { setConvs((cs) => cs.filter((c) => c.id !== id)); if (id === activeId) setActive(null); }} />
      <main className="main">
        <header className="top">
          <button className="burger" onClick={() => setOpen(true)} aria-label="Menü öffnen">☰</button>
          <span className="title">{active?.title || "Neue Unterhaltung"}</span>
          <button className="theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Design wechseln">{theme === "dark" ? "☀️" : "🌙"}</button>
          <button className="ghost" onClick={logout}>Abmelden</button>
        </header>
        <section className="thread" aria-live="polite">
          {!msgs.length && !busy ? (
            <motion.div className="welcome" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
              <Disc size={96} /><h2>Was möchtest du wissen?</h2>
              <div className="examples">{EXAMPLES.map((e) => <motion.button key={e} whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} onClick={() => send(e)}>{e}</motion.button>)}</div>
            </motion.div>
          ) : (
            <div className="col">
              {msgs.map((m, i) => <Message key={m.id} m={m} canRegen={i === msgs.length - 1 && !busy} onRegenerate={() => regenerate(i)}
                onFeedback={(r) => feedback(token, msgs[i - 1]?.content || "", m.content, r)} />)}
              <AnimatePresence>{busy && <Thinking key="t" />}</AnimatePresence>
              <div ref={endRef} />
            </div>
          )}
        </section>
        <Composer onSend={send} busy={busy} inputRef={inputRef} />
      </main>
    </div>
  );
}
