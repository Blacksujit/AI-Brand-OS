import { Navigation } from "./components/Navigation";
import { Hero } from "./components/Hero";
import { Problem } from "./components/Problem";
import { Solution } from "./components/Solution";
import { ProductPreview } from "./components/ProductPreview";
import { Workflow } from "./components/Workflow";
import { FeatureGrid } from "./components/FeatureGrid";
import { WorkspacePreview } from "./components/WorkspacePreview";
import { WhyBrandOS } from "./components/WhyBrandOS";
import { Security } from "./components/Security";
import { Pricing } from "./components/Pricing";
import { FAQ } from "./components/FAQ";
import { Footer } from "./components/Footer";

function DotGrid() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0" aria-hidden="true">
      <svg className="w-full h-full opacity-[0.02]" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="landing-dot-grid" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
            <circle cx="6" cy="6" r="0.75" fill="currentColor" className="text-foreground" />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#landing-dot-grid)" />
      </svg>
    </div>
  );
}

function AmbientGlow() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
      <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-orange-500/5 blur-[120px]" />
      <div className="absolute top-[40%] right-[-10%] w-[400px] h-[400px] rounded-full bg-orange-500/3 blur-[80px]" />
      <div className="absolute bottom-[20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-orange-500/3 blur-[100px]" />
    </div>
  );
}

function SectionDivider() {
  return (
    <div className="max-w-7xl mx-auto px-4 lg:px-8" aria-hidden="true">
      <div className="h-px bg-gradient-to-r from-transparent via-border/30 to-transparent" />
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="relative min-h-dvh bg-background text-foreground">
      <DotGrid />
      <AmbientGlow />
      <Navigation />
      <main className="relative z-10">
        <Hero />
        <SectionDivider />
        <Problem direction="left" />
        <SectionDivider />
        <Solution direction="right" />
        <SectionDivider />
        <ProductPreview direction="up" />
        <SectionDivider />
        <Workflow direction="left" />
        <SectionDivider />
        <FeatureGrid />
        <SectionDivider />
        <WorkspacePreview direction="up" />
        <SectionDivider />
        <WhyBrandOS direction="left" />
        <SectionDivider />
        <Security direction="right" />
        <SectionDivider />
        <Pricing direction="up" />
        <SectionDivider />
        <FAQ direction="left" />
      </main>
      <Footer />
    </div>
  );
}
