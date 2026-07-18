---
name: animation-vocabulary
description: Reverse-lookup glossary mapping vague design descriptions to precise animation terminology. When someone says "bouncy thing" or "that fadey thing", map it to the correct term and implementation.
triggers:
- animation
- animation name
- what animation
- which easing
- motion
- transition
- easing
- cubic-bezier
- spring
- bouncy
- fade in
- slide in
- pop in
- stagger
- scroll animation
- micro-interaction
---

# Animation Vocabulary (Reverse Lookup)

Extracted from Emil Kowalski's animation-vocabulary skill. Maps natural-language descriptions to precise animation terms.

## Searchable Glossary

### Entrances
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Pop in** | `scale(0.95)` → `scale(1)` + opacity fade | Buttons, tags, small UI elements appearing |
| **Fade in** | Opacity 0 → 1 only | Background content, subtle reveals |
| **Slide in** | `translateY(8px)` → `translateY(0)` + opacity | Cards, list items entering viewport |
| **Scale up** | `scale(0.9)` → `scale(1)` | Modals, dialogs, overlays |
| **Reveal** | Clip-path or mask animation exposing content | Text reveals, image masks |
| **Stagger** | Sequential entrance with 30-80ms delay between items | Lists, grids, multi-element reveals |
| **Spring entrance** | Physics-based overshoot + settle | Playful elements, toggles |

### Exits
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Fade out** | Opacity 1 → 0 | Background content disappearing |
| **Slide out** | Reverse of slide in | Cards leaving viewport |
| **Pop out** | Reverse of pop in | Small elements disappearing |
| **Collapse** | Height animation to 0 with opacity | Accordion closing, section hiding |
| **Dismiss** | Combined slide + fade with reduced opacity | Toasts, notifications |

### Interactions
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Press** | `scale(0.97)` on mousedown, `scale(1)` on release | Buttons, interactive elements |
| **Rubber-banding** | Overscroll with spring physics | iOS-style pull-to-refresh |
| **Drag** | Transform follows pointer with momentum | Draggable elements |
| **Scrub** | Animation progress tied to scroll position | Scroll-linked animations |
| **Hover lift** | `translateY(-2px)` + shadow increase | Cards, interactive surfaces |
| **Hover glow** | Subtle border or shadow color shift | Links, buttons |
| **Ripple** | Expanding circle from click point | Material-style buttons |

### Transitions
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Crossfade** | Opacity blend between two states | Image transitions, tab switches |
| **Morph** | Element shape/size animates between states | Shared element transitions |
| **Shared element** | Element appears to move between two positions | Page transitions, FAB→header |
| **Layout shift** | `layout` animation (FLIP) | Reordering, resizing |
| **Flip** | First-Last-Invert-Play technique | Position changes |

### Easing Curves
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Ease-out** | Fast start, decelerating end | Elements entering UI |
| **Ease-in** | Slow start, accelerating end | Elements leaving UI (avoid on enter) |
| **Ease-in-out** | Symmetric acceleration/deceleration | Neutral transitions |
| **Snap** | Very strong ease-out (cubic-bezier(0.2, 0, 0, 1)) | Fast, responsive feedback |
| **Bounce** | Spring with overshoot | Playful, lively elements |
| **Smooth** | Gentle ease-out (cubic-bezier(0.25, 0.1, 0.25, 1)) | Page transitions |
| **Linear** | Constant speed | Progress bars, loading spinners |

### Gestures
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Inertia** | Continued motion after release with deceleration | Scroll, swipe |
| **Snap back** | Spring return to original position | Pull-to-refresh, overscroll |
| **Follow finger** | Transform directly maps to pointer position | Drawers, sheets |

### Special
| Term | Description | Typical Use |
|------|-------------|-------------|
| **Shimmer** | Animated gradient placeholder | Loading skeletons |
| **Breathing** | Subtle scale pulse (1.0 → 1.02 → 1.0) | Attention indicator |
| **Wiggle** | Quick rotation oscillation | Error indication, attention |
| **Confetti** | Particle burst | Success, celebration |
| **Morph** | Shape A transitions to Shape B | Icon transitions, tab indicators |
| **Parallax** | Layers move at different speeds on scroll | Depth, hero sections |

## Quick Reference — "What should I use?"

- **"That bouncy thing"** → Pop in with spring easing or scale(0.95)→scale(1)
- **"Fadey thing"** → Simple fade in/out with opacity
- **"The slidey thing"** → Slide in with translateY(8px)→0 + opacity
- **"That wiggle"** → Quick rotation oscillation (error state)
- **"The loading thing"** → Shimmer animation on skeleton placeholder
- **"The thing that follows the mouse"** → Drag gesture with follow-finger transform
- **"Pop-up"** → Scale up from 0.9 with opacity fade
- **"Toast notification"** → Slide in from edge, auto-dismiss with fade out after delay
