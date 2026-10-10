#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source tests/lib.sh

TMP="$(mktemp -d)"
python3 tests/fake_ollama.py 0 > "$TMP/port" &
FAKE=$!
trap 'kill $FAKE 2>/dev/null; rm -rf "$TMP"' EXIT
for _ in $(seq 50); do [[ -s "$TMP/port" ]] && break; sleep 0.1; done
HOST="http://127.0.0.1:$(head -1 "$TMP/port")"

echo "== przebieg na atrapie =="
python3 scripts/eval.py --task-dir tests/fixtures/eval-task --model m-a:1b --model m-b \
  --quick --timeout 1 --host "$HOST" --out "$TMP/run" 2> "$TMP/stderr"
assert_eq "$?" "0" "eval.py konczy sie kodem 0"
RES="$TMP/run/results.tsv"
assert_eq "$(($(wc -l < "$RES") - 1))" "6" "2 modele x 3 pytania x 1 powtorzenie = 6 wierszy"
assert_contains "$RES" "TIMEOUT" "wolne pytanie konczy sie timeoutem"
assert_eq "$(awk -F'\t' '$5=="q-style" && $2=="m-a:1b" {print $8}' "$RES")" "vectorstore" "pytanie o styl -> vectorstore"
assert_eq "$(awk -F'\t' '$5=="q-code" && $2=="m-a:1b" {print $8}' "$RES")" "web_search" "pytanie o kod -> web_search"
assert_eq "$(awk -F'\t' '$5=="q-slow" && $2=="m-a:1b" {print $8}' "$RES")" "" "przy timeoucie decyzja jest pusta"
assert_contains "$TMP/run/run.json" "0.0.0-fake" "run.json ma wersje Ollamy"
assert_contains "$TMP/run/run.json" "bbbbbbbbbbbb2222" "run.json ma digest modelu podanego bez :latest"
assert_contains "$TMP/run/run.json" "langchain-dict" "run.json zapisuje tryb renderowania"

echo "== wariant z dataset z innego zadania i zagniezdzonym pytaniem =="
python3 scripts/eval.py --task nested --task-dir tests/fixtures/eval-task-nested --model m-a:1b \
  --quick --timeout 1 --host "$HOST" --out "$TMP/run-nested" 2> /dev/null
assert_eq "$?" "0" "wariant konczy sie kodem 0"
assert_eq "$(($(wc -l < "$TMP/run-nested/results.tsv") - 1))" "3" "uzywa 3 pytan z ../eval-task/dataset.tsv"
assert_eq "$(awk -F'\t' '$5=="q-style" {print $8}' "$TMP/run-nested/results.tsv")" "vectorstore" "pytanie przechodzi przez zagniezdzenie"
assert_contains "$TMP/run-nested/run.json" "langchain-dict-nested" "run.json zapisuje tryb nested"
assert_contains "$TMP/run-nested/run.json" '"label": "nested"' "run.json zapisuje etykiete wariantu"
assert_contains "$TMP/run-nested/run.json" "eval-task/dataset.tsv" "run.json zapisuje uzyty plik pytan"

echo "== brakujacy model =="
python3 scripts/eval.py --task-dir tests/fixtures/eval-task --model nope:1b --quick \
  --host "$HOST" --out "$TMP/run2" 2> "$TMP/stderr2"
assert_eq "$?" "2" "brak modelu -> kod 2"
assert_contains "$TMP/stderr2" "ollama pull nope:1b" "komunikat mowi, jak sciagnac model"

echo "== Ollama nie odpowiada =="
python3 scripts/eval.py --task-dir tests/fixtures/eval-task --model m-a:1b --quick \
  --host "http://127.0.0.1:9" --out "$TMP/run3" 2> "$TMP/stderr3"
assert_eq "$?" "1" "brak uslugi -> kod 1"
assert_contains "$TMP/stderr3" "Ollama nie odpowiada" "komunikat o niedostepnej usludze"

finish
