# Data licence

The code in this repository is under the MIT licence (see `LICENSE`). The data
files are licensed separately, as listed below.

| Files | Licence | Source |
|---|---|---|
| `eval/tasks/coding-router/kb-questions.tsv` (20 questions about Python style and ML practice, each tied to a section of PEP 8, the Google Python Style Guide or Google's Rules of Machine Learning) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode) | written by the authors of this repository |
| `eval/tasks/coding-router/sardor-questions.tsv` (3 code requests) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode) | test queries from `llm_RAG.ipynb` and from Sardor Sheraliev's diploma thesis |
| `eval/tasks/coding-router/sources/conala-curated-test.jsonl` and the 20 `code-*` rows of `dataset.tsv` | MIT | CoNaLa, `curated/test` split, field `intent` (Stack Overflow question titles). Yin, P., Deng, B., Chen, E., Vasilescu, B., Neubig, G.: Learning to mine aligned code and natural language pairs from Stack Overflow. MSR 2018. https://huggingface.co/datasets/neulab/conala |
| `eval/tasks/coding-router/sources/retrievalqa-recent.jsonl` and the 10 `recent-*` rows of `dataset.tsv` | MIT | RetrievalQA, rows with `data_source` in {freshqa, realtimeqa} and `param_knowledge_answerable = 0`. Zhang, Z., Fang, M., Chen, L.: RetrievalQA: Assessing adaptive retrieval-augmented generation for short-form open-domain question answering. Findings of ACL 2024. https://github.com/hyintell/RetrievalQA |
| `eval/results/**` (model replies, decisions, timings and reports from the runs of 10 October 2026) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode) | produced by the authors of this repository |

When you use the questions or the results, please cite the paper listed in
`README.md` and the original datasets above.

The language models used in the evaluation are not part of this repository.
Their weights are downloaded through Ollama and come with their own terms:
Gemma 3 (Google's Gemma Terms of Use), Llama 3.1 (Llama 3.1 Community
License), Qwen2.5 and Qwen2.5-Coder (Apache 2.0).
