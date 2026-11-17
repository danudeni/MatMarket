"""Pembuat tabel kebenaran, klasifikasi, dan uji ekuivalensi."""
from itertools import product

from config import MAX_VARIABLES
from .parser import ExpressionError, evaluate, parse, subexpressions, to_text, variables


def _combos(names):
    for combo in product([True, False], repeat=len(names)):
        yield combo, dict(zip(names, combo))


def build(expression):
    ast = parse(expression)
    names = variables(ast)
    if len(names) > MAX_VARIABLES:
        raise ExpressionError(f"Maksimal {MAX_VARIABLES} variabel (ditemukan {len(names)}).")
    steps = [(t, n) for t, n in subexpressions(ast) if n != ast]
    rows = []
    for combo, env in _combos(names):
        rows.append({
            "inputs": list(combo),
            "steps": [evaluate(n, env) for _, n in steps],
            "result": evaluate(ast, env),
        })
    results = [r["result"] for r in rows]
    if all(results):
        kind = "Tautologi (selalu benar)"
    elif not any(results):
        kind = "Kontradiksi (selalu salah)"
    else:
        kind = "Kontingensi (bergantung kondisi)"
    return {"normalized": to_text(ast), "variables": names,
            "step_headers": [t for t, _ in steps], "rows": rows, "kind": kind,
            "true_count": sum(results), "total": len(results)}


def equivalent(expr_a, expr_b):
    """True jika kedua ekspresi punya nilai kebenaran sama pada semua kombinasi."""
    a, b = parse(expr_a), parse(expr_b)
    names = list(dict.fromkeys(variables(a) + variables(b)))
    if len(names) > MAX_VARIABLES:
        raise ExpressionError(f"Maksimal {MAX_VARIABLES} variabel.")
    return all(evaluate(a, env) == evaluate(b, env) for _, env in _combos(names))
