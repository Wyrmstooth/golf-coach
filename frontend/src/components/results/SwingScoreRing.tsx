import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  score: number; // 0–100
  quality: string;
  faultSummary?: { critical_count: number; major_count: number; minor_count: number; total_faults: number };
}

function getColor(score: number): string {
  if (score <= 30) return "#16a34a"; // green - excellent
  if (score <= 50) return "#ca8a04"; // amber - good
  return "#ef4444";                   // red - needs work
}

function getLabel(quality: string): { bg: string; text: string } {
  const q = quality.toLowerCase();
  if (q.includes("excellent") || q.includes("good")) return { bg: "bg-golf-green/20", text: "text-golf-green" };
  if (q.includes("fair"))                             return { bg: "bg-amber-500/20", text: "text-amber-400" };
  return { bg: "bg-red-500/20", text: "text-red-400" };
}

function getTip(score: number): string {
  if (score <= 15) return "Tour-level mechanics. Minimal faults detected.";
  if (score <= 30) return "Strong fundamentals. Only minor adjustments needed.";
  if (score <= 50) return "Solid swing with some key issues. Work on critical faults listed below.";
  if (score <= 70) return "Several significant faults detected. Consider professional coaching.";
  return "Major swing rebuilding needed. Start with address posture and grip fundamentals.";
}

export default function SwingScoreRing({ score, quality, faultSummary }: Props) {
  const [displayed, setDisplayed] = useState(0);
  const animRef = useRef<number>(0);

  // Count-up animation
  useEffect(() => {
    let start: number | null = null;
    const duration = 1400;

    const step = (ts: number) => {
      if (!start) start = ts;
      const elapsed = ts - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
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
          {/* Background track */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="10"
          />
          {/* Animated progress arc */}
          <motion.circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${strokeDash} ${circumference}`}
            strokeDashoffset="0"
            transform="rotate(-90 80 80)"
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${strokeDash} ${circumference}` }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
          />
          {/* Score text */}
          <text
            x="80" y="72"
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            fontSize="30"
            fontWeight="800"
            fontFamily="DM Sans, Inter, sans-serif"
          >
            {displayed}
          </text>
          <text
            x="80" y="96"
            textAnchor="middle"
            dominantBaseline="middle"
            fill="rgba(255,255,255,0.4)"
            fontSize="11"
            fontFamily="Inter, sans-serif"
          >
            / 100
          </text>
        </svg>
        {/* Glow */}
        <div
          className="absolute inset-0 rounded-full blur-xl opacity-30 pointer-events-none"
          style={{ background: color }}
        />
      </div>

      <div className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest ${labelStyle.bg} ${labelStyle.text}`}>
        {quality}
      </div>

      {/* Fault breakdown mini-badges */}
      {faultSummary && faultSummary.total_faults > 0 && (
        <div className="flex gap-2">
          {faultSummary.critical_count > 0 && (
            <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded-full text-[10px] font-bold">
              {faultSummary.critical_count} Critical
            </span>
          )}
          {faultSummary.major_count > 0 && (
            <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded-full text-[10px] font-bold">
              {faultSummary.major_count} Major
            </span>
          )}
          {faultSummary.minor_count > 0 && (
            <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded-full text-[10px] font-bold">
              {faultSummary.minor_count} Minor
            </span>
          )}
        </div>
      )}

      <p className="text-white/30 text-[11px] text-center max-w-[240px] leading-relaxed">{getTip(score)}</p>
    </div>
  );
}
