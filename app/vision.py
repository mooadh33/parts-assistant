"""Step 11: extract part type / dimensions / part numbers from a drawing or photo as JSON, then match against the parts DB."""
import base64
import json
import re
from . import llm, db

PROMPT = ("Analysiere diese technische Zeichnung oder dieses Teilefoto. Antworte NUR mit JSON: "
          '{"part_type": str, "dimensions": [{"name": str, "value": float, "unit": str}], "part_numbers": [str], "confidence": "low|medium|high"}. '
          "Rate nichts: unlesbare Werte weglassen.")


def analyze_drawing(image_bytes, media_type="image/png", model=None):
    b64 = base64.b64encode(image_bytes).decode()
    res = llm.complete(PROMPT, "Du bist ein Kfz-Technik-Experte.", model, image_b64=b64, media_type=media_type)
    m = re.search(r"\{.*\}", res.text, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}
    if res.model == "mock":
        data = {"part_type": "Bremsscheibe", "dimensions": [{"name": "Durchmesser", "value": 280.0, "unit": "mm"}],
                "part_numbers": [], "confidence": "low", "note": "MOCK output"}
    return res, data, match_parts(data)


def match_parts(data):
    con = db.readonly_conn()
    rows = []
    if data.get("part_numbers"):
        q = ",".join("?" * len(data["part_numbers"]))
        rows = con.execute(f"SELECT part_number,name,price_eur,stock FROM parts WHERE part_number IN ({q})", data["part_numbers"]).fetchall()
    if not rows and data.get("part_type"):
        rows = con.execute("SELECT part_number,name,price_eur,stock FROM parts WHERE category LIKE ? LIMIT 5",
                           (f"%{data['part_type']}%",)).fetchall()
    con.close()
    return rows
