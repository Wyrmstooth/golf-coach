import { motion } from "framer-motion";
import type { RefObject } from "react";
import { CheckCircle2 } from "lucide-react";

interface Props {
  phaseRanges: Record<string, [number, number]>;
  phaseFaultSummary: Record<string, {
    max_severity: string;
    counts: { critical: number; major: number; minor: number };
    score: number;
    top_fault_titles: string[];
  }>;
  fps?: number;
  videoRef?: RefObject<HTMLVideoElement>;
}

const PHASE_META: Record<string, { color: string; icon: string }> = {
  ADDRESS:        { color: "#6b7280", icon: "🏌️" },
  BACKSWING:      { color: "#3b82f6", icon: "↗️" },
  TOP:            { color: "#f59e0b", icon: "⬆️" },
  DOWNSWING:      { color: "#22c55e", icon: "↙️" },
  IMPACT:         { color: "#ef4444", icon: "💥" },
  FOLLOW_THROUGH: { color: "#a855f7", icon: "🔄" },
};

const SEVERITY_BORDER: Record<string, string> = {
  none:     "border-white/10",
  minor:    "border-yellow-400/60",
  major:    "border-orange-400/60",
  critical: "border-red-500/80",
};

const SEVERITY_BG: Record<string, string> = {
  none:     "bg-white/5",
  minor:    "bg-yellow-400/10",
  major:    "bg-orange-400/10",
  critical: "bg-red-500/15",
};

function scoreColor(score: number): string {
  if (score >= 85) return "#10b981";  // green - excellent
  if (score >= 70) return "#22c55e";  // green - good
  if (score >= 50) return "#f59e0b";  // amber - fair
  if (score >= 30) return "#f97316";  // orange - poor
  return "#ef4444";                   // red - needs work
}

function scoreLabel(score: number): string {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Fair";
  if (score >= 30) return "Poor";
  return "Weak";
}

export default function PhaseTimeline({ phaseRanges, phaseFaultSummary, fps = 30, videoRef }: Props) {
  const allFrames = Object.values(phaseRanges).flat();
  const totalFrames = Math.max(...allFrames) - Math.min(...allFrames) + 1 || 1;

  const phases = Object.entries(phaseRanges);

  const handlePhaseClick = (start: number) => {
    if (videoRef?.current) {
      videoRef.current.currentTime = start / fps;
      videoRef.current.play();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
          Swing Phases
        </h3>
        <span className="text-[10px] text-white/25">Click a phase to jump to it in the video</span>
      </div>

      {/* Timeline strip */}
      <div className="flex h-12 rounded-lg overflow-hidden gap-0.5">
        {phases.map(([phase, [start, end]], i) => {
          const width = ((end - start + 1) / totalFrames) * 100;
          const meta = PHASE_META[phase] ?? { color: "#6b7280", icon: "▪️" };
          const severity = phaseFaultSummary[phase]?.max_severity ?? "none";
          const phaseScore = phaseFaultSummary[phase]?.score ?? 100;

          return (
            <motion.button
              key={phase}
              initial={{ scaleY: 0, opacity: 0 }}
              animate={{ scaleY: 1, opacity: 1 }}
              transition={{ delay: i * 0.07, duration: 0.35 }}
              onClick={() => handlePhaseClick(start)}
              title={`${phase}: frames ${start}–${end} • Score: ${phaseScore}`}
              className={`relative flex flex-col items-center justify-center text-white text-xs font-bold overflow-hidden cursor-pointer hover:brightness-125 transition-all duration-200 ${
                severity === "critical" ? "ring-2 ring-red-500" : ""
              }`}
              style={{ width: `${Math.max(width, 6)}%`, backgroundColor: meta.color + "40", borderTop: `3px solid ${meta.color}` }}
            >
              <span className="text-sm leading-none">{meta.icon}</span>
              <span className="truncate px-1 text-[9px] text-white/60 mt-0.5">
                {phase.split("_")[0].slice(0, 4)}
              </span>
            </motion.button>
          );
        })}
      </div>

      {/* Phase cards grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {phases.map(([phase, [start, end]], i) => {
          const meta = PHASE_META[phase] ?? { color: "#6b7280", icon: "▪️" };
          const summary = phaseFaultSummary[phase];
          const severity = summary?.max_severity ?? "none";
          const totalFaults = (summary?.counts.critical ?? 0) + (summary?.counts.major ?? 0) + (summary?.counts.minor ?? 0);
          const phaseScore = summary?.score ?? 100;
          const sColor = scoreColor(phaseScore);
          const sLabel = scoreLabel(phaseScore);

          return (
            <motion.button
              key={phase}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 + 0.1 }}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handlePhaseClick(start)}
              className={`text-left p-3 rounded-xl border ${SEVERITY_BORDER[severity]} ${SEVERITY_BG[severity]} transition-all duration-200 cursor-pointer`}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: meta.color }} />
                <span className="text-[10px] font-bold text-white/60 uppercase tracking-wide truncate">
                  {phase.replace("_", " ")}
                </span>
              </div>

              {/* Score bar */}
              <div className="mb-2">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[9px] text-white/25">Score</span>
                  <span className="text-[9px] font-bold ml-1" style={{ color: sColor }}>{sLabel}</span>
                </div>
                <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: sColor }}
                    initial={{ width: 0 }}
                    animate={{ width: `${phaseScore}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 + 0.2 }}
                  />
                </div>
              </div>

              <div className="text-[9px] text-white/25 mb-1.5">
                {end - start + 1} frames · {((end - start + 1) / fps).toFixed(2)}s
              </div>

              {totalFaults > 0 ? (
                <div className="space-y-1">
                  <div className="flex gap-1 flex-wrap">
                    {summary.counts.critical > 0 && (
                      <span className="px-1.5 py-0.5 bg-red-500/30 text-red-400 rounded text-[9px] font-bold">
                        {summary.counts.critical} crit
                      </span>
                    )}
                    {summary.counts.major > 0 && (
                      <span className="px-1.5 py-0.5 bg-orange-500/30 text-orange-400 rounded text-[9px] font-bold">
                        {summary.counts.major} maj
                      </span>
                    )}
                    {summary.counts.minor > 0 && (
                      <span className="px-1.5 py-0.5 bg-yellow-500/30 text-yellow-400 rounded text-[9px] font-bold">
                        {summary.counts.minor} min
                      </span>
                    )}
                  </div>
                  {/* Top fault name */}
                  {summary.top_fault_titles?.[0] && (
                    <p className="text-[8px] text-white/30 truncate leading-tight">
                      {summary.top_fault_titles[0]}
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1">
                  <CheckCircle2 size={10} className="text-golf-green" />
                  <span className="text-[9px] text-golf-green font-semibold">Clean</span>
                </div>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
