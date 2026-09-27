# Dev Team — Specialist Overview

This directory contains the dev-team specialists for ${CIV_NAME}. They are spawned BY `dev-lead` (the team-lead at `.claude/team-leads/dev/manifest.md`) to handle engineering work.

**Do NOT spawn these specialists directly from Primary.** Always route through dev-lead so the team-lead can apply routing patterns + orchestration discipline.

## Roster

| Specialist | Domain |
|------------|--------|
| **cto** | Architecture decisions, ADRs, technical strategy |
| **full-stack-developer** | Frontend + backend feature implementation |
| **ai-ml-engineer** | ML model integration, AI feature implementation |
| **data-engineer** | Data pipelines, ETL, schema design |
| **data-scientist** | Analytics, statistical work, model evaluation |
| **devops-engineer** | CI/CD, deployment, container ops, infra automation |
| **qa-engineer** | Test strategy, test execution, regression coverage |
| **test-architect** | Test framework design, end-to-end test strategy |
| **security-engineer** | Threat modeling, security review |
| **security-engineer-tech** | Technical security implementation, hardening |
| **ui-ux-designer** | Interface design, user flows, accessibility |
| **pattern-detector** | Codebase pattern analysis, smell detection |
| **performance-optimizer** | Profiling, bottleneck identification |
| **refactoring-specialist** | Code health, debt reduction, refactor planning |

## Templates

`.claude/agents/dev-team/templates/` holds reusable spec templates (FEATURE-SPEC, API-SPEC, DESIGN-SPEC, DATA-PIPELINE-SPEC, SECURITY-ASSESSMENT, TEST-PLAN, BRAND-ASSETS-GUIDE) that specialists fill in for their work products.

## Mission Anchor

These specialists serve the ${CIV_NAME} mission per `MISSION.md`. They inherit the four anti-patterns the civilization defeats: no self-grading, no memo theater, no sandbagging, no post-compact laziness.
