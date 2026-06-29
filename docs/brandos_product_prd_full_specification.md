# Project PRD: BrandOS — AI Personal Brand Operating System

## 1. Product Vision
**BrandOS** is an AI Personal Brand Operating System designed for technical professionals (engineers, researchers, founders). It transforms raw engineering work into authentic technical authority by continuously learning from a user's GitHub repositories, portfolio, and learning notes.

**The Mission:** Turn today's work into tomorrow's reputation.

---

## 2. Target Audience
- **Software Engineers & AI Researchers:** Building in public but struggling with the "blank page" problem.
- **Technical Founders:** Need to maintain a high-authority presence without sacrificing engineering time.
- **Developer Advocates:** Looking for data-driven ways to align their content with real-world technical trends.

---

## 3. Core Product Pillars
1. **Knowledge-First AI:** Unlike generic wrappers, BrandOS anchors every generation in the user's actual codebase and documentation.
2. **Technical Authenticity:** Eliminates "AI flavor" by adopting the user's unique architectural reasoning and vocabulary.
3. **Strategic Research:** Automatically scans technical trends (GitHub, ArXiv, Tech Twitter) to suggest high-impact topics relevant to the user's work.

---

## 4. Key Features & Functional Requirements

### 4.1 Knowledge Engine (The Foundation)
- **Multi-Source Import:** Support for GitHub (OAuth), local PDF/Markdown uploads, and URL crawling (Portfolios).
- **Knowledge Graph:** Vectorize and map imported work to identify recurring themes and expertise areas.
- **Privacy First:** Local knowledge storage options and secure architecture for proprietary code.

### 4.2 AI Workspace (The Core Loop)
- **Research Summary:** A sidebar providing real-time technical context and trend alignment.
- **Explainable Hook Generation:** Suggests 3-5 distinct angles for any topic with reasoning based on user "knowledge hits."
- **Focus-First Editor:** A split-pane Markdown editor with high-fidelity technical previews.
- **AI Reviewer:** A secondary "editorial" layer that flags generic phrasing and suggests deeper technical trade-offs.

### 4.3 Style Engine
- **Voice Fingerprinting:** Analyzes previous writing to calculate a "Style Convergence %."
- **Persona Archetypes:** Toggle between "The Architect" (structural), "The Builder" (tutorial-heavy), and "The Researcher" (insight-driven).

---

## 5. Information Architecture
- **Marketing/Public:** Landing Page, Login, Registration.
- **Onboarding:** Welcome → Profile Setup → Knowledge Import → Style Selection.
- **App Shell:**
    - **Dashboard:** Daily brief, metrics, and trending topics.
    - **Content Library:** All drafts, revisions, and published items.
    - **Knowledge Base:** Management of connected sources and tags.
    - **Analytics:** Engagement metrics and style convergence tracking.
    - **Settings:** API keys, profile, and preferences.

---

## 6. Design Principles
- **Editorial Dark-First:** High-contrast, minimal, and professional. Use Ink Black (#131315) and Canvas Cream (#F3F0EE).
- **Handcrafted Precision:** Avoid generic dashboard templates. Use oversized radii (40px) and stadium shapes.
- **Whitespace as a Feature:** Generous breathing room (96px section padding) to reduce cognitive load.
- **Trust-Driven UX:** Every AI suggestion must be explainable ("Why this topic?").

---

## 7. Technical Stack
- **Frontend:** Next.js 14+ (App Router), React 19, Tailwind CSS.
- **UI Components:** shadcn/ui, Radix UI, Lucide Icons.
- **State/Data:** TanStack Query, Zustand.
- **Animation:** Framer Motion (subtle, state-driven transitions).
- **AI/LLM:** LangGraph for agentic workflows, ChromaDB for vector storage.

---

## 8. Success Metrics
- **Activation:** 1st draft generated within 5 minutes of onboarding.
- **Retention:** Weekly Style Convergence improvement.
- **Trust:** User "rating" of AI suggestions (aiming for 4.5/5 stars).
