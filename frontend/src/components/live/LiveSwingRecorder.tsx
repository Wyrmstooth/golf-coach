import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Video, Square, Loader2, RotateCcw } from "lucide-react";
import axios from "axios";
import type { AnalysisReport } from "../../api/analysis";
import { getApiBase } from "../../api/base";
import SwingScoreRing from "../results/SwingScoreRing";
import FaultCards from "../results/FaultCards";
import PerformanceMetrics from "../results/PerformanceMetrics";
import ReportDownload from "../results/ReportDownload";

type RecorderState = "idle" | "countdown" | "recording" | "processing" | "done" | "error";

interface Props {
  stream: MediaStream | null;
}

export default function LiveSwingRecorder({ stream }: Props) {
  const [state, setState] = useState<RecorderState>("idle");
  const [countdown, setCountdown] = useState(3);
  const [progress, setProgress] = useState(0);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = () => {
    if (!stream) return;
    setState("countdown");
    let cnt = 3;
    setCountdown(cnt);

    const tick = setInterval(() => {
      cnt--;
      setCountdown(cnt);
      if (cnt === 0) {
        clearInterval(tick);
        doRecord();
      }
    }, 1000);
  };

  const doRecord = () => {
    if (!stream) return;
    chunksRef.current = [];

    const mimeType = ["video/webm;codecs=vp9", "video/webm", "video/mp4"].find(
      (m) => MediaRecorder.isTypeSupported(m)
    ) ?? "";

    const mr = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = mr;

    mr.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    mr.onstop = async () => {
      setState("processing");
      const blob = new Blob(chunksRef.current, { type: mimeType || "video/webm" });
      const ext = mimeType.includes("mp4") ? ".mp4" : ".webm";
      const file = new File([blob], `swing${ext}`, { type: blob.type });

      try {
        const form = new FormData();
        form.append("file", file);
        const { data } = await axios.post<AnalysisReport>(`${getApiBase()}/live/swing`, form, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 300_000,
          onUploadProgress: (e) => {
            if (e.total) setProgress(Math.round((e.loaded / e.total) * 30));
          },
        });
        setReport(data);
        setState("done");
      } catch (err: any) {
        setError(err?.response?.data?.detail ?? "Analysis failed. Please try again.");
        setState("error");
      }
    };

    setState("recording");
    mr.start(100);

    // Record for 5 seconds
    let elapsed = 0;
    const progInterval = setInterval(() => {
      elapsed += 100;
      setProgress(Math.min(Math.round((elapsed / 5000) * 100), 99));
    }, 100);

    setTimeout(() => {
      clearInterval(progInterval);
      mr.stop();
    }, 5000);
  };

  const reset = () => {
    setState("idle");
    setReport(null);
    setError(null);
    setProgress(0);
  };

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">
        {/* IDLE */}
        {state === "idle" && (
          <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.button
              whileHover={{ scale: 1.03, boxShadow: "0 0 32px rgba(22,163,74,0.5)" }}
              whileTap={{ scale: 0.97 }}
              onClick={startRecording}
              disabled={!stream}
              className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${
                stream
                  ? "bg-golf-green text-white shadow-glow"
                  : "bg-white/5 text-white/30 cursor-not-allowed"
              }`}
            >
              <Video size={20} />
              {stream ? "Start Recording (5 sec)" : "Enable camera first"}
            </motion.button>
          </motion.div>
        )}

        {/* COUNTDOWN */}
        {state === "countdown" && (
          <motion.div
            key="countdown"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4 py-8"
          >
            <motion.div
              key={countdown}
              initial={{ scale: 1.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="font-display font-extrabold text-8xl text-gradient"
            >
              {countdown}
            </motion.div>
            <p className="text-white/50">Get ready to swing!</p>
          </motion.div>
        )}

        {/* RECORDING */}
        {state === "recording" && (
          <motion.div
            key="recording"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 justify-center">
              <motion.div
                className="w-4 h-4 rounded-full bg-red-500"
                animate={{ opacity: [1, 0.2, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              />
              <span className="font-bold text-red-400">RECORDING</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-red-500 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.1 }}
              />
            </div>
            <button
              onClick={() => mediaRecorderRef.current?.stop()}
              className="w-full py-3 glass border border-red-500/40 text-red-400 rounded-xl flex items-center justify-center gap-2 hover:bg-red-500/10 transition-colors"
            >
              <Square size={16} /> Stop Early
            </button>
          </motion.div>
        )}

        {/* PROCESSING */}
        {state === "processing" && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4 py-8"
          >
            <Loader2 size={36} className="text-golf-green animate-spin" />
            <p className="font-semibold text-white">Analyzing your swing...</p>
            <div className="w-48 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-golf-green rounded-full"
                animate={{ width: ["0%", "90%"] }}
                transition={{ duration: 30, ease: "easeOut" }}
              />
            </div>
            <p className="text-xs text-white/30">This may take up to 2 minutes</p>
          </motion.div>
        )}

        {/* DONE */}
        {state === "done" && report && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass rounded-2xl p-6 flex flex-col items-center gap-4">
              <SwingScoreRing
                score={report.fault_analysis.overall_score ?? 0}
                quality={report.fault_analysis.swing_quality}
              />
              <div className="flex gap-3">
                <ReportDownload report={report} />
                <button
                  onClick={reset}
                  className="flex items-center gap-2 px-4 py-2.5 glass rounded-xl text-sm text-white/60 hover:text-white transition-colors"
                >
                  <RotateCcw size={14} /> Record Again
                </button>
              </div>
            </div>
            <div className="glass rounded-2xl p-6">
              <FaultCards faultDetails={report.fault_analysis.fault_details} />
            </div>
            <PerformanceMetrics performance={report.performance_prediction} ballTracking={report.ball_tracking} />
          </motion.div>
        )}

        {/* ERROR */}
        {state === "error" && (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass rounded-2xl p-6 text-center space-y-4 border border-red-500/30"
          >
            <div className="text-3xl">❌</div>
            <p className="text-red-400 font-semibold">{error}</p>
            <button onClick={reset} className="px-6 py-2.5 bg-red-500/20 text-red-400 rounded-xl text-sm hover:bg-red-500/30 transition-colors">
              Try Again
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
