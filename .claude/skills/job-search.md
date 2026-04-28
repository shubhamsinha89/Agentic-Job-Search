---
name: job-search
description: Run the agentic job search — build prompt from resume + config, then deploy or trigger the Claude remote routine
---

Run the automated job search agent for this project.

## What this skill does
1. Reads `resume/resume.md` and `config/search_config.yaml`
2. Builds the agent prompt via `scripts/build_prompt.py`
3. Deploys or updates the Claude remote routine via `scripts/deploy_routine.py`

## Steps

### Build the prompt
```bash
python scripts/build_prompt.py
```
This generates `agent/generated_prompt.md`.

### Deploy the routine
```bash
python scripts/deploy_routine.py
```
This creates or updates the scheduled Claude remote routine using the generated prompt.

### Trigger a manual run
Use `/schedule` in Claude Code, select "Run now", and pick the `agentic-job-search-daily` routine.

## Customisation
- Edit `resume/resume.md` to update the candidate profile
- Edit `config/search_config.yaml` to change portals, locations, scoring, or email recipient
- Re-run `build_prompt.py` then `deploy_routine.py` after any change

## Routine details (current deployment)
- Routine ID: trig_01TW4xC69XHmjgFZaHvcruy3
- Schedule: 0 5 * * * (9:00 PM PST / 5:00 AM UTC daily)
- Gmail connector: 2701e52f-b826-4aaf-8b25-11f2a97c98b0
- Email: shivamsinha2189@gmail.com
- Manage at: https://claude.ai/code/routines/trig_01TW4xC69XHmjgFZaHvcruy3