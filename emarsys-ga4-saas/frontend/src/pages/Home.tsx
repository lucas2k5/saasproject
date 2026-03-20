import DashboardShowcase from "../components/landing/DashboardShowcase";
import Faq from "../components/landing/Faq";
import Features from "../components/landing/Features";
import Footer from "../components/landing/Footer";
import Hero from "../components/landing/Hero";
import HowItWorks from "../components/landing/HowItWorks";
import Integrations from "../components/landing/Integrations";
import Navbar from "../components/landing/Navbar";
import Pricing from "../components/landing/Pricing";
import RecommenderShowcase from "../components/landing/RecommenderShowcase";
import SocialProof from "../components/landing/SocialProof";

function Home() {
  return (
    <div className="min-h-screen bg-[#0b0c14] text-white">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),transparent_45%),radial-gradient(circle_at_right,_rgba(249,115,22,0.18),transparent_40%)]" />
      <Navbar />
      <main className="flex flex-col gap-24 px-4 pb-20 pt-10 sm:px-6 sm:pt-16 lg:px-8">
        <Hero />
        <Features />
        <RecommenderShowcase />
        <HowItWorks />
        <SocialProof />
        <DashboardShowcase />
        <Integrations />
        <Pricing />
        <Faq />
      </main>
      <Footer />
    </div>
  );
}

export default Home;
