from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from flask import Flask, render_template, request, redirect, url_for, abort, Response

APP_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILENAME = "quran-uthmani-hafs.clean.json"
JSON_PATH = os.path.join(APP_DIR, JSON_FILENAME)

app = Flask(__name__)


def to_arabic_number(n: int) -> str:
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    return "".join(arabic_digits[int(d)] for d in str(n))


@lru_cache(maxsize=1)
def load_quran() -> Dict[str, Any]:
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {JSON_PATH}\n"
            f"Pastikan {JSON_FILENAME} satu folder dengan app.py"
        )
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_surah_by_id(surah_id: int) -> Optional[Dict[str, Any]]:
    data = load_quran()
    for s in data.get("surahs", []):
        if s.get("surah_id") == surah_id:
            return s
    return None


@app.get("/")
def home():
    # tampil kosong dulu, atau langsung redirect ke /surah/1 jika mau
    return render_template("index.html", surah=None, error=None)


@app.post("/go")
def go():
    raw = (request.form.get("surah_id") or "").strip()
    try:
        sid = int(raw)
    except Exception:
        return render_template("index.html", surah=None, error="Masukkan angka 1–114.")
    return redirect(url_for("show_surah", surah_id=sid))


@app.get("/surah/<int:surah_id>")
def show_surah(surah_id: int):
    if not (1 <= surah_id <= 114):
        return render_template("index.html", surah=None, error="Nomor surah harus 1 sampai 114.")
    surah = get_surah_by_id(surah_id)
    if not surah:
        abort(404)

    # siapkan data untuk template
    ayahs_view = []
    for a in surah.get("ayahs", []):
        no = a.get("ayah_no")
        no_ar = to_arabic_number(no) if isinstance(no, int) else ""
        ayahs_view.append(
            {
                "no": no,
                "no_ar": no_ar,
                "text": a.get("text", ""),
            }
        )

    view = {
        "surah_id": surah_id,
        "name": surah.get("name", str(surah_id)),
        "count": len(ayahs_view),
        "ayahs": ayahs_view,
        "prev_id": surah_id - 1 if surah_id > 1 else None,
        "next_id": surah_id + 1 if surah_id < 114 else None,
    }
    return render_template("index.html", surah=view, error=None)


@app.get("/export/<int:surah_id>.txt")
def export_txt(surah_id: int):
    if not (1 <= surah_id <= 114):
        abort(404)
    surah = get_surah_by_id(surah_id)
    if not surah:
        abort(404)

    name = surah.get("name", str(surah_id))
    title = f"Surah {name} (#{surah_id}) — {len(surah.get('ayahs', []))} ayat"

    lines = [title, ""]
    for a in surah.get("ayahs", []):
        no = a.get("ayah_no")
        no_ar = to_arabic_number(no) if isinstance(no, int) else ""
        text = a.get("text", "")
        lines.append(f"{text} ۝{no_ar}")

    content = "\n".join(lines) + "\n"
    filename = f"surah_{surah_id:03d}.txt"

    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    # akses dari HP dalam 1 wifi: app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(debug=True)
