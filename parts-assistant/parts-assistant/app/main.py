"""Step 6: FastAPI backend. Run: uvicorn app.main:app --reload"""
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from . import config, db, llm, rag, security, vision, voice

app = FastAPI(title="Parts Assistant API", version="0.1")


class Login(BaseModel):
    username: str
    password: str


class ChatIn(BaseModel):
    question: str
    model: str | None = None


class FeedbackIn(BaseModel):
    question: str
    answer: str
    rating: int  # 1 = thumbs up, -1 = thumbs down
    comment: str | None = None


def log(user, route, res, blocked=0):
    con = db.usage_conn()
    con.execute("INSERT INTO usage(user,route,model,tokens_in,tokens_out,latency_ms,cost_usd,blocked) VALUES(?,?,?,?,?,?,?,?)",
                (user, route, res.model if res else "-", res.tokens_in if res else 0, res.tokens_out if res else 0,
                 res.latency_ms if res else 0, res.cost_usd if res else 0, blocked))
    con.commit(); con.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(b: Login):
    if config.USERS.get(b.username) != b.password:
        raise HTTPException(401, "Bad credentials")
    return {"access_token": security.make_token(b.username), "token_type": "bearer"}


@app.post("/chat")
def chat(b: ChatIn, user: str = Depends(security.current_user)):
    security.rate_limit(user)
    if security.looks_like_injection(b.question):
        log(user, "blocked", None, blocked=1)
        return {"answer": "Diese Anfrage wurde aus Sicherheitsgründen blockiert.", "route": "blocked", "sources": []}
    q = security.redact_pii(b.question)
    route, rr = rag_route = rag.route(q)
    log(user, "router", rr)
    if route == "sql":
        try:
            res, sql, cols, rows = rag.ask_sql(q, b.model)
        except ValueError as e:
            log(user, "sql", None, blocked=1)
            return {"answer": f"SQL abgelehnt: {e}", "route": "sql", "sources": []}
        log(user, "sql", res)
        return {"answer": f"{len(rows)} Treffer", "route": "sql", "sql": sql, "columns": cols, "rows": rows[:50],
                "cost_usd": res.cost_usd, "latency_ms": res.latency_ms, "model": res.model}
    res, sources = rag.ask_rag(q, b.model)
    log(user, "rag", res)
    return {"answer": res.text, "route": "rag", "sources": sources, "cost_usd": res.cost_usd,
            "latency_ms": res.latency_ms, "model": res.model, "tokens_in": res.tokens_in, "tokens_out": res.tokens_out}


@app.post("/feedback")
def feedback(b: FeedbackIn, user: str = Depends(security.current_user)):
    con = db.usage_conn()
    con.execute("INSERT INTO feedback(user,question,answer,rating,comment) VALUES(?,?,?,?,?)",
                (user, b.question, b.answer, b.rating, b.comment))
    con.commit(); con.close()
    return {"ok": True}


@app.get("/usage")
def usage(user: str = Depends(security.current_user)):
    con = db.usage_conn()
    q = lambda sql: con.execute(sql).fetchall()
    out = {
        "total": q("SELECT COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(AVG(latency_ms),0), COALESCE(SUM(blocked),0) FROM usage")[0],
        "per_day": q("SELECT date(ts), COUNT(*), SUM(cost_usd) FROM usage GROUP BY 1 ORDER BY 1"),
        "per_user": q("SELECT user, COUNT(*), SUM(cost_usd) FROM usage GROUP BY 1"),
        "per_model": q("SELECT model, COUNT(*), SUM(cost_usd), AVG(latency_ms) FROM usage GROUP BY 1"),
        "feedback": q("SELECT SUM(rating=1), SUM(rating=-1) FROM feedback")[0],
    }
    con.close()
    return out


@app.post("/upload-drawing")
async def upload_drawing(file: UploadFile = File(...), user: str = Depends(security.current_user)):
    security.rate_limit(user)
    res, data, matches = vision.analyze_drawing(await file.read(), file.content_type or "image/png")
    log(user, "vision", res)
    return {"extracted": data, "db_matches": matches, "cost_usd": res.cost_usd}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), user: str = Depends(security.current_user)):
    security.rate_limit(user)
    return {"text": voice.transcribe(await file.read(), file.filename or "audio.wav")}
