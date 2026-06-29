# Landing Page Design — BrandOS

> Phase: Design
> Status: Complete
> Target: Product Hunt Launch

## 1. User Journey

```
Visitor → Curiosity → Problem → Solution → Proof → Trust → How It Works → Features → Testimonials → Pricing → FAQ → CTA → Signup
```

### Journey Stages

| Stage | Section | Emotion | Goal |
|-------|---------|---------|------|
| Discovery | Hero | Curiosity | Stop scrolling in 3s |
| Empathy | Problem | Recognition | "That's me" |
| Hope | Solution | Interest | "This is different" |
| Evidence | ProductPreview | Excitement | "I want to use this" |
| Understanding | Workflow | Clarity | "I see how it works" |
| Validation | FeatureGrid | Confidence | "This solves my problems" |
| Trust | WhyBrandOS + Security | Assurance | "This is legitimate" |
| Decision | Pricing | Evaluation | "Is it worth it?" |
| Conviction | FAQ | Reassurance | "All my concerns addressed" |
| Action | CTA | Urgency | "Let me try it now" |

## 2. Information Architecture

```
Navigation (floating pill)
├── Logo + BrandOS
├── Features | How It Works | Pricing
└── Get Started (primary CTA)

Hero
├── Animated badge
├── Headline + subheadline
├── Dual CTAs (primary + secondary)
└── Trust indicators (GitHub, LangGraph, Privacy)

Social Proof
├── GitHub Stars (placeholder)
├── Posts Generated (placeholder)
├── Hours Saved (placeholder)
└── Active Developers (placeholder)

Problem
├── AlertTriangle icon
├── Headline
└── Four pain points

Solution
├── Headline + subheadline
└── 6 pillar cards (Research → Publish)

ProductPreview
├── Headline + subheadline
└── 5-tab interactive UI (Research, Knowledge, Hooks, Draft, Review)

Workflow
├── Headline + subheadline
└── 6-step horizontal flow (Research → Publish)

FeatureGrid
├── Headline
└── 4 outcome/feature cards

WorkspacePreview
├── Headline + subheadline
└── Full workspace screenshot/mockup

WhyBrandOS
├── Headline
└── 5 differentiator cards

Security
├── Headline + subheadline
└── 4 security cards

Pricing
├── Headline
└── 4 tiers (Free, Pro, Team, Enterprise)

FAQ
├── Headline
└── 6 accordion Q&As

CTA
├── Sparkles icon
├── Headline + subheadline
└── Primary button

Footer
├── Brand column + social icons
├── Product links
├── Company links
├── Legal links
└── Copyright + tech stack credit
```

## 3. Visual Language (Dark-First Mastercard)

### Color System

```
Background:       #141413 (Ink Black)
Surface:          #1A1A19 (Lifted Ink)
Surface hover:    #222221 (Subtle Ink)
Border:           rgba(243, 240, 238, 0.08)  (Cream at 8%)

Text primary:     #F3F0EE (Canvas Cream)
Text secondary:   rgba(243, 240, 238, 0.7)  (Cream at 70%)
Text muted:       rgba(243, 240, 238, 0.45) (Cream at 45%)

Primary:          #CF4500 (Signal Orange)
Primary hover:    #E04E00 (Brighter Orange)
Primary soft:     rgba(207, 69, 0, 0.1)

Accent:           #F37338 (Light Signal Orange)
Accent soft:      rgba(243, 115, 56, 0.08)

Destructive:      #CF4500 (same as primary, used for problem section)
Success:          #22C55E (Green for checks)
```

### Typography

```
H1 (Hero):        56-64px / weight 500 / -2% letter-spacing
H2 (Section):     36-42px / weight 500 / -2% letter-spacing
H3 (Card):        18-22px / weight 500 / -1% letter-spacing
Body:             16px / weight 450 / -1% letter-spacing
Small:            14px / weight 450 / normal letter-spacing
Eyebrow:          13px / weight 600 / +4% letter-spacing / uppercase
```

### Border Radius Scale

```
20px    — CTA buttons, card containers
40px    — Hero preview frame, large containers
999px   — Navigation pill, pill buttons
50%     — Icon containers, avatars
```

### Shadows

```
Level 0:  none (default canvas)
Level 1:  0px 4px 24px rgba(0, 0, 0, 0.25)  — floating nav, cards
Level 2:  0px 24px 48px rgba(0, 0, 0, 0.35) — elevated cards, modals
Level 3:  0px 70px 110px rgba(0, 0, 0, 0.5) — hero glow
```

### Glow Effect

```
Orange glow:  radial-gradient at center, rgba(207, 69, 0, 0.08) 0%, transparent 60%
```

## 4. Key Design Decisions

### 4.1 Dark-First Inversion
The Mastercard cream canvas (`#F3F0EE`) becomes text color. The Mastercard ink (`#141413`) becomes background. Signal orange remains the primary action color — more vibrant against dark than it is against cream.

### 4.2 Floating Nav Pill
Inverted from Mastercard: dark-translucent pill (`bg-background/95 backdrop-blur`) floating on dark background with orange accent on the Get Started button. Matches the existing component.

### 4.3 Gradient Hero Background
`bg-gradient-to-b from-background via-primary/5 to-background` creates a subtle orange wash at the hero center — a "warm glow" effect that signals the orange brand color without overwhelming.

### 4.4 Grid Structure
- 1-column (mobile) → 2-column (tablet) → 3-column (desktop) for card grids
- 1200px max-width container, centered
- 96px vertical section padding (desktop), 48px (mobile)
- 24-32px gap between cards

### 4.5 Motion Philosophy
- Page load: staggered entrance from bottom (hero first, then social proof)
- Scroll reveal: fade-up with `whileInView`, staggered per card
- Tab transitions: subtle cross-fade
- Hover: scale(1.02) on cards, opacity transitions on links
- Reduced motion: respect `prefers-reduced-motion`

## 5. Component Refinement Plan

| Component | Current | Target Improvement |
|-----------|---------|-------------------|
| Navigation | Complete | Add scroll-aware background opacity |
| Hero | Complete | Replace product preview placeholder with richer mockup |
| SocialProof | Placeholder values | Add animated counter (0 → N) or keep as-is |
| Problem | Complete | Add visual comparison (before/after) |
| Solution | Complete | Add hover lift effect on cards |
| ProductPreview | Placeholder tabs | Replace each tab panel with rich mock content |
| Workflow | Complete | Add connecting animated lines between steps |
| FeatureGrid | Complete | Add hover card lift effect |
| WorkspacePreview | Placeholder box | Build a CSS mockup of the workspace UI |
| WhyBrandOS | Complete | Add icon background color variation |
| Security | Complete | Minor polish |
| Pricing | Complete | Add hover lift effect |
| FAQ | Complete | Already has AnimatePresence — solid |
| CTA | Complete | Add subtle glow behind CTA |
| Footer | Complete | Minor polish |

## 6. Performance Targets

| Metric | Target |
|--------|--------|
| Lighthouse Performance | ≥ 95 |
| Lighthouse Accessibility | ≥ 95 |
| Lighthouse Best Practices | ≥ 95 |
| Lighthouse SEO | ≥ 95 |
| LCP | < 2.5s |
| FCP | < 1.5s |
| TTI | < 3.5s |
| JS Bundle | < 150 KB gzip |
