#!/usr/bin/env python3
"""Przelicza results.tsv ewaluacji na raport markdown i tabele LaTeX do papera.

Jeden --input: raport jednego przebiegu. Kilka --input: jedna tabela z kolumna
wariantu (etykieta 'label' z run.json kazdego przebiegu), np. dwa prompty routera.

Uzywa wylacznie biblioteki standardowej — zadnego venv.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evallib  # noqa: E402

CODE_CATEGORIES = ("code", "sardor")
CATEGORY_ORDER = ("code", "kb", "recent", "sardor")


def pct(pair):
    num, den = pair
    return "n/a" if den == 0 else f"{100.0 * num / den:.1f}%"


def count(rows, pred):
    return sum(1 for r in rows if pred(r))


def summarize(rows):
    """Miary dla kazdej pary (wariant, model), w kolejnosci pierwszego wystapienia."""
    groups = list(dict.fromkeys((r.get("variant", ""), r["model"]) for r in rows))
    out = []
    for variant, model in groups:
        mr = [r for r in rows if r.get("variant", "") == variant and r["model"] == model]
        ok = [r for r in mr if r["status"] == "ok"]
        code = [r for r in ok if r["category"] in CODE_CATEGORIES]
        kb = [r for r in ok if r["category"] == "kb"]
        decisions = {}
        for r in ok:
            decisions.setdefault(r["id"], set()).add(r["decision_sardor"])
        multi_rep = len({r["rep"] for r in mr}) > 1
        out.append({
            "variant": variant,
            "model": model,
            "digest": mr[0]["model_digest"],
            "errors": len(mr) - len(ok),
            "acc_sardor": (count(ok, lambda r: r["decision_sardor"] == r["label"]), len(ok)),
            "acc_strict": (count(ok, lambda r: r["decision_strict"] == r["label"]), len(ok)),
            "one_word": (count(ok, lambda r: r["decision_strict"] != evallib.INVALID), len(ok)),
            "code_to_web": (count(code, lambda r: r["decision_sardor"] == "web_search"), len(code)),
            "kb_to_kb": (count(kb, lambda r: r["decision_sardor"] == "vectorstore"), len(kb)),
            "stable": ((sum(1 for s in decisions.values() if len(s) == 1), len(decisions))
                       if multi_rep else (0, 0)),
            "per_category": {
                c: (count(ok, lambda r, c=c: r["category"] == c and r["decision_sardor"] == r["label"]),
                    count(ok, lambda r, c=c: r["category"] == c))
                for c in CATEGORY_ORDER
            },
            "confusion": {
                (lab, dec): count(ok, lambda r, lab=lab, dec=dec: r["label"] == lab and r["decision_sardor"] == dec)
                for lab in evallib.LABELS for dec in evallib.LABELS
            },
        })
    return out


def run_lines(run):
    return [
        f"- Ollama {run.get('ollama_version', '?')}, host `{run.get('host', '?')}`",
        f"- Przebieg: {run.get('started', '?')} – {run.get('finished', '?')}",
        f"- Powtórzenia: {run.get('reps', '?')}; opcje `{json.dumps(run.get('options', {}))}`; "
        f"renderowanie `{run.get('render', '?')}`",
        f"- Prompt sha256 `{run.get('prompt_sha256', '?')}`; dataset `{run.get('dataset', '?')}`, "
        f"sha256 `{run.get('dataset_sha256', '?')}` ({run.get('dataset_rows', '?')} pytań)",
        f"- Commit repo `{run.get('repo_commit', '?')}`",
    ]


def render_markdown(summary, runs):
    variants = any(s["variant"] for s in summary)
    first = runs[0][1] if runs else {}
    lines = [f"# Raport ewaluacji: {first.get('task', 'coding-router')}", ""]
    if len(runs) == 1 and first:
        lines += run_lines(first) + [""]
    elif len(runs) > 1:
        for label, run in runs:
            lines += [f"### Wariant `{label}`", ""] + run_lines(run) + [""]
    vcol, vsep = ("| Wariant ", "|---") if variants else ("", "")

    def lead(s):
        return f"| {s['variant']} " if variants else ""

    lines += [
        "## Wyniki",
        "",
        f"{vcol}| Model | Digest | Trafność (reguła Sardora) | Trafność (ścisła) | Odpowiedzi jednym słowem "
        "| Prośby o kod → sieć | Pytania KB → baza | Stabilność | Błędy |",
        f"{vsep}|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summary:
        lines.append(
            f"{lead(s)}| {s['model']} | `{s['digest'][:12]}` | {pct(s['acc_sardor'])} | {pct(s['acc_strict'])} "
            f"| {pct(s['one_word'])} | {pct(s['code_to_web'])} | {pct(s['kb_to_kb'])} "
            f"| {pct(s['stable'])} | {s['errors']} |")
    lines += ["", "## Trafność w kategoriach (reguła Sardora)", "",
              f"{vcol}| Model | " + " | ".join(CATEGORY_ORDER) + " |",
              f"{vsep}|---|" + "---|" * len(CATEGORY_ORDER)]
    for s in summary:
        lines.append(f"{lead(s)}| {s['model']} | "
                     + " | ".join(pct(s["per_category"][c]) for c in CATEGORY_ORDER) + " |")
    lines += ["", "## Macierze pomyłek (wiersz: etykieta, kolumna: decyzja wg reguły Sardora)", ""]
    for s in summary:
        title = f"{s['variant']} / {s['model']}" if variants else s["model"]
        lines += [f"**{title}**", "", "| | vectorstore | web_search |", "|---|---|---|"]
        for lab in evallib.LABELS:
            lines.append(f"| {lab} | {s['confusion'][(lab, 'vectorstore')]} | {s['confusion'][(lab, 'web_search')]} |")
        lines.append("")
    lines += [
        "## Legenda",
        "",
        "- Reguła Sardora: odpowiedź zawierająca „vectorstore” idzie do bazy, każda inna do sieci "
        "(dosłownie jak w `rag_llm_app.py`).",
        "- Reguła ścisła: odpowiedź musi być dokładnie jednym z dwóch słów; inaczej `invalid`.",
        "- Prośby o kod → sieć: kategorie `code` i `sardor`; to, czego chce prompt routera, "
        "ale też powód, dla którego baza ze stylem nie wpływa na generowany kod.",
        "- Miary liczone na wywołaniach ze statusem `ok`; błędy (timeouty) liczone osobno.",
        "",
    ]
    return "\n".join(lines)


def render_latex(summary):
    """Tabela do papera: zwiezle naglowki, etykieta wariantu bez nawiasu (szerokosc LNCS)."""
    variants = any(s["variant"] for s in summary)

    def tex(pair):
        return pct(pair).replace("%", "\\%")

    def short(label):
        return label.split(" (")[0]
    lines = [
        "\\begin{tabular}{llrrrr}" if variants else "\\begin{tabular}{lrrrr}",
        "\\hline",
        ("Prompt & " if variants else "")
        + "Model & Accuracy & One word & Code\\,$\\to$\\,web & KB\\,$\\to$\\,KB \\\\",
        "\\hline",
    ]
    for s in summary:
        lines.append((f"{short(s['variant'])} & " if variants else "")
                     + f"\\texttt{{{s['model']}}} & {tex(s['acc_sardor'])} & {tex(s['one_word'])} "
                     f"& {tex(s['code_to_web'])} & {tex(s['kb_to_kb'])} \\\\")
    lines += ["\\hline", "\\end{tabular}", ""]
    return "\n".join(lines)


def load(path):
    """Zwraca (katalog, run, wiersze) dla katalogu przebiegu albo pliku results.tsv."""
    if os.path.isdir(path):
        run_dir, results = path, os.path.join(path, "results.tsv")
    else:
        run_dir, results = os.path.dirname(os.path.abspath(path)), path
    run = {}
    run_path = os.path.join(run_dir, "run.json")
    if os.path.exists(run_path):
        with open(run_path, encoding="utf-8") as fh:
            run = json.load(fh)
    return run_dir, run, evallib.read_tsv(results)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--input", action="append", required=True,
                   help="katalog przebiegu albo plik results.tsv; mozna podac wiele razy")
    p.add_argument("--output", help="raport markdown (domyslnie report.md obok wynikow)")
    p.add_argument("--latex", help="tabela LaTeX (domyslnie table.tex obok wynikow)")
    args = p.parse_args()
    if len(args.input) > 1 and not (args.output and args.latex):
        p.error("przy kilku --input podaj --output i --latex")
    runs, rows = [], []
    for path in args.input:
        run_dir, run, part = load(path)
        label = run.get("label") or run.get("task") or os.path.basename(run_dir)
        if len(args.input) > 1:
            for r in part:
                r["variant"] = label
        runs.append((label, run))
        rows += part
    first_dir = load(args.input[0])[0] if len(args.input) == 1 else None
    summary = summarize(rows)
    with open(args.output or os.path.join(first_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(summary, runs))
    with open(args.latex or os.path.join(first_dir, "table.tex"), "w", encoding="utf-8") as fh:
        fh.write(render_latex(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
