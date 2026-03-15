import { motion } from "framer-motion";
import type { RefObject } from "react";

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

const PHASE_COLORS: Record<string, string> = {
  ADDRESS:        "#6b7280",
  BACKSWING:      "#3b82f6",
  TOP:            "#f59e0b",
  DOWNSWING:      "#22c55e",
  IMPACT:         "#ef4444",
  FOLLOW_THROUGH: "#a855f7",
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
      <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
        Swing Phases
      </h3>

      {/* Timeline strip */}
      <div className="flex h-10 rounded-lg overflow-hidden gap-0.5">
        {phases.map(([phase, [start, end]], i) => {
          const width = ((end - start + 1) / totalFrames) * 100;
          const color = PHASE_COLORS[phase] ?? "#6b7280";
          const severity = phaseFaultSummary[phase]?.max_severity ?? "none";

          return (
            <motion.button
              key={phase}
              initial={{ scaleY: 0, opacity: 0 }}
              animate={{ scaleY: 1, opacity: 1 }}
              transition={{ delay: i * 0.07, duration: 0.35 }}
              onClick={() => handlePhaseClick(start)}
              title={`${phase}: frames ${start}–${end}`}
              className={`relative flex items-center justify-center text-white text-xs font-bold overflow-hidden cursor-pointer hover:brightness-125 transition-all duration-200 ${
                severity === "critical" ? "ring-2 ring-red-500" : ""
              }`}
              style={{ width: `${Math.max(width, 4)}%`, backgroundColor: color + "40", borderTop: `3px solid ${color}` }}
            >
              <span className="truncate px-1 text-[10px]">
                {phase.split("_")[0].slice(0, 3)}
              </span>
            </motion.button>
          );
        })}
      </div>

      {/* Phase cards grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {phases.map(([phase, [start, end]], i) => {
          const color = PHASE_COLORS[phase] ?? "#6b7280";
          const summary = phaseFaultSummary[phase];
          const severity = summary?.max_severity ?? "none";
          const totalFaults = (summary?.counts.critical ?? 0) + (summary?.counts.major ?? 0) + (summary?.counts.minor ?? 0);

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
              <div className="flex items-center gap-1.5 mb-1">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-[10px] font-bold text-white/60 uppercase tracking-wide">
                  {phase.replace("_", " ")}
                </span>
              </div>
              <div className="text-xs text-white/30 mb-1.5">
                {end - start + 1} frames
              </div>
              {totalFaults > 0 ? (
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
              ) : (
                <span className="text-[9px] text-golf-green font-semibold">No faults</span>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
