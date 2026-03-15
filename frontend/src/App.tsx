import { Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Navbar from "./components/layout/Navbar";
import LandingPage from "./pages/LandingPage";
import AnalyzePage from "./pages/AnalyzePage";
import LivePage from "./pages/LivePage";

export default function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-golf-navy">
      <Navbar />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/live" element={<LivePage />} />
        </Routes>
      </AnimatePresence>
    </div>
  );
}
