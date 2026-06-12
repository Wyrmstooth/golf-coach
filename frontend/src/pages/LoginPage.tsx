import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, Lock, AlertCircle, LogIn } from "lucide-react";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token, user } = await authApi.login(email, password);
      setAuth(user, access_token);
      navigate("/dashboard");
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Login failed. Check your credentials.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-golf-navy flex items-center justify-center px-4">
      {/* Ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[40rem] h-[20rem] bg-golf-green/[0.04] rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative"
      >
        <div className="glass rounded-2xl p-8 space-y-6">
          <div className="text-center space-y-1.5">
            <h1 className="font-display font-bold text-2xl">Welcome back</h1>
            <p className="text-white/45 text-sm">Sign in to your GolfCoach account</p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/15 rounded-xl px-4 py-3"
            >
              <AlertCircle size={15} className="flex-shrink-0" />
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-white/45 uppercase tracking-widest">
                Email
              </label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/15 outline-none focus:border-golf-green/40 focus:ring-2 focus:ring-golf-green/15 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-white/45 uppercase tracking-widest">
                Password
              </label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20 pointer-events-none" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="········"
                  className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/15 outline-none focus:border-golf-green/40 focus:ring-2 focus:ring-golf-green/15 transition-all"
                />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="w-full flex items-center justify-center gap-2 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                />
              ) : (
                <>
                  <LogIn size={15} />
                  Sign In
                </>
              )}
            </motion.button>
          </form>

          <p className="text-center text-sm text-white/30">
            Don't have an account?{" "}
            <Link to="/register" className="text-golf-green hover:text-golf-green/80 font-semibold transition-colors">
              Create one
            </Link>
          </p>
        </div>

        <p className="text-center mt-4">
          <Link to="/" className="text-xs text-white/20 hover:text-white/40 transition-colors">
            &larr; Back to home
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
