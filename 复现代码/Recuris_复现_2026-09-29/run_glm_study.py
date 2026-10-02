import json, os, subprocess, sys
from pathlib import Path
base=Path('/home/hust/research_recuris')
root=base/'Recuris'
d={}
for line in Path('/home/hust/.config/m3-agent/bigmodel.env').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1); d[k.strip()]=v.strip().strip('"').strip("'")
env=os.environ.copy()
env.update({'OPENAI_API_KEY':d['GLM_API_KEY'],'OPENAI_BASE_URL':d['GLM_API_BASE_URL'],'OPENAI_API_BASE':d['GLM_API_BASE_URL'],'RECURIS_TAU2_REFERENCE_MODEL':d['GLM_CHAT_MODEL'],'TAU2_GATE_TERM':'1','TAU2_GATE_TERM_WM':'1','TAU2_STATUS_BOARD':'1','LITELLM_LOCAL_MODEL_COST_MAP':'True','RECURIS_META_MODEL':d['GLM_CHAT_MODEL'],'RECURIS_CLAUDE_BIN':str(base/'npm/node_modules/.bin/claude'),'PROXY_REASONING_EFFORT':'low'})
model='openai/'+d['GLM_CHAT_MODEL']
recuris=str(root/'.venv/bin/recuris')
arm=sys.argv[1]
if arm in ('bare','m0','champ'):
    cmd=[recuris,'tau2','--domain','retail','--agent','llm_agent' if arm=='bare' else 'recuris_agent','--agent-llm',model,'--user-llm',model,'--task-ids','5','6','--num-trials','1','--max-concurrency','1','--max-retries','0','--simulation-timeout','900','--save-to','glm_'+arm+'_pair_20260929']
    if arm=='m0': cmd += ['--skill-memory',str(base/'neutral_m0')]
    if arm=='champ': cmd += ['--skill-memory','tau2_retail']
elif arm=='discover':
    cmd=[recuris,'tau2','--domain','retail','--agent','llm_agent','--agent-llm',model,'--user-llm',model,'--task-ids','13','18','21','26','--num-trials','1','--max-concurrency','1','--max-retries','0','--simulation-timeout','900','--save-to','glm_discover_20260929']
elif arm=='evolve':
    cmd=[recuris,'metaagent','run','--domain','retail','--run-id','glm_retail_one_round_v5_20260929','--splits',str(base/'split_glm_one_round_41_k4.json'),'--reuse-artifacts-run','glm_retail_one_round_v2_20260929','--rounds','1','--k','4','--arm','autonomous','--base','neutral','--worker-model',d['GLM_CHAT_MODEL'],'--worker-reasoning','low','--simulator-model',d['GLM_CHAT_MODEL'],'--simulator-reasoning','low','--meta-model',d['GLM_CHAT_MODEL'],'--meta-reasoning','low','--round-gate','relaxed','--power-gate','off','--reg-cap','1','--meta-workflow','continuous','--max-concurrency','2','--max-sims','30','--proxy-port','4049','--cc-timeout','900']
else:
    raise SystemExit('unknown arm')
print('ARM',arm,'MODEL',model,'TASKS','5,6' if arm!='evolve' else 'train=41,76 dev=6',flush=True)
raise SystemExit(subprocess.call(cmd,cwd=root,env=env))
