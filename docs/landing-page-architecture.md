# BrandOS Landing Page — Information Architecture

## Component Hierarchy

```
landing/
├── page.tsx (main landing page)
├── components/
│   ├── Navigation.tsx (floating nav pill)
│   ├── Hero.tsx (headline, value prop, CTAs, product preview)
│   ├── SocialProof.tsx (metrics placeholder)
│   ├── Problem.tsx (why current AI tools fail)
│   ├── Solution.tsx (BrandOS introduction)
│   ├── ProductPreview.tsx (interactive mock workspace)
│   ├── Workflow.tsx (visual timeline)
│   ├── FeatureGrid.tsx (outcome-focused features)
│   ├── WorkspacePreview.tsx (desktop app preview)
│   ├── WhyBrandOS.tsx (differentiators)
│   ├── Security.tsx (trust indicators)
│   ├── Pricing.tsx (pricing preview)
│   ├── FAQ.tsx (common questions)
│   ├── CTA.tsx (final call to action)
│   └── Footer.tsx (site footer)
```

## Section Breakdown

### 1. Navigation
- Floating pill design (Mastercard-inspired)
- Logo left, links center, CTA right
- Sticky positioning
- Mobile responsive with hamburger menu

### 2. Hero Section
**Purpose:** Make visitor stop scrolling
**Elements:**
- Headline: "Turn Today's Work Into Tomorrow's Reputation"
- Subheadline: "The AI Personal Brand Operating System for technical professionals"
- Primary CTA: "Start Building Your AI Brand"
- Secondary CTA: "See How It Works"
- Product screenshot/animated preview
- Trust indicators (GitHub stars, tech stack badges)
- Dark background with subtle gradient

### 3. Social Proof
**Purpose:** Build credibility
**Elements:**
- GitHub Stars (placeholder)
- Posts Generated (placeholder)
- Hours Saved (placeholder)
- Active Developers (placeholder)
- Clean metric cards with icons

### 4. Problem Section
**Purpose:** Explain why current solutions fail
**Elements:**
- Headline: "Why AI Writing Tools Fail Technical Professionals"
- Pain points:
  - Generic content that lacks authenticity
  - No personal knowledge integration
  - No technical depth
  - Inconsistent voice
- Visual comparison (generic vs authentic)

### 5. Solution Section
**Purpose:** Introduce BrandOS approach
**Elements:**
- Headline: "Knowledge-First AI. Human-Reviewed Content."
- Core pillars:
  - Research (trend detection)
  - Knowledge (your expertise)
  - Reasoning (strategic thinking)
  - Writing (authentic voice)
  - Review (quality assurance)
  - Publish (multi-platform)

### 6. Interactive Product Preview
**Purpose:** Show the product in action
**Elements:**
- Mock workspace UI
- Interactive tabs showing:
  - Research panel
  - Knowledge base
  - Hook generation
  - Draft editor
  - AI review
- Animated transitions between states

### 7. Workflow Section
**Purpose:** Show the process visually
**Elements:**
- Visual timeline with arrows
- Steps: Research → Knowledge → Topic → Draft → Review → Publish
- Minimal text, focus on flow
- Animated progress indicators

### 8. Feature Grid
**Purpose:** Communicate outcomes, not features
**Elements:**
- Grid of feature cards
- Each card: outcome → feature
- Examples:
  - "Never wonder what to write" → Research Today's AI
  - "Write from your real experience" → Knowledge Engine
  - "Generate authentic technical posts" → Writing Assistant
  - "Improve clarity and originality" → Review AI

### 9. Workspace Preview
**Purpose:** Show the premium desktop experience
**Elements:**
- Full workspace screenshot
- Annotations showing:
  - Sidebar navigation
  - Research panel
  - Knowledge base
  - Editor
  - History
  - Quality score

### 10. Why BrandOS
**Purpose:** Differentiators
**Elements:**
- Knowledge-first AI
- Human review required
- No hallucinated experience
- Transparent reasoning
- Modern AI architecture (LangGraph)

### 11. Security Section
**Purpose:** Build trust with professional users
**Elements:**
- Privacy first
- Local knowledge storage
- Secure architecture
- Rate limiting
- Data ownership
- Security badges

### 12. Pricing Preview
**Purpose:** Show future pricing structure
**Elements:**
- Free tier (placeholder)
- Pro tier (placeholder)
- Team tier (placeholder)
- Enterprise tier (placeholder)
- Feature comparison table

### 13. FAQ
**Purpose:** Address common questions
**Elements:**
- Who is this for?
- How is it different from ChatGPT?
- How does the AI learn my voice?
- Do you auto-post to LinkedIn?
- Can I use my own writing samples?
- What data do you store?

### 14. Final CTA
**Purpose:** Drive conversion
**Elements:**
- Strong headline
- Single primary button
- No competing actions
- Minimal distraction

### 15. Footer
**Purpose:** Navigation and trust
**Elements:**
- Product links
- Company links
- Legal links
- Social links
- Copyright

## Design Principles

1. **Dark-first aesthetic** with high contrast
2. **Minimal, editorial design** with generous whitespace
3. **Typography-driven hierarchy** using Sofia Sans
4. **Subtle motion** using Framer Motion
5. **Performance-first** with lazy loading and code splitting
6. **Accessibility-first** with keyboard navigation and ARIA labels
7. **Mobile-responsive** with mobile-first approach

## Color Strategy

Adapt Mastercard colors for dark theme:
- Background: Dark ink (#141413)
- Text: Canvas cream (#F3F0EE)
- Primary: Signal orange (#CF4500) for CTAs
- Accent: Light signal orange (#F37338) for highlights
- Borders: Subtle opacity on ink black

## Typography Scale

- H1 (Hero): 64px / weight 500 / tight tracking
- H2 (Section): 48px / weight 500
- H3 (Card): 24px / weight 500
- Body: 16px / weight 450
- Small: 14px / weight 450

## Spacing System

- Base unit: 8px
- Section padding: 96px vertical (desktop), 48px (mobile)
- Card padding: 32px (desktop), 24px (mobile)
- Gap between elements: 24px, 32px, 48px

## Animation Strategy

- Page load: Fade in + slide up (staggered)
- Scroll reveal: Fade in elements as they enter viewport
- Hover: Subtle scale and color transitions
- Interactive preview: Smooth tab transitions with fade
- No excessive motion - keep it professional

## Performance Targets

- Lighthouse Performance: ≥95
- Lighthouse Accessibility: ≥95
- Lighthouse Best Practices: ≥95
- Lighthouse SEO: ≥95
- First Contentful Paint: <1.5s
- Largest Contentful Paint: <2.5s
- Time to Interactive: <3.5s
