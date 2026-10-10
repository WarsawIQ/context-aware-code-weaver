# Router evaluation

The router of Context-Aware Code Weaver reads a question and answers with one
word, `vectorstore` (answer from the local knowledge base) or `web_search`.
This directory measures that decision on 53 questions, with the two versions
of the routing prompt found in the code and with four local models. The
numbers in the paper come from the run of 10 October 2026 kept in `results/`.

Everything here uses the Python standard library only; no virtual environment
is needed. The only service required is a running Ollama.

## Layout

```
scripts/
  eval.py                 run one task on one or more models, write results.tsv + run.json
  eval-report.py          turn results.tsv into report.md and a LaTeX table
  eval-build-dataset.py   assemble dataset.tsv from the sources (offline) or fetch them (--fetch)
  evallib.py              scoring rules, prompt rendering, TSV helpers
tasks/
  coding-router/          prompt of rag_llm_app.py, dataset.tsv (53 questions), sources/
  coding-router-notebook/ prompt of llm_RAG.ipynb, shares the dataset of coding-router
results/
  coding-router/2026-10-10-full/           run.json, results.tsv, progress.log, report.md, table.tex
  coding-router-notebook/2026-10-10-full/  same for the notebook prompt
  router-table.tex                         combined table used in the paper
tests/                    shell tests against a fake Ollama (no models needed)
```

## The questions

`tasks/coding-router/dataset.tsv` has four groups, labelled according to what
the routing prompt asks for:

| id prefix | n | what | label |
|---|---|---|---|
| `code-` | 20 | Stack Overflow question titles sampled (seed 42) from the 364 distinct questions of the CoNaLa `curated/test` split | `web_search` |
| `recent-` | 10 | current-event questions sampled from the 242 FreshQA and RealTimeQA questions that RetrievalQA marks as needing retrieval | `web_search` |
| `kb-` | 20 | questions about Python style and ML practice written by the authors, each tied to a section of PEP 8 (8), the Google Python Style Guide (8) or the Rules of ML (4) | `vectorstore` |
| `sardor-` | 3 | the first author's own code requests (merge sort, a regression model, clustering) | `web_search` |

Licences and provenance are in `../DATA-LICENSE.md`.

## The prompts

`tasks/*/prompt.txt` start with a header of `# key: value` lines (source,
rendering mode, label), then the template with a `{question}` placeholder.
The rendering mode reproduces what LangChain actually puts into the prompt:
the application passes the question as a Python dictionary,
`{'question': ...}`, and the notebook wraps it twice. Both were checked by
running the original chains with a stub model.

## Scoring

Two rules are recorded for every reply:

- `decision_sardor`: the rule of `rag_llm_app.py`, a reply containing the
  word `vectorstore` goes to the knowledge base, anything else to web search;
- `decision_strict`: the reply must be exactly one of the two words
  (trailing period allowed), otherwise `invalid`.

Accuracy in the paper uses the first rule. The "one word" column of the table
is the share of replies that pass the second.

## Reproducing the run

```bash
ollama pull gemma3:4b
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:14b

python3 eval/scripts/eval.py --task coding-router
python3 eval/scripts/eval.py --task coding-router-notebook
```

Each call prints the output directory (`eval/results/<task>/<date-time>`).
Options: `--model NAME` (repeatable), `--reps N` (default 3), `--quick`
(1 repetition), `--host URL`, `--timeout SECONDS`, `--out DIR`. Every call to
Ollama uses `temperature 0`, `seed 42`, `num_predict 256`. On a laptop with an
AMD Ryzen AI 9 HX 370 and its integrated GPU the two runs (1,272 calls) took
15 minutes.

`run.json` records the Ollama version, the digest of every model, the SHA-256
of the prompt and of the dataset, and the git commit. Results are
deterministic for a given model digest and Ollama version; different weights
behind the same tag, or a different Ollama build, may change some decisions.

The report and the LaTeX table for one run:

```bash
python3 eval/scripts/eval-report.py --input eval/results/coding-router/2026-10-10-full
```

The combined table with both prompts, as used in the paper:

```bash
python3 eval/scripts/eval-report.py \
  --input eval/results/coding-router/2026-10-10-full \
  --input eval/results/coding-router-notebook/2026-10-10-full \
  --output eval/results/router-report.md --latex eval/results/router-table.tex
```

## Rebuilding the dataset

```bash
python3 eval/scripts/eval-build-dataset.py            # offline, from tasks/coding-router/sources/
python3 eval/scripts/eval-build-dataset.py --fetch    # re-download the CoNaLa and RetrievalQA excerpts first
```

The offline build is deterministic (seed 42) and reproduces `dataset.tsv`
byte for byte; `run.json` holds its SHA-256.

## Tests

```bash
cd eval
bash tests/test-eval-scoring.sh
bash tests/test-eval-dataset.sh
bash tests/test-eval-report.sh
bash tests/test-eval-run.sh      # starts tests/fake_ollama.py on a free port
```

The scripts were written in a Polish-language repository; comments, CLI help
and the Markdown report are still in Polish. The LaTeX table and the TSV
columns are in English.
