# Context-Aware Code Weaver

A local retrieval-augmented assistant for Python and machine learning code.
It runs an open-weight model (Gemma 3 4B) through Ollama on the user's
machine. For each question a one-word routing prompt decides whether the
answer should come from a small knowledge base built from PEP 8, the Google
Python Style Guide and Google's Rules of Machine Learning (ChromaDB, local
embeddings), or from a web search (Tavily). Only the web search path sends
the question outside the machine.

This repository holds the prototype and the evaluation of its router
described in:

> Sheraliev, S., Chlasta, K.: Context-Aware Code Weaver: A Local
> Retrieval-Augmented Assistant for Python and Machine Learning Code.
> Submitted to MIDI 2026 (Machine Intelligence and Digital Interaction).

The prototype was written by Sardor Sheraliev as his BSc diploma project at
Kozminski University (2025, original repository:
[ssheraliev/ml-dip-workshop](https://github.com/ssheraliev/ml-dip-workshop),
original README in `docs/original-README.md`). The evaluation and the further
development are by Karol Chlasta (WarsawIQ).

## What is in the repository

| Path | What |
|---|---|
| `rag_llm_app.py` | the Streamlit application: router, knowledge-base chain, web-search chain |
| `llm_RAG.ipynb` | notebook that builds the ChromaDB index and holds a second version of the router prompt |
| `llm_app.py`, `proof_of_concept/` | earlier experiments without retrieval |
| `eval/` | router evaluation: scripts, the 53-question dataset, both prompts, results of 10 October 2026, tests (see `eval/README.md`) |
| `docs/` | the original README |

## Running the assistant

Prerequisites:

- Python 3.10 or newer and the packages the code imports: `streamlit`,
  `langchain-core`, `langchain-community`, `langchain-text-splitters`,
  `langchain-nomic`, `nomic[local]`, `chromadb`, `tavily-python`
  (`llm_app.py` also needs `langchain-ollama`). The original project did not
  record versions; the evaluation checked the prompt rendering against
  `langchain-core` 0.3.59.
- [Ollama](https://ollama.com/) with the default Gemma 3 tag: `ollama pull gemma3`
  (the 4B variant, Q4_K_M, 3.4 GB).
- A [Tavily](https://tavily.com/) API key. Without it the application starts,
  but every question routed to web search gets a fixed "web search is
  disabled" reply.

Steps:

1. Build the knowledge base once by running `llm_RAG.ipynb` up to the
   indexing cell. It downloads the three guides, splits them into chunks of
   1,000 characters (overlap 200), embeds them locally with
   `nomic-embed-text-v1.5` and writes `./chroma_db_nomic_v1_notebook_final/`.
2. Put the key in `.streamlit/secrets.toml`:
   ```toml
   TAVILY_API_KEY = "..."
   ```
3. Start the application:
   ```bash
   streamlit run rag_llm_app.py
   ```

Routing and answering use the same model at temperature 0. The knowledge-base
chain retrieves the three most similar chunks and is told to answer only from
them. The web chain receives Tavily's results (the code passes `k=3`, but the
LangChain tool has no such parameter and returns its default of up to five)
and a four-step prompt: intent, answer, style, insufficient information.

## Evaluating the router

The router can be measured without the knowledge base or the web search. The
53 questions, the two prompt versions, the scoring rules and the results of
the run reported in the paper are in `eval/`, with instructions in
`eval/README.md`. In short:

```bash
ollama pull gemma3:4b llama3.1:8b qwen2.5:14b qwen2.5-coder:14b
python3 eval/scripts/eval.py --task coding-router
python3 eval/scripts/eval.py --task coding-router-notebook
```

Main finding: questions about style and about current events are routed as
intended, but with the application prompt all four models send most code
requests to the knowledge base, against the prompt's own rule; only Qwen2.5
14B with the notebook prompt follows it (93.1% accuracy).

## Known limitations

- Scoring of retrieved passages (as in CRAG) and self-checking of answers
  (as in Self-RAG) are not implemented.
- Each question is sent to the model on its own; the chat history shown in
  the window is not passed to the model.
- The style guides reach the model only on the knowledge-base path, so they
  do not influence code generated on the web path.
- Only the router has been measured; the quality of the generated code has not.

## Licence

Code: MIT (see `LICENSE`). Data and results: see `DATA-LICENSE.md`
(CC BY 4.0 for the authors' questions and the results; CoNaLa and RetrievalQA
excerpts under their MIT licences). The model weights are not part of this
repository and come with their own terms.
