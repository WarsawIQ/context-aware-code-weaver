#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source tests/lib.sh

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp tests/fixtures/eval-results.tsv "$TMP/results.tsv"
cp tests/fixtures/eval-run.json "$TMP/run.json"

echo "== raport z katalogu przebiegu =="
python3 scripts/eval-report.py --input "$TMP"
assert_eq "$?" "0" "eval-report.py konczy sie kodem 0"
OUT="$TMP/report.md"
assert_contains "$OUT" "| m-a:1b | \`aaaaaaaaaaaa\` | 62.5% | 62.5% | 75.0% | 25.0% | 100.0% | 75.0% | 0 |" "wiersz modelu A"
assert_contains "$OUT" "| m-b:2b | \`bbbbbbbbbbbb\` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 1 |" "wiersz modelu B z jednym bledem"
assert_contains "$OUT" "| m-a:1b | 50.0% | 100.0% | 100.0% | 0.0% |" "trafnosc A w kategoriach code/kb/recent/sardor"
assert_contains "$OUT" "0.0.0-fake" "raport podaje wersje Ollamy"
assert_contains "$OUT" "abc1234" "raport podaje commit repo"

TEX="$TMP/table.tex"
assert_contains "$TEX" '\texttt{m-a:1b} & 62.5\% & 75.0\% & 25.0\% & 100.0\% \\' "wiersz LaTeX modelu A"
assert_contains "$TEX" '\end{tabular}' "tabela LaTeX jest domknieta"

echo "== dwa przebiegi w jednym raporcie (warianty promptu) =="
mkdir -p "$TMP/app" "$TMP/nb"
cp tests/fixtures/eval-results.tsv "$TMP/app/results.tsv"
cp tests/fixtures/eval-results.tsv "$TMP/nb/results.tsv"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d['label']=sys.argv[3]; json.dump(d, open(sys.argv[2],'w'))" \
  tests/fixtures/eval-run.json "$TMP/app/run.json" "app (rag_llm_app.py)"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d['label']=sys.argv[3]; json.dump(d, open(sys.argv[2],'w'))" \
  tests/fixtures/eval-run.json "$TMP/nb/run.json" notebook
python3 scripts/eval-report.py --input "$TMP/app" --input "$TMP/nb" --output "$TMP/both.md" --latex "$TMP/both.tex"
assert_eq "$?" "0" "raport z dwoch przebiegow konczy sie kodem 0"
assert_contains "$TMP/both.md" "| app (rag_llm_app.py) | m-a:1b | \`aaaaaaaaaaaa\` | 62.5% |" "markdown ma pelna etykiete wariantu"
assert_contains "$TMP/both.md" "| notebook | m-b:2b | \`bbbbbbbbbbbb\` | 100.0% |" "wiersz wariantu notebook"
assert_contains "$TMP/both.tex" 'app & \texttt{m-a:1b} & 62.5\% & 75.0\% & 25.0\% & 100.0\% \\' "LaTeX z kolumna wariantu"
assert_contains "$TMP/both.tex" '\begin{tabular}{llrrrr}' "LaTeX ma dodatkowa kolumne"
assert_not_contains "$TMP/both.tex" 'rag_llm_app.py' "LaTeX ma krotka etykiete (bez nawiasu)"
assert_contains "$TMP/both.tex" 'Code\,$\to$\,web' "LaTeX ma zwiezly naglowek"

echo "== sam plik results.tsv bez run.json =="
rm "$TMP/run.json"
python3 scripts/eval-report.py --input "$TMP/results.tsv" --output "$TMP/r2.md" --latex "$TMP/t2.tex"
assert_eq "$?" "0" "dziala bez run.json"
assert_contains "$TMP/r2.md" "62.5%" "liczy miary bez run.json"

finish
