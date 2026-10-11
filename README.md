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

The prototype was written by Sardor Sheraliev in 2025 as his BSc diploma
project at Kozminski University, in the Diploma Workshop led by Karol
Chlasta, PhD, who also supervised the thesis. The original repository is
[ssheraliev/ml-dip-workshop](https://github.com/ssheraliev/ml-dip-workshop)
and its README is kept in `docs/original-README.md`. The design started
from LangChain's example
[Adaptive RAG using local LLMs](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_adaptive_rag_local.ipynb)
(same embeddings, vector store, web search tool and routing labels), with a
different knowledge base, a one-word router reply in place of JSON, and
without the example's document grader and query rewriter. The router
evaluation and further development are done as part of WarsawIQ's research,
and the project is now developed in the open.

## Open to the community

We publish this repository to open the project to anyone who wants to use it,
study it or build on it. The code is under the MIT licence and the questions
and results under CC BY 4.0, so commercial use, forks and derived research are
all allowed; we only ask for attribution and a citation of the paper.

Contributions are welcome. The paper found the one-word router to be the
weakest part of the assistant, so there is real work to do. Good places to
start:

- a routing method that brings the style guides onto the code path, or
  retrieves them for every code request, instead of offering them as an
  alternative;
- measuring the generated code with unit tests and a linter instead of the
  model's own statement that it follows the style guide;
- a classifier trained on labelled questions in place of the one-word prompt;
- more documents in the knowledge base (project documentation, internal code)
  and a different vector store;
- the evaluation repeated on other models, quantisations or Ollama versions,
  with the results sent back as a pull request (`eval/results/<task>/<date>/`,
  with the `run.json` the script writes);
- an editor integration in place of the Streamlit window.

Open an issue to discuss an idea, or send a pull request. Please keep the
evaluation reproducible: every new run should come with its `run.json`, and
every change to a prompt or to the dataset should be a separate commit.

## What is in the repository

| Path | What |
|---|---|
| `rag_llm_app.py` | the Streamlit application: router, knowledge-base chain, web-search chain |
| `llm_RAG.ipynb` | notebook that builds the ChromaDB index and holds a second version of the router prompt |
| `llm_app.py`, `proof_of_concept/` | earlier experiments without retrieval |
| `eval/` | router evaluation: scripts, the 53-question dataset, both prompts, results of 10 October 2026, tests (see `eval/README.md`) |
| `docs/` | the original README |

## Installation, step by step

Checked on 11 October 2026 on Linux with Python 3.13; the steps should work
the same on macOS and Windows. You need about 4 GB of disk for the model and the
embedding model, and a machine that can hold a 4B model in memory (8 GB of
RAM is enough; a GPU is not needed).

1. **Install Ollama** from [ollama.com/download](https://ollama.com/download)
   (Linux: `curl -fsSL https://ollama.com/install.sh | sh`) and pull the
   model the application uses:
   ```bash
   ollama pull gemma3        # Gemma 3 4B, Q4_K_M, 3.4 GB
   ollama list               # should show gemma3:latest
   ```
   Ollama runs as a service on `http://127.0.0.1:11434`; if it is not
   running, start it with `ollama serve`.

2. **Clone the repository and install the Python packages** into a virtual
   environment:
   ```bash
   git clone https://github.com/WarsawIQ/context-aware-code-weaver.git
   cd context-aware-code-weaver
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   `requirements.txt` pins the versions this was checked with. The
   `langchain-community` package prints a deprecation warning at import;
   it is harmless with these versions.

3. **Get a Tavily key** for the web search path. Sign up at
   [tavily.com](https://tavily.com/) (a free tier exists) and put the key
   where Streamlit reads secrets:
   ```bash
   mkdir -p .streamlit
   echo 'TAVILY_API_KEY = "tvly-..."' > .streamlit/secrets.toml
   ```
   Without the key the application still starts, but every question routed
   to web search gets a fixed "web search is disabled" reply. The file is
   listed in `.gitignore`, so the key is not committed.

4. **Build the knowledge base** once. The notebook downloads PEP 8, the
   Google Python Style Guide and the Rules of ML, splits them into 277
   chunks of 1,000 characters, embeds them locally with
   `nomic-embed-text-v1.5` (a 274 MB model, downloaded on first use into
   `~/.cache/gpt4all/`) and writes `chroma_db_nomic_v1_notebook_final/`
   (about 4 MB, also excluded by `.gitignore`). It takes about two minutes. Either open it in Jupyter and
   run the cells in order,
   ```bash
   jupyter notebook llm_RAG.ipynb
   ```
   or run it without a browser (the key can also be given as an
   environment variable, which the notebook picks up instead of asking):
   ```bash
   TAVILY_API_KEY="tvly-..." jupyter nbconvert --to notebook --execute \
     llm_RAG.ipynb --output executed.ipynb
   ```
   The last cells of the notebook send two test questions through the
   whole chain, so a working Ollama is needed at that point. Messages
   about `libllamamodel-mainline-cuda.so` mean only that no CUDA was
   found; the embeddings are computed on the CPU.

5. **Start the assistant:**
   ```bash
   streamlit run rag_llm_app.py
   ```
   and open [http://localhost:8501](http://localhost:8501). Try a style
   question, for example *Should I compare a value to None with == or with
   is?* (routed to the knowledge base), and a code request, for example
   *How to write Merge Sort Algorithm?* (routed to web search).

If the application reports `Vector store not found`, step 4 has not been
run in this directory; if it reports that it cannot connect to Ollama, see
step 1.

## Using it from Visual Studio Code

The prototype is a web application, so in VS Code it runs in a panel
rather than as an extension:

1. Open the repository folder in VS Code and select the `.venv`
   interpreter (`Python: Select Interpreter` in the Command Palette). The
   notebook from step 4 can be run in VS Code's notebook editor with that
   interpreter as the kernel.
2. In the integrated terminal run `streamlit run rag_llm_app.py`.
3. Open the Command Palette, choose `Simple Browser: Show` and enter
   `http://localhost:8501`. The chat window opens as an editor tab next to
   your code.

Code completion or inline chat inside the editor is not part of the
prototype. An editor integration (for example through
[Continue](https://github.com/continuedev/continue), which already talks to
Ollama) is on the list of contributions we would welcome.

## Evaluating the router

The router can be measured without the knowledge base or the web search. The
53 questions, the two prompt versions, the scoring rules and the results of
the run reported in the paper are in `eval/`, with instructions in
`eval/README.md`. In short:

```bash
ollama pull gemma3:4b
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:14b
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

## Related projects

Local, open-source coding assistants exist; none of them routes between a
curated knowledge base of style guides and a web search, or measures that
decision, which is what this repository adds.

- [Continue](https://github.com/continuedev/continue) (Apache-2.0): VS Code
  and JetBrains extension with local models through Ollama and context from
  documentation and the repository.
- [Tabby](https://github.com/TabbyML/tabby): self-hosted server that indexes
  repositories and serves completion and chat.
- [Twinny](https://github.com/twinnydotdev/twinny) (MIT): lightweight VS Code
  extension for Ollama and OpenAI-compatible backends.
- [PrivateGPT](https://github.com/zylon-ai/private-gpt) (Apache-2.0) and
  [Open WebUI](https://github.com/open-webui/open-webui): general local RAG
  applications with knowledge bases and web search.

Research on retrieval for code generation: DocPrompting (Zhou et al., ICLR
2023) retrieves documentation before generating; RepoCoder (Zhang et al.,
EMNLP 2023) retrieves from the repository; CodeRAG-Bench (Wang et al.,
Findings of NAACL 2025) finds that retrieval helps when the retrieved context
is good, which retrievers often fail to provide.

## Licence

Code: MIT (see `LICENSE`). Data and results: see `DATA-LICENSE.md`
(CC BY 4.0 for the authors' questions and the results; CoNaLa and RetrievalQA
excerpts under their MIT licences). The model weights are not part of this
repository and come with their own terms.
