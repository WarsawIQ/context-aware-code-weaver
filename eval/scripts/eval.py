#!/usr/bin/env python3
"""Ewaluacja jakosci: zadanie x modele x powtorzenia na lokalnej Ollamie.

Uzywa wylacznie biblioteki standardowej — zadnego venv. Nie dotyka uslugi
systemd: czyta /api/version i /api/tags, wysyla /api/generate.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evallib  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODELS = ["gemma3:4b", "qwen2.5-coder:14b", "qwen2.5:14b", "llama3.1:8b"]
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 256}
RESULT_COLUMNS = ["task", "model", "model_digest", "rep", "id", "category", "label",
                  "decision_sardor", "decision_strict", "latency_s", "status", "raw_output"]


def api(host, path, payload=None, timeout=30):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(host.rstrip("/") + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def installed_models(host):
    """Mapa nazwa -> digest z /api/tags; 'x:latest' dostepny tez jako 'x'."""
    out = {}
    for m in api(host, "/api/tags").get("models", []):
        out[m["name"]] = m.get("digest", "")
        if m["name"].endswith(":latest"):
            out[m["name"][: -len(":latest")]] = m.get("digest", "")
    return out


def generate(host, model, prompt, timeout):
    """Jedno wywolanie /api/generate. Zwraca (status, odpowiedz, czas_s)."""
    start = time.monotonic()
    try:
        resp = api(host, "/api/generate",
                   {"model": model, "prompt": prompt, "stream": False, "options": OPTIONS},
                   timeout=timeout)
        return "ok", resp.get("response", ""), time.monotonic() - start
    except TimeoutError:
        return "TIMEOUT", "", time.monotonic() - start
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            return "TIMEOUT", "", time.monotonic() - start
        return "ERROR", str(exc.reason), time.monotonic() - start


def repo_commit():
    try:
        return subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--task", default="coding-router")
    p.add_argument("--task-dir", help="katalog zadania (domyslnie tasks/<task>)")
    p.add_argument("--model", action="append", help="model; mozna podac wiele razy")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--quick", action="store_true", help="1 powtorzenie zamiast 3")
    p.add_argument("--host", default="http://127.0.0.1:11434")
    p.add_argument("--timeout", type=float, default=120.0, help="sekundy na jedno wywolanie")
    p.add_argument("--out", help="katalog wynikow (domyslnie results/<task>/<data-czas>)")
    args = p.parse_args()

    task_dir = args.task_dir or os.path.join(REPO, "tasks", args.task)
    models = args.model or DEFAULT_MODELS
    reps = 1 if args.quick else args.reps
    prompt_path = os.path.join(task_dir, "prompt.txt")
    template, meta = evallib.read_prompt(prompt_path)
    mode = meta.get("render", "plain")
    # Warianty promptu moga wskazac wspolny zbior pytan innego zadania.
    dataset_path = os.path.normpath(os.path.join(task_dir, meta.get("dataset", "dataset.tsv")))
    dataset = evallib.read_tsv(dataset_path)

    try:
        version = api(args.host, "/api/version").get("version", "?")
        have = installed_models(args.host)
    except (urllib.error.URLError, OSError) as exc:
        print(f"Ollama nie odpowiada na {args.host}: {exc}", file=sys.stderr)
        return 1
    missing = [m for m in models if m not in have]
    if missing:
        for m in missing:
            print(f"Brak modelu {m}. Sciagnij: ollama pull {m}", file=sys.stderr)
        return 2

    out_dir = args.out or os.path.join(
        REPO, "results", args.task, datetime.datetime.now().strftime("%Y-%m-%d-%H%M"))
    os.makedirs(out_dir, exist_ok=True)
    run = {
        "task": args.task, "label": meta.get("label", args.task),
        "started": now(), "finished": None,
        "ollama_version": version, "host": args.host,
        "models": {m: have[m] for m in models}, "options": OPTIONS, "reps": reps,
        "render": mode, "prompt_sha256": evallib.sha256_file(prompt_path),
        "dataset": os.path.relpath(dataset_path, REPO),
        "dataset_sha256": evallib.sha256_file(dataset_path), "dataset_rows": len(dataset),
        "repo_commit": repo_commit(),
    }
    run_path = os.path.join(out_dir, "run.json")
    with open(run_path, "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=2, ensure_ascii=False)

    with open(os.path.join(out_dir, "results.tsv"), "w", encoding="utf-8") as fh:
        fh.write("\t".join(RESULT_COLUMNS) + "\n")
        for model in models:
            for rep in range(1, reps + 1):
                for row in dataset:
                    prompt = evallib.render(template, row["question"], mode)
                    status, answer, secs = generate(args.host, model, prompt, args.timeout)
                    ok = status == "ok"
                    rec = {
                        "task": args.task, "model": model, "model_digest": have[model],
                        "rep": rep, "id": row["id"], "category": row["category"],
                        "label": row["label"],
                        "decision_sardor": evallib.score_sardor(answer) if ok else "",
                        "decision_strict": evallib.score_strict(answer) if ok else "",
                        "latency_s": f"{secs:.2f}", "status": status, "raw_output": answer,
                    }
                    fh.write("\t".join(evallib.esc(rec[c]) for c in RESULT_COLUMNS) + "\n")
                    fh.flush()
                    print(f"[{model} {rep}/{reps}] {row['id']}: "
                          f"{rec['decision_sardor'] or status} ({secs:.1f} s)", file=sys.stderr)

    run["finished"] = now()
    with open(run_path, "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=2, ensure_ascii=False)
    print(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
