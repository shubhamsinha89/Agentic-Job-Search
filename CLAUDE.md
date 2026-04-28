# Agentic Job Search — Claude Code Instructions

## What this project does
Automated daily job search agent. Searches Indian job portals, scores results against a candidate resume, emails top 20 matches via Gmail MCP.

## Routine details
- **Routine ID:** trig_01TW4xC69XHmjgFZaHvcruy3
- **Schedule:** `0 5 * * *` (5:00 AM UTC = 9:00 PM PST daily)
- **Environment:** Shubham Sinha (env_01H5Utph82Vk59M1ufitKEaU)
- **Gmail MCP:** connector_uuid 2701e52f-b826-4aaf-8b25-11f2a97c98b0

## To update the routine prompt
1. Edit `resume/resume.md` and/or `config/search_config.yaml`
2. Run `python scripts/build_prompt.py` to regenerate `agent/generated_prompt.md`
3. Run `python scripts/deploy_routine.py` to push the update

## To create a new routine from scratch
Use `/schedule` in Claude Code and reference `agent/generated_prompt.md` for the prompt content.

## Portals that work best for automated search
- naukri.com — best results
- timesjobs.com — good for plant/manufacturing
- iimjobs.com — senior roles
- in.indeed.com — broad coverage
- shine.com — secondary

## Portals to avoid (block bots)
- linkedin.com/jobs — rate limited and blocks automated access
- foundit.in — inconsistent results
