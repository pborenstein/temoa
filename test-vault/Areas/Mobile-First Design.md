---
created: 2025-11-16
tags: [design, mobile, ux]
---

# Mobile-First Design

Design principle: If it doesn't work well on mobile, it doesn't work at all.

## Why Mobile-First

1. **Usage context**: Most spontaneous searches happen on mobile
2. **Constraints breed creativity**: Mobile limitations force simplicity
3. **Habit formation**: If tool is accessible anywhere, more likely to use it

## Key Constraints

- Small screen (320px - 428px width)
- Touch targets (min 44px for comfortable tapping)
- Variable network conditions
- Limited processing power
- One-handed use patterns

## Design Guidelines

### Performance
- Sub-2-second response time (or users abandon)
- Loading states for anything >500ms
- Optimistic UI updates where possible

### Layout
- Single column design
- Large touch targets (44px minimum)
- Clear visual hierarchy
- Minimal scrolling

### Input
- Avoid tiny form fields (causes zoom on iOS)
- `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Autofocus on primary input
- Enter key support

### Network
- Graceful degradation for slow connections
- Retry logic for failed requests
- Cache when possible

## Anti-Patterns

- Desktop-first design that "adapts" to mobile
- Tiny tap targets (<40px)
- Complex multi-step workflows
- Heavy JavaScript bundles
- Assuming fast wifi

## Examples

- [[Temoa]] - Search interface designed for mobile
- Google AMP (controversial but fast)
- Tailwind mobile utilities

## Resources

- [Apple HIG - iOS Design](https://developer.apple.com/design/human-interface-guidelines/ios)
- [Material Design - Mobile](https://material.io/design)
