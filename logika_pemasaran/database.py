"""Lapisan data SQLite: aturan bisnis dan riwayat analisis."""
import json
import sqlite3
from datetime import datetime

from config import DB_PATH

DEFAULT_RULES = [
    ("Stok menipis", "NOT stok_cukup", "Tunda promo besar dan prioritaskan restock", "peringatan", 0),
    ("Promo musiman", "musim_ramai AND stok_cukup", "Kampanye promo musiman (diskon bundling)", "strategi", 1),
    ("Loyalitas", "pelanggan_loyal AND anggaran_besar", "Program poin dan reward untuk pelanggan setia", "strategi", 2),
    ("Peluncuran produk", "produk_baru AND anggaran_besar", "Iklan digital dan kolaborasi influencer", "strategi", 2),
    ("Perang harga", "kompetitor_agresif AND NOT harga_kompetitif", "Sesuaikan harga atau tawarkan price matching", "strategi", 1),
    ("Hemat anggaran", "NOT anggaran_besar AND pelanggan_loyal", "Pemasaran organik: referral dan media sosial", "strategi", 3),
    ("Soft launching", "produk_baru AND NOT musim_ramai", "Soft launching dengan sampel gratis", "strategi", 3),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, condition TEXT NOT NULL, strategy TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'strategi', priority INTEGER NOT NULL DEFAULT 5);
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL, facts TEXT NOT NULL, outcome TEXT NOT NULL);
        """)
        if db.execute("SELECT COUNT(*) FROM rules").fetchone()[0] == 0:
            db.executemany("INSERT INTO rules (name, condition, strategy, kind, priority) "
                        "VALUES (?, ?, ?, ?, ?)", DEFAULT_RULES)
def get_rules():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM rules ORDER BY priority, id")]
def add_rule(name, condition, strategy, kind, priority):
    with connect() as db:
        db.execute("INSERT INTO rules (name, condition, strategy, kind, priority) VALUES (?, ?, ?, ?, ?)",
                (name, condition, strategy, kind, priority))
def delete_rule(rule_id):
    with connect() as db:
        db.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
def save_history(facts, triggered):
    outcome = [{"name": r["name"], "strategy": r["strategy"], "kind": r["kind"]} for r in triggered]
    with connect() as db:
        db.execute("INSERT INTO history (created_at, facts, outcome) VALUES (?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(facts), json.dumps(outcome)))
def get_history(limit=50):
    with connect() as db:
        rows = db.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": r["id"], "created_at": r["created_at"],
            "facts": json.loads(r["facts"]), "outcome": json.loads(r["outcome"])} for r in rows]
def clear_history():
    with connect() as db:
        db.execute("DELETE FROM history")
