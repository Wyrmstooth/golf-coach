import { motion } from "framer-motion";
import { CheckCircle, Circle } from "lucide-react";

interface Props {
  status: "pending" | "running" | "done" | "error" | string;
  progress: number;
}

const STEPS = [
  { label: "Uploading video", threshold: 5, icon: "🏌️" },
  { label: "Detecting pose landmarks", threshold: 20, icon: "🦴" },
  { label: "Analyzing swing phases", threshold: 40, icon: "🔄" },
  { label: "Identifying faults", threshold: 60, icon: "🎯" },
  { label: "Predicting performance", threshold: 75, icon: "📊" },
  { label: "Ball tracking", threshold: 88, icon: "⛳" },
  { label: "Generating report", threshold: 100, icon: "📋" },
];

function GolfBallLoader({ spinning = true }: { spinning?: boolean }) {
  return (
    <div className="relative flex flex-col items-center">
      <motion.div
        className="absolute bottom-0 w-12 h-3 rounded-full bg-golf-green/20 blur-sm"
        animate={spinning ? { scaleX: [1, 0.6, 1], opacity: [0.3, 0.15, 0.3] } : {}}
        transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="golf-ball"
        style={{ width: 56, height: 56 }}
        animate={
          spinning
            ? { y: [0, -24, 0], rotate: [0, 180, 360] }
            : { y: 0, rotate: 0, scale: [1, 1.1, 1] }
        }
        transition={
          spinning
            ? { duration: 1, repeat: Infinity, ease: "easeInOut" }
            : { duration: 0.5 }
        }
      />
    </div>
  );
}

function GolfFlag() {
  return (
    <motion.svg
      viewBox="0 0 48 48"
      className="w-14 h-14"
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 12 }}
    >
      <ellipse cx="24" cy="42" rx="14" ry="4" fill="#10b981" opacity="0.25" />
      <rect x="22.5" y="8" width="3" height="34" rx="1.5" fill="#94a3b8" />
      <motion.path
        d="M25.5 8 L42 14 L25.5 20 Z"
        fill="#10b981"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: [1, 0.95, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        style={{ transformOrigin: "25.5px 14px" }}
      />
      <circle cx="24" cy="39" r="4" fill="#fafaf5" stroke="#e5e5db" strokeWidth="0.5" />
    </motion.svg>
  );
}

function RollingBallProgress({ progress }: { progress: number }) {
  return (
    <div className="relative w-full max-w-md mx-auto">
      <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-golf-dark via-golf-green/30 to-golf-dark rounded-full" />
      <div className="relative h-8 mb-1">
        <div className="absolute bottom-1 left-0 right-0 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: "linear-gradient(90deg, #022c22, #10b981, #a7f3d0)",
            }}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        <motion.div
          className="absolute bottom-0"
          animate={{ left: `${Math.min(progress, 96)}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{ translateX: "-50%" }}
        >
          <motion.div
            className="golf-ball"
            style={{ width: 20, height: 20 }}
            animate={{ rotate: progress * 7.2 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </motion.div>
        <div className="absolute right-0 bottom-0">
          <svg viewBox="0 0 16 20" className="w-4 h-5" style={{ transform: "translateY(-4px)" }}>
            <rect x="7" y="0" width="1.5" height="18" fill="#94a3b8" rx="0.75" />
            <path d="M8.5 1 L15 4 L8.5 7 Z" fill={progress >= 95 ? "#10b981" : "#475569"} />
          </svg>
        </div>
      </div>
    </div>
  );
}

export default function AnalysisProgress({ status, progress }: Props) {
  const isDone = status === "done";
  const isError = status === "error";

  return (
    <div className="glass rounded-2xl p-8 max-w-lg mx-auto relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-[0.015] pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle, #10b981 1px, transparent 1px)",
          backgroundSize: "20px 20px",
        }}
      />

      <div className="relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="mb-4">
            {isDone ? (
              <GolfFlag />
            ) : isError ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-14 h-14 rounded-full bg-red-500/10 ring-1 ring-red-500/20 flex items-center justify-center"
              >
                <span className="text-red-400 text-2xl font-bold">!</span>
              </motion.div>
            ) : (
              <GolfBallLoader spinning />
            )}
          </div>

          <h3 className="font-display font-bold text-xl mb-1">
            {isDone
              ? "Analysis Complete!"
              : isError
              ? "Analysis Failed"
              : "Analyzing Your Swing..."}
          </h3>
          <p className="text-white/45 text-sm">{progress}% complete</p>
        </div>

        <div className="mb-8">
          <RollingBallProgress progress={progress} />
        </div>

        <div className="space-y-2.5">
          {STEPS.map((step, i) => {
            const done = progress >= step.threshold;
            const active =
              !done &&
              i > 0 &&
              progress >= STEPS[i - 1].threshold &&
              progress < step.threshold;
            const isFirst = i === 0 && progress < step.threshold && progress > 0;

            return (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: done || active || isFirst ? 1 : 0.25, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="flex items-center gap-3"
              >
                <div className="flex-shrink-0 w-7 text-center">
                  {done ? (
                    <CheckCircle size={16} className="text-golf-green mx-auto" />
                  ) : active || isFirst ? (
                    <motion.span
                      className="text-base"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                    >
                      {step.icon}
                    </motion.span>
                  ) : (
                    <Circle size={16} className="text-white/15 mx-auto" />
                  )}
                </div>
                <span
                  className={`text-sm font-medium ${
                    done
                      ? "text-white/90"
                      : active || isFirst
                      ? "text-golf-green"
                      : "text-white/25"
                  }`}
                >
                  {step.label}
                </span>
                {(active || isFirst) && (
                  <motion.div
                    className="flex gap-1 ml-auto"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    {[0, 1, 2].map((d) => (
                      <motion.div
                        key={d}
                        className="w-1.5 h-1.5 rounded-full bg-golf-green"
                        animate={{ opacity: [0.2, 1, 0.2] }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: d * 0.2,
                        }}
                      />
                    ))}
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
