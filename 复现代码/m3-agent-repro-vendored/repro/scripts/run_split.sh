#!/usr/bin/env bash
set -euo pipefail

SPLIT="${1:?Usage: run_split.sh robot-smoke|robot|web [--max-qas N] [--run-id ID] [--with-eval]}"
shift
case "${SPLIT}" in robot-smoke|robot|web) ;; *) echo "Invalid split: ${SPLIT}" >&2; exit 2;; esac

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${SPLIT}"
MAX_QAS=""
EVAL_MODE="skip"
GENERATION_ONLY=0
EMBEDDING_PROVIDER="azure"
CONTROL_PROVIDER="qwen"
while (($#)); do
  case "$1" in
    --run-id) RUN_ID="${2:?--run-id needs a value}"; shift 2 ;;
    --max-qas) MAX_QAS="${2:?--max-qas needs a number}"; shift 2 ;;
    --skip-eval) EVAL_MODE="skip"; shift ;;
    --with-eval) EVAL_MODE="azure"; shift ;;
    --glm-eval) EVAL_MODE="glm"; EMBEDDING_PROVIDER="glm"; shift ;;
    --generation-only) GENERATION_ONLY=1; EVAL_MODE="skip"; shift ;;
    --glm-embedding) EMBEDDING_PROVIDER="glm"; shift ;;
    --glm-control) CONTROL_PROVIDER="glm"; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ "${GENERATION_ONLY}" -eq 1 ]]; then EVAL_MODE="skip"; fi
if [[ "${CONTROL_PROVIDER}" == "glm" && "${GENERATION_ONLY}" -eq 0 ]]; then
  EMBEDDING_PROVIDER="glm"
fi
if [[ "${SPLIT}" == "robot-smoke" && -z "${MAX_QAS}" ]]; then MAX_QAS=10; fi
if [[ -n "${MAX_QAS}" && ! "${MAX_QAS}" =~ ^[1-9][0-9]*$ ]]; then echo "--max-qas must be a positive integer" >&2; exit 2; fi
if [[ ! "${RUN_ID}" =~ ^[A-Za-z0-9._-]+$ ]]; then echo "Invalid run ID" >&2; exit 2; fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="${ROOT}/runs/${RUN_ID}"
RESULTS="${RUN_DIR}/answers.jsonl"
REPORT="${RUN_DIR}/report.md"
LOG_TMP="${RUN_DIR}/.run-output.tmp"
DATASET="${SPLIT}"
if [[ "${SPLIT}" == "robot-smoke" ]]; then DATASET="robot"; fi
MODE="local-inference"
if [[ "${EVAL_MODE}" == "azure" ]]; then MODE="azure-evaluation"; fi
if [[ "${EMBEDDING_PROVIDER}" == "glm" && "${GENERATION_ONLY}" -eq 0 ]]; then MODE="glm-embedding-inference"; fi
if [[ "${CONTROL_PROVIDER}" == "glm" ]]; then MODE="glm-control-inference"; fi
if [[ "${EVAL_MODE}" == "glm" ]]; then MODE="glm-evaluation"; fi
if [[ "${GENERATION_ONLY}" -eq 1 ]]; then MODE="local-generation-only"; fi
if [[ "${EVAL_MODE}" == "azure" && ( "${EMBEDDING_PROVIDER}" == "glm" || "${CONTROL_PROVIDER}" == "glm" ) ]]; then
  echo "--with-eval currently supports only the original Azure/Qwen configuration" >&2
  exit 2
fi

source /home/hust/miniconda3/etc/profile.d/conda.sh
conda activate "${M3_CONDA_ENV:-m3-agent-repro}"
cd "${ROOT}"
export CUDA_VISIBLE_DEVICES="${M3_GPUS:-0,1}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export TOKENIZERS_PARALLELISM=false
export M3_TENSOR_PARALLEL_SIZE=2
export M3_EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER}"
export M3_CHECK_MAX_QAS="${MAX_QAS}"

test ! -e "${RUN_DIR}"
mkdir -p "${RUN_DIR}"
: >"${LOG_TMP}"
touch "${RESULTS}"
STARTED_EPOCH="$(date +%s)"

finish_run() {
  local exit_code=$?
  trap - EXIT
  set +e
  local summary_args=(
    --split "${SPLIT}" --results "${RESULTS}" --annotations "data/annotations/${DATASET}.json" \
    --report "${REPORT}" --run-id "${RUN_ID}" --mode "${MODE}" \
    --exit-code "${exit_code}" --started-epoch "${STARTED_EPOCH}" --log-file "${LOG_TMP}"
  )
  if [[ -n "${MAX_QAS}" ]]; then summary_args+=(--max-qas "${MAX_QAS}"); fi
  python repro/scripts/summarize_results.py "${summary_args[@]}" >>"${LOG_TMP}" 2>&1
  local report_code=$?
  rm -f "${LOG_TMP}" "${REPORT}.tmp"
  if [[ ${exit_code} -eq 0 && ${report_code} -ne 0 ]]; then exit_code=${report_code}; fi
  exit "${exit_code}"
}
trap finish_run EXIT

if [[ "${EMBEDDING_PROVIDER}" == "glm" && "${GENERATION_ONLY}" -eq 0 ]]; then
  bash repro/scripts/run_preflight.sh glm "${DATASET}" >>"${LOG_TMP}" 2>&1
elif [[ "${EVAL_MODE}" == "azure" ]]; then
  bash repro/scripts/run_preflight.sh azure "${DATASET}" >>"${LOG_TMP}" 2>&1
else
  bash repro/scripts/run_preflight.sh local "${DATASET}" >>"${LOG_TMP}" 2>&1
fi

ARGS=(--data_file "data/annotations/${DATASET}.json" --output_file "${RESULTS}")
ARGS+=(--control-provider "${CONTROL_PROVIDER}")
if [[ "${EVAL_MODE}" == "skip" ]]; then ARGS+=(--skip-eval); fi
if [[ "${EVAL_MODE}" == "glm" ]]; then ARGS+=(--eval-provider glm); fi
if [[ "${GENERATION_ONLY}" -eq 1 ]]; then ARGS+=(--skip-retrieval); fi
if [[ -n "${MAX_QAS}" ]]; then ARGS+=(--max-qas "${MAX_QAS}"); fi
timeout "${M3_RUN_TIMEOUT:-24h}" python m3_agent/control.py "${ARGS[@]}" >>"${LOG_TMP}" 2>&1
