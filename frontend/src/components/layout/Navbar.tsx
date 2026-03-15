import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Camera, Home } from "lucide-react";

const navLinks = [
  { to: "/", label: "Home", icon: Home },
  { to: "/analyze", label: "Analyze", icon: Activity },
  { to: "/live", label: "Live", icon: Camera },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-golf-green to-golf-gold flex items-center justify-center shadow-glow group-hover:shadow-glow-gold transition-shadow duration-300">
            <span className="text-sm font-bold text-white">G</span>
          </div>
          <span className="font-display font-bold text-lg tracking-tight">
            Golf<span className="text-gradient">Coach</span>
            <span className="text-xs text-white/40 ml-1 font-normal">AI</span>
          </span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {navLinks.map(({ to, label, icon: Icon }) => {
            const active = pathname === to;
            return (
              <Link key={to} to={to}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.97 }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    active
                      ? "bg-golf-green/20 text-golf-green border border-golf-green/30"
                      : "text-white/60 hover:text-white hover:bg-white/5"
                  }`}
                >
                  <Icon size={15} />
                  {label}
                </motion.div>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
