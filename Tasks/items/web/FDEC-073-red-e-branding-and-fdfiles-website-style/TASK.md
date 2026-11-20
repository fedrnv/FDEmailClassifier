---
schema: fdtasks-spec/v3
id: FDEC-073
title: "Adopt red E branding and FDFiles visual language for the public website"
type: Task
area: web
component: public-information-website
epic_id: FDEC-EPIC-D009
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-058]
created_at: 2026-11-20T11:35:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Create the public website's consistent theme and branding layer using the official red E logo and FDFiles visual design as the reference."]
  packets: ["Implement cohesive design tokens, brand assets and visual application on the existing public website shell."]
  independent_acceptance: false
  boundary_reason: "Brand identity and visual tokens are one reusable website styling contract applied to the page shell."
---

# FDEC-073 — Red E logo and FDFiles website visual language

## Goal
Use the **red rounded-square E** as the official FDEmailClassifier logo and style the information site at **https://emailclassifier.fedrv.de** consistently with **https://files.fedrv.de**. This is a visual-family reference, not a mandate to copy private FDFiles code or proprietary assets.

## Inputs and source baseline
- Existing SVG assets: `assets/branding/logo-red-light.svg` and `assets/branding/logo-red-dark.svg`.
- Source of visual reference: `https://files.fedrv.de` (inspect current desktop/mobile appearance during implementation); if not publicly accessible, obtain authorized screenshots or reusable styling specification before dispatch. Do not invent unverified color, font or layout measurements.
- Related task: FDEC-058 (homepage), FDEC-072 (GitHub presentation) for brand consistency.
- FDTasks v5.6 policy, with source SHA and current project revision pinned at readiness.

## Scope and allowed paths
- `website/src/`, `website/public/`, `website/styles/`: theme variables, header/navigation, buttons, cards, sections, spacing, typography and dark/light styling consistent with FDFiles visual identity.
- `assets/branding/`: reuse official red logo variants as source assets (do not replace with another color).
- `docs/branding/`: public design tokens/brand usage and accessibility guidance, with no private code/assets.

## Required visual rules
1. **Official logo:** uppercase white `E` on red, rounded-square tile, using existing `logo-red-light.svg` and `logo-red-dark.svg`; ensure favicon, site header, Open Graph/social preview and mobile app/site icon derive from this approved red mark. Light/dark variants chosen appropriately.
2. **FDFiles style continuity:** inspect `files.fedrv.de` and reproduce its general page structure, typography scale, spacing rhythm, button/card shapes, navigation, responsive breakpoints, light/dark theme behavior and interaction feel where applicable. Use a reusable token/theme system rather than one-off CSS. Project identity remains **FDEmailClassifier**; primary branding accent is red.
3. **Accessibility:** readable contrasts, keyboard focus, semantic headings, prefers-reduced-motion, responsive mobile/tablet/desktop; both themes visually inspected.
4. **Public licensing:** use only independent original implementations or demonstrably reusable assets; never copy private FDFiles source, private screenshots, secrets or third-party branding into an Apache-2.0 public repository without confirmed authorization.
5. **Accuracy:** no presentation implies classifier features, supported-language performance or website functions are already released before verification.

## Non-goals
New classification functionality, training, backend or release automation, redesigning FDFiles itself, deployment, transfer of FDFiles private source/assets or unrelated GitHub metadata tasks.

## Boundaries and compatibility
Keep site static and portable. Preserve existing planned SDK/API documentation routes, links and accessibility. Avoid design drift across light/dark and mobile layouts. The red E logo is the canonical default, whereas other SVG colors remain optional branding resources, not default site choices.

## Failure and recovery
If reference site cannot be inspected, record a blocker and request authorized visual references at task execution; do not claim pixel-accurate match. If an asset fails contrast or renders incorrectly, retain previous accessible site version. Do not commit private design materials.

## Ordered implementation packets
One cohesive styling/branding result: brand assets + website design tokens + application to common public page shell.

## Readiness, impact and acceptance matrix
Policy: FDTasks v5.6; source-bound readiness and local commands at dispatch. Risk: medium (public identity/accessibility). Scope: website styling, shared public red SVG, brand guidance. Stop on missing reference/rights, failing responsive or accessibility checks.

| AC ID | Observable criterion | Test level/scenario | Trusted command or manual steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Website uses red E consistently in both themes, favicon, header and preview | Visual/local build | Run local static-site preview; inspect icons and metadata on light/dark desktop/mobile | Local website preview | Correct red E brand asset in each placement, no obsolete default-color logo |
| AC-02 | Website resembles the visible design language of files.fedrv.de | Visual comparison | Compare authorized reference screenshots/site with site desktop/mobile light/dark; document reusable tokens | Reference site and local preview | Consistent navigation, typography rhythm, spacing, shapes and interaction feel while retaining project identity |
| AC-03 | Contrast, focus and responsive layout meet accessibility standards | UI/manual and automated checks | Run local accessibility audit and keyboard/mobile inspection, capturing actual commands/screenshots | Local page snapshots | No critical accessibility failures or clipped/overlapping elements |
| AC-04 | Published design tokens/assets have acceptable IP provenance and do not expose private files | Security/license inspection | Review git diff, dependency assets, links and provenance | Public checkout | No private source, secrets or unlicensed copied assets |

## Completion evidence and cleanup
Store exact source and policy SHA, local commands/results, reference comparison screenshots or explicit unavailability, license checks and cleanup. Planned task is not evidence of completed work.
