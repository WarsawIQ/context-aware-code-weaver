# Źródła zbioru pytań coding-router

Pobrane 2026-10-10 przez `scripts/eval-build-dataset.py --fetch`.

| Plik | Źródło | Licencja | Wierszy |
|---|---|---|---|
| `conala-curated-test.jsonl` | CoNaLa, split `curated/test`, pole `intent` (tytuły pytań ze Stack Overflow). Yin i in., „Learning to Mine Aligned Code and Natural Language Pairs from Stack Overflow”, arXiv:1805.08949. https://huggingface.co/datasets/neulab/conala | MIT | 500 |
| `retrievalqa-recent.jsonl` | RetrievalQA, `data_source` ∈ {freshqa, realtimeqa} i `param_knowledge_answerable = 0`. Zhang, Fang, Chen, „RetrievalQA: Assessing Adaptive Retrieval-Augmented Generation for Short-form Open-Domain Question Answering”, Findings of ACL 2024. https://github.com/hyintell/RetrievalQA | MIT | 242 |

Pytania z `kb-questions.tsv` napisali autorzy, każde z odnośnikiem do sekcji PEP 8,
Google Python Style Guide albo Rules of Machine Learning. Pytania z
`sardor-questions.tsv` to dosłowne zapytania z repozytorium `ssheraliev/ml-dip-workshop`
(commit `98288b7`) i z rysunku 11 pracy dyplomowej.
