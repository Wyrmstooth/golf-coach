import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

interface TrajectoryPoint {
  frame: number;
  t: number;
  x: number | null;
  y: number | null;
  confidence: number;
}

interface Props {
  trajectory: TrajectoryPoint[];
  phaseRanges?: Record<string, [number, number]>;
  fps?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl px-4 py-3 text-xs space-y-1 shadow-xl border border-white/10">
      <p className="font-bold text-white">t = {Number(label).toFixed(2)}s</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {Number(p.value).toFixed(1)} px
        </p>
      ))}
    </div>
  );
};

export default function BallTrajectoryChart({ trajectory, phaseRanges, fps = 30 }: Props) {
  if (!trajectory || trajectory.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center">
        <div className="text-3xl mb-3">⚽</div>
        <p className="text-white/40 text-sm">Ball trajectory data not available</p>
        <p className="text-white/25 text-xs mt-1">
          A trained ball detector model is required for trajectory tracking.
        </p>
      </div>
    );
  }

  const firstX = trajectory.find((p) => p.x !== null)?.x ?? 0;
  const firstY = trajectory.find((p) => p.y !== null)?.y ?? 0;

  const data = trajectory
    .filter((p) => p.x !== null && p.y !== null)
    .map((p) => ({
      time: p.t.toFixed(2),
      horizontal: parseFloat(((p.x! - firstX)).toFixed(1)),
      vertical: parseFloat(((firstY - p.y!)).toFixed(1)),
      confidence: parseFloat((p.confidence * 100).toFixed(0)),
    }));

  // Impact reference line time
  const impactTime = phaseRanges?.["IMPACT"]
    ? (phaseRanges["IMPACT"][0] / fps).toFixed(2)
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6 space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-golf-green" />
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
            Ball Trajectory
          </h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-blue-400 rounded" />
            <span className="text-xs text-white/40">Horizontal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-orange-400 rounded" />
            <span className="text-xs text-white/40">Vertical (up)</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="time"
            tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
            label={{ value: "Time (s)", position: "insideBottom", offset: -2, fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
            label={{ value: "px", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
          />
          <Tooltip content={<CustomTooltip />} />
          {impactTime && (
            <ReferenceLine
              yAxisId="left"
              x={impactTime}
              stroke="#ef4444"
              strokeDasharray="4 4"
              label={{ value: "Impact", fill: "#ef4444", fontSize: 10, position: "top" }}
            />
          )}
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="horizontal"
            name="Horizontal"
            stroke="#3b82f6"
            fill="#3b82f620"
            strokeWidth={2}
            dot={false}
            isAnimationActive
            animationDuration={1200}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="vertical"
            name="Vertical"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            isAnimationActive
            animationDuration={1400}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <p className="text-[10px] text-white/25 text-center">
        Horizontal displacement from launch point · Vertical displacement (positive = upward)
      </p>
    </motion.div>
  );
}
