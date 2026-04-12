import { motion, AnimatePresence } from "framer-motion";
import type { AddressFeedback } from "../../api/live";
import { CheckCircle, XCircle, Wifi, WifiOff, AlertTriangle, Clock, TrendingUp } from "lucide-react";

interface Props {
  feedback: AddressFeedback | null;
  connected: boolean;
  poseHoldMs: number;
}

const ANGLE_TARGETS: Record<string, {
  label: string;
  description: string;
  min: number;
  max: number;
  unit: string;
}> = {
  spine:    { label: "Spine Tilt",  description: "Slight forward lean from hips", min: 150, max: 165, unit: "°" },
  knee:     { label: "Knee Flex",   description: "Athletic bent-knee stance",       min: 130, max: 170, unit: "°" },
  left_arm: { label: "Lead Arm",    description: "Extended but relaxed",            min: 150, max: 180, unit: "°" },
};

function AngleBar({
  value, min, max, label, description, unit,
}: {
  value: number; min: number; max: number; label: string; description: string; unit: string;
}) {
  const inRange = value >= min && value <= max;
  // Expand view range by 2× the target width on each side
  const halfRange = (max - min) / 2;
  const viewMin = min - halfRange * 3;
  const viewMax = max + halfRange * 3;
  const viewSpan = viewMax - viewMin;

  const pct = Math.min(Math.max((value - viewMin) / viewSpan, 0), 1) * 100;
  const tMinPct = ((min - viewMin) / viewSpan) * 100;
  const tMaxPct = ((max - viewMin) / viewSpan) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-semibold text-white/80 leading-tight">{label}</p>
          <p className="text-[10px] text-white/30 leading-tight mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className={`text-sm font-bold tabular-nums ${inRange ? "text-golf-green" : "text-red-400"}`}>
            {value.toFixed(0)}{unit}
          </span>
          {inRange
            ? <CheckCircle size={13} className="text-golf-green" />
            : <XCircle size={13} className="text-red-400" />}
        </div>
      </div>
      <div className="relative h-2 bg-white/8 rounded-full">
        {/* Target zone highlight */}
        <div
          className="absolute top-0 h-full rounded bg-golf-green/25"
          style={{ left: `${tMinPct}%`, width: `${tMaxPct - tMinPct}%` }}
        />
        {/* Animated value dot */}
        <motion.div
          className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white/80 shadow-lg ${inRange ? "bg-golf-green" : "bg-red-400"}`}
          animate={{ left: `${pct}%` }}
          style={{ translateX: "-50%", boxShadow: inRange ? "0 0 8px rgba(74,222,128,0.6)" : "0 0 8px rgba(248,113,113,0.6)" }}
          transition={{ type: "spring", stiffness: 280, damping: 22 }}
        />
      </div>
      <p className="text-[9px] text-white/20">Target: {min}–{max}{unit}</p>
    </div>
  );
}

export default function AddressMetrics({ feedback, connected, poseHoldMs }: Props) {
  const isTracking  = feedback?.status === "ok";
  const isGood      = isTracking && feedback?.overall === "GOOD ADDRESS";
  const holdSecs    = Math.floor(poseHoldMs / 1000);
  const corrections = feedback?.corrections?.filter(Boolean) ?? [];
  const hasAngles   = isTracking && feedback?.angles && Object.keys(feedback.angles).length > 0;

  return (
    <div className="glass rounded-2xl p-5 space-y-5">

      {/* ── Connection status ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {connected ? (
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2.5, repeat: Infinity }}
            >
              <Wifi size={13} className="text-golf-green" />
            </motion.div>
          ) : (
            <WifiOff size={13} className="text-white/25" />
          )}
          <span className={`text-xs font-semibold ${connected ? "text-golf-green" : "text-white/30"}`}>
            {connected ? "AI analysis active" : "Disconnected"}
          </span>
        </div>
        {isTracking && (
          <span className="text-[10px] text-white/25 px-2 py-0.5 glass rounded-full">
            Pose detected
          </span>
        )}
      </div>

      {/* ── Overall status banner ─────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {isGood ? (
          <motion.div
            key="good"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="relative rounded-xl px-4 py-4 text-center bg-golf-green/12 border border-golf-green/25 overflow-hidden"
          >
            {/* Ambient glow pulse */}
            <motion.div
              className="absolute inset-0 bg-golf-green/8 rounded-xl"
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 2.2, repeat: Infinity }}
            />
            <p className="font-bold text-golf-green text-base relative z-10">✅ GOOD ADDRESS</p>
            {holdSecs > 0 && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-golf-green/60 text-xs mt-1 flex items-center justify-center gap-1 relative z-10"
              >
                <Clock size={10} />
                Held for {holdSecs}s
                {holdSecs >= 3 && " — great!"}
              </motion.p>
            )}
          </motion.div>

        ) : isTracking ? (
          <motion.div
            key="adjust"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="rounded-xl px-4 py-3 text-center bg-amber-500/8 border border-amber-500/20"
          >
            <p className="font-bold text-amber-400 text-sm">⚠️ ADJUST POSITION</p>
            <p className="text-white/30 text-xs mt-0.5">
              {corrections.length} correction{corrections.length !== 1 ? "s" : ""} needed
            </p>
          </motion.div>

        ) : feedback?.status === "no_pose" ? (
          <motion.div
            key="no_pose"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-xl px-4 py-3 text-center glass border border-white/5"
          >
            <p className="text-white/40 text-sm">No pose detected</p>
            <p className="text-white/20 text-xs mt-0.5">Step in front of the camera</p>
          </motion.div>

        ) : (
          <motion.div
            key="waiting"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl px-4 py-3 text-center glass border border-white/5"
          >
            <p className="text-white/30 text-sm">Waiting for pose…</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Angle gauges ─────────────────────────────────────────────────── */}
      {hasAngles && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp size={11} className="text-white/30" />
            <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-widest">Body Angles</h4>
          </div>
          {Object.entries(ANGLE_TARGETS).map(([key, cfg]) => {
            const val = feedback!.angles[key];
            if (val === undefined || val === null) return null;
            return (
              <AngleBar
                key={key}
                value={val}
                min={cfg.min}
                max={cfg.max}
                label={cfg.label}
                description={cfg.description}
                unit={cfg.unit}
              />
            );
          })}
        </div>
      )}

      {/* ── Corrections list ─────────────────────────────────────────────── */}
      {/* Corrections persist until the panel re-renders with empty list, so
          they never vanish instantly — they fade out gracefully via exit animations */}
      <AnimatePresence>
        {corrections.length > 0 && (
          <motion.div
            key="corrections"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle size={11} className="text-amber-400/60" />
              <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-widest">
                Corrections needed
              </h4>
            </div>
            {corrections.map((c, i) => (
              <motion.div
                key={c}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ delay: i * 0.07 }}
                className="flex items-start gap-2.5 text-xs text-amber-200/80 glass px-3 py-2.5 rounded-lg border border-amber-500/12"
              >
                <AlertTriangle size={11} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <span>{c}</span>
              </motion.div>
            ))}
          </motion.div>
        )}

        {isGood && corrections.length === 0 && (
          <motion.div
            key="perfect"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 text-xs text-golf-green/70 glass px-3 py-2.5 rounded-lg border border-golf-green/15"
          >
            <CheckCircle size={11} className="text-golf-green flex-shrink-0" />
            All angles in range — maintain this position
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}


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
