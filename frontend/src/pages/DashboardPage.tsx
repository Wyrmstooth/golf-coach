import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity, Trophy, Target, TrendingUp, Clock, AlertTriangle,
  BarChart2, ChevronRight, Video
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from "recharts";
import { sessionsApi, type DashboardStats, type SwingSessionOut } from "../api/auth";
import { useAuthStore } from "../store/authStore";

function StatCard({
  icon: Icon, label, value, sub, color = "text-golf-green",
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5 space-y-3"
    >
      <div className="flex items-center gap-2">
        <Icon size={14} className={color} />
        <span className="text-xs font-semibold text-white/40 uppercase tracking-widest">{label}</span>
      </div>
      <p className={`text-3xl font-bold font-display ${color}`}>{value}</p>
      {sub && <p className="text-xs text-white/25">{sub}</p>}
    </motion.div>
  );
}

function ScoreChip({ score }: { score: number | null }) {
  if (score === null) return <span className="text-white/20 text-xs">—</span>;
  const color =
    score >= 70 ? "text-golf-green bg-golf-green/10 border-golf-green/20"
    : score >= 50 ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
    : "text-red-400 bg-red-500/10 border-red-500/20";
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border tabular-nums ${color}`}>
      {score.toFixed(0)}
    </span>
  );
}

function SessionRow({ s }: { s: SwingSessionOut }) {
  const date = new Date(s.created_at).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 px-4 py-3 rounded-xl glass border border-white/5 hover:border-white/10 transition-all group"
    >
      <div className="w-8 h-8 rounded-lg bg-golf-green/10 flex items-center justify-center flex-shrink-0">
        <Video size={14} className="text-golf-green" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/80 font-medium truncate">
          {s.video_filename || "Analysis"}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <Clock size={10} className="text-white/20" />
          <span className="text-[10px] text-white/25">{date}</span>
          {s.swing_quality && (
            <span className="text-[10px] text-white/20 ml-1">· {s.swing_quality}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <ScoreChip score={s.overall_score} />
        {s.job_id && (
          <Link
            to={`/analyze?job=${s.job_id}`}
            className="opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ChevronRight size={14} className="text-white/30" />
          </Link>
        )}
      </div>
    </motion.div>
  );
}

const FAULT_COLORS = [
  "#ef4444", "#f97316", "#eab308", "#22c55e",
  "#06b6d4", "#8b5cf6", "#ec4899", "#6b7280",
];

export default function DashboardPage() {
  const token = useAuthStore((s) => s.token)!;
  const user  = useAuthStore((s) => s.user)!;
  const [stats, setStats]   = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    sessionsApi.dashboard(token)
      .then(setStats)
      .catch(() => setError("Could not load dashboard data."))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="min-h-screen bg-golf-navy pt-20 sm:pt-24 pb-16 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">
            Welcome back, <span className="text-gradient">{user.display_name.split(" ")[0]}</span>
          </h1>
          <p className="text-white/35 text-sm mt-1">
            Here's your swing performance overview
            {user.handicap != null && ` · Handicap: ${user.handicap}`}
          </p>
        </motion.div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-8 h-8 border-2 border-golf-green/30 border-t-golf-green rounded-full"
            />
          </div>
        )}

        {error && (
          <div className="glass rounded-2xl p-6 text-center">
            <AlertTriangle size={24} className="text-amber-400 mx-auto mb-2" />
            <p className="text-white/50 text-sm">{error}</p>
          </div>
        )}

        {stats && !loading && (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                icon={Activity}
                label="Total Sessions"
                value={stats.total_sessions}
                sub="Swings analyzed"
              />
              <StatCard
                icon={BarChart2}
                label="Avg Score"
                value={stats.avg_score != null ? `${stats.avg_score}` : "—"}
                sub="Swing quality (higher is better)"
                color={stats.avg_score != null && stats.avg_score >= 70 ? "text-golf-green" : "text-amber-400"}
              />
              <StatCard
                icon={Trophy}
                label="Best Score"
                value={stats.best_score != null ? `${stats.best_score}` : "—"}
                sub="Highest swing quality score"
                color="text-golf-green"
              />
              <StatCard
                icon={Target}
                label="Top Fault"
                value={stats.fault_frequency[0]?.fault.replace(/_/g, " ") || "None"}
                sub={stats.fault_frequency[0] ? `${stats.fault_frequency[0].count}× detected` : "Clean swings!"}
                color="text-amber-400"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Score trend */}
              {stats.score_trend.length > 1 && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="glass rounded-2xl p-5 space-y-4"
                >
                  <div className="flex items-center gap-2">
                    <TrendingUp size={13} className="text-golf-green" />
                    <h3 className="text-sm font-semibold text-white/70">Score Trend</h3>
                    <span className="text-xs text-white/20 ml-auto">last {stats.score_trend.length} sessions</span>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={stats.score_trend}>
                      <XAxis
                        dataKey="date"
                        tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        width={28}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#1e293b",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 12,
                          color: "#fff",
                          fontSize: 12,
                        }}
                        formatter={(value) => [String(value ?? 0), "Score"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#16a34a"
                        strokeWidth={2}
                        dot={{ fill: "#16a34a", r: 3, strokeWidth: 0 }}
                        activeDot={{ r: 5, fill: "#16a34a" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </motion.div>
              )}

              {/* Fault frequency */}
              {stats.fault_frequency.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="glass rounded-2xl p-5 space-y-4"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={13} className="text-amber-400" />
                    <h3 className="text-sm font-semibold text-white/70">Most Common Faults</h3>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={stats.fault_frequency} layout="vertical">
                      <XAxis
                        type="number"
                        tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="fault"
                        tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        width={90}
                        tickFormatter={(v: string) => v.replace(/_/g, " ")}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#1e293b",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 12,
                          color: "#fff",
                          fontSize: 12,
                        }}
                        formatter={(value) => [`${value ?? 0}×`, "Occurrences"]}
                      />
                      <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                        {stats.fault_frequency.map((_, i) => (
                          <Cell key={i} fill={FAULT_COLORS[i % FAULT_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </motion.div>
              )}
            </div>

            {/* Recent sessions */}
            {stats.recent_sessions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass rounded-2xl p-5 space-y-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock size={13} className="text-white/40" />
                    <h3 className="text-sm font-semibold text-white/70">Recent Sessions</h3>
                  </div>
                  <Link
                    to="/analyze"
                    className="text-xs text-golf-green hover:text-golf-green/80 transition-colors font-medium"
                  >
                    New analysis →
                  </Link>
                </div>
                <div className="space-y-2">
                  {stats.recent_sessions.map((s) => (
                    <SessionRow key={s.id} s={s} />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Empty state */}
            {stats.total_sessions === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass rounded-2xl p-12 text-center space-y-4"
              >
                <Activity size={40} className="text-white/15 mx-auto" />
                <p className="text-white/50 font-medium">No sessions yet</p>
                <p className="text-white/25 text-sm">Analyze your first swing to start tracking progress</p>
                <Link
                  to="/analyze"
                  className="inline-flex items-center gap-2 mt-2 bg-golf-green text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-golf-green/90 transition-colors"
                >
                  Analyze a Swing
                </Link>
              </motion.div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
