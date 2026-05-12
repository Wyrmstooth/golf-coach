import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  score: number;
  quality: string;
  faultSummary?: { critical_count: number; major_count: number; minor_count: number; total_faults: number };
}

function getColor(score: number): string {
  if (score >= 70) return "#10b981";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

function getLabel(quality: string): { bg: string; text: string } {
  const q = quality.toLowerCase();
  if (q.includes("excellent") || q.includes("good")) return { bg: "bg-golf-green/10 ring-1 ring-golf-green/20", text: "text-golf-green" };
  if (q.includes("fair"))                             return { bg: "bg-amber-500/10 ring-1 ring-amber-500/20", text: "text-amber-400" };
  return { bg: "bg-red-500/10 ring-1 ring-red-500/20", text: "text-red-400" };
}

function getTip(score: number): string {
  if (score >= 90) return "Tour-level mechanics. Minimal faults detected.";
  if (score >= 75) return "Strong fundamentals. Only minor adjustments needed.";
  if (score >= 60) return "Solid swing with some key issues. Work on faults listed below.";
  if (score >= 40) return "Several significant faults detected. Consider professional coaching.";
  return "Major swing rebuilding needed. Start with address posture and grip fundamentals.";
}

export default function SwingScoreRing({ score, quality, faultSummary }: Props) {
  const [displayed, setDisplayed] = useState(0);
  const animRef = useRef<number>(0);

  useEffect(() => {
    let start: number | null = null;
    const duration = 1400;

    const step = (ts: number) => {
      if (!start) start = ts;
      const elapsed = ts - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(eased * score));
      if (progress < 1) animRef.current = requestAnimationFrame(step);
    };

    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [score]);

  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (displayed / 100) * circumference;
  const color = getColor(score);
  const labelStyle = getLabel(quality);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="12"
          />
          <motion.circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${strokeDash} ${circumference}`}
            strokeDashoffset="0"
            transform="rotate(-90 80 80)"
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${strokeDash} ${circumference}` }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 10px ${color}AA)` }}
          />
          <text
            x="80" y="72"
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            fontSize="32"
            fontWeight="800"
            fontFamily="DM Sans, Inter, sans-serif"
          >
            {displayed}
          </text>
          <text
            x="80" y="98"
            textAnchor="middle"
            dominantBaseline="middle"
            fill="rgba(255,255,255,0.35)"
            fontSize="11"
            fontFamily="Inter, sans-serif"
          >
            / 100
          </text>
        </svg>
        <div
          className="absolute inset-0 rounded-full blur-xl opacity-25 pointer-events-none"
          style={{ background: color }}
        />
      </div>

      <div className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest ${labelStyle.bg} ${labelStyle.text}`}>
        {quality}
      </div>

      {faultSummary && faultSummary.total_faults > 0 && (
        <div className="flex gap-2">
          {faultSummary.critical_count > 0 && (
            <span className="px-2.5 py-0.5 bg-red-500/10 ring-1 ring-red-500/20 text-red-400 rounded-full text-[10px] font-bold">
              {faultSummary.critical_count} Critical
            </span>
          )}
          {faultSummary.major_count > 0 && (
            <span className="px-2.5 py-0.5 bg-orange-500/10 ring-1 ring-orange-500/20 text-orange-400 rounded-full text-[10px] font-bold">
              {faultSummary.major_count} Major
            </span>
          )}
          {faultSummary.minor_count > 0 && (
            <span className="px-2.5 py-0.5 bg-yellow-500/10 ring-1 ring-yellow-500/20 text-yellow-400 rounded-full text-[10px] font-bold">
              {faultSummary.minor_count} Minor
            </span>
          )}
        </div>
      )}

      <p className="text-white/35 text-[11px] text-center max-w-[240px] leading-relaxed">{getTip(score)}</p>
    </div>
  );
}
