"""Mesin inferensi aturan bisnis: fakta (benar/salah) -> strategi pemasaran."""
from .parser import ExpressionError, evaluate, parse, to_text, variables


def fact_variables(rules):
    """Semua variabel fakta yang dipakai oleh seluruh aturan (urut kemunculan)."""
    names = []
    for rule in rules:
        try:
            for name in variables(parse(rule["condition"])):
                if name not in names:
                    names.append(name)
        except ExpressionError:
            continue
    return names


def evaluate_rules(rules, facts):
    """Kembalikan (aturan terpenuhi, aturan tidak terpenuhi); diurutkan menurut prioritas."""
    triggered, skipped = [], []
    for rule in rules:
        try:
            ast = parse(rule["condition"])
        except ExpressionError:
            continue
        item = dict(rule, formal=to_text(ast))
        (triggered if evaluate(ast, facts) else skipped).append(item)
    triggered.sort(key=lambda r: r["priority"])
    return triggered, skipped


def label(name):
    return name.replace("_", " ").capitalize()
