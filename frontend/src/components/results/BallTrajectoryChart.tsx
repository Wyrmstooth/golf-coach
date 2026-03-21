import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Info } from "lucide-react";

interface TrajectoryPoint {
  frame: number;
  t: number;
  x: number | null;
  y: number | null;
  confidence: number;
}

interface BallTrackingInfo {
  enabled: boolean;
  status: string;
  quality: Record<string, number | string>;
  distance_estimation: {
    carry_yards: number;
    distance_yards: number;
    confidence: number;
    method: string;
    notes: string;
  } | null;
  trajectory_2d: TrajectoryPoint[];
}

interface Props {
  trajectory: TrajectoryPoint[];
  phaseRanges?: Record<string, [number, number]>;
  fps?: number;
  ballTracking?: BallTrackingInfo | null;
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

/* Golf ball icon for empty states */
function GolfBallIcon({ size = 48 }: { size?: number }) {
  return (
    <svg viewBox="0 0 48 48" width={size} height={size}>
      <defs>
        <radialGradient id="emptyBallGrad" cx="40%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="60%" stopColor="#f0f0e8" />
          <stop offset="100%" stopColor="#d4d4c8" />
        </radialGradient>
        <pattern id="emptyDimples" x="0" y="0" width="6" height="6" patternUnits="userSpaceOnUse">
          <circle cx="1.5" cy="1.5" r="0.8" fill="rgba(0,0,0,0.06)" />
          <circle cx="4.5" cy="4.5" r="0.8" fill="rgba(0,0,0,0.06)" />
        </pattern>
      </defs>
      <circle cx="24" cy="24" r="20" fill="url(#emptyBallGrad)" opacity="0.4" />
      <circle cx="24" cy="24" r="19" fill="url(#emptyDimples)" opacity="0.4" />
      <ellipse cx="20" cy="19" rx="4" ry="3" fill="rgba(255,255,255,0.3)" transform="rotate(-15 20 19)" />
    </svg>
  );
}

/* Determine specific error message based on tracking data */
function getTrackingErrorInfo(ballTracking?: BallTrackingInfo | null, trajectory?: TrajectoryPoint[]) {
  if (!ballTracking) {
    return {
      title: "Ball Tracking Not Available",
      message: "Ball tracking module is not enabled or the detector model is not loaded.",
      tip: "Ensure the ball_detector.pt model file exists in the models/ directory.",
      severity: "info" as const,
    };
  }

  if (!ballTracking.enabled) {
    return {
      title: "Ball Tracking Disabled",
      message: "Ball tracking was disabled for this analysis. Distance estimation used ML pose-based prediction instead.",
      tip: "To enable vision-based tracking, place a trained ball_detector.pt in the models/ folder.",
      severity: "info" as const,
    };
  }

  const status = ballTracking.status?.toLowerCase() ?? "";

  if (status.includes("not_detected") || status.includes("no_ball")) {
    return {
      title: "Ball Not Detected",
      message: "The system could not detect a golf ball in your video. This can happen with low contrast, poor lighting, or if the ball is too small in the frame.",
      tip: "Try recording from closer distance with good lighting. Ensure the ball is visible in the impact zone.",
      severity: "warning" as const,
    };
  }

  if (status.includes("insufficient") || status.includes("low_quality")) {
    return {
      title: "Insufficient Tracking Data",
      message: `Only ${trajectory?.filter(p => p.x !== null).length ?? 0} valid tracking points detected. At least 5 points are needed for reliable trajectory estimation.`,
      tip: "Use a higher frame-rate video (60fps) and ensure the ball path is visible for at least 0.5 seconds after impact.",
      severity: "warning" as const,
    };
  }

  if (!trajectory || trajectory.length === 0) {
    return {
      title: "No Trajectory Data",
      message: "Ball was detected but trajectory data could not be extracted from the video.",
      tip: "The ball may have been detected in too few frames. Try a clearer angle where the ball flight is visible.",
      severity: "warning" as const,
    };
  }

  return null;
}

/* Compute projection/prediction data points */
function computeProjection(data: Array<{ time: string; horizontal: number; vertical: number }>, numPoints = 8) {
  if (data.length < 3) return [];

  // Use last 3 points to compute velocity
  const last = data.slice(-3);
  const dt = parseFloat(last[2].time) - parseFloat(last[0].time);
  if (dt === 0) return [];

  const vx = (last[2].horizontal - last[0].horizontal) / dt;
  const vy = (last[2].vertical - last[0].vertical) / dt;
  const lastTime = parseFloat(last[2].time);
  const stepTime = dt / 2;

  const projected: Array<{ time: string; projH: number; projV: number }> = [];
  for (let i = 1; i <= numPoints; i++) {
    const t = lastTime + stepTime * i;
    projected.push({
      time: t.toFixed(2),
      projH: parseFloat((last[2].horizontal + vx * stepTime * i).toFixed(1)),
      projV: parseFloat((last[2].vertical + vy * stepTime * i - 0.5 * 9.8 * (stepTime * i) * (stepTime * i) * 0.1).toFixed(1)),
    });
  }
  return projected;
}

export default function BallTrajectoryChart({ trajectory, phaseRanges, fps = 30, ballTracking }: Props) {
  // Check for error states
  const errorInfo = getTrackingErrorInfo(ballTracking, trajectory);

  if (!trajectory || trajectory.length === 0 || trajectory.filter(p => p.x !== null).length < 2) {
    const info = errorInfo ?? {
      title: "Ball Trajectory Data Not Available",
      message: "A trained ball detector model is required for trajectory tracking.",
      tip: "Place ball_detector.pt in the models/ folder and re-analyze.",
      severity: "info" as const,
    };

    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-8"
      >
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="relative">
            <GolfBallIcon size={56} />
            {info.severity === "warning" && (
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center">
                <AlertTriangle size={14} className="text-amber-400" />
              </div>
            )}
          </div>

          <div>
            <h4 className={`font-display font-bold text-base mb-1 ${
              info.severity === "warning" ? "text-amber-400" : "text-white/60"
            }`}>
              {info.title}
            </h4>
            <p className="text-white/40 text-sm max-w-md">
              {info.message}
            </p>
          </div>

          <div className="flex items-start gap-2 glass rounded-lg px-4 py-3 max-w-md">
            <Info size={14} className="text-golf-green mt-0.5 flex-shrink-0" />
            <p className="text-xs text-white/50">{info.tip}</p>
          </div>

          {/* Distance fallback info */}
          {ballTracking?.distance_estimation && (
            <div className="glass-green rounded-xl px-4 py-3 text-sm">
              <span className="text-golf-green font-semibold">ML Fallback: </span>
              <span className="text-white/60">
                Estimated {ballTracking.distance_estimation.distance_yards.toFixed(0)} yds
                ({ballTracking.distance_estimation.confidence.toFixed(0)}% confidence)
              </span>
            </div>
          )}
        </div>
      </motion.div>
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

  // Compute projection line data
  const projection = computeProjection(data);
  const combinedData = [
    ...data.map(d => ({ ...d, projH: null as number | null, projV: null as number | null })),
    // Bridge point: last real data point with projection values
    ...(projection.length > 0 ? [{
      time: data[data.length - 1].time,
      horizontal: data[data.length - 1].horizontal,
      vertical: data[data.length - 1].vertical,
      confidence: data[data.length - 1].confidence,
      projH: data[data.length - 1].horizontal,
      projV: data[data.length - 1].vertical,
    }] : []),
    ...projection.map(p => ({
      time: p.time,
      horizontal: null as any,
      vertical: null as any,
      confidence: 0,
      projH: p.projH,
      projV: p.projV,
    })),
  ];

  // Impact reference line time
  const impactTime = phaseRanges?.["IMPACT"]
    ? (phaseRanges["IMPACT"][0] / fps).toFixed(2)
    : null;

  // Tracking quality badge
  const detectionRate = ballTracking?.quality?.detection_rate;
  const qualityColor = typeof detectionRate === "number"
    ? detectionRate > 0.7 ? "text-golf-green" : detectionRate > 0.4 ? "text-amber-400" : "text-red-400"
    : "text-white/40";
  const qualityLabel = typeof detectionRate === "number"
    ? detectionRate > 0.7 ? "Good" : detectionRate > 0.4 ? "Fair" : "Poor"
    : "N/A";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6 space-y-4"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-golf-green" />
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
            Ball Trajectory
          </h3>
        </div>
        <div className="flex items-center gap-4 flex-wrap">
          {/* Tracking quality badge */}
          <div className="flex items-center gap-1.5 glass px-2.5 py-1 rounded-full">
            <div className={`w-2 h-2 rounded-full ${
              qualityLabel === "Good" ? "bg-golf-green" : qualityLabel === "Fair" ? "bg-amber-400" : "bg-red-400"
            }`} />
            <span className={`text-xs font-semibold ${qualityColor}`}>
              Tracking: {qualityLabel}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-blue-400 rounded" />
            <span className="text-xs text-white/40">Horizontal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-orange-400 rounded" />
            <span className="text-xs text-white/40">Vertical</span>
          </div>
          {projection.length > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 border-t border-dashed border-emerald-400" />
              <span className="text-xs text-white/40">Projected</span>
            </div>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={combinedData} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
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
          {/* Actual trajectory */}
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="horizontal"
            name="Horizontal"
            stroke="#3b82f6"
            fill="#3b82f620"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
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
            connectNulls={false}
            isAnimationActive
            animationDuration={1400}
          />
          {/* Projection lines */}
          {projection.length > 0 && (
            <>
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="projH"
                name="Projected H"
                stroke="#34d399"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                connectNulls
                isAnimationActive
                animationDuration={1600}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="projV"
                name="Projected V"
                stroke="#34d399"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                connectNulls
                isAnimationActive
                animationDuration={1800}
              />
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>

      <div className="flex items-center justify-between">
        <p className="text-[10px] text-white/25">
          Horizontal displacement from launch point · Vertical displacement (positive = upward)
          {projection.length > 0 && " · Dashed line = projected trajectory"}
        </p>
        {data.length > 0 && (
          <span className="text-[10px] text-white/25">
            {data.length} tracking points
          </span>
        )}
      </div>
    </motion.div>
  );
}
