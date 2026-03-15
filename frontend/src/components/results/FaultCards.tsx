import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ChevronDown, ChevronUp, Target, Info } from "lucide-react";
import type { FaultDetail, FaultDetails } from "../../api/analysis";

interface Props {
  faultDetails: FaultDetails;
}

const SEVERITY_CONFIG = {
  critical: {
    label: "Critical",
    emoji: "🔴",
    bg: "bg-red-500/10",
    border: "border-red-500/40",
    badge: "bg-red-500/20 text-red-400",
    icon: "text-red-400",
    headerBg: "bg-red-500/15",
  },
  major: {
    label: "Major",
    emoji: "🟠",
    bg: "bg-orange-500/10",
    border: "border-orange-400/40",
    badge: "bg-orange-500/20 text-orange-400",
    icon: "text-orange-400",
    headerBg: "bg-orange-500/15",
  },
  minor: {
    label: "Minor",
    emoji: "🟡",
    bg: "bg-yellow-500/10",
    border: "border-yellow-400/40",
    badge: "bg-yellow-500/20 text-yellow-400",
    icon: "text-yellow-400",
    headerBg: "bg-yellow-500/15",
  },
};

const PHASE_COLORS: Record<string, string> = {
  ADDRESS: "bg-gray-500/20 text-gray-300",
  BACKSWING: "bg-blue-500/20 text-blue-300",
  TOP: "bg-amber-500/20 text-amber-300",
  DOWNSWING: "bg-green-500/20 text-green-300",
  IMPACT: "bg-red-500/20 text-red-300",
  FOLLOW_THROUGH: "bg-purple-500/20 text-purple-300",
};

function FaultCard({ fault, index }: { fault: FaultDetail; index: number }) {
  const [expanded, setExpanded] = useState(fault.severity === "critical");
  const cfg = SEVERITY_CONFIG[fault.severity] ?? SEVERITY_CONFIG.minor;
  const phaseStyle = PHASE_COLORS[fault.phase] ?? "bg-white/10 text-white/60";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      className={`rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className={`w-full text-left px-4 py-3.5 flex items-center gap-3 ${cfg.headerBg} hover:brightness-110 transition-all`}
      >
        <span className="text-lg flex-shrink-0">{cfg.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-white">{fault.title}</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${phaseStyle}`}>
              {fault.phase.replace("_", " ")}
            </span>
          </div>
          <p className="text-xs text-white/50 mt-0.5 truncate">{fault.description}</p>
        </div>
        <div className="flex-shrink-0">
          {expanded ? (
            <ChevronUp size={14} className="text-white/40" />
          ) : (
            <ChevronDown size={14} className="text-white/40" />
          )}
        </div>
      </button>

      {/* Expanded body */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-4 space-y-3 border-t border-white/5">
              {/* Value vs expected */}
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

              {/* Fix */}
              <div className="flex items-start gap-2 glass-green rounded-lg px-3 py-2.5">
                <Target size={13} className="text-golf-green mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-[10px] text-golf-green/70 font-semibold uppercase tracking-wider mb-0.5">Fix</div>
                  <p className="text-xs text-white/70">{fault.fix}</p>
                </div>
              </div>

              {/* Feature key */}
              <div className="flex items-center gap-1.5">
                <Info size={11} className="text-white/20" />
                <span className="text-[10px] text-white/20 font-mono">{fault.feature}</span>
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
        <div className="text-4xl mb-3">✅</div>
        <h3 className="font-display font-bold text-lg text-golf-green">Excellent Swing!</h3>
        <p className="text-white/50 text-sm mt-1">No faults detected across all 6 phases.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary badges */}
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

      {/* Fault groups */}
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
              <div className="flex-1 h-px bg-white/5" />
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
