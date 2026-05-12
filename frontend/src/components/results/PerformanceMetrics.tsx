import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Zap, MapPin, Flag, Target, AlertTriangle, Info } from "lucide-react";

interface Props {
  performance: {
    BallSpeed: number;
    Distance: number;
    Carry: number;
    confidence: number;
  } | null;
  ballTracking?: {
    enabled: boolean;
    status: string;
    quality?: Record<string, number | string>;
    distance_estimation: {
      carry_yards: number;
      distance_yards: number;
      confidence: number;
      method: string;
      notes?: string;
    } | null;
  };
}

function useCountUp(target: number, duration = 1200): number {
  const [value, setValue] = useState(0);
  const animRef = useRef<number>(0);

  useEffect(() => {
    let start: number | null = null;
    const step = (ts: number) => {
      if (!start) start = ts;
      const elapsed = ts - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) animRef.current = requestAnimationFrame(step);
    };
    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [target, duration]);

  return value;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  color,
  delay,
  subtitle,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  unit: string;
  color: string;
  delay: number;
  subtitle?: string;
}) {
  const displayed = useCountUp(Math.round(value), 1400);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, duration: 0.4 }}
      className="glass rounded-2xl p-6 flex flex-col gap-3 relative overflow-hidden group hover:border-white/20 border border-white/10 transition-all duration-300"
    >
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{ background: `radial-gradient(ellipse at top left, ${color}15 0%, transparent 70%)` }}
      />

      <div className="flex items-center justify-between">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: `${color}20` }}
        >
          <Icon size={20} style={{ color }} />
        </div>
        <span className="text-[10px] font-semibold text-white/30 uppercase tracking-widest">{label}</span>
      </div>

      <div>
        <div className="flex items-end gap-1">
          <span
            className="font-display font-extrabold text-4xl"
            style={{ color }}
          >
            {displayed}
          </span>
          <span className="text-white/40 text-sm mb-1.5">{unit}</span>
        </div>
        {subtitle && <p className="text-xs text-white/30 mt-0.5">{subtitle}</p>}
      </div>
    </motion.div>
  );
}

/* Confidence bar */
function ConfidenceBar({ confidence, method }: { confidence: number; method: string }) {
  const color = confidence > 70 ? "#10b981" : confidence > 40 ? "#f59e0b" : "#ef4444";
  const label = confidence > 70 ? "High" : confidence > 40 ? "Medium" : "Low";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-white/40 uppercase tracking-wider">Confidence</span>
        <span className="text-xs font-bold" style={{ color }}>
          {confidence.toFixed(0)}% — {label}
        </span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${confidence}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
        />
      </div>
    </div>
  );
}

export default function PerformanceMetrics({ performance, ballTracking }: Props) {
  const distEstimation = ballTracking?.distance_estimation;

  const distance = distEstimation?.distance_yards ?? performance?.Distance ?? 0;
  const carry = distEstimation?.carry_yards ?? performance?.Carry ?? 0;
  const ballSpeed = performance?.BallSpeed ?? 0;
  const confidence = distEstimation?.confidence ?? performance?.confidence ?? 0;
  const method = distEstimation?.method ?? "ml_pose_fallback";

  const isVision = method === "vision";
  const trackingFailed = ballTracking && !ballTracking.enabled;
  const ballNotDetected = ballTracking?.status?.toLowerCase().includes("not_detected");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
          Performance Prediction
        </h3>
        <div className="flex items-center gap-2 glass px-3 py-1 rounded-full">
          <Target size={11} className="text-golf-green" />
          <span className="text-xs text-white/50">
            {isVision ? "Vision tracking" : "ML Pose model"}
          </span>
        </div>
      </div>

      {/* Tracking status banner */}
      {(trackingFailed || ballNotDetected) && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-2 glass rounded-xl px-4 py-3 border border-amber-500/20"
        >
          <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-semibold text-amber-400 mb-0.5">
              {ballNotDetected ? "Ball Not Tracked" : "Vision Tracking Unavailable"}
            </p>
            <p className="text-[11px] text-white/40">
              {ballNotDetected
                ? "The ball could not be detected in your video. Distance is estimated using ML pose analysis instead."
                : "Ball detector model not loaded. Distance is estimated using ML pose analysis as a fallback."}
            </p>
          </div>
        </motion.div>
      )}

      {/* Confidence bar */}
      <ConfidenceBar confidence={confidence} method={method} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          icon={Zap}
          label="Ball Speed"
          value={ballSpeed}
          unit="mph"
          color="#10b981"
          delay={0}
        />
        <MetricCard
          icon={Flag}
          label="Distance"
          value={distance}
          unit="yds"
          color="#f59e0b"
          delay={0.1}
          subtitle="Total distance"
        />
        <MetricCard
          icon={MapPin}
          label="Carry"
          value={carry}
          unit="yds"
          color="#3b82f6"
          delay={0.2}
          subtitle="Carry distance"
        />
      </div>

      {/* Method info */}
      {distEstimation?.notes && (
        <div className="flex items-start gap-2 text-[10px] text-white/30">
          <Info size={12} className="mt-0.5 flex-shrink-0" />
          <span>{distEstimation.notes}</span>
        </div>
      )}
    </div>
  );
}
