import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ChevronDown, ChevronUp, Target, Info, Dumbbell, BarChart3 } from "lucide-react";
import type { FaultDetail, FaultDetails } from "../../api/analysis";

interface Props {
  faultDetails: FaultDetails;
}

const SEVERITY_CONFIG = {
  critical: {
    label: "Critical",
    emoji: "🔴",
    bg: "bg-red-500/[0.07]",
    border: "border-red-500/25",
    badge: "bg-red-500/10 text-red-400 ring-1 ring-red-500/20",
    icon: "text-red-400",
    headerBg: "bg-red-500/10",
    barColor: "#ef4444",
  },
  major: {
    label: "Major",
    emoji: "🟠",
    bg: "bg-orange-500/[0.07]",
    border: "border-orange-400/25",
    badge: "bg-orange-500/10 text-orange-400 ring-1 ring-orange-500/20",
    icon: "text-orange-400",
    headerBg: "bg-orange-500/10",
    barColor: "#f97316",
  },
  minor: {
    label: "Minor",
    emoji: "🟡",
    bg: "bg-yellow-500/[0.07]",
    border: "border-yellow-400/25",
    badge: "bg-yellow-500/10 text-yellow-400 ring-1 ring-yellow-500/20",
    icon: "text-yellow-400",
    headerBg: "bg-yellow-500/10",
    barColor: "#eab308",
  },
};

const PHASE_COLORS: Record<string, string> = {
  ADDRESS: "bg-gray-500/10 text-gray-300 ring-1 ring-gray-500/15",
  BACKSWING: "bg-blue-500/10 text-blue-300 ring-1 ring-blue-500/15",
  TOP: "bg-amber-500/10 text-amber-300 ring-1 ring-amber-500/15",
  DOWNSWING: "bg-green-500/10 text-green-300 ring-1 ring-green-500/15",
  IMPACT: "bg-red-500/10 text-red-300 ring-1 ring-red-500/15",
  FOLLOW_THROUGH: "bg-purple-500/10 text-purple-300 ring-1 ring-purple-500/15",
};

function DeviationGauge({ value, expected, color }: { value: number; expected: string; color: string }) {
  const match = expected.match(/([-\d.]+)[°]?\s*to\s*([-\d.]+)/);
  if (!match) return null;
  const lo = parseFloat(match[1]);
  const hi = parseFloat(match[2]);
  const min = Math.min(lo, hi) - Math.abs(hi - lo) * 0.5;
  const max = Math.max(lo, hi) + Math.abs(hi - lo) * 0.5;
  const range = max - min || 1;
  const goodLeft = ((Math.min(lo, hi) - min) / range) * 100;
  const goodWidth = (Math.abs(hi - lo) / range) * 100;
  const valuePos = Math.max(0, Math.min(100, ((value - min) / range) * 100));

  return (
    <div className="space-y-1">
      <div className="relative h-2 bg-white/[0.08] rounded-full overflow-visible">
        <div
          className="absolute top-0 h-full bg-golf-green/25 rounded-full"
          style={{ left: `${goodLeft}%`, width: `${goodWidth}%` }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border-2 border-white shadow-md"
          style={{ left: `${valuePos}%`, backgroundColor: color, transform: `translate(-50%, -50%)` }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-white/25">
        <span>{min.toFixed(0)}°</span>
        <span className="text-golf-green/60">Good: {expected}</span>
        <span>{max.toFixed(0)}°</span>
      </div>
    </div>
  );
}

function FaultCard({ fault, index }: { fault: FaultDetail; index: number }) {
  const [expanded, setExpanded] = useState(fault.severity === "critical");
  const cfg = SEVERITY_CONFIG[fault.severity] ?? SEVERITY_CONFIG.minor;
  const phaseStyle = PHASE_COLORS[fault.phase] ?? "bg-white/5 text-white/55";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      className={`rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}
    >
      <button
        onClick={() => setExpanded((v) => !v)}
        className={`w-full text-left px-4 py-3.5 flex items-center gap-3 ${cfg.headerBg} hover:brightness-110 transition-all`}
      >
        <span className="text-lg flex-shrink-0">{cfg.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm">{fault.title}</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${phaseStyle}`}>
              {fault.phase.replace("_", " ")}
            </span>
          </div>
          <p className="text-xs text-white/45 mt-0.5 truncate">{fault.description}</p>
        </div>
        <div className="flex-shrink-0">
          {expanded ? (
            <ChevronUp size={14} className="text-white/35" />
          ) : (
            <ChevronDown size={14} className="text-white/35" />
          )}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-4 space-y-3 border-t border-white/[0.06]">
              <div className="flex gap-4">
                <div className="flex-1 glass rounded-lg px-3 py-2">
                  <div className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">Measured</div>
                  <div className={`font-bold text-sm ${cfg.icon}`}>
                    {fault.value.toFixed(1)}°
                  </div>
                </div>
                <div className="flex-1 glass rounded-lg px-3 py-2">
                  <div className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">Expected</div>
                  <div className="font-bold text-sm text-golf-green">{fault.expected}</div>
                </div>
              </div>

              <DeviationGauge value={fault.value} expected={fault.expected} color={cfg.barColor} />

              <div className="flex items-start gap-2 glass-green rounded-lg px-3 py-2.5">
                <Target size={13} className="text-golf-green mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-[10px] text-golf-green/70 font-semibold uppercase tracking-wider mb-0.5">How to Fix</div>
                  <p className="text-xs text-white/65">{fault.fix}</p>
                </div>
              </div>

              {fault.drill && (
                <div className="flex items-start gap-2 rounded-lg px-3 py-2.5 bg-blue-500/10 border border-blue-500/15">
                  <Dumbbell size={13} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-[10px] text-blue-400/70 font-semibold uppercase tracking-wider mb-0.5">Practice Drill</div>
                    <p className="text-xs text-white/65">{fault.drill}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-1.5">
                <Info size={11} className="text-white/15" />
                <span className="text-[10px] text-white/15 font-mono">{fault.feature}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function FaultCards({ faultDetails }: Props) {
  const bySeverity = faultDetails.by_severity;
  const summary = faultDetails.summary;

  if (summary.total_faults === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center">
        <div className="text-4xl mb-3">⛳</div>
        <h3 className="font-display font-bold text-lg text-golf-green">Excellent Swing!</h3>
        <p className="text-white/45 text-sm mt-1">No faults detected across all 6 phases.</p>
        <p className="text-white/30 text-xs mt-3">Your technique matches professional-level biomechanics.</p>
      </div>
    );
  }

  const topIssues = faultDetails.faults
    .slice()
    .sort((a, b) => {
      const sevOrder = { critical: 0, major: 1, minor: 2 };
      return (sevOrder[a.severity] ?? 3) - (sevOrder[b.severity] ?? 3);
    })
    .slice(0, 3);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        {(["critical", "major", "minor"] as const).map((sev) => {
          const count = summary[`${sev}_count`];
          if (!count) return null;
          const cfg = SEVERITY_CONFIG[sev];
          return (
            <div key={sev} className={`flex items-center gap-2 px-4 py-2 rounded-full border ${cfg.border} ${cfg.bg}`}>
              <AlertTriangle size={13} className={cfg.icon} />
              <span className={`text-xs font-bold ${cfg.icon}`}>
                {count} {cfg.label}
              </span>
            </div>
          );
        })}
      </div>

      {topIssues.length > 0 && (
        <div className="glass rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={14} className="text-golf-gold" />
            <span className="text-xs font-bold text-golf-gold uppercase tracking-wider">Focus Areas</span>
          </div>
          <div className="space-y-1.5">
            {topIssues.map((fault, i) => {
              const cfg = SEVERITY_CONFIG[fault.severity] ?? SEVERITY_CONFIG.minor;
              return (
                <div key={`${fault.phase}-${fault.title}`} className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white/25 w-4">{i + 1}.</span>
                  <span className="text-xs">{cfg.emoji}</span>
                  <span className="text-xs text-white/75 font-medium">{fault.title}</span>
                  <span className="text-[10px] text-white/30">({fault.phase.replace("_", " ")})</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {(["critical", "major", "minor"] as const).map((sev) => {
        const faults = bySeverity[sev] ?? [];
        if (!faults.length) return null;
        const cfg = SEVERITY_CONFIG[sev];

        return (
          <div key={sev} className="space-y-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm">{cfg.emoji}</span>
              <h4 className={`text-xs font-bold uppercase tracking-widest ${cfg.icon}`}>
                {cfg.label} Faults
              </h4>
              <div className="flex-1 h-px bg-white/[0.06]" />
              <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.badge}`}>{faults.length}</span>
            </div>
            <div className="space-y-2">
              {faults.map((fault, i) => (
                <FaultCard key={`${fault.phase}-${fault.title}`} fault={fault} index={i} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
