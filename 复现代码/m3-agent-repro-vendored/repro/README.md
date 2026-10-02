# M3-Agent reproduction runner

This directory adds operational tooling around the upstream M3-Agent Control
evaluation. It does not change the default agent algorithm or its default
two-way tensor parallelism.

## One-time bootstrap

```bash
cd ~/projects/WXM/rsi/m3-agent-repro
bash repro/scripts/bootstrap_env.sh
python repro/scripts/download_artifacts.py --split both --download-model
```

The scripts default to the reachable Tsinghua PyPI mirror and `hf-mirror.com`.
Override them only when needed:

```bash
export M3_PIP_INDEX_URL='https://your-pypi-mirror/simple'
export HF_ENDPOINT='https://your-huggingface-endpoint'
```

## Azure configuration

Set these variables in the shell that will run evaluation; never commit their
values:

```bash
export AZURE_OPENAI_API_KEY='...'
export AZURE_OPENAI_ENDPOINT='https://...openai.azure.com/'
export AZURE_OPENAI_API_VERSION='2024-10-21'
export M3_AZURE_DEPLOYMENT='gpt-4o-2024-11-20'
```

The deployment defaults to the paper's evaluator name. A different deployment
is supported operationally but makes the result non-comparable to the paper.

For unattended runs on node01, the same keys may instead be placed in
`~/.config/m3-agent/azure.env` with mode `600`; the runner reads this file
without printing its values.

```bash
mkdir -p ~/.config/m3-agent
cp repro/azure.env.example ~/.config/m3-agent/azure.env
chmod 600 ~/.config/m3-agent/azure.env
# Edit the copied file locally; do not paste credentials into chat.
```

## Local smoke without API access

```bash
bash repro/scripts/run_preflight.sh local robot
bash repro/scripts/run_split.sh robot-smoke --generation-only
```

Generation-only mode verifies that the Control model loads and generates
answers, but skips both memory retrieval and GPT scoring. It is diagnostic only;
it does not reproduce the complete M3-Agent retrieval path.

`--skip-eval` skips only GPT judging. Normal memory retrieval still calls the
`text-embedding-3-large` embedding API, so it requires a compatible embedding
endpoint and configuration even when Azure judging is off.

Each run uses GPU 0/1 and creates exactly two final files in a new
`runs/<run-id>/` directory: `answers.jsonl` and `report.md`. The report combines
run metadata, relevant console output, answer coverage, errors, and per-type
completion. It does not report accuracy unless evaluator scores exist.

The smoke selector runs inside `control.py`; it chooses up to 10 QA records
across videos and question types without creating a separate annotation file.

Once the embedding API is available, run retrieval with
`bash repro/scripts/run_split.sh robot-smoke --skip-eval`. After the embedding
configuration and Azure GPT-4o judge are both ready, use `--with-eval` for the
paper-style scored run.

## GLM-adapted comparison (BigModel general API or Alibaba Model Studio)

The official graph has OpenAI 3072-dimensional text vectors. The alternate
embedding model must encode both graph text and retrieval queries; never mix
vectors from different models. BigModel uses `embedding-3`; Alibaba Model
Studio uses `text-embedding-v4` with explicit 2048 dimensions and a maximum
batch of 10 texts. Their graph copies are kept separately under
`data/memory_graphs_glm/` and `data/memory_graphs_bailian/`; official graphs
remain unchanged. BigModel Coding Plan quota cannot be used for this general
API workflow. Configure `~/.config/m3-agent/glm.env` from
`repro/glm.env.example` with mode `600` and fill the key locally. For Alibaba,
use a Beijing-region API key and activate `ZHIPU/GLM-5.3-Flash`. The example
uses the Beijing DashScope endpoint; a workspace-specific Beijing endpoint may
be used instead.

```bash
python repro/scripts/reembed_graphs.py --split robot --smoke-max-qas 10 --dry-run
python repro/scripts/reembed_graphs.py --split robot --smoke-max-qas 10
bash repro/scripts/run_split.sh robot-smoke --glm-embedding --skip-eval
bash repro/scripts/run_split.sh robot-smoke --glm-control --skip-eval
```

After the matched smoke tests, convert the remaining Robot graphs with
`python repro/scripts/reembed_graphs.py --split robot`; completed graph copies
are reused. For GLM judged results, add `--glm-eval` to either Control run.
These are GLM-adapted results; the original paper used OpenAI embeddings and
GPT-4o judging.

When Azure is configured, use `--with-eval` to call the configured GPT-4o
deployment. Paper targets are Robot 30.7% and Web 48.9% All accuracy, with a
target difference within +/-1.0 percentage point.
