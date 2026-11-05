---
name: design
description: "Use for frontend UI design review and refinement tasks: audit, critique, polish, harden, layout, typeset, colorize, clarify, or distill pages, components, dashboards, forms, landing pages, app shells, onboarding surfaces, and design systems. Covers UX quality, visual hierarchy, spacing, typography, color, accessibility, responsive behavior, i18n, error states, text overflow, edge cases, and production readiness. Not for backend-only work."
argument-hint: "[audit|critique|polish|harden|layout|typeset|colorize|clarify|distill] [target]"
user-invocable: true
allowed-tools:
  - Bash(npx impeccable *)
license: Apache-2.0. Adapted from pbakaus/impeccable, which is based on Anthropic's frontend-design skill. See NOTICE.md.
---

Frontend design review and refinement for production interfaces.

This skill vendors the focused review/refinement subset of `pbakaus/impeccable` under the easier name `design`. The underlying detector CLI is still `npx impeccable`; do not rename that package command.

## Invocation

Use one of these forms:

- Claude Code: `/design audit src/app`
- Codex: `$design audit src/app`
- Natural language: "Use design polish on this settings page."

The first word after `design` is the subcommand. If no subcommand is provided, show the command menu below and ask which pass the user wants.

## Setup

Before design work or file edits:

1. Run the context loader if this is the first design pass in the session:

   ```bash
   node .agents/skills/design/scripts/load-context.mjs
   ```

   Consume the full JSON output. Do not pipe it through `head`, `tail`, `grep`, or `jq`.
2. If `PRODUCT.md` or `DESIGN.md` exists, use it as context. If either is missing, proceed from the codebase and user request; do not block on creating new docs.
3. Identify the surface as either `brand` or `product`:
   - `brand`: marketing, landing, campaign, portfolio, content where design is the product.
   - `product`: apps, dashboards, tools, forms, settings, operational UI where design serves repeated use.
4. Load the matching register reference: [reference/brand.md](reference/brand.md) or [reference/product.md](reference/product.md).
5. If a subcommand is provided, load its reference file and follow it.

## Shared Rules

- Avoid generic AI-looking UI: gradient text, decorative glass cards, identical card grids, hero-metric templates, and category-reflex palettes.
- Do not default to dark or light mode by category. Choose from the actual usage scene.
- Use layout, type, spacing, color, and motion deliberately. No decoration that does not clarify or improve the experience.
- For product UI, prefer dense but calm, scannable, repeatable workflows over marketing composition.
- For brand UI, make the product, object, or offer visible in the first viewport and avoid generic decorative backgrounds.
- Treat text overflow, i18n, long labels, empty states, loading states, and error states as design requirements, not afterthoughts.
- Make findings concrete and actionable. For review passes, lead with issues and file references when available.

## Commands

| Command | Use When | Reference |
|---|---|---|
| `audit [target]` | Accessibility, performance, responsive behavior, theming, and technical design-quality checks | [reference/audit.md](reference/audit.md) |
| `critique [target]` | UX review, visual hierarchy, information architecture, cognitive load, and heuristic scoring | [reference/critique.md](reference/critique.md) |
| `polish [target]` | Final pass for alignment, spacing, consistency, and shipping-quality details | [reference/polish.md](reference/polish.md) |
| `harden [target]` | Error states, i18n, text overflow, real-world data, and edge-case resilience | [reference/harden.md](reference/harden.md) |
| `layout [target]` | Spacing, rhythm, alignment, composition, density, and hierarchy problems | [reference/layout.md](reference/layout.md) |
| `typeset [target]` | Typography, font choice, hierarchy, sizing, weight, and readability | [reference/typeset.md](reference/typeset.md) |
| `colorize [target]` | Gray, dull, or under-committed UI that needs strategic color | [reference/colorize.md](reference/colorize.md) |
| `clarify [target]` | UX copy, labels, instructions, empty states, and error messages | [reference/clarify.md](reference/clarify.md) |
| `distill [target]` | Simplifying, decluttering, removing noise, and focusing the UI | [reference/distill.md](reference/distill.md) |

## Routing

1. If the first word matches a command above, load that command's reference and use the rest of the prompt as the target.
2. If the first word does not match, treat the whole prompt as a general design request and choose the closest command. State the chosen command briefly.
3. Only recommend follow-up commands from the supported list above.
4. End heavy implementation passes with `polish` only when the user explicitly wants fixes applied after the initial review.

## Pin / Unpin

Pinned shortcuts are optional. They create lightweight skill aliases such as `audit` that redirect to `design audit`.

```bash
node .agents/skills/design/scripts/pin.mjs <pin|unpin> <command>
```

Valid commands are: `audit`, `critique`, `polish`, `harden`, `layout`, `typeset`, `colorize`, `clarify`, `distill`.
