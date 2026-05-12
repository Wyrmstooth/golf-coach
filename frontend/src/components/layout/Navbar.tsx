import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Camera, Home, LayoutDashboard, LogIn, LogOut, Menu, User, X, Shield } from "lucide-react";
import { useState, useEffect } from "react";
import { useAuthStore } from "../../store/authStore";

const navLinks = [
  { to: "/", label: "Home", icon: Home },
  { to: "/analyze", label: "Analyze", icon: Activity },
  { to: "/live", label: "Live", icon: Camera },
];

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
          <stop offset="60%" stopColor="#f5f5ee" />
          <stop offset="100%" stopColor="#dcdcc8" />
        </radialGradient>
        <radialGradient id="ballGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </radialGradient>
        <pattern id="dimples" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1" fill="rgba(0,0,0,0.05)" />
          <circle cx="6" cy="6" r="1" fill="rgba(0,0,0,0.05)" />
        </pattern>
      </defs>
      <circle cx="18" cy="18" r="17" fill="url(#ballGlow)" />
      <circle cx="18" cy="18" r="14" fill="url(#ballGrad)" />
      <circle cx="18" cy="18" r="13" fill="url(#dimples)" />
      <ellipse cx="14" cy="13" rx="5" ry="3.5" fill="rgba(255,255,255,0.45)" transform="rotate(-20 14 13)" />
      <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(0,0,0,0.07)" strokeWidth="0.5" />
    </motion.svg>
  );
}

export default function Navbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
    setProfileOpen(false);
  }, [pathname]);

  function handleLogout() {
    logout();
    setProfileOpen(false);
    setMobileOpen(false);
    navigate("/");
  }

  const isActive = (to: string) => pathname === to;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/[0.08]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group flex-shrink-0">
          <GolfBallLogo />
          <span className="font-display font-bold text-base sm:text-lg tracking-tight hidden xs:inline">
            Golf<span className="text-gradient">Coach</span>
            <span className="text-xs text-white/35 ml-1 font-normal">AI</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to}>
              <motion.div
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive(to)
                    ? "bg-golf-green/15 text-golf-green ring-1 ring-golf-green/25"
                    : "text-white/55 hover:text-white hover:bg-white/[0.06]"
                }`}
              >
                <Icon size={15} />
                {label}
              </motion.div>
            </Link>
          ))}

          {user && (
            <Link to="/dashboard">
              <motion.div
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive("/dashboard")
                    ? "bg-golf-green/15 text-golf-green ring-1 ring-golf-green/25"
                    : "text-white/55 hover:text-white hover:bg-white/[0.06]"
                }`}
              >
                <LayoutDashboard size={15} />
                Dashboard
              </motion.div>
            </Link>
          )}

          {user?.is_admin && (
            <Link to="/admin">
              <motion.div
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive("/admin")
                    ? "bg-red-500/10 text-red-400 ring-1 ring-red-500/15"
                    : "text-white/45 hover:text-red-400 hover:bg-red-500/5"
                }`}
              >
                <Shield size={15} />
                Admin
              </motion.div>
            </Link>
          )}
        </div>

        <div className="hidden md:flex items-center gap-2">
          {user ? (
            <div className="relative">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setProfileOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass border border-white/[0.10] hover:border-white/[0.18] transition-all"
              >
                <div className="w-7 h-7 rounded-lg bg-golf-green/15 ring-1 ring-golf-green/20 flex items-center justify-center">
                  <span className="text-golf-green text-[10px] font-bold">
                    {user.avatar_initials ?? user.display_name.slice(0, 2).toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-white/65 font-medium max-w-[80px] truncate">
                  {user.display_name.split(" ")[0]}
                </span>
              </motion.button>

              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 4, scale: 0.97 }}
                    className="absolute right-0 top-full mt-2 w-48 glass rounded-xl border border-white/[0.12] py-1.5 z-50 shadow-xl"
                  >
                    <Link
                      to="/profile"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-white/65 hover:text-white hover:bg-white/[0.06] transition-colors"
                    >
                      <User size={13} /> Profile
                    </Link>
                    <Link
                      to="/dashboard"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-white/65 hover:text-white hover:bg-white/[0.06] transition-colors"
                    >
                      <LayoutDashboard size={13} /> Dashboard
                    </Link>
                    <div className="border-t border-white/[0.08] my-1" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-white/[0.06] transition-colors"
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
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-golf-green/12 text-golf-green ring-1 ring-golf-green/20 hover:bg-golf-green/20 transition-all"
              >
                <LogIn size={14} />
                Sign In
              </motion.div>
            </Link>
          )}
        </div>

        <div className="md:hidden flex items-center gap-2">
          {user && (
            <div className="w-7 h-7 rounded-lg bg-golf-green/15 ring-1 ring-golf-green/20 flex items-center justify-center">
              <span className="text-golf-green text-[10px] font-bold">
                {user.avatar_initials ?? user.display_name.slice(0, 2).toUpperCase()}
              </span>
            </div>
          )}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setMobileOpen((o) => !o)}
            className="p-2 rounded-xl glass border border-white/[0.10] text-white/55 hover:text-white transition-colors"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </motion.button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden glass border-t border-white/[0.08] overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              {navLinks.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(to)
                      ? "bg-golf-green/15 text-golf-green ring-1 ring-golf-green/20"
                      : "text-white/55 hover:text-white hover:bg-white/[0.06]"
                  }`}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              ))}
              {user && (
                <>
                  <Link
                    to="/dashboard"
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      isActive("/dashboard")
                        ? "bg-golf-green/15 text-golf-green ring-1 ring-golf-green/20"
                        : "text-white/55 hover:text-white hover:bg-white/[0.06]"
                    }`}
                  >
                    <LayoutDashboard size={16} />
                    Dashboard
                  </Link>
                  <Link
                    to="/profile"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white/55 hover:text-white hover:bg-white/[0.06] transition-all"
                  >
                    <User size={16} />
                    Profile
                  </Link>
                </>
              )}
              {user?.is_admin && (
                <Link
                  to="/admin"
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive("/admin")
                      ? "bg-red-500/10 text-red-400 ring-1 ring-red-500/15"
                      : "text-white/45 hover:text-red-400 hover:bg-red-500/5"
                  }`}
                >
                  <Shield size={16} />
                  Admin Panel
                </Link>
              )}
              <div className="border-t border-white/[0.08] my-2" />
              {user ? (
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/5 transition-all"
                >
                  <LogOut size={16} />
                  Sign out
                </button>
              ) : (
                <Link
                  to="/login"
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold bg-golf-green/12 text-golf-green ring-1 ring-golf-green/20 transition-all"
                >
                  <LogIn size={16} />
                  Sign In
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
