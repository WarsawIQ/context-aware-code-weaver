#!/usr/bin/env python3
"""Sklada dataset.tsv zadania coding-router z wycinkow zrodel i pytan wlasnych.

  --fetch   pobiera wycinki CoNaLa i RetrievalQA do <task-dir>/sources/ (wymaga sieci)
  bez flagi skladanie offline z <task-dir>/sources/ i plikow TSV z pytaniami

Uzywa wylacznie biblioteki standardowej — zadnego venv.
"""
import argparse
import datetime
import json
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evallib  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONALA_URL = ("https://datasets-server.huggingface.co/rows?dataset=neulab%2Fconala"
              "&config=curated&split=test&offset={offset}&length=100")
RETRIEVALQA_URL = "https://raw.githubusercontent.com/hyintell/RetrievalQA/main/data/retrievalqa.jsonl"
CONALA_FILE = "conala-curated-test.jsonl"
RQA_FILE = "retrievalqa-recent.jsonl"
DATASET_COLUMNS = ["id", "category", "source", "source_ref", "license", "question", "label"]

SOURCES_MD = """# Źródła zbioru pytań coding-router

Pobrane {date} przez `scripts/eval-build-dataset.py --fetch`.

| Plik | Źródło | Licencja | Wierszy |
|---|---|---|---|
| `{conala}` | CoNaLa, split `curated/test`, pole `intent` (tytuły pytań ze Stack Overflow). Yin i in., „Learning to Mine Aligned Code and Natural Language Pairs from Stack Overflow”, arXiv:1805.08949. https://huggingface.co/datasets/neulab/conala | MIT | {n_conala} |
| `{rqa}` | RetrievalQA, `data_source` ∈ {{freshqa, realtimeqa}} i `param_knowledge_answerable = 0`. Zhang, Fang, Chen, „RetrievalQA: Assessing Adaptive Retrieval-Augmented Generation for Short-form Open-Domain Question Answering”, Findings of ACL 2024. https://github.com/hyintell/RetrievalQA | MIT | {n_rqa} |

Pytania z `kb-questions.tsv` napisali autorzy, każde z odnośnikiem do sekcji PEP 8,
Google Python Style Guide albo Rules of Machine Learning. Pytania z
`sardor-questions.tsv` to dosłowne zapytania z repozytorium `ssheraliev/ml-dip-workshop`
(commit `98288b7`) i z rysunku 11 pracy dyplomowej.
"""


def http_get(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "moj-lokalny-llm-eval"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_conala():
    """Caly split curated/test CoNaLa (500 wierszy), tylko question_id i intent."""
    rows = []
    offset = 0
    while True:
        data = json.loads(http_get(CONALA_URL.format(offset=offset)))
        batch = [r["row"] for r in data["rows"]]
        rows += [{"question_id": str(r["question_id"]), "intent": r["intent"]} for r in batch]
        offset += len(batch)
        if not batch or offset >= data["num_rows_total"]:
            return rows


def fetch_retrievalqa():
    """Pytania RetrievalQA wymagajace wyszukiwania z FreshQA i RealTimeQA."""
    rows = []
    for line in http_get(RETRIEVALQA_URL).decode("utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["data_source"] in ("freshqa", "realtimeqa") and int(r["param_knowledge_answerable"]) == 0:
            rows.append({"question_id": str(r["question_id"]), "data_source": r["data_source"],
                         "question": r["question"]})
    return rows


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fetch(task_dir):
    src = os.path.join(task_dir, "sources")
    os.makedirs(src, exist_ok=True)
    conala = fetch_conala()
    rqa = fetch_retrievalqa()
    write_jsonl(os.path.join(src, CONALA_FILE), conala)
    write_jsonl(os.path.join(src, RQA_FILE), rqa)
    with open(os.path.join(src, "SOURCES.md"), "w", encoding="utf-8") as fh:
        fh.write(SOURCES_MD.format(date=datetime.date.today().isoformat(), conala=CONALA_FILE,
                                   rqa=RQA_FILE, n_conala=len(conala), n_rqa=len(rqa)))
    print(f"Pobrano: CoNaLa {len(conala)}, RetrievalQA {len(rqa)} -> {src}")


def sample(rng, rows, n, what):
    if n > len(rows):
        raise SystemExit(f"za malo pytan w {what}: jest {len(rows)}, potrzeba {n}")
    return rng.sample(rows, n)


def unique_questions(rows):
    """Jeden wiersz na pytanie. CoNaLa ma kilka wierszy (fragmentow kodu) na to samo pytanie."""
    seen_ids, seen_text, out = set(), set(), []
    for r in rows:
        if r["question_id"] in seen_ids or r["intent"] in seen_text:
            continue
        seen_ids.add(r["question_id"])
        seen_text.add(r["intent"])
        out.append(r)
    return out


def build(task_dir, n_code, n_recent, seed):
    src = os.path.join(task_dir, "sources")
    conala = unique_questions(
        sorted(read_jsonl(os.path.join(src, CONALA_FILE)), key=lambda r: int(r["question_id"])))
    rqa = sorted(read_jsonl(os.path.join(src, RQA_FILE)), key=lambda r: str(r["question_id"]))
    rng = random.Random(seed)
    rows = []
    for i, r in enumerate(sample(rng, conala, n_code, CONALA_FILE), start=1):
        rows.append({"id": f"code-{i:02d}", "category": "code", "source": "conala",
                     "source_ref": f"stackoverflow:{r['question_id']}", "license": "MIT",
                     "question": r["intent"], "label": "web_search"})
    for i, r in enumerate(sample(rng, rqa, n_recent, RQA_FILE), start=1):
        rows.append({"id": f"recent-{i:02d}", "category": "recent", "source": "retrievalqa",
                     "source_ref": f"{r['data_source']}:{r['question_id']}", "license": "MIT",
                     "question": r["question"], "label": "web_search"})
    for r in evallib.read_tsv(os.path.join(task_dir, "kb-questions.tsv")):
        rows.append({"id": r["id"], "category": "kb", "source": "authors",
                     "source_ref": r["section"], "license": "", "question": r["question"],
                     "label": "vectorstore"})
    for r in evallib.read_tsv(os.path.join(task_dir, "sardor-questions.tsv")):
        rows.append({"id": r["id"], "category": "sardor", "source": "ml-dip-workshop",
                     "source_ref": r["origin"], "license": "", "question": r["question"],
                     "label": "web_search"})
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("zduplikowane id w zbiorze pytan")
    evallib.write_tsv(os.path.join(task_dir, "dataset.tsv"), DATASET_COLUMNS, rows)
    for cat in ("code", "recent", "kb", "sardor"):
        print(f"{cat}: {sum(r['category'] == cat for r in rows)}")
    print(f"razem: {len(rows)} -> {os.path.join(task_dir, 'dataset.tsv')}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--task-dir", default=os.path.join(REPO, "tasks", "coding-router"))
    p.add_argument("--fetch", action="store_true", help="pobierz wycinki zrodel z sieci")
    p.add_argument("--n-code", type=int, default=20)
    p.add_argument("--n-recent", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if args.fetch:
        fetch(args.task_dir)
    build(args.task_dir, args.n_code, args.n_recent, args.seed)


if __name__ == "__main__":
    main()
