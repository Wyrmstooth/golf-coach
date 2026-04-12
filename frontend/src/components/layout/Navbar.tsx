import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Camera, Home, LayoutDashboard, LogIn, LogOut, User } from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "../../store/authStore";

const navLinks = [
  { to: "/", label: "Home", icon: Home },
  { to: "/analyze", label: "Analyze", icon: Activity },
  { to: "/live", label: "Live", icon: Camera },
];

/* Inline golf ball SVG logo with dimple pattern */
function GolfBallLogo() {
  return (
    <motion.svg
      viewBox="0 0 36 36"
      className="w-9 h-9"
      whileHover={{ rotate: 360 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
    >
      <defs>
        <radialGradient id="ballGrad" cx="40%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="60%" stopColor="#f0f0e8" />
          <stop offset="100%" stopColor="#d4d4c8" />
        </radialGradient>
        <radialGradient id="ballGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#16a34a" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#16a34a" stopOpacity="0" />
        </radialGradient>
        <pattern id="dimples" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1" fill="rgba(0,0,0,0.06)" />
          <circle cx="6" cy="6" r="1" fill="rgba(0,0,0,0.06)" />
        </pattern>
      </defs>
      {/* Glow */}
      <circle cx="18" cy="18" r="17" fill="url(#ballGlow)" />
      {/* Ball body */}
      <circle cx="18" cy="18" r="14" fill="url(#ballGrad)" />
      {/* Dimples */}
      <circle cx="18" cy="18" r="13" fill="url(#dimples)" />
      {/* Highlight */}
      <ellipse cx="14" cy="13" rx="5" ry="3.5" fill="rgba(255,255,255,0.4)" transform="rotate(-20 14 13)" />
      {/* Shadow rim */}
      <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth="0.5" />
    </motion.svg>
  );
}

export default function Navbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const user   = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [profileOpen, setProfileOpen] = useState(false);

  function handleLogout() {
    logout();
    setProfileOpen(false);
    navigate("/");
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <GolfBallLogo />
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

          {/* Dashboard link when logged in */}
          {user && (
            <Link to="/dashboard">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.97 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  pathname === "/dashboard"
                    ? "bg-golf-green/20 text-golf-green border border-golf-green/30"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`}
              >
                <LayoutDashboard size={15} />
                Dashboard
              </motion.div>
            </Link>
          )}
        </div>

        {/* Auth */}
        <div className="flex items-center gap-2">
          {user ? (
            <div className="relative">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setProfileOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass border border-white/10 hover:border-white/20 transition-all"
              >
                <div className="w-6 h-6 rounded-lg bg-golf-green/20 flex items-center justify-center">
                  <span className="text-golf-green text-[10px] font-bold">
                    {user.avatar_initials ?? user.display_name.slice(0, 2).toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-white/70 font-medium max-w-[80px] truncate">
                  {user.display_name.split(" ")[0]}
                </span>
              </motion.button>

              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 4, scale: 0.97 }}
                    className="absolute right-0 top-full mt-2 w-44 glass rounded-xl border border-white/10 py-1 z-50 shadow-xl"
                  >
                    <Link
                      to="/profile"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <User size={13} /> Profile
                    </Link>
                    <Link
                      to="/dashboard"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <LayoutDashboard size={13} /> Dashboard
                    </Link>
                    <div className="border-t border-white/8 my-1" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-white/5 transition-colors"
                    >
                      <LogOut size={13} /> Sign out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link to="/login">
              <motion.div
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-golf-green/15 text-golf-green border border-golf-green/25 hover:bg-golf-green/25 transition-all"
              >
                <LogIn size={14} />
                Sign In
              </motion.div>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
