# 19. Accessibility and Localization

## Assessment

**CONFIRMED.** Keyboard-first operation, CJK IME-safe sending, labeled transfer-review controls, non-color status cues, Taiwan Traditional Chinese copy, contrast, responsive geometry, and reduced-motion behavior form the active accessibility contract.

## Required Coverage

- Keyboard shortcuts, CJK IME, transfer-review focus entry and return, accessible labels, non-color status, Traditional Chinese copy, contrast, reduced motion, responsive geometry, and field-review gates.

## Detailed Findings

### Keyboard, language, and status communication

**CONFIRMED.** Keyboard entry reaches repository search, thread search, composer, send/queue, Stop, inspector, and settings actions. Enter-to-send respects active CJK input-method composition, while Shift+Enter retains multiline input. Controls carry accessible names and focus behavior; state combines text, iconography, and shape so color is supplementary. Taiwan-facing product copy uses Taiwan Traditional Chinese service terms. The Live transfer review starts on the safe return action, preserves logical tab order, restores focus, and keeps full-transcript acknowledgement reachable at 1024×768.

### Visual and motion controls

**CONFIRMED.** Central tokens govern contrast, spacing, typography, focus rings, minimum target size, and reduced-motion behavior across responsive geometries. The transfer-review evidence adds ten native states, explicit blocked text, collapsed technical disclosure, and non-modal Demo local-only presentation. The operator references are `docs/agent-workspace/keyboard-shortcuts.md` and `docs/agent-workspace/ux-redesign/08-accessibility-plan.md`.

**PARTIALLY VERIFIED.** Offscreen keyboard, focus, IME, label, and geometry checks are recorded. Screen-reader, switch-control, high-contrast desktop-theme, and assistive-technology field review remain the next validation layer.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../validation/ui-redesign-validation-report.md`, `transfer-review-visual-review.md`, and the source keyboard and accessibility guides.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
