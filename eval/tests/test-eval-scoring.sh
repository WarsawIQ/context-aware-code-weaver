#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
source tests/lib.sh

check() {  # regula, tekst, oczekiwana decyzja
  assert_eq "$(python3 scripts/evallib.py score "$1" "$2")" "$3" "$1: '$2' -> $3"
}

echo "== regula sardor (dokladnie jak rag_llm_app.py) =="
check sardor "vectorstore" "vectorstore"
check sardor "'Vectorstore.'" "vectorstore"
check sardor '"web_search"' "web_search"
check sardor "I would use vectorstore or web_search" "vectorstore"
check sardor "" "web_search"
check sardor "Web Search" "web_search"
check sardor $'vectorstore\n\nThe question is about PEP 8.' "vectorstore"

echo "== regula scisla =="
check strict "vectorstore" "vectorstore"
check strict "'Vectorstore.'" "vectorstore"
check strict "web_search." "web_search"
check strict "I would use vectorstore or web_search" "invalid"
check strict "" "invalid"
check strict "Web Search" "invalid"
check strict $'vectorstore\n\nThe question is about PEP 8.' "invalid"

echo "== renderowanie promptu =="
assert_eq "$(python3 scripts/evallib.py render plain 'Q: {question}' 'How to sort?')" \
  "Q: How to sort?" "tryb plain wstawia samo pytanie"
assert_eq "$(python3 scripts/evallib.py render langchain-dict 'Q: {question}' 'How to sort?')" \
  "Q: {'question': 'How to sort?'}" "tryb langchain-dict wstawia slownik jak LangChain"
assert_eq "$(python3 scripts/evallib.py render langchain-dict 'Q: {question}' "What's new?")" \
  "Q: {'question': \"What's new?\"}" "apostrof w pytaniu jak w repr Pythona"
assert_eq "$(python3 scripts/evallib.py render langchain-dict-nested 'Q: {question}' 'How to sort?')" \
  "Q: {'question': {'question': 'How to sort?'}}" "tryb nested jak router w llm_RAG.ipynb"

finish
