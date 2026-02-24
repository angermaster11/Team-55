import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import FeaturesSection from "./components/FeaturesSection";
import HowItWorksSection from "./components/HowItWorksSection";
import LoginSection from "./components/LoginSection";
import FAQSection from "./components/FAQSection";
import CTASection from "./components/CTASection";
import Footer from "./components/Footer";

export default function App() {
  return (
    <div className="min-h-screen bg-base">
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <LoginSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </div>
  );
}
