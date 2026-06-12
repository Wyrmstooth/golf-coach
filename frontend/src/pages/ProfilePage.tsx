import { useState } from "react";
import { motion } from "framer-motion";
import { User, Hash, Mail, Save, CheckCircle, AlertCircle, LogOut } from "lucide-react";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";

export default function ProfilePage() {
  const navigate  = useNavigate();
  const token     = useAuthStore((s) => s.token)!;
  const user      = useAuthStore((s) => s.user)!;
  const setUser   = useAuthStore((s) => s.setUser);
  const logout    = useAuthStore((s) => s.logout);

  const [displayName, setDisplayName] = useState(user.display_name);
  const [handicap, setHandicap]       = useState(user.handicap?.toString() ?? "");
  const [saving, setSaving]           = useState(false);
  const [saved, setSaved]             = useState(false);
  const [error, setError]             = useState<string | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const updated = await authApi.updateProfile(token, {
        display_name: displayName || undefined,
        handicap: handicap ? parseFloat(handicap) : undefined,
      });
      setUser(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Save failed. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/");
  }

  const joinDate = new Date(user.created_at).toLocaleDateString("en-US", {
    month: "long", year: "numeric",
  });

  return (
    <div className="min-h-screen bg-golf-navy pt-20 sm:pt-24 pb-16 px-4 sm:px-6">
      <div className="max-w-xl mx-auto space-y-6">

        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display font-bold text-2xl sm:text-3xl">Profile</h1>
          <p className="text-white/40 text-sm mt-1">Manage your account details</p>
        </motion.div>

        {/* Avatar + info */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6 flex items-center gap-5"
        >
          <div className="w-16 h-16 rounded-2xl bg-golf-green/10 ring-1 ring-golf-green/20 flex items-center justify-center flex-shrink-0">
            <span className="text-golf-green font-bold text-xl font-display">
              {user.avatar_initials ?? user.display_name.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-white font-semibold text-lg leading-tight">{user.display_name}</p>
            <p className="text-white/40 text-sm mt-0.5">{user.email}</p>
            <p className="text-white/25 text-xs mt-1">Member since {joinDate}</p>
          </div>
        </motion.div>

        {/* Edit form */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass rounded-2xl p-6 space-y-5"
        >
          <h2 className="text-xs font-semibold text-white/50 uppercase tracking-widest">Edit Details</h2>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/15 rounded-xl px-4 py-3"
            >
              <AlertCircle size={15} className="flex-shrink-0" />
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-white/40 uppercase tracking-widest">Email</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/12 pointer-events-none" />
                <input
                  type="email"
                  disabled
                  value={user.email}
                  className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl pl-10 pr-4 py-3 text-sm text-white/25 cursor-not-allowed"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-white/45 uppercase tracking-widest">Display Name</label>
              <div className="relative">
                <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20 pointer-events-none" />
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/15 outline-none focus:border-golf-green/40 focus:ring-2 focus:ring-golf-green/15 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-white/45 uppercase tracking-widest">
                Handicap Index
              </label>
              <div className="relative">
                <Hash size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20 pointer-events-none" />
                <input
                  type="number"
                  step="0.1"
                  min="-10"
                  max="54"
                  value={handicap}
                  onChange={(e) => setHandicap(e.target.value)}
                  placeholder="e.g. 18.4"
                  className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/15 outline-none focus:border-golf-green/40 focus:ring-2 focus:ring-golf-green/15 transition-all"
                />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={saving}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={`w-full flex items-center justify-center gap-2 font-semibold py-3 rounded-xl transition-all ${
                saved
                  ? "bg-golf-green/10 text-golf-green border border-golf-green/20"
                  : "btn-primary"
              } disabled:opacity-50`}
            >
              {saving ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                />
              ) : saved ? (
                <>
                  <CheckCircle size={15} />
                  Saved!
                </>
              ) : (
                <>
                  <Save size={15} />
                  Save Changes
                </>
              )}
            </motion.button>
          </form>
        </motion.div>

        {/* Sign out */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-6 space-y-3 border border-red-500/10"
        >
          <h2 className="text-[11px] font-semibold text-white/30 uppercase tracking-widest">Account</h2>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors font-medium"
          >
            <LogOut size={15} />
            Sign out
          </button>
        </motion.div>
      </div>
    </div>
  );
}
