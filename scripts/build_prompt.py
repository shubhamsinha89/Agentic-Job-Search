#!/usr/bin/env python3
"""
build_prompt.py
Generates the final agent prompt by combining:
  - resume/resume.md
  - config/search_config.yaml
  - agent/prompt_template.md

Output: agent/generated_prompt.md
Run:    python scripts/build_prompt.py
"""

import os
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_file(path: Path) -> str:
    if not path.exists():
        print(f"ERROR: {path} not found.")
        if "resume.md" in str(path):
            print("  -> Copy resume/resume_template.md to resume/resume.md and fill it in.")
        if "search_config.yaml" in str(path):
            print("  -> Copy config/search_config.example.yaml to config/search_config.yaml and fill it in.")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def build_location_scoring(locations: list) -> str:
    lines = []
    for loc in locations:
        kw = " / ".join(loc["keywords"][:3]) if loc["keywords"] else "Any other location"
        lines.append(f"- {kw}: {loc['score']} pts")
    return "\n".join(lines)


def build_industry_scoring(industries: list) -> str:
    return "\n".join(f"- {ind['name']}: {ind['score']} pts" for ind in industries)


def build_role_scoring(target_roles: list, role_max: int) -> str:
    lines = []
    for i, role in enumerate(target_roles[:6]):
        lines.append(f"- {role}: {max(role_max - i, role_max - 7)} pts")
    lines.append(f"- General / unspecified role: {max(role_max - 7, 5)} pts")
    return "\n".join(lines)


def build_search_queries(config: dict) -> str:
    portals = [p for p in config["portals"] if p.get("enabled", True)]
    roles = config["target_roles"]
    primary = " OR ".join([f'"{r}"' for r in roles[:3]])
    secondary = " OR ".join([f'"{r}"' for r in roles[3:6]])
    queries = []
    for i, portal in enumerate(portals[:6]):
        role_str = primary if i % 2 == 0 else secondary
        queries.append(f"{i + 1}. site:{portal['site']} {role_str} India")
    return "\n".join(queries)


def build_location_priority_list(locations: list) -> str:
    return " > ".join(loc["name"] for loc in locations if loc.get("keywords"))


def build_portals_list(portals: list) -> str:
    return " . ".join(p["name"].capitalize() for p in portals if p.get("enabled", True))


def build_target_roles_list(roles: list) -> str:
    return "\n".join(f"- {role}" for role in roles)


def main():
    print("Building agent prompt...")

    resume_content = load_file(ROOT / "resume" / "resume.md")
    config_raw = load_file(ROOT / "config" / "search_config.yaml")
    template = load_file(ROOT / "agent" / "prompt_template.md")

    config = yaml.safe_load(config_raw)
    scoring = config["scoring"]
    exp = config["experience"]
    candidate = config["candidate"]

    replacements = {
        "{{TOP_N}}": str(config["results"]["top_n"]),
        "{{EMAIL_RECIPIENT}}": config["email"]["recipient"],
        "{{RESUME_CONTENT}}": resume_content.strip(),
        "{{TARGET_ROLES_LIST}}": build_target_roles_list(config["target_roles"]),
        "{{MAX_PER_SEARCH}}": str(config["results"]["max_per_search"]),
        "{{SEARCH_QUERIES}}": build_search_queries(config),
        "{{TOTAL_MAX}}": str(scoring["total_max"]),
        "{{LOCATION_MAX}}": str(scoring["location_max"]),
        "{{ROLE_MAX}}": str(scoring["role_match_max"]),
        "{{INDUSTRY_MAX}}": str(scoring["industry_match_max"]),
        "{{EXPERIENCE_MAX}}": str(scoring["experience_fit_max"]),
        "{{FRESHNESS_MAX}}": str(scoring["freshness_max"]),
        "{{LOCATION_SCORING}}": build_location_scoring(config["locations"]),
        "{{ROLE_SCORING}}": build_role_scoring(config["target_roles"], scoring["role_match_max"]),
        "{{INDUSTRY_SCORING}}": build_industry_scoring(config["industries"]),
        "{{TARGET_MIN}}": str(exp["target_min"]),
        "{{TARGET_MAX}}": str(exp["target_max"]),
        "{{TARGET_MIN_MINUS2}}": str(exp["target_min"] - 2),
        "{{TARGET_MIN_MINUS4}}": str(exp["target_min"] - 4),
        "{{EXPERIENCE_MAX_MINUS1}}": str(scoring["experience_fit_max"] - 1),
        "{{EXPERIENCE_MAX_MINUS2}}": str(scoring["experience_fit_max"] - 2),
        "{{FRESHNESS_MAX_MINUS1}}": str(scoring["freshness_max"] - 1),
        "{{FRESHNESS_MAX_MINUS2}}": str(scoring["freshness_max"] - 2),
        "{{FRESHNESS_MAX_MINUS3}}": str(scoring["freshness_max"] - 3),
        "{{CANDIDATE_NAME}}": candidate["name"],
        "{{CANDIDATE_SUMMARY}}": (
            f"{exp['candidate_years']} yrs | " + " | ".join(config["target_roles"][:3])
        ),
        "{{PORTALS_LIST}}": build_portals_list(config["portals"]),
        "{{LOCATION_PRIORITY_LIST}}": build_location_priority_list(config["locations"]),
    }

    prompt = template
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Strip the template header (everything before first ---)
    lines = prompt.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == "---"), 0)
    prompt = "\n".join(lines[start + 1:]).strip()

    output_path = ROOT / "agent" / "generated_prompt.md"
    output_path.write_text(prompt, encoding="utf-8")

    print(f"Prompt written to: {output_path}")
    print(f"  Candidate  : {candidate['name']}")
    print(f"  Roles      : {len(config['target_roles'])} targets")
    print(f"  Portals    : {build_portals_list(config['portals'])}")
    print(f"  Email to   : {config['email']['recipient']}")
    print(f"  Top N      : {config['results']['top_n']} results")
    print()
    print("Next step: run  python scripts/deploy_routine.py")


if __name__ == "__main__":
    main()