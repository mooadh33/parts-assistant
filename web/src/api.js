const H = (t) => ({ "Content-Type": "application/json", ...(t && { Authorization: `Bearer ${t}` }) });
export async function login(username, password) {
  const r = await fetch("/api/login", { method: "POST", headers: H(), body: JSON.stringify({ username, password }) });
  if (!r.ok) throw new Error("Benutzer oder Passwort stimmt nicht.");
  return (await r.json()).access_token;
}
export async function chat(token, question) {
  let r;
  try { r = await fetch("/api/chat", { method: "POST", headers: H(token), body: JSON.stringify({ question }) }); }
  catch { throw new Error("Die API ist nicht erreichbar. Läuft uvicorn auf Port 8000?"); }
  if (r.status === 401 || r.status === 403) throw Object.assign(new Error("Sitzung abgelaufen. Bitte neu anmelden."), { auth: true });
  if (r.status === 429) throw new Error("Zu viele Anfragen. Bitte kurz warten.");
  if (!r.ok) throw new Error("Serverfehler. Bitte erneut versuchen.");
  return r.json();
}
export const feedback = (token, question, answer, rating) =>
  fetch("/api/feedback", { method: "POST", headers: H(token), body: JSON.stringify({ question, answer, rating }) });
