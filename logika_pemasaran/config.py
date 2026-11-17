"""Konfigurasi aplikasi."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "app.db"
SECRET_KEY = "ganti-dengan-kunci-rahasia-anda"
MAX_VARIABLES = 6  # batas variabel pada tabel kebenaran (2^6 = 64 baris)
