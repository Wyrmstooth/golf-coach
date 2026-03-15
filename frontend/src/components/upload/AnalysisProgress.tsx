import { motion } from "framer-motion";
import { CheckCircle, Loader2, Circle } from "lucide-react";

interface Props {
  status: "pending" | "running" | "done" | "error" | string;
  progress: number;
}

const STEPS = [
  { label: "Uploading video", threshold: 5 },
  { label: "Detecting pose landmarks", threshold: 20 },
  { label: "Analyzing swing phases", threshold: 40 },
  { label: "Identifying faults", threshold: 60 },
  { label: "Predicting performance", threshold: 75 },
  { label: "Ball tracking", threshold: 88 },
  { label: "Generating report", threshold: 100 },
];

export default function AnalysisProgress({ status, progress }: Props) {
  return (
    <div className="glass rounded-2xl p-8 max-w-lg mx-auto">
      <div className="text-center mb-8">
        <motion.div
          animate={{ rotate: status === "done" ? 0 : 360 }}
          transition={{ duration: 2, repeat: status === "done" ? 0 : Infinity, ease: "linear" }}
          className={`w-14 h-14 rounded-full border-4 flex items-center justify-center mx-auto mb-4 ${
            status === "done"
              ? "border-golf-green bg-golf-green/20"
              : status === "error"
              ? "border-red-500 bg-red-500/20"
              : "border-golf-green border-t-transparent bg-golf-green/10"
          }`}
        >
          {status === "done" ? (
            <CheckCircle size={24} className="text-golf-green" />
          ) : status === "error" ? (
            <span className="text-red-400 text-xl font-bold">!</span>
          ) : (
            <Loader2 size={22} className="text-golf-green" />
          )}
        </motion.div>
        <h3 className="font-display font-bold text-xl">
          {status === "done"
            ? "Analysis Complete!"
            : status === "error"
            ? "Analysis Failed"
            : "Analyzing Your Swing..."}
        </h3>
        <p className="text-white/40 text-sm mt-1">{progress}% complete</p>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-white/10 rounded-full mb-8 overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-golf-green to-emerald-400 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {STEPS.map((step, i) => {
          const done = progress >= step.threshold;
          const active =
            !done &&
            i > 0 &&
            progress >= STEPS[i - 1].threshold &&
            progress < step.threshold;

          return (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: done || active ? 1 : 0.35, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="flex items-center gap-3"
            >
              <div className="flex-shrink-0">
                {done ? (
                  <CheckCircle size={16} className="text-golf-green" />
                ) : active ? (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                  >
                    <Loader2 size={16} className="text-golf-green animate-spin" />
                  </motion.div>
                ) : (
                  <Circle size={16} className="text-white/20" />
                )}
              </div>
              <span
                className={`text-sm font-medium ${
                  done
                    ? "text-white"
                    : active
                    ? "text-golf-green"
                    : "text-white/30"
                }`}
              >
                {step.label}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
