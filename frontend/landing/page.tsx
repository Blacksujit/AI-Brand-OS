import { Navigation } from "./components/Navigation";
import { Hero } from "./components/Hero";
import { SocialProof } from "./components/SocialProof";
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
import { CTA } from "./components/CTA";
import { Footer } from "./components/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />
      <main>
        <Hero />
        <SocialProof />
        <Problem />
        <Solution />
        <ProductPreview />
        <Workflow />
        <FeatureGrid />
        <WorkspacePreview />
        <WhyBrandOS />
        <Security />
        <Pricing />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
