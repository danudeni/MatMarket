"""Parser dan evaluator ekspresi logika proposisi (aman, tanpa eval).

Operator yang didukung (huruf besar/kecil bebas):
  NOT / TIDAK / ~ / ! / ¬     negasi
  AND / DAN / & / ∧           konjungsi
  XOR / ^                     disjungsi eksklusif
  OR / ATAU / | / ∨           disjungsi
  -> / => / → / IMPLIES       implikasi (jika ... maka ...)
  <-> / <=> / ↔ / IFF         biimplikasi

Prioritas (tinggi -> rendah): NOT, AND, XOR, OR, IMPLIES, IFF.
"""
import re


class ExpressionError(ValueError):
    """Dilempar saat ekspresi logika tidak valid."""


_TOKEN = re.compile(r"\s*(<->|<=>|->|=>|[()~!&|^¬∧∨→↔]|[A-Za-z_][A-Za-z0-9_]*)")

_OPS = {
    "AND": "AND", "DAN": "AND", "&": "AND", "∧": "AND",
    "OR": "OR", "ATAU": "OR", "|": "OR", "∨": "OR",
    "NOT": "NOT", "TIDAK": "NOT", "~": "NOT", "!": "NOT", "¬": "NOT",
    "XOR": "XOR", "^": "XOR",
    "IMPLIES": "IMP", "->": "IMP", "=>": "IMP", "→": "IMP",
    "IFF": "IFF", "<->": "IFF", "<=>": "IFF", "↔": "IFF",
}

SYMBOL = {"AND": "∧", "OR": "∨", "XOR": "⊕", "IMP": "→", "IFF": "↔"}


def tokenize(text):
    text = (text or "").strip()
    if not text:
        raise ExpressionError("Ekspresi tidak boleh kosong.")
    tokens, pos = [], 0
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if not match:
            raise ExpressionError(f"Karakter tidak dikenali dekat '{text[pos:pos + 10].strip()}'.")
        raw, pos = match.group(1), match.end()
        key = raw.upper()
        if key in _OPS:
            tokens.append(("op", _OPS[key]))
        elif raw in ("(", ")"):
            tokens.append((raw, raw))
        else:
            tokens.append(("var", raw))
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens, self.i = tokens, 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def parse(self):
        node = self.iff()
        if self.i != len(self.tokens):
            raise ExpressionError("Ekspresi tidak lengkap atau tanda kurung tidak seimbang.")
        return node

    def iff(self):
        left = self.imp()
        while self.peek() == ("op", "IFF"):
            self.take()
            left = ("IFF", left, self.imp())
        return left

    def imp(self):  # asosiatif kanan
        left = self.or_()
        if self.peek() == ("op", "IMP"):
            self.take()
            return ("IMP", left, self.imp())
        return left

    def or_(self):
        left = self.xor()
        while self.peek() == ("op", "OR"):
            self.take()
            left = ("OR", left, self.xor())
        return left

    def xor(self):
        left = self.and_()
        while self.peek() == ("op", "XOR"):
            self.take()
            left = ("XOR", left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.peek() == ("op", "AND"):
            self.take()
            left = ("AND", left, self.not_())
        return left

    def not_(self):
        if self.peek() == ("op", "NOT"):
            self.take()
            return ("NOT", self.not_())
        return self.atom()

    def atom(self):
        kind, value = self.take()
        if kind == "var":
            return ("VAR", value)
        if kind == "(":
            node = self.iff()
            if self.take()[0] != ")":
                raise ExpressionError("Tanda kurung penutup ')' tidak ditemukan.")
            return node
        raise ExpressionError("Operand hilang: periksa urutan operator dan variabel.")


def parse(text):
    """Ubah teks menjadi pohon sintaks (AST berupa tuple)."""
    return _Parser(tokenize(text)).parse()


def evaluate(node, env):
    """Hitung nilai kebenaran AST. Variabel yang tidak ada di env dianggap salah."""
    op = node[0]
    if op == "VAR":
        return bool(env.get(node[1], False))
    if op == "NOT":
        return not evaluate(node[1], env)
    a, b = evaluate(node[1], env), evaluate(node[2], env)
    return {"AND": a and b, "OR": a or b, "XOR": a != b,
            "IMP": (not a) or b, "IFF": a == b}[op]


def variables(node, found=None):
    """Daftar variabel unik sesuai urutan kemunculan."""
    found = [] if found is None else found
    if node[0] == "VAR":
        if node[1] not in found:
            found.append(node[1])
    else:
        for child in node[1:]:
            variables(child, found)
    return found


def to_text(node):
    if node[0] == "VAR":
        return node[1]
    if node[0] == "NOT":
        inner = node[1]
        text = to_text(inner)
        return "¬" + (text if inner[0] in ("VAR", "NOT") else f"({text})")
    return f"({to_text(node[1])} {SYMBOL[node[0]]} {to_text(node[2])})"


def subexpressions(node, out=None):
    """Sub-ekspresi non-variabel secara post-order (untuk kolom antara tabel kebenaran)."""
    out = [] if out is None else out
    if node[0] != "VAR":
        for child in node[1:]:
            subexpressions(child, out)
        if all(to_text(node) != t for t, _ in out):
            out.append((to_text(node), node))
    return out
