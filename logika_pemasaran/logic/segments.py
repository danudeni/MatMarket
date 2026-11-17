"""Segmentasi pelanggan memakai teori himpunan + logika proposisi."""
import re
from itertools import combinations

from .parser import ExpressionError, evaluate, parse, to_text, variables

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_members(text):
    return {m.strip() for m in re.split(r"[,;\n]", text or "") if m.strip()}


def analyze(named_sets, expression=""):
    """named_sets: dict nama -> set anggota. expression: ekspresi logika antar-nama himpunan."""
    if len(named_sets) < 2:
        raise ExpressionError("Isi minimal dua himpunan pelanggan.")
    universe = set().union(*named_sets.values())
    pairs = []
    for (na, a), (nb, b) in combinations(named_sets.items(), 2):
        inter, union = a & b, a | b
        pairs.append({
            "a": na, "b": nb,
            "union": sorted(union), "intersection": sorted(inter),
            "a_minus_b": sorted(a - b), "b_minus_a": sorted(b - a),
            "inclusion_exclusion": f"|{na}∪{nb}| = {len(a)} + {len(b)} − {len(inter)} = {len(union)}",
        })
    result = None
    if expression.strip():
        ast = parse(expression)
        unknown = [v for v in variables(ast) if v not in named_sets]
        if unknown:
            raise ExpressionError("Himpunan tidak dikenal: " + ", ".join(unknown))
        members = sorted(m for m in universe
                         if evaluate(ast, {n: m in s for n, s in named_sets.items()}))
        result = {"formal": to_text(ast), "members": members,
                  "share": round(100 * len(members) / len(universe), 1) if universe else 0}
    return {"universe": sorted(universe), "sizes": {n: len(s) for n, s in named_sets.items()},
            "pairs": pairs, "result": result}
