# Raport ewaluacji: coding-router

### Wariant `app (rag_llm_app.py)`

- Ollama 0.30.11, host `http://127.0.0.1:11434`
- Przebieg: 2026-10-10T22:36:46 – 2026-10-10T22:44:57
- Powtórzenia: 3; opcje `{"temperature": 0, "seed": 42, "num_predict": 256}`; renderowanie `langchain-dict`
- Prompt sha256 `0a70c0d6f3e68b2d78a273f77821bc7c4cc0e7fb47f42f739f644b0a8e207fbd`; dataset `eval/tasks/coding-router/dataset.tsv`, sha256 `f9845d928c2f105392672cae0c8a3572daaa02c6b85b5d2b8a58878cbc37d45a` (53 pytań)
- Commit repo `825c9b2`

### Wariant `notebook (llm_RAG.ipynb)`

- Ollama 0.30.11, host `http://127.0.0.1:11434`
- Przebieg: 2026-10-10T22:44:57 – 2026-10-10T22:52:12
- Powtórzenia: 3; opcje `{"temperature": 0, "seed": 42, "num_predict": 256}`; renderowanie `langchain-dict-nested`
- Prompt sha256 `2241483a459c1737b34dccac72be2134b1f8ec84dbc4751e8ccdf8e46fb6fe2d`; dataset `eval/tasks/coding-router/dataset.tsv`, sha256 `f9845d928c2f105392672cae0c8a3572daaa02c6b85b5d2b8a58878cbc37d45a` (53 pytań)
- Commit repo `825c9b2`

## Wyniki

| Wariant | Model | Digest | Trafność (reguła Sardora) | Trafność (ścisła) | Odpowiedzi jednym słowem | Prośby o kod → sieć | Pytania KB → baza | Stabilność | Błędy |
|---|---|---|---|---|---|---|---|---|---|
| app (rag_llm_app.py) | gemma3:4b | `68ceab7e468a` | 64.2% | 64.2% | 100.0% | 21.7% | 95.0% | 100.0% | 0 |
| app (rag_llm_app.py) | qwen2.5-coder:14b | `9ec8897f747e` | 62.3% | 62.3% | 100.0% | 13.0% | 100.0% | 100.0% | 0 |
| app (rag_llm_app.py) | qwen2.5:14b | `7cdf5a0187d5` | 69.8% | 69.8% | 100.0% | 39.1% | 90.0% | 100.0% | 0 |
| app (rag_llm_app.py) | llama3.1:8b | `46e0c10c039e` | 66.0% | 62.9% | 96.9% | 21.7% | 100.0% | 100.0% | 0 |
| notebook (llm_RAG.ipynb) | gemma3:4b | `68ceab7e468a` | 71.7% | 71.7% | 100.0% | 34.8% | 100.0% | 100.0% | 0 |
| notebook (llm_RAG.ipynb) | qwen2.5-coder:14b | `9ec8897f747e` | 66.0% | 66.0% | 100.0% | 21.7% | 100.0% | 100.0% | 0 |
| notebook (llm_RAG.ipynb) | qwen2.5:14b | `7cdf5a0187d5` | 93.1% | 93.1% | 100.0% | 92.8% | 90.0% | 98.1% | 0 |
| notebook (llm_RAG.ipynb) | llama3.1:8b | `46e0c10c039e` | 62.3% | 58.5% | 96.2% | 17.4% | 95.0% | 100.0% | 0 |

## Trafność w kategoriach (reguła Sardora)

| Wariant | Model | code | kb | recent | sardor |
|---|---|---|---|---|---|
| app (rag_llm_app.py) | gemma3:4b | 25.0% | 95.0% | 100.0% | 0.0% |
| app (rag_llm_app.py) | qwen2.5-coder:14b | 15.0% | 100.0% | 100.0% | 0.0% |
| app (rag_llm_app.py) | qwen2.5:14b | 40.0% | 90.0% | 100.0% | 33.3% |
| app (rag_llm_app.py) | llama3.1:8b | 20.0% | 100.0% | 100.0% | 33.3% |
| notebook (llm_RAG.ipynb) | gemma3:4b | 35.0% | 100.0% | 100.0% | 33.3% |
| notebook (llm_RAG.ipynb) | qwen2.5-coder:14b | 15.0% | 100.0% | 100.0% | 66.7% |
| notebook (llm_RAG.ipynb) | qwen2.5:14b | 91.7% | 90.0% | 100.0% | 100.0% |
| notebook (llm_RAG.ipynb) | llama3.1:8b | 20.0% | 95.0% | 100.0% | 0.0% |

## Macierze pomyłek (wiersz: etykieta, kolumna: decyzja wg reguły Sardora)

**app (rag_llm_app.py) / gemma3:4b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 57 | 3 |
| web_search | 54 | 45 |

**app (rag_llm_app.py) / qwen2.5-coder:14b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 60 | 0 |
| web_search | 60 | 39 |

**app (rag_llm_app.py) / qwen2.5:14b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 54 | 6 |
| web_search | 42 | 57 |

**app (rag_llm_app.py) / llama3.1:8b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 60 | 0 |
| web_search | 54 | 45 |

**notebook (llm_RAG.ipynb) / gemma3:4b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 60 | 0 |
| web_search | 45 | 54 |

**notebook (llm_RAG.ipynb) / qwen2.5-coder:14b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 60 | 0 |
| web_search | 54 | 45 |

**notebook (llm_RAG.ipynb) / qwen2.5:14b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 54 | 6 |
| web_search | 5 | 94 |

**notebook (llm_RAG.ipynb) / llama3.1:8b**

| | vectorstore | web_search |
|---|---|---|
| vectorstore | 57 | 3 |
| web_search | 57 | 42 |

## Legenda

- Reguła Sardora: odpowiedź zawierająca „vectorstore” idzie do bazy, każda inna do sieci (dosłownie jak w `rag_llm_app.py`).
- Reguła ścisła: odpowiedź musi być dokładnie jednym z dwóch słów; inaczej `invalid`.
- Prośby o kod → sieć: kategorie `code` i `sardor`; to, czego chce prompt routera, ale też powód, dla którego baza ze stylem nie wpływa na generowany kod.
- Miary liczone na wywołaniach ze statusem `ok`; błędy (timeouty) liczone osobno.
