import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Activity, Camera, FileText, Target, Zap, Award, TrendingUp, ShieldCheck } from "lucide-react";
import PageWrapper from "../components/layout/PageWrapper";

const PHASES = ["Address", "Backswing", "Top", "Downswing", "Impact", "Follow Through"];

const STATS = [
  { value: "6", label: "Swing Phases Analyzed", icon: Activity },
  { value: "15+", label: "Fault Detections", icon: Target },
  { value: "< 2 min", label: "Analysis Speed", icon: Zap },
  { value: "Full PDF", label: "AI Reports", icon: FileText },
];

const FEATURES = [
  {
    icon: Activity,
    title: "Full Swing Analysis",
    desc: "Upload your swing video and get a deep biomechanical breakdown across all 6 phases with fault severity ratings and fix suggestions.",
    color: "from-emerald-500 to-teal-500",
  },
  {
    icon: Camera,
    title: "Live Posture Feedback",
    desc: "Real-time posture correction using your webcam. Get instant audio and visual guidance on your address position before you swing.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: FileText,
    title: "Detailed PDF Reports",
    desc: "Download a comprehensive multi-page PDF with phase summaries, fault tables, performance predictions, and ball trajectory charts.",
    color: "from-amber-500 to-yellow-500",
  },
];

function AnimatedGolfer() {
  return (
    <motion.svg
      viewBox="0 0 200 340"
      className="w-56 h-auto drop-shadow-2xl"
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <defs>
        <radialGradient id="heroGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </radialGradient>
        <filter id="heroFilter">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="bodyFill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
      </defs>

      <ellipse cx="100" cy="330" rx="70" ry="8" fill="url(#heroGlow)" />

      <motion.g
        filter="url(#heroFilter)"
        animate={{ rotate: [-6, 6] }}
        transition={{ duration: 2.5, ease: "easeInOut", repeat: Infinity, repeatType: "reverse" }}
        style={{ transformOrigin: "100px 200px" }}
      >
        {/* Head */}
        <circle cx="100" cy="36" r="24" fill="url(#bodyFill)" />
        <rect x="76" y="16" width="48" height="12" rx="6" fill="#022c22" />

        {/* Torso */}
        <path d="M78 56 Q100 50 122 56 L127 170 L73 170 Z" fill="url(#bodyFill)" />

        {/* Left arm + club */}
        <line x1="78" y1="78" x2="26" y2="122" stroke="#10b981" strokeWidth="12" strokeLinecap="round" />
        <line x1="26" y1="122" x2="8" y2="210" stroke="#f59e0b" strokeWidth="5" strokeLinecap="round" />
        <rect x="-2" y="206" width="22" height="16" rx="5" fill="#f59e0b" />

        {/* Right arm */}
        <line x1="122" y1="78" x2="158" y2="112" stroke="#10b981" strokeWidth="12" strokeLinecap="round" />

        {/* Legs */}
        <line x1="86" y1="170" x2="78" y2="280" stroke="#022c22" strokeWidth="16" strokeLinecap="round" />
        <line x1="114" y1="170" x2="122" y2="280" stroke="#022c22" strokeWidth="16" strokeLinecap="round" />

        {/* Feet */}
        <ellipse cx="76" cy="284" rx="18" ry="7" fill="#022c22" />
        <ellipse cx="124" cy="284" rx="18" ry="7" fill="#022c22" />
      </motion.g>

      {/* Ball trajectory arc */}
      <motion.path
        d="M 8 210 Q 80 70 200 50"
        fill="none"
        stroke="#f59e0b"
        strokeWidth="2"
        strokeDasharray="8 5"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 0.5 }}
        transition={{ duration: 2.2, ease: "easeOut", repeat: Infinity, repeatDelay: 1.5 }}
      />

      {/* Flying ball */}
      <motion.circle
        cx="8" cy="210" r="7"
        fill="#fafaf5"
        stroke="#dcdcc8"
        strokeWidth="0.5"
        initial={{ cx: 8, cy: 210 }}
        animate={{ cx: [8, 200], cy: [210, 50] }}
        transition={{ duration: 2.2, ease: "easeOut", repeat: Infinity, repeatDelay: 1.5 }}
      />
    </motion.svg>
  );
}

function GrassStrip() {
  return (
    <div className="absolute bottom-0 left-0 right-0 overflow-hidden pointer-events-none">
      <motion.svg
        viewBox="0 0 1440 80"
        className="w-full h-16"
        preserveAspectRatio="none"
        animate={{ y: [0, -2, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      >
        <path d="M0 40 Q360 8 720 40 Q1080 72 1440 40 L1440 80 L0 80 Z" fill="#022c22" opacity="0.35" />
        <path d="M0 50 Q360 22 720 50 Q1080 78 1440 50 L1440 80 L0 80 Z" fill="#022c22" opacity="0.55" />
        <path d="M0 62 Q360 38 720 62 Q1080 82 1440 62 L1440 80 L0 80 Z" fill="#090d14" />
      </motion.svg>
    </div>
  );
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.10 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <PageWrapper>
      {/* ── HERO ── */}
      <section className="relative min-h-[95vh] flex items-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-golf-dark via-golf-navy to-golf-slate animate-gradient-bg bg-300% opacity-90" />

        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(#10b981 1px, transparent 1px), linear-gradient(90deg, #10b981 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        {/* Glowing orbs */}
        <div className="absolute top-1/3 right-[15%] w-[30rem] h-[30rem] bg-golf-green/[0.07] rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 left-[10%] w-[22rem] h-[22rem] bg-golf-gold/[0.06] rounded-full blur-3xl" />

        {/* Floating golf balls */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[
            { x: "12%", y: "18%", s: 16, delay: 0 },
            { x: "85%", y: "22%", s: 12, delay: 1.8 },
            { x: "70%", y: "75%", s: 14, delay: 3.2 },
            { x: "22%", y: "72%", s: 10, delay: 4.6 },
          ].map((p, i) => (
            <motion.div
              key={i}
              className="absolute"
              style={{ left: p.x, top: p.y }}
              animate={{ y: [0, -18, 0], opacity: [0.08, 0.2, 0.08] }}
              transition={{ duration: 6, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
            >
              <div className="golf-ball" style={{ width: p.s, height: p.s }} />
            </motion.div>
          ))}
        </div>

        <div className="relative max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text */}
          <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
            <motion.div variants={itemVariants}>
              <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass-green text-golf-green text-xs font-semibold tracking-widest uppercase mb-5">
                <Zap size={11} /> AI-Powered Golf Coach
              </span>
              <h1 className="font-display text-4xl sm:text-5xl lg:text-7xl font-extrabold leading-[1.05] tracking-tight">
                Perfect your
                <br />
                <span className="text-gradient">golf swing</span>
                <br />
                with AI
              </h1>
            </motion.div>

            <motion.p variants={itemVariants} className="text-base sm:text-lg text-white/55 leading-relaxed max-w-xl">
              Upload a video of your swing and receive an instant AI-powered biomechanical analysis
              covering all 6 phases, fault detection, performance predictions, and ball trajectory
              &mdash; in under two minutes.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-col xs:flex-row flex-wrap gap-3 sm:gap-4">
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: "0 0 36px rgba(16,185,129,0.45)" }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate("/analyze")}
                className="btn-primary text-base px-10 py-4"
              >
                Analyze My Swing
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: "0 0 28px rgba(245,158,11,0.3)" }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate("/live")}
                className="flex items-center gap-2 px-8 py-4 glass-gold text-golf-gold font-semibold rounded-xl transition-all duration-300 text-base"
              >
                <Camera size={18} /> Live Feedback
              </motion.button>
            </motion.div>

            <motion.div variants={itemVariants} className="flex flex-wrap gap-2 pt-1">
              {PHASES.map((p, i) => (
                <motion.span
                  key={p}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.06 }}
                  className="px-3 py-1.5 glass rounded-lg text-xs font-medium text-white/50"
                >
                  {p}
                </motion.span>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: Animated Golfer */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.15 }}
            className="flex justify-center items-center"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-golf-green/[0.04] rounded-full blur-3xl scale-150" />
              <AnimatedGolfer />

              {/* Floating metric cards */}
              <motion.div
                animate={{ y: [-5, 5] }}
                transition={{ duration: 2.8, repeat: Infinity, repeatType: "reverse" }}
                className="absolute -left-20 top-6 glass px-4 py-3 rounded-xl shadow-xl"
              >
                <div className="text-golf-green font-bold text-base">87/100</div>
                <div className="text-white/40 text-xs">Swing Score</div>
              </motion.div>
              <motion.div
                animate={{ y: [4, -4] }}
                transition={{ duration: 3.1, repeat: Infinity, repeatType: "reverse" }}
                className="absolute -right-20 bottom-20 glass px-4 py-3 rounded-xl shadow-xl"
              >
                <div className="text-golf-gold font-bold text-base">214 yds</div>
                <div className="text-white/40 text-xs">Distance</div>
              </motion.div>
              <motion.div
                animate={{ y: [-4, 4] }}
                transition={{ duration: 3.4, repeat: Infinity, repeatType: "reverse" }}
                className="absolute -right-16 top-4 glass px-4 py-3 rounded-xl shadow-xl"
              >
                <div className="text-red-400 font-bold text-base">2 Faults</div>
                <div className="text-white/40 text-xs">Detected</div>
              </motion.div>
            </div>
          </motion.div>
        </div>

        <GrassStrip />

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-24 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-white/25 text-xs"
          animate={{ y: [0, 6] }}
          transition={{ duration: 1.5, repeat: Infinity, repeatType: "reverse" }}
        >
          <div className="w-px h-8 bg-gradient-to-b from-transparent to-golf-green/60" />
          <span>Scroll to explore</span>
        </motion.div>
      </section>

      {/* ── STATS STRIP ── */}
      <section className="py-12 border-y border-white/[0.06] bg-white/[0.015]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map(({ value, label, icon: Icon }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="flex items-center gap-4 glass rounded-2xl px-5 py-4"
            >
              <div className="w-11 h-11 rounded-xl bg-golf-green/10 ring-1 ring-golf-green/20 flex items-center justify-center flex-shrink-0">
                <Icon size={20} className="text-golf-green" />
              </div>
              <div>
                <div className="text-2xl font-display font-bold text-gradient-subtle">{value}</div>
                <div className="text-xs text-white/40">{label}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-3xl sm:text-4xl font-bold">
            Everything you need to{" "}
            <span className="text-gradient">shoot lower scores</span>
          </h2>
          <p className="mt-4 text-white/45 max-w-xl mx-auto text-sm sm:text-base">
            Professional-grade swing analysis powered by computer vision and machine learning.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="glass rounded-2xl p-7 group cursor-default"
            >
              <div
                className={`w-13 h-13 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-5 shadow-glow group-hover:scale-110 transition-transform duration-200`}
              >
                <Icon size={22} className="text-white" />
              </div>
              <h3 className="font-display font-bold text-lg mb-2 text-white/90">{title}</h3>
              <p className="text-white/45 text-sm leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto glass rounded-3xl p-12 text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-golf-green/[0.08] to-golf-gold/[0.04] rounded-3xl" />
          <Award size={44} className="text-golf-gold mx-auto mb-5 relative" />
          <h2 className="font-display text-3xl sm:text-4xl font-bold mb-3 relative">
            Ready to transform your swing?
          </h2>
          <p className="text-white/50 mb-8 relative max-w-md mx-auto">
            Upload a video and get your full AI analysis report in under two minutes.
          </p>
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: "0 0 48px rgba(16,185,129,0.5)" }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate("/analyze")}
            className="relative btn-primary text-lg px-12 py-4 rounded-xl"
          >
            Get Started Free
          </motion.button>
        </motion.div>
      </section>
    </PageWrapper>
  );
}
