#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source tests/lib.sh

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
TASK="$TMP/task"
mkdir -p "$TASK/sources"

# Fixture'y generowane w locie: 25 pytan CoNaLa, 12 RetrievalQA, 3 KB, 2 Sardora.
python3 - "$TASK" <<'EOF'
import json, os, sys
task = sys.argv[1]
with open(os.path.join(task, "sources", "conala-curated-test.jsonl"), "w") as fh:
    for i in range(25):
        fh.write(json.dumps({"question_id": str(1000 + i), "intent": f"conala intent {i}"}) + "\n")
    # Jak w prawdziwej CoNaLa: to samo pytanie w kilku wierszach (po jednym na fragment kodu).
    for _ in range(30):
        fh.write(json.dumps({"question_id": "1000", "intent": "conala intent 0"}) + "\n")
with open(os.path.join(task, "sources", "retrievalqa-recent.jsonl"), "w") as fh:
    for i in range(12):
        fh.write(json.dumps({"question_id": f"rq{i:03d}", "data_source": "freshqa",
                             "question": f"recent question {i}"}) + "\n")
with open(os.path.join(task, "kb-questions.tsv"), "w") as fh:
    fh.write("id\tsection\tquestion\n")
    for i in range(1, 4):
        fh.write(f"kb-{i:02d}\tPEP 8: Section {i}\tkb question {i}\n")
with open(os.path.join(task, "sardor-questions.tsv"), "w") as fh:
    fh.write("id\torigin\tquestion\n")
    fh.write("sardor-01\tllm_RAG.ipynb test_queries\tHow to write Merge Sort Algorithm?\n")
    fh.write("sardor-02\tFigure 11\tHow to write Unsupervised Learning algorithm - Clustering?\n")
EOF

echo "== skladanie offline =="
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 5 --n-recent 3 > "$TMP/out.txt"
assert_eq "$?" "0" "skrypt konczy sie kodem 0"
DS="$TASK/dataset.tsv"
assert_eq "$(head -1 "$DS")" $'id\tcategory\tsource\tsource_ref\tlicense\tquestion\tlabel' "naglowek datasetu"
assert_eq "$(($(wc -l < "$DS") - 1))" "13" "5 code + 3 recent + 3 kb + 2 sardor = 13"
assert_eq "$(awk -F'\t' '$2=="code"' "$DS" | wc -l)" "5" "5 pytan code"
assert_eq "$(awk -F'\t' '$2=="recent"' "$DS" | wc -l)" "3" "3 pytania recent"
assert_eq "$(awk -F'\t' '$2=="kb" && $7=="vectorstore"' "$DS" | wc -l)" "3" "kb ma etykiete vectorstore"
assert_eq "$(awk -F'\t' '$2!="kb" && NR>1 && $7!="web_search"' "$DS" | wc -l)" "0" "reszta ma etykiete web_search"
assert_contains "$DS" "stackoverflow:10" "code ma odnosnik do pytania na Stack Overflow"
assert_contains "$DS" "freshqa:rq" "recent ma odnosnik do RetrievalQA"
assert_contains "$DS" "How to write Unsupervised Learning algorithm - Clustering?" "zapytania Sardora doslownie"
assert_contains "$TMP/out.txt" "code: 5" "podsumowanie liczy kategorie"
assert_eq "$(awk -F'\t' 'NR>1 {print $6}' "$DS" | sort | uniq -d | wc -l)" "0" "zadne pytanie sie nie powtarza"

echo "== duplikaty CoNaLa nie zwiekszaja puli =="
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 25 --n-recent 3 > /dev/null
assert_eq "$?" "0" "25 unikalnych pytan wystarcza na probe 25"
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 26 --n-recent 3 > /dev/null 2>&1
assert_eq "$?" "1" "26 > 25 unikalnych -> kod 1, mimo 55 wierszy w pliku"
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 5 --n-recent 3 > /dev/null

echo "== powtarzalnosc losowania =="
cp "$DS" "$TMP/first.tsv"
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 5 --n-recent 3 > /dev/null
if cmp -s "$DS" "$TMP/first.tsv"; then echo "  ok: drugi przebieg daje identyczny plik"; else echo "  FAIL: losowanie nie jest powtarzalne"; FAILED=1; fi

echo "== za duza proba =="
python3 scripts/eval-build-dataset.py --task-dir "$TASK" --n-code 99 > /dev/null 2> "$TMP/err.txt"
assert_eq "$?" "1" "za duza proba -> kod 1"
assert_contains "$TMP/err.txt" "za malo" "komunikat o zbyt malej liczbie pytan"

finish
