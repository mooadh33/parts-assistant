import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

export const Disc = ({ size = 32, fast }) => (
  <svg width={size} height={size} viewBox="0 0 220 220" aria-hidden="true">
    <g className={`spin ${fast ? "fast" : ""}`}><circle cx="110" cy="110" r="96" fill="var(--disc)"/>
      <circle cx="110" cy="110" r="66" fill="none" stroke="var(--bg)" strokeWidth="20" strokeDasharray="16 14"/>
      <circle cx="110" cy="110" r="30" fill="var(--hub)"/><circle cx="110" cy="110" r="11" fill="var(--bg)"/></g>
    <path d="M146 10A106 106 0 0 1 212 83L178 92A70 70 0 0 0 134 44Z" fill="var(--red)"/>
  </svg>
);

export function Thinking() {
  return (
    <motion.div className="msg ai" initial={{ opacity: 0 }} animate={{ opacity: 1 }} role="status" aria-live="polite">
      <div className="think"><Disc size={28} fast /><span>Durchsuche Dokumente und Datenbank</span></div>
      <div className="sk" style={{ width: "90%" }} /><div className="sk" style={{ width: "60%" }} />
    </motion.div>
  );
}

function Rich({ text }) {   // minimal renderer for what the API returns: paragraphs, "- " lists, ``` code
  const out = []; let list = [], code = null;
  const flush = () => { if (list.length) { out.push(<ul key={out.length}>{list.map((l, i) => <li key={i}>{l}</li>)}</ul>); list = []; } };
  text.split("\n").forEach((line) => {
    if (line.startsWith("```")) { if (code) { out.push(<pre key={out.length}><code>{code.join("\n")}</code></pre>); code = null; } else { flush(); code = []; } }
    else if (code) code.push(line);
    else if (/^[-*•] /.test(line)) list.push(line.slice(2));
    else { flush(); if (line.trim()) out.push(<p key={out.length}>{line}</p>); }
  });
  flush(); return <>{out}</>;
}

const Table = ({ cols, rows }) => (
  <div className="tbl"><table><thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className={typeof v === "number" ? "num" : ""}>{String(v)}</td>)}</tr>)}</tbody></table></div>
);

function useReveal(text, fresh) {
  const [n, setN] = useState(fresh ? 0 : Infinity);
  useEffect(() => {
    if (!fresh) return;
    const parts = text.split(/(\s+)/); let i = 0;
    const t = setInterval(() => { i += 2; setN(i); if (i >= parts.length) clearInterval(t); }, 22);
    return () => clearInterval(t);
  }, [text, fresh]);
  return n === Infinity ? text : text.split(/(\s+)/).slice(0, n).join("");
}

const Icon = ({ d }) => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={d}/></svg>;
const ICONS = { copy: "M9 9h11v11H9zM5 15V5h10", redo: "M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5", up: "M7 11v9H3v-9zM7 11l4-8a2 2 0 0 1 2 2v4h6a2 2 0 0 1 2 2l-1 6a2 2 0 0 1-2 2H7", down: "M17 13V4h4v9zM17 13l-4 8a2 2 0 0 1-2-2v-4H5a2 2 0 0 1-2-2l1-6a2 2 0 0 1 2-2h11" };

export function Message({ m, onRegenerate, onFeedback, canRegen }) {
  const text = useReveal(m.content || "", m.fresh);
  const [copied, setCopied] = useState(false), [rated, setRated] = useState(0);
  const copy = async () => { await navigator.clipboard?.writeText(m.content); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  const motionProps = { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.28, ease: [0.2, 0.7, 0.2, 1] } };
  if (m.role === "user") return <motion.div className="msg user" {...motionProps}><p>{m.content}</p></motion.div>;
  if (m.error) return <motion.div className="msg ai err" role="alert" {...motionProps}><p>{m.error}</p><button className="ghost" onClick={onRegenerate}>Erneut versuchen</button></motion.div>;
  const label = { rag: "Aus Dokumenten", sql: "Aus Datenbank", blocked: "Blockiert" }[m.route];
  return (
    <motion.article className="msg ai" {...motionProps}>
      {label && <span className={`chip ${m.route}`}><i />{label}</span>}
      <Rich text={text} />
      {m.rows?.length > 0 && <Table cols={m.columns} rows={m.rows} />}
      {m.sql && <details><summary>SQL-Abfrage</summary><pre><code>{m.sql}</code></pre></details>}
      {m.sources?.length > 0 && <details><summary>Quellen ({m.sources.length})</summary>{m.sources.map((s, i) => <p key={i} className="src"><b>{s.source}</b>, S.{s.page}<br /><em>{s.snippet}</em></p>)}</details>}
      <div className="meta">{m.model === "mock" ? "Demo-Modus: Auszug aus den Dokumenten" : `${m.model} · ${m.latency_ms} ms · $${(m.cost_usd ?? 0).toFixed(5)}`}</div>
      <div className="actions" role="toolbar" aria-label="Nachrichtenaktionen">
        <button onClick={copy} aria-label="Kopieren"><Icon d={ICONS.copy} /><span>{copied ? "Kopiert" : "Kopieren"}</span></button>
        {canRegen && <button onClick={onRegenerate} aria-label="Neu generieren"><Icon d={ICONS.redo} /><span>Neu</span></button>}
        {["up", "down"].map((k, i) => <button key={k} aria-pressed={rated === (i ? -1 : 1)} aria-label={i ? "Nicht hilfreich" : "Hilfreich"} className={rated === (i ? -1 : 1) ? "on" : ""}
          onClick={() => { setRated(i ? -1 : 1); onFeedback(i ? -1 : 1); }}><Icon d={ICONS[k]} /></button>)}
      </div>
    </motion.article>
  );
}

export function Composer({ onSend, busy, inputRef }) {
  const [v, setV] = useState("");
  const fit = (el) => { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 160) + "px"; };
  const send = () => { if (v.trim() && !busy) { onSend(v.trim()); setV(""); requestAnimationFrame(() => inputRef.current && fit(inputRef.current)); } };
  return (
    <div className="composer-wrap">
      <div className="composer">
        <svg className="mag" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
        <textarea ref={inputRef} rows={1} value={v} aria-label="Frage eingeben" placeholder="Suchen oder fragen …"
          onChange={(e) => { setV(e.target.value); fit(e.target); }} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
        <motion.button className="send" onClick={send} disabled={!v.trim() || busy} aria-label="Senden" whileTap={{ scale: 0.9 }} whileHover={{ scale: 1.06 }}>
          <Icon d="M12 19V5M5 12l7-7 7 7" /></motion.button>
      </div>
      <p className="hint">Enter sendet · Shift+Enter neue Zeile · Strg/Cmd+K Suche</p>
    </div>
  );
}

export function Sidebar({ convs, activeId, onSelect, onNew, onDelete, query, setQuery, open, onClose, searchRef }) {
  const list = convs.filter((c) => c.title.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <AnimatePresence>{open && <motion.div className="scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />}</AnimatePresence>
      <aside className={`side ${open ? "open" : ""}`} aria-label="Unterhaltungen">
        <div className="brand"><Disc size={34} /><b>Parts Assistant</b></div>
        <button className="new" onClick={onNew}>+ Neue Unterhaltung</button>
        <input ref={searchRef} className="search" type="search" placeholder="Verlauf durchsuchen" aria-label="Verlauf durchsuchen" value={query} onChange={(e) => setQuery(e.target.value)} />
        <nav className="convs">
          <AnimatePresence initial={false}>
            {list.map((c) => (
              <motion.div key={c.id} layout initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, height: 0 }} className={`conv ${c.id === activeId ? "active" : ""}`}>
                <button onClick={() => onSelect(c.id)} aria-current={c.id === activeId}>{c.title}</button>
                <button className="del" onClick={() => onDelete(c.id)} aria-label={`${c.title} löschen`}>×</button>
              </motion.div>))}
          </AnimatePresence>
          {!list.length && <p className="empty">{query ? "Keine Treffer" : "Noch keine Unterhaltungen"}</p>}
        </nav>
      </aside>
    </>
  );
}
