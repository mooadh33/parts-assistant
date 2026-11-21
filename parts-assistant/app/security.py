"""Step 9: auth (JWT), rate limit, PII filter, prompt-injection heuristics, SQL validator."""
import re
import time
from collections import defaultdict, deque
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from . import config

bearer = HTTPBearer()


def make_token(user):
    return jwt.encode({"sub": user, "exp": int(time.time()) + 8 * 3600}, config.JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        return jwt.decode(creds.credentials, config.JWT_SECRET, algorithms=["HS256"])["sub"]
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


_hits = defaultdict(deque)


def rate_limit(user, limit=None):
    limit = limit or config.RATE_LIMIT_PER_MIN
    q, now = _hits[user], time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Rate limit exceeded")
    q.append(now)


PII = [(re.compile(r"\bDE\d{2}(?:\s?\d{4}){4}\s?\d{2}\b"), "[IBAN]"),  # IBAN first, otherwise the phone rule eats part of it
       (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
       (re.compile(r"\b(?:\+49|0049|0)\s?\d{2,4}[\s/-]?\d{4,10}\b"), "[PHONE]"),
       (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[CARD]")]


def redact_pii(text):
    for rx, tag in PII:
        text = rx.sub(tag, text)
    return text


INJECTION = [r"ignor\w* (all |any )?(previous|prior|above) (instructions|prompts?)", r"vergiss .{0,30}(anweisung|instruktion)",
             r"ignorier\w* .{0,30}(anweisung|instruktion|regeln)", r"system ?prompt", r"you are now", r"du bist jetzt",
             r"reveal .{0,20}(prompt|instructions|key)", r"zeige? .{0,20}(prompt|api.?key|passwort)",
             r"developer mode", r"jailbreak", r"DROP\s+TABLE", r"</?(system|assistant)>"]
_inj = re.compile("|".join(INJECTION), re.I)


def looks_like_injection(text):
    return bool(_inj.search(text))


def sanitize_context(chunk):
    """Neutralise instructions hidden in retrieved documents (indirect injection)."""
    return "[REDACTED-INSTRUCTION]" if looks_like_injection(chunk) else chunk


ALLOWED_TABLES = {"parts", "fitment"}


def validate_sql(sql):
    s = sql.strip().rstrip(";")
    if ";" in s:
        raise ValueError("multiple statements not allowed")
    if not re.match(r"(?is)^select\b", s):
        raise ValueError("only SELECT allowed")
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|attach|pragma|create|replace|vacuum)\b", s):
        raise ValueError("forbidden keyword")
    tables = set(re.findall(r"(?i)\b(?:from|join)\s+([a-z_]+)", s))
    if not tables or not tables <= ALLOWED_TABLES:
        raise ValueError(f"table not allowed: {tables - ALLOWED_TABLES}")
    if not re.search(r"(?i)\blimit\b", s):
        s += " LIMIT 50"
    return s
