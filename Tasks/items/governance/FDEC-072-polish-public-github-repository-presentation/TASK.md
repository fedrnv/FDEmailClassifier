---
schema: fdtasks-spec/v3
id: FDEC-072
title: "Polish public GitHub repository presentation"
type: Task
area: governance
component: github-public-presentation
epic_id: FDEC-EPIC-D001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-001]
created_at: 2026-11-20T11:05:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Deliver a consistent, accurate public GitHub landing presentation for FDEmailClassifier."]
  packets: ["Update repository metadata, presentation assets and the public entry README as one coherent landing presentation."]
  independent_acceptance: false
  boundary_reason: "The About description, topics, social preview and entry README form one public first-impression contract."
---

# FDEC-072 — Polish public GitHub repository presentation

## Goal
Present FDEmailClassifier as an independent Apache-2.0-intended open-source project on GitHub, clearly differentiating **planned** from implemented functionality.

## Inputs and source baseline
Current public repository README, architecture/project plan, FDEC-EPIC-D001, current upstream FDTasks 5.6 contract. At execution readiness, pin upstream policy SHA and repository source revision, and confirm FDEC-001 licensing notices are complete before advertising Apache-2.0 as an active license.

## Scope and allowed paths
- GitHub repository About description, website and Topics through authorized metadata settings/API.
- `README.md` — public product overview, goals, key features (planned/current), architecture, quickstart availability, links to SDKs/docs and contribution/security/license links.
- `assets/github/social-preview.*` or `docs/assets/` — original social preview illustration (only if the design asset is available and rights cleared).
- Documentation files immediately supporting the landing content.
- English is canonical; avoid introducing misleading promised dates or accuracy claims.

## Expected GitHub metadata
- Description: `Open-source multilingual AI email classifier with Rust, Python, C and C++ SDKs. Local inference, privacy-first, Apache 2.0.`
- Website: `https://emailclassifier.fedrv.de` (mark site as planned until deployed).
- Topics: `rust`, `email-classification`, `machine-learning`, `qwen3`, `multilingual`, `python`, `cpp`, `privacy`, `apache-2-0`.
- Social preview: legible FDEmailClassifier identity and local/privacy-first nature, no third-party copyrighted branding.

## Non-goals
Implementation of classification, model training, SDK releases, production website deployment, public weight/dataset publication, license inference for third-party assets, repository-wide refactoring.

## Boundaries and compatibility
Public claims must reflect actual shipped capabilities. 119-language coverage is a **base-model scope / experimental project target**, not a verified accuracy claim. Retain third-party attribution, avoid linking to unreleased binaries as downloadable, and do not include private data/credentials.

## Failure and recovery
If GitHub settings or social image upload cannot be changed with available authorized tools, prepare the exact metadata/image and document the remaining manual step without marking it complete. Do not alter immutable task specs or release unverified assets.

## Ordered implementation packets
One cohesive presentation update: metadata, README and social preview, with consistent links/claims and focused validation.

## Readiness, impact and acceptance matrix
Policy: FDTasks v5.6; pin source hash at readiness admission. Risk: low for docs, medium for public factual accuracy. Paths: `README.md`, `assets/github/`, `docs/assets/`, authorized repository metadata only. Stop on unverified license/rights or unavailable permissions.

| AC ID | Observable criterion | Test level and scenario | Trusted command or manual steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | GitHub About and topics match the accepted public positioning | Metadata inspection | Open GitHub repo About and compare required description, URL and topics | Public repository | Accurate metadata visible |
| AC-02 | README describes mission, architecture, intended APIs, status, license and how to contribute | Docs inspection | Inspect README and check relative links locally | Local checkout | All entry links resolve; planned features marked planned |
| AC-03 | Social preview displays correctly and uses owned/cleared assets | Visual | Upload via GitHub Settings → General → Social preview and inspect generated card | Public GitHub UI | Preview legible and correct |
| AC-04 | No private data, unsupported accuracy claims or unreleased artifacts represented as available | Negative/content review | Scan docs/assets and review each public claim against repository release state | Local checkout | No misleading statements or secrets |

## Completion evidence and cleanup
Record source SHA, metadata snapshots, local link/lint commands, screenshot of preview if available and verification results. No implementation or acceptance is asserted by this task record.
