"""Aplikasi web Flask: Implementasi Logika Matematika dalam Sistem Bisnis
untuk Mendukung Penentuan Strategi Pemasaran."""
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

import database as db
from config import SECRET_KEY
from logic import rules as rule_engine
from logic import segments, truth_table
from logic.parser import ExpressionError, parse

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.jinja_env.globals["label"] = rule_engine.label

@app.route("/")
def index():
    history = db.get_history(limit=1)
    return render_template("index.html", rule_count=len(db.get_rules()),
                           last=history[0] if history else None)


@app.route("/strategi", methods=["GET", "POST"])
def strategi():
    rules = db.get_rules()
    names = rule_engine.fact_variables(rules)
    facts = {n: False for n in names}
    result = None
    if request.method == "POST":
        facts = {n: request.form.get(n) == "on" for n in names}
        triggered, skipped = rule_engine.evaluate_rules(rules, facts)
        result = {"warnings": [r for r in triggered if r["kind"] == "peringatan"],
                  "strategies": [r for r in triggered if r["kind"] != "peringatan"],
                  "skipped": skipped}
        db.save_history(facts, triggered)
    return render_template("strategi.html", names=names, facts=facts, result=result)


@app.route("/aturan", methods=["GET", "POST"])
def aturan():
    if request.method == "POST":
        f = request.form
        try:
            parse(f.get("condition", ""))
            if not f.get("name", "").strip() or not f.get("strategy", "").strip():
                raise ExpressionError("Nama aturan dan strategi wajib diisi.")
            db.add_rule(f["name"].strip(), f["condition"].strip(), f["strategy"].strip(),
                        f.get("kind", "strategi"), int(f.get("priority") or 5))
            flash("Aturan disimpan.", "ok")
        except (ExpressionError, ValueError) as err:
            flash(f"Aturan belum disimpan: {err}", "error")
        return redirect(url_for("aturan"))
    return render_template("aturan.html", rules=db.get_rules())


@app.post("/aturan/<int:rule_id>/hapus")
def hapus_aturan(rule_id):
    db.delete_rule(rule_id)
    flash("Aturan dihapus.", "ok")
    return redirect(url_for("aturan"))


@app.route("/tabel-kebenaran", methods=["GET", "POST"])
def tabel_kebenaran():
    expr = (request.values.get("expr") or "").strip()
    other = (request.values.get("other") or "").strip()
    table = same = None
    if expr:
        try:
            table = truth_table.build(expr)
            if other:
                same = truth_table.equivalent(expr, other)
        except ExpressionError as err:
            flash(str(err), "error")
    return render_template("tabel_kebenaran.html", expr=expr, other=other, table=table, same=same)


@app.route("/segmentasi", methods=["GET", "POST"])
def segmentasi():
    defaults = [("Member", "Ani, Budi, Citra, Dedi, Eka"),
                ("Pembeli_Online", "Budi, Eka, Fajar, Gita"),
                ("Pembeli_Promo", "Citra, Eka, Gita, Hana")]
    entries = [{"name": n, "members": m} for n, m in defaults]
    expression = "Member AND NOT Pembeli_Online"
    analysis = None
    if request.method == "POST":
        entries = [{"name": request.form.get(f"name{i}", "").strip(),
                    "members": request.form.get(f"members{i}", "")} for i in range(3)]
        expression = request.form.get("expression", "").strip()
        try:
            named = {}
            for e in entries:
                if not e["name"] and not e["members"].strip():
                    continue
                if not segments.NAME_RE.match(e["name"]):
                    raise ExpressionError(f"Nama himpunan '{e['name']}' tidak valid (huruf, angka, garis bawah).")
                named[e["name"]] = segments.parse_members(e["members"])
            analysis = segments.analyze(named, expression)
        except ExpressionError as err:
            flash(str(err), "error")
    return render_template("segmentasi.html", entries=entries, expression=expression, analysis=analysis)


@app.route("/riwayat")
def riwayat():
    return render_template("riwayat.html", items=db.get_history())


@app.post("/riwayat/hapus")
def hapus_riwayat():
    db.clear_history()
    return redirect(url_for("riwayat"))


@app.get("/api/tabel-kebenaran")
def api_tabel():
    try:
        return jsonify(truth_table.build(request.args.get("expr", "")))
    except ExpressionError as err:
        return jsonify(error=str(err)), 400


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
