import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users, Activity, Shield, BarChart2, Clock, Wrench,
  Search, Trash2, ToggleLeft, ToggleRight, ChevronDown,
  AlertTriangle, RefreshCw, UserCog, Video, Target,
  TrendingUp, UserX, UserCheck, X,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from "recharts";
import PageWrapper from "../components/layout/PageWrapper";
import { adminApi, type AdminStats, type AdminSessionOut, type UserStats } from "../api/admin";
import type { UserOut } from "../api/auth";

type Tab = "dashboard" | "users" | "sessions" | "jobs";

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
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5 space-y-3"
    >
      <div className="flex items-center gap-2">
        <Icon size={15} className={color} />
        <span className="text-xs font-semibold text-white/40 uppercase tracking-widest">{label}</span>
      </div>
      <p className={`text-3xl font-bold font-display ${color}`}>{value}</p>
      {sub && <p className="text-xs text-white/25">{sub}</p>}
    </motion.div>
  );
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<UserOut[]>([]);
  const [sessions, setSessions] = useState<AdminSessionOut[]>([]);
  const [jobs, setJobs] = useState<Record<string, unknown>[]>([]);
  const [search, setSearch] = useState("");
  const [selectedUser, setSelectedUser] = useState<UserOut | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "dashboard", label: "Dashboard", icon: BarChart2 },
    { key: "users", label: "Users", icon: Users },
    { key: "sessions", label: "Sessions", icon: Video },
    { key: "jobs", label: "Jobs", icon: Wrench },
  ];

  const fetchStats = () => {
    adminApi.getStats().then(setStats).catch(console.error);
  };

  const fetchUsers = () => {
    adminApi.listUsers(search).then(setUsers).catch(console.error);
  };

  const fetchSessions = () => {
    adminApi.listSessions(100).then(setSessions).catch(console.error);
  };

  const fetchJobs = () => {
    adminApi.listJobs().then((d) => setJobs(d as Record<string, unknown>[])).catch(console.error);
  };

  useEffect(() => {
    setError(null);
    setLoading(true);
    Promise.all([adminApi.getStats(), adminApi.listUsers()])
      .then(([s, u]) => {
        setStats(s);
        setUsers(u);
      })
      .catch((e) => setError(e?.response?.data?.detail ?? e?.message ?? "Failed to load admin data"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (activeTab === "sessions") fetchSessions();
    if (activeTab === "jobs") fetchJobs();
  }, [activeTab]);

  useEffect(() => {
    fetchStats();
  }, [activeTab]);

  const handleToggleAdmin = async (user: UserOut) => {
    await adminApi.updateUser(user.id, { is_admin: !user.is_admin });
    fetchUsers();
  };

  const handleToggleActive = async (user: UserOut) => {
    await adminApi.updateUser(user.id, { is_active: !user.is_active });
    fetchUsers();
  };

  const handleDeleteUser = async (user: UserOut) => {
    if (!window.confirm(`Delete user "${user.display_name}" (${user.email})? This cannot be undone.`)) return;
    await adminApi.deleteUser(user.id);
    fetchUsers();
    fetchStats();
  };

  const handleViewUser = async (user: UserOut) => {
    setSelectedUser(user);
    try {
      const stats = await adminApi.getUserStats(user.id);
      setUserStats(stats);
    } catch {
      setUserStats(null);
    }
  };

  const handleSearch = () => {
    fetchUsers();
  };

  if (loading) {
    return (
      <PageWrapper className="bg-golf-navy min-h-screen pt-24 pb-16">
        <div className="flex items-center justify-center py-32">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-2 border-golf-green/30 border-t-golf-green rounded-full"
          />
        </div>
      </PageWrapper>
    );
  }

  if (error) {
    return (
      <PageWrapper className="bg-golf-navy min-h-screen pt-24 pb-16">
        <div className="glass rounded-2xl p-12 text-center max-w-lg mx-auto">
          <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-white mb-2">Access Denied</h2>
          <p className="text-white/50 text-sm">{error}</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper className="bg-golf-navy min-h-screen pt-24 pb-16 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
              <Shield size={20} className="text-red-400" />
            </div>
            <div>
              <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">Admin Panel</h1>
              <p className="text-white/35 text-sm">System management & monitoring</p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-2">
          {tabs.map(({ key, label, icon: Icon }) => (
            <motion.button
              key={key}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === key
                  ? "bg-golf-green/20 text-golf-green border border-golf-green/30"
                  : "text-white/40 hover:text-white/70 glass border border-white/5"
              }`}
            >
              <Icon size={14} />
              {label}
            </motion.button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === "dashboard" && stats && (
            <motion.div key="dashboard" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                <StatCard icon={Users} label="Total Users" value={stats.total_users} sub={`${stats.active_users} active`} color="text-blue-400" />
                <StatCard icon={Shield} label="Admin Users" value={stats.admin_users} color="text-red-400" />
                <StatCard icon={Activity} label="Total Sessions" value={stats.total_sessions} color="text-golf-green" />
                <StatCard icon={BarChart2} label="Avg Score" value={stats.avg_score_all ?? "—"} sub="Across all users" color="text-amber-400" />
                <StatCard icon={Wrench} label="Active Jobs" value={stats.active_jobs} sub={`${stats.total_jobs} total`} color={stats.active_jobs > 0 ? "text-golf-green" : "text-white/30"} />
              </div>

              <div className="glass rounded-2xl p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <RefreshCw size={14} className="text-white/30" />
                  <span className="text-sm text-white/50">Refresh data</span>
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => { fetchStats(); fetchUsers(); }}
                  className="flex items-center gap-2 px-4 py-2 glass border border-white/10 rounded-xl text-sm text-white/60 hover:text-white transition-all"
                >
                  <RefreshCw size={13} /> Refresh
                </motion.button>
              </div>
            </motion.div>
          )}

          {activeTab === "users" && (
            <motion.div key="users" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-6">
              {/* Search */}
              <div className="flex gap-3">
                <div className="flex-1 glass rounded-xl flex items-center px-4 gap-2">
                  <Search size={15} className="text-white/30" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Search by name or email..."
                    className="w-full bg-transparent py-3 text-sm text-white placeholder-white/20 outline-none"
                  />
                </div>
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={handleSearch}
                  className="px-5 py-3 bg-golf-green/20 border border-golf-green/30 text-golf-green rounded-xl text-sm font-medium hover:bg-golf-green/30 transition-all"
                >
                  Search
                </motion.button>
              </div>

              {/* User Table */}
              <div className="glass rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider">User</th>
                        <th className="text-left px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden sm:table-cell">Email</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden md:table-cell">Handicap</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden md:table-cell">Joined</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider">Status</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-golf-green/10 flex items-center justify-center flex-shrink-0">
                                <span className="text-golf-green text-xs font-bold">
                                  {user.avatar_initials ?? user.display_name.slice(0, 2).toUpperCase()}
                                </span>
                              </div>
                              <div className="min-w-0">
                                <button
                                  onClick={() => handleViewUser(user)}
                                  className="text-white/80 font-medium text-sm hover:text-golf-green transition-colors truncate block max-w-[120px]"
                                >
                                  {user.display_name}
                                </button>
                                {user.is_admin && (
                                  <span className="text-[10px] text-red-400 font-semibold">Admin</span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 text-white/50 hidden sm:table-cell truncate max-w-[160px]">{user.email}</td>
                          <td className="px-5 py-3.5 text-center text-white/40 hidden md:table-cell">{user.handicap ?? "—"}</td>
                          <td className="px-5 py-3.5 text-center text-white/30 hidden md:table-cell">
                            {new Date(user.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                          </td>
                          <td className="px-5 py-3.5 text-center">
                            <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${
                              user.is_active
                                ? "text-golf-green bg-golf-green/10 border-golf-green/20"
                                : "text-red-400 bg-red-500/10 border-red-500/20"
                            }`}>
                              {user.is_active ? <UserCheck size={10} /> : <UserX size={10} />}
                              {user.is_active ? "Active" : "Disabled"}
                            </span>
                          </td>
                          <td className="px-5 py-3.5">
                            <div className="flex items-center justify-center gap-1">
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => handleToggleAdmin(user)}
                                title={user.is_admin ? "Remove admin" : "Make admin"}
                                className={`p-2 rounded-lg transition-colors ${
                                  user.is_admin ? "bg-red-500/10 text-red-400" : "bg-white/5 text-white/30 hover:text-white hover:bg-white/10"
                                }`}
                              >
                                <Shield size={14} />
                              </motion.button>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => handleToggleActive(user)}
                                title={user.is_active ? "Deactivate" : "Activate"}
                                className={`p-2 rounded-lg transition-colors ${
                                  user.is_active ? "bg-amber-500/10 text-amber-400" : "bg-golf-green/10 text-golf-green"
                                }`}
                              >
                                {user.is_active ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                              </motion.button>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => handleDeleteUser(user)}
                                className="p-2 rounded-lg bg-white/5 text-white/20 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                              >
                                <Trash2 size={14} />
                              </motion.button>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => handleViewUser(user)}
                                className="p-2 rounded-lg bg-white/5 text-white/30 hover:text-white hover:bg-white/10 transition-colors"
                              >
                                <ChevronDown size={14} />
                              </motion.button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {users.length === 0 && (
                        <tr>
                          <td colSpan={6} className="px-5 py-12 text-center text-white/20 text-sm">
                            No users found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* User Detail Panel */}
              <AnimatePresence>
                {selectedUser && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="glass rounded-2xl p-6 space-y-5 overflow-hidden"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-golf-green/10 flex items-center justify-center">
                          <UserCog size={20} className="text-golf-green" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-white">{selectedUser.display_name}</h3>
                          <p className="text-sm text-white/40">{selectedUser.email}</p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => { setSelectedUser(null); setUserStats(null); }}
                        className="p-2 rounded-xl glass border border-white/10 text-white/40 hover:text-white"
                      >
                        <X size={16} />
                      </motion.button>
                    </div>

                    {userStats ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                          <div className="glass rounded-xl p-3 text-center">
                            <p className="text-2xl font-bold text-white">{userStats.total_sessions}</p>
                            <p className="text-[10px] text-white/30 uppercase tracking-wider">Sessions</p>
                          </div>
                          <div className="glass rounded-xl p-3 text-center">
                            <p className="text-2xl font-bold text-golf-green">{userStats.avg_score ?? "—"}</p>
                            <p className="text-[10px] text-white/30 uppercase tracking-wider">Avg Score</p>
                          </div>
                          <div className="glass rounded-xl p-3 text-center">
                            <p className="text-2xl font-bold text-amber-400">{userStats.best_score ?? "—"}</p>
                            <p className="text-[10px] text-white/30 uppercase tracking-wider">Best Score</p>
                          </div>
                        </div>

                        {userStats.score_trend.length > 1 && (
                          <div className="glass rounded-xl p-4">
                            <p className="text-xs text-white/40 font-medium mb-3">Score Trend</p>
                            <ResponsiveContainer width="100%" height={140}>
                              <LineChart data={userStats.score_trend}>
                                <XAxis dataKey="date" tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                                <Tooltip contentStyle={{ background: "#131c31", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, color: "#fff", fontSize: 12 }} />
                                <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: "#10b981", r: 3 }} />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {userStats.top_faults.length > 0 && (
                          <div className="glass rounded-xl p-4">
                            <p className="text-xs text-white/40 font-medium mb-3">Top Faults</p>
                            <ResponsiveContainer width="100%" height={120}>
                              <BarChart data={userStats.top_faults} layout="vertical">
                                <XAxis type="number" tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis type="category" dataKey="fault" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
                                <Bar dataKey="count" radius={[0, 4, 4, 0]} fill="#10b981" />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center py-8">
                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="w-5 h-5 border-2 border-golf-green/30 border-t-golf-green rounded-full" />
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {activeTab === "sessions" && (
            <motion.div key="sessions" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">All Sessions</h3>
                <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={fetchSessions} className="flex items-center gap-2 px-3 py-1.5 text-xs text-white/40 hover:text-white glass border border-white/5 rounded-lg transition-all">
                  <RefreshCw size={11} /> Refresh
                </motion.button>
              </div>

              <div className="glass rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider">User</th>
                        <th className="text-left px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden sm:table-cell">Video</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider">Score</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden md:table-cell">Quality</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden lg:table-cell">Faults</th>
                        <th className="text-center px-5 py-4 text-white/30 font-medium text-xs uppercase tracking-wider hidden sm:table-cell">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((s) => (
                        <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                          <td className="px-5 py-3.5">
                            <p className="text-white/80 font-medium text-sm">{s.user_name}</p>
                            <p className="text-white/25 text-xs">{s.user_email}</p>
                          </td>
                          <td className="px-5 py-3.5 text-white/40 hidden sm:table-cell truncate max-w-[140px]">{s.video_filename || "—"}</td>
                          <td className="px-5 py-3.5 text-center">
                            <span className={`inline-flex px-2 py-0.5 text-xs font-bold rounded-full border ${
                              s.overall_score !== null && s.overall_score <= 30
                                ? "text-golf-green bg-golf-green/10 border-golf-green/20"
                                : s.overall_score !== null && s.overall_score <= 50
                                ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                                : "text-red-400 bg-red-500/10 border-red-500/20"
                            }`}>
                              {s.overall_score?.toFixed(0) ?? "—"}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-center text-white/50 hidden md:table-cell">{s.swing_quality || "—"}</td>
                          <td className="px-5 py-3.5 text-center text-white/30 hidden lg:table-cell">{s.faults.length > 0 ? s.faults.slice(0, 3).join(", ") : "—"}</td>
                          <td className="px-5 py-3.5 text-center text-white/30 hidden sm:table-cell">
                            {new Date(s.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                          </td>
                        </tr>
                      ))}
                      {sessions.length === 0 && (
                        <tr>
                          <td colSpan={6} className="px-5 py-12 text-center text-white/20 text-sm">
                            No sessions found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "jobs" && (
            <motion.div key="jobs" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">Analysis Jobs</h3>
                <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={fetchJobs} className="flex items-center gap-2 px-3 py-1.5 text-xs text-white/40 hover:text-white glass border border-white/5 rounded-lg transition-all">
                  <RefreshCw size={11} /> Refresh
                </motion.button>
              </div>

              <div className="grid gap-3">
                {jobs.map((job: any) => (
                  <div key={job.job_id} className="glass rounded-xl p-4 flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
                      job.status === "done" ? "bg-golf-green" :
                      job.status === "running" ? "bg-amber-400 animate-pulse" :
                      job.status === "error" ? "bg-red-500" :
                      "bg-white/20"
                    }`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/70 font-medium truncate">{job.job_id?.substring(0, 8)}...</p>
                      <p className="text-xs text-white/30">{job.video_path ? job.video_path.split(/[\\/]/).pop() : "—"}</p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full border ${
                      job.status === "done" ? "text-golf-green bg-golf-green/10 border-golf-green/20" :
                      job.status === "running" ? "text-amber-400 bg-amber-500/10 border-amber-500/20" :
                      job.status === "error" ? "text-red-400 bg-red-500/10 border-red-500/20" :
                      "text-white/30 bg-white/5 border-white/10"
                    }`}>
                      {job.status}
                    </span>
                    {job.progress != null && (
                      <span className="text-xs text-white/40">{job.progress}%</span>
                    )}
                  </div>
                ))}
                {jobs.length === 0 && (
                  <div className="glass rounded-2xl p-12 text-center">
                    <Wrench size={32} className="text-white/15 mx-auto mb-3" />
                    <p className="text-white/30 text-sm">No analysis jobs in queue</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageWrapper>
  );
}
