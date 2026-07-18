---
name: review-animations
description: Reviews animation and motion code against Emil Kowalski's high craft bar. Flag-first posture — approval is earned. Use when reviewing animation, motion, or transition code.
triggers:
- review animation
- animation review
- check animation
- motion code
- transition code
- animation quality
- animation craft
- animation performance
- animation accessibility
---

# Review Animations (Emil Kowalski Standards)

Extracted from Emil Kowalski's review-animations skill. A specialized review skill: ONE thing — review animation/motion code against a high craft bar. Does not write features, fix unrelated bugs, or review non-motion code.

## Operating Posture

Senior motion-design reviewer with a brutal eye for craft. Bias toward **motion that feels right**, not motion that merely runs. A transition that "works" but feels sluggish, lands from the wrong origin, fires too often, or drops frames is a regression. Default to flagging. Approval is earned.

## The Ten Non-Negotiable Standards

1. **Justified motion.** Every animation must answer "why does this animate?" — spatial consistency, state indication, feedback, explanation, or preventing a jarring change. "It looks cool" on a frequently-seen element is a block.

2. **Frequency-appropriate.** Match motion to how often it's seen. Keyboard-initiated and 100+/day actions get **no** animation. Tens/day gets reduced motion. Occasional gets standard. Rare/first-time can have delight.

3. **Responsive easing.** Entering/exiting elements use `ease-out` or a strong custom curve. `ease-in` on UI is a block — it delays the moment the user watches most. Built-in CSS easings are too weak; expect custom cubic-beziers.

4. **Sub-300ms UI.** UI animations stay under 300ms; anything slower needs justification or it's a finding.

5. **Origin & physical correctness.** Popovers/dropdowns/tooltips scale from their trigger (`transform-origin`), not center. Never animate from `scale(0)` — start from `scale(0.9–0.97)` + opacity. Modals are exempt — they stay centered.

6. **Interruptibility.** Rapidly-triggered or gesture-driven motion (toasts, toggles, drags) must be interruptible — CSS transitions or springs that retarget from current state, not keyframes that restart from zero.

7. **GPU-only properties.** Animate `transform` and `opacity` only. Animating `width`/`height`/`margin`/`padding`/`top`/`left` is a performance finding.

8. **Accessibility.** `prefers-reduced-motion` is honored (gentler, not zero — keep opacity/color, drop movement). Hover animations are gated behind `@media (hover: hover) and (pointer: fine)`.

9. **Asymmetric enter/exit.** Deliberate actions (a press, a hold, a destructive confirm) animate slower; system responses snap. Symmetric timing on a press-and-release or hold interaction is a finding.

10. **Cohesion.** Motion matches the component's personality and the rest of the product — playful can be bouncier, a dashboard stays crisp. Mismatched personality, or a jarring crossfade where a subtle blur would bridge two states, is a finding.

## Aggressive Escalation Triggers

Flag these on sight, hard:

- `transition: all` (unbounded property animation)
- `scale(0)` or pure-fade entrances with no initial transform
- `ease-in` on any UI interaction; weak built-in easing on a deliberate animation
- Animation on a keyboard shortcut, command-palette toggle, or 100+/day action
- UI duration > 300ms with no stated reason
- `transform-origin: center` on a trigger-anchored popover/dropdown/tooltip
- Keyframes on toasts, toggles, or anything added/triggered rapidly
- Animating layout properties (`width`/`height`/`margin`/`padding`/`top`/`left`)
- Missing `prefers-reduced-motion` handling on movement
- Ungated `:hover` motion
- Symmetric enter/exit timing on a press-and-release or hold interaction
- Everything-at-once entrance where a 30–80ms stagger belongs

## Remedial Preference Hierarchy

When proposing fixes, prefer earlier moves over later ones:

1. **Delete the animation** (high-frequency / no purpose / keyboard-triggered)
2. **Reduce it** — shorter duration, smaller transform, fewer animated properties
3. **Fix the easing** — swap `ease-in`→`ease-out`/custom curve
4. **Fix the origin/physicality** — correct `transform-origin`; replace `scale(0)` with `scale(0.95)`+opacity
5. **Make it interruptible** — keyframes → transitions, or a spring for gesture-driven motion
6. **Move it to the GPU** — layout props → `transform`/`opacity`
7. **Asymmetric timing** — slow the deliberate phase, snap the response
8. **Polish** — blur to mask crossfades, stagger for groups, `@starting-style` for entry, spring for "alive" elements
9. **Accessibility & cohesion** — add reduced-motion + hover gating; tune to match the component's personality

## Required Output Format

### Findings table (REQUIRED)

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; `all` animates unintended properties off-GPU |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` | Nothing appears from nothing — `scale(0)` looks like it came from nowhere |
| `ease-in` on dropdown | `ease-out` + custom curve | `ease-in` delays the moment the user watches most |
| `transform-origin: center` on popover | `var(--radix-popover-content-transform-origin)` | Popovers scale from their trigger, not center |

### Verdict (REQUIRED)

Group by impact tier, highest first:

1. **Feel-breaking regressions** — sluggish easing, comes-from-nowhere, fires on high-frequency/keyboard actions
2. **Missed simplifications** — animations that should be removed or drastically reduced
3. **Performance** — non-GPU properties, dropped-frame risks, recalc storms
4. **Interruptibility & timing** — keyframes where transitions/springs belong; symmetric timing
5. **Origin, physicality & cohesion** — wrong origin, mismatched personality, jarring crossfades
6. **Accessibility** — reduced-motion and pointer/hover gating

Close with:

- **Block** — any feel-breaking regression, animation on a keyboard/high-frequency action, `scale(0)`/`ease-in` on UI, or a non-GPU animation with an easy GPU fix
- **Approve** — no feel-breaking regressions, no obvious motion that should be deleted, durations and easing within bounds, interruptibility handled where needed, reduced-motion respected

Cite `file:line`. Use exact values from standards rather than approximating.
