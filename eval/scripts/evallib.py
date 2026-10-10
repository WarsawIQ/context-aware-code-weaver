#!/usr/bin/env python3
"""Wspolne funkcje ewaluacji jakosci: reguly oceny, prompt, TSV, hashe.

Uzywa wylacznie biblioteki standardowej — zadnego venv.

Z linii polecen (dla testow):
  python3 scripts/evallib.py score sardor "'Vectorstore.'"
  python3 scripts/evallib.py render langchain-dict "Q: {question}" "How to sort?"
"""
import hashlib
import sys

LABELS = ("vectorstore", "web_search")
INVALID = "invalid"


def clean(text):
    """Czyszczenie jak w rag_llm_app.py: strip, lower, bez cudzyslowow."""
    return text.strip().lower().replace("'", "").replace('"', "")


def score_sardor(text):
    """Regula z rag_llm_app.py: 'vectorstore' w odpowiedzi -> baza, inaczej siec."""
    return "vectorstore" if "vectorstore" in clean(text) else "web_search"


def score_strict(text):
    """Czy model odpowiedzial dokladnie jednym z dwoch slow (kropka na koncu dozwolona)."""
    word = clean(text).rstrip(".")
    return word if word in LABELS else INVALID


RULES = {"sardor": score_sardor, "strict": score_strict}


def render(template, question, mode):
    """Wstawia pytanie w miejsce {question}.

    plain: samo pytanie.
    langchain-dict: slownik {'question': ...}, bo tak router w rag_llm_app.py
    przekazuje pytanie do PromptTemplate (sprawdzone na langchain-core 0.3.59).
    langchain-dict-nested: {'question': {'question': ...}}, jak router
    w llm_RAG.ipynb, gdzie RunnablePassthrough opakowuje pytanie dwa razy.
    """
    if mode == "plain":
        value = question
    elif mode == "langchain-dict":
        value = str({"question": question})
    elif mode == "langchain-dict-nested":
        value = str({"question": {"question": question}})
    else:
        raise ValueError(f"nieznany tryb renderowania: {mode}")
    return template.replace("{question}", value)


def read_prompt(path):
    """Czyta prompt.txt: naglowek z linii '# klucz: wartosc', pusta linia, szablon.

    Zwraca (szablon, metadane). Szablon bez koncowych znakow nowej linii.
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    meta = {}
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        key, _, value = lines[i][1:].partition(":")
        if value:
            meta[key.strip()] = value.strip()
        i += 1
    if i < len(lines) and lines[i] == "":
        i += 1
    return "\n".join(lines[i:]).rstrip("\n"), meta


_ESC = {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}
_UNESC = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}


def esc(value):
    """Escapuje backslash, tabulator i nowe linie, zeby wartosc miescila sie w komorce TSV."""
    return "".join(_ESC.get(ch, ch) for ch in str(value))


def unesc(value):
    """Odwraca esc()."""
    out = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value) and value[i + 1] in _UNESC:
            out.append(_UNESC[value[i + 1]])
            i += 2
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def read_tsv(path):
    """Czyta TSV z naglowkiem jako liste slownikow. Pomija puste linie i komentarze '#'."""
    with open(path, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]
    if not lines:
        return []
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(header):
            raise SystemExit(
                f"{path}: wiersz ma {len(parts)} kolumn zamiast {len(header)}: {line!r}"
            )
        rows.append({k: unesc(v) for k, v in zip(header, parts)})
    return rows


def write_tsv(path, columns, rows):
    """Zapisuje liste slownikow jako TSV z naglowkiem (wartosci escapowane)."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(columns) + "\n")
        for row in rows:
            fh.write("\t".join(esc(row.get(c, "")) for c in columns) + "\n")


def sha256_file(path):
    """sha256 pliku jako hex."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) == 3 and argv[0] == "score" and argv[1] in RULES:
        print(RULES[argv[1]](argv[2]))
        return 0
    if len(argv) == 4 and argv[0] == "render":
        print(render(argv[2], argv[3], argv[1]))
        return 0
    print("Uzycie: evallib.py score {sardor|strict} TEKST | render TRYB SZABLON PYTANIE",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
