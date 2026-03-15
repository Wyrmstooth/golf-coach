import { motion, AnimatePresence } from "framer-motion";
import type { AddressFeedback } from "../../api/live";
import { CheckCircle, XCircle, Wifi, WifiOff } from "lucide-react";

interface Props {
  feedback: AddressFeedback | null;
  connected: boolean;
}

const ANGLE_TARGETS: Record<string, { label: string; min: number; max: number; unit: string }> = {
  spine: { label: "Spine Angle", min: 150, max: 165, unit: "°" },
  knee:  { label: "Avg Knee Bend", min: 130, max: 170, unit: "°" },
  left_arm: { label: "Left Arm", min: 150, max: 180, unit: "°" },
};

function AngleBar({ name, value, min, max, label, unit }: {
  name: string; value: number; min: number; max: number; label: string; unit: string;
}) {
  const inRange = value >= min && value <= max;
  const pct = Math.min(Math.max((value - (min - 20)) / (max - min + 40), 0), 1) * 100;
  const targetMin = ((min - (min - 20)) / (max - min + 40)) * 100;
  const targetMax = ((max - (min - 20)) / (max - min + 40)) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium text-white/60">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold ${inRange ? "text-golf-green" : "text-red-400"}`}>
            {value.toFixed(0)}{unit}
          </span>
          {inRange ? <CheckCircle size={12} className="text-golf-green" /> : <XCircle size={12} className="text-red-400" />}
        </div>
      </div>
      <div className="relative h-2 bg-white/10 rounded-full overflow-visible">
        {/* Target zone */}
        <div
          className="absolute top-0 h-full bg-golf-green/20 rounded"
          style={{ left: `${targetMin}%`, width: `${targetMax - targetMin}%` }}
        />
        {/* Current value */}
        <motion.div
          className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white ${inRange ? "bg-golf-green" : "bg-red-400"}`}
          animate={{ left: `${pct}%` }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          style={{ translateX: "-50%" }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-white/25">
        <span>Target: {min}–{max}{unit}</span>
      </div>
    </div>
  );
}

export default function AddressMetrics({ feedback, connected }: Props) {
  const isGood = feedback?.overall === "GOOD ADDRESS";

  return (
    <div className="glass rounded-2xl p-6 space-y-6">
      {/* Connection status */}
      <div className="flex items-center gap-2">
        {connected ? (
          <Wifi size={14} className="text-golf-green" />
        ) : (
          <WifiOff size={14} className="text-white/30" />
        )}
        <span className={`text-xs font-semibold ${connected ? "text-golf-green" : "text-white/30"}`}>
          {connected ? "Connected" : "Not connected"}
        </span>
      </div>

      {/* Overall status */}
      <AnimatePresence mode="wait">
        {feedback && feedback.status === "ok" ? (
          <motion.div
            key="status"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`rounded-xl px-4 py-3 text-center font-bold text-lg ${
              isGood
                ? "bg-golf-green/20 text-golf-green border border-golf-green/30"
                : "bg-red-500/20 text-red-400 border border-red-500/30"
            }`}
          >
            {isGood ? "✅ GOOD ADDRESS" : "⚠️ NEEDS ADJUSTMENT"}
          </motion.div>
        ) : (
          <motion.div
            key="detecting"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl px-4 py-3 text-center text-white/40 glass border border-white/5"
          >
            {feedback?.status === "no_pose" ? "No pose detected" : "Detecting..."}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Angle bars */}
      {feedback?.angles && Object.keys(ANGLE_TARGETS).length > 0 && (
        <div className="space-y-4">
          <h4 className="text-xs font-semibold text-white/40 uppercase tracking-widest">Angles</h4>
          {Object.entries(ANGLE_TARGETS).map(([key, cfg]) => {
            const val = feedback.angles[key];
            if (val === undefined) return null;
            return (
              <AngleBar
                key={key}
                name={key}
                value={val}
                min={cfg.min}
                max={cfg.max}
                label={cfg.label}
                unit={cfg.unit}
              />
            );
          })}
        </div>
      )}

      {/* Corrections */}
      {feedback?.corrections && feedback.corrections.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-white/40 uppercase tracking-widest">Corrections</h4>
          {feedback.corrections.map((c, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-start gap-2 text-xs text-red-300 glass px-3 py-2 rounded-lg border border-red-500/20"
            >
              <XCircle size={12} className="text-red-400 mt-0.5 flex-shrink-0" />
              {c}
            </motion.div>
          ))}
        </div>
      )}

      {feedback?.status === "ok" && (!feedback.corrections || feedback.corrections.length === 0) && (
        <div className="flex items-center gap-2 text-xs text-golf-green glass px-3 py-2 rounded-lg border border-golf-green/20">
          <CheckCircle size={12} />
          All angles in target range
        </div>
      )}
    </div>
  );
}
