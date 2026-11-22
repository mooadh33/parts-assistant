"""Mock ERP / product DB (read-only for the SQL agent) and usage log DB."""
import random
import sqlite3
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS parts(
  part_number TEXT PRIMARY KEY, name TEXT, category TEXT, brand TEXT,
  position TEXT, price_eur REAL, stock INTEGER);
CREATE TABLE IF NOT EXISTS fitment(
  part_number TEXT, make TEXT, model TEXT, year_from INTEGER, year_to INTEGER);
"""
VEHICLES = [("VW", "Golf VII", 2012, 2020), ("VW", "Passat B8", 2014, 2023), ("Audi", "A3 8V", 2012, 2020),
            ("BMW", "3er F30", 2011, 2019), ("Mercedes", "C-Klasse W205", 2014, 2021),
            ("Opel", "Astra K", 2015, 2022), ("Ford", "Focus III", 2011, 2018), ("Skoda", "Octavia III", 2012, 2020)]
CATS = {"Stoßdämpfer": 70, "Querlenker": 55, "Bremsscheibe": 45, "Bremsbelag": 30, "Koppelstange": 20, "Radlager": 60}
BRANDS = ["Bilstein", "Sachs", "Monroe", "Febi", "Meyle"]  # illustrative only


def seed(n_per_vehicle=24, seed_value=42):
    random.seed(seed_value)
    config.DATA.mkdir(exist_ok=True)
    if config.PARTS_DB.exists():
        config.PARTS_DB.unlink()
    con = sqlite3.connect(config.PARTS_DB)
    con.executescript(SCHEMA)
    i = 1000
    for make, model, y0, y1 in VEHICLES:
        for cat, base in CATS.items():
            for _ in range(max(1, n_per_vehicle // len(CATS) + 1)):
                i += 1
                pn = f"PA-{i}"
                pos = random.choice(["Vorderachse", "Hinterachse"]) if cat != "Bremsbelag" else "Vorderachse"
                con.execute("INSERT INTO parts VALUES(?,?,?,?,?,?,?)",
                            (pn, f"{cat} {random.choice(BRANDS)} {pos}", cat, random.choice(BRANDS), pos,
                             round(base * random.uniform(0.8, 2.2), 2), random.randint(0, 120)))
                con.execute("INSERT INTO fitment VALUES(?,?,?,?,?)", (pn, make, model, y0, y1))
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
    con.close()
    return n


def readonly_conn():
    return sqlite3.connect(f"file:{config.PARTS_DB}?mode=ro", uri=True)


def usage_conn():
    con = sqlite3.connect(config.USAGE_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS usage(
      id INTEGER PRIMARY KEY, ts TEXT DEFAULT CURRENT_TIMESTAMP, user TEXT, route TEXT, model TEXT,
      tokens_in INTEGER, tokens_out INTEGER, latency_ms INTEGER, cost_usd REAL, blocked INTEGER DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS feedback(
      id INTEGER PRIMARY KEY, ts TEXT DEFAULT CURRENT_TIMESTAMP, user TEXT, question TEXT,
      answer TEXT, rating INTEGER, comment TEXT)""")
    return con


if __name__ == "__main__":
    print("seeded rows:", seed())
