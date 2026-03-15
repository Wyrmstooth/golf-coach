import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Activity, Camera, FileText, Target, Zap, Award } from "lucide-react";
import PageWrapper from "../components/layout/PageWrapper";

const PHASES = ["Address", "Backswing", "Top", "Downswing", "Impact", "Follow Through"];

const STATS = [
  { value: "6", label: "Swing Phases", icon: Activity },
  { value: "15+", label: "Fault Detections", icon: Target },
  { value: "Real-time", label: "AI Feedback", icon: Zap },
  { value: "AI", label: "Report Generation", icon: FileText },
];

const FEATURES = [
  {
    icon: Activity,
    title: "Full Swing Analysis",
    desc: "Upload your golf video and get a deep biomechanical breakdown across all 6 swing phases with fault severity ratings.",
    color: "from-golf-green to-emerald-400",
  },
  {
    icon: Camera,
    title: "Live Feedback",
    desc: "Real-time posture correction using your webcam. Get instant guidance on your address position before you swing.",
    color: "from-blue-500 to-cyan-400",
  },
  {
    icon: FileText,
    title: "Detailed PDF Reports",
    desc: "Download a comprehensive multi-page PDF report with phase summaries, fault tables, and performance metrics.",
    color: "from-golf-gold to-amber-400",
  },
];

// Animated SVG golfer silhouette
function GolferSVG() {
  return (
    <motion.svg
      viewBox="0 0 200 320"
      className="w-48 h-auto drop-shadow-2xl"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      {/* Glow effect */}
      <defs>
        <radialGradient id="glowGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#16a34a" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#16a34a" stopOpacity="0" />
        </radialGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <ellipse cx="100" cy="310" rx="60" ry="8" fill="url(#glowGrad)" />

      {/* Body */}
      <motion.g
        filter="url(#glow)"
        animate={{ rotate: [-8, 8] }}
        transition={{ duration: 2, ease: "easeInOut", repeat: Infinity, repeatType: "reverse" }}
        style={{ transformOrigin: "100px 200px" }}
      >
        {/* Head */}
        <circle cx="100" cy="40" r="22" fill="#16a34a" />
        {/* Cap brim */}
        <rect x="78" y="22" width="44" height="10" rx="5" fill="#052e16" />
        {/* Torso */}
        <path d="M80 60 Q100 55 120 60 L125 160 L75 160 Z" fill="#16a34a" />
        {/* Left arm / club swing */}
        <line x1="80" y1="80" x2="30" y2="120" stroke="#16a34a" strokeWidth="10" strokeLinecap="round" />
        {/* Club shaft */}
        <line x1="30" y1="120" x2="10" y2="200" stroke="#ca8a04" strokeWidth="4" strokeLinecap="round" />
        {/* Club head */}
        <rect x="0" y="196" width="20" height="14" rx="4" fill="#ca8a04" />
        {/* Right arm */}
        <line x1="120" y1="80" x2="150" y2="110" stroke="#16a34a" strokeWidth="10" strokeLinecap="round" />
        {/* Left leg */}
        <line x1="88" y1="160" x2="80" y2="260" stroke="#052e16" strokeWidth="14" strokeLinecap="round" />
        {/* Right leg */}
        <line x1="112" y1="160" x2="120" y2="260" stroke="#052e16" strokeWidth="14" strokeLinecap="round" />
        {/* Left foot */}
        <ellipse cx="78" cy="264" rx="16" ry="6" fill="#052e16" />
        {/* Right foot */}
        <ellipse cx="122" cy="264" rx="16" ry="6" fill="#052e16" />
      </motion.g>

      {/* Trajectory arc */}
      <motion.path
        d="M 10 200 Q 80 80 190 60"
        fill="none"
        stroke="#ca8a04"
        strokeWidth="2"
        strokeDasharray="6 4"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeOut", repeat: Infinity, repeatDelay: 1 }}
        opacity={0.6}
      />
      {/* Ball */}
      <motion.circle
        cx="10"
        cy="200"
        r="5"
        fill="#ca8a04"
        animate={{ cx: [10, 190], cy: [200, 60] }}
        transition={{ duration: 2, ease: "easeOut", repeat: Infinity, repeatDelay: 1 }}
      />
    </motion.svg>
  );
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <PageWrapper>
      {/* Hero */}
      <section className="relative min-h-[92vh] flex items-center overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-golf-dark via-golf-navy to-golf-slate animate-gradient-bg bg-300% opacity-80" />
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage:
              "linear-gradient(#16a34a 1px, transparent 1px), linear-gradient(90deg, #16a34a 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        {/* Green glow orb */}
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-golf-green/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 w-64 h-64 bg-golf-gold/10 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-8"
          >
            <motion.div variants={itemVariants}>
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-green text-golf-green text-xs font-semibold tracking-widest uppercase mb-4">
                <Zap size={11} /> AI-Powered Golf Coach
              </span>
              <h1 className="font-display text-5xl lg:text-7xl font-extrabold leading-tight">
                Elevate Your
                <br />
                <span className="text-gradient">Golf Swing</span>
                <br />
                with AI
              </h1>
            </motion.div>

            <motion.p variants={itemVariants} className="text-lg text-white/60 leading-relaxed max-w-lg">
              Upload your swing video and receive instant AI-powered biomechanical analysis,
              fault detection across all 6 phases, performance predictions, and ball trajectory
              tracking — all in seconds.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: "0 0 30px rgba(22,163,74,0.5)" }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate("/analyze")}
                className="px-8 py-4 bg-golf-green text-white font-semibold rounded-xl shadow-glow hover:bg-green-500 transition-colors duration-200 text-base"
              >
                Analyze My Swing
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: "0 0 30px rgba(202,138,4,0.4)" }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate("/live")}
                className="px-8 py-4 glass border border-golf-gold/40 text-golf-gold font-semibold rounded-xl hover:bg-golf-gold/10 transition-all duration-200 text-base flex items-center gap-2"
              >
                <Camera size={18} /> Live Feedback
              </motion.button>
            </motion.div>

            {/* Phase pills */}
            <motion.div variants={itemVariants} className="flex flex-wrap gap-2 pt-2">
              {PHASES.map((p, i) => (
                <motion.span
                  key={p}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6 + i * 0.07 }}
                  className="px-3 py-1 glass rounded-full text-xs font-medium text-white/70"
                >
                  {p}
                </motion.span>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: Golfer animation */}
          <motion.div
            initial={{ opacity: 0, x: 60 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="flex justify-center items-center"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-golf-green/5 rounded-full blur-3xl scale-150" />
              <GolferSVG />
              {/* Floating metric cards */}
              <motion.div
                animate={{ y: [-4, 4] }}
                transition={{ duration: 2.5, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                className="absolute -left-16 top-8 glass px-3 py-2 rounded-lg text-xs shadow-xl"
              >
                <div className="text-golf-green font-bold text-sm">87/100</div>
                <div className="text-white/50">Swing Score</div>
              </motion.div>
              <motion.div
                animate={{ y: [4, -4] }}
                transition={{ duration: 2.8, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                className="absolute -right-16 bottom-16 glass px-3 py-2 rounded-lg text-xs shadow-xl"
              >
                <div className="text-golf-gold font-bold text-sm">214 yds</div>
                <div className="text-white/50">Distance</div>
              </motion.div>
              <motion.div
                animate={{ y: [-3, 3] }}
                transition={{ duration: 3.2, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                className="absolute -right-12 top-4 glass px-3 py-2 rounded-lg text-xs shadow-xl"
              >
                <div className="text-red-400 font-bold text-sm">2 Faults</div>
                <div className="text-white/50">Detected</div>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-white/30 text-xs"
          animate={{ y: [0, 6] }}
          transition={{ duration: 1.5, repeat: Infinity, repeatType: "reverse" }}
        >
          <div className="w-px h-8 bg-gradient-to-b from-transparent to-golf-green" />
          <span>Scroll</span>
        </motion.div>
      </section>

      {/* Stats strip */}
      <section className="py-10 border-y border-white/5 bg-white/2">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map(({ value, label, icon: Icon }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-4 glass rounded-xl px-5 py-4"
            >
              <div className="w-10 h-10 rounded-lg bg-golf-green/20 flex items-center justify-center flex-shrink-0">
                <Icon size={20} className="text-golf-green" />
              </div>
              <div>
                <div className="text-2xl font-display font-bold text-gradient">{value}</div>
                <div className="text-xs text-white/50">{label}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-4xl font-bold">
            Everything you need to{" "}
            <span className="text-gradient">improve your game</span>
          </h2>
          <p className="mt-4 text-white/50 max-w-xl mx-auto">
            Professional-grade golf analysis powered by computer vision and machine learning.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="glass rounded-2xl p-7 group cursor-default"
            >
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-5 shadow-glow group-hover:scale-110 transition-transform duration-200`}
              >
                <Icon size={22} className="text-white" />
              </div>
              <h3 className="font-display font-bold text-lg mb-2">{title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA banner */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto glass rounded-3xl p-12 text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-golf-green/10 to-golf-gold/5 rounded-3xl" />
          <Award size={40} className="text-golf-gold mx-auto mb-4 relative" />
          <h2 className="font-display text-3xl font-bold mb-3 relative">
            Ready to master your swing?
          </h2>
          <p className="text-white/60 mb-8 relative">
            Upload a video and get your full AI analysis report in under 2 minutes.
          </p>
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: "0 0 40px rgba(22,163,74,0.6)" }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate("/analyze")}
            className="relative px-10 py-4 bg-golf-green text-white font-bold rounded-xl text-lg shadow-glow"
          >
            Get Started Free
          </motion.button>
        </motion.div>
      </section>
    </PageWrapper>
  );
}
