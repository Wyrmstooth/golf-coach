import React, { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, Image, Target, AlertCircle, RefreshCw, Clock, TrendingUp, Camera } from "lucide-react";

import PageWrapper from "../components/layout/PageWrapper";
import VideoDropzone from "../components/upload/VideoDropzone";
import AnalysisProgress from "../components/upload/AnalysisProgress";
import SwingScoreRing from "../components/results/SwingScoreRing";
import PhaseTimeline from "../components/results/PhaseTimeline";
import FaultCards from "../components/results/FaultCards";
import PerformanceMetrics from "../components/results/PerformanceMetrics";
import BallTrajectoryChart from "../components/results/BallTrajectoryChart";
import VideoPlayer from "../components/results/VideoPlayer";
import ReportDownload from "../components/results/ReportDownload";

import { uploadVideo } from "../api/analysis";
import { getFileUrl } from "../api/analysis";
import { useAnalysisJob } from "../hooks/useAnalysisJob";
import { useAppStore } from "../store/appStore";

type Phase = "idle" | "analyzing" | "done" | "error";

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { jobId, setJobId, report, reset } = useAppStore();
  const { status, progress, error: jobError } = useAnalysisJob(jobId);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Transition to done when report arrives
  if (phase === "analyzing" && status === "done" && report) {
    setPhase("done");
  }

  // Transition to error when job fails
  if (phase === "analyzing" && status === "error") {
    setPhase("error");
    if (!errorMsg) {
      setErrorMsg(
        typeof jobError === "string"
          ? jobError
          : jobError?.message ?? "Analysis failed. The backend may be missing required ML packages (scikit-learn, opencv, mediapipe)."
      );
    }
  }

  const handleAnalyze = async () => {
    if (!file) return;
    reset();
    setErrorMsg(null);
    setPhase("analyzing");
    try {
      const { job_id } = await uploadVideo(file);
      setJobId(job_id);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err?.response?.data?.detail ??
          err?.message ??
          "Failed to upload video. Make sure the backend is running on port 8000."
      );
      setPhase("error");
    }
  };

  const handleReset = () => {
    reset();
    setFile(null);
    setErrorMsg(null);
    setPhase("idle");
  };

  // Build video URL from report outputs
  const videoFilename = report?.outputs?.annotated_video
    ? report.outputs.annotated_video.split(/[\\/]/).pop()
    : null;
  const videoUrl = jobId && videoFilename
    ? getFileUrl(jobId, videoFilename)
    : null;

  // Ball trajectory plot image
  const ballPlotFilename = report?.outputs?.ball_plot
    ? report.outputs.ball_plot.split(/[\\/]/).pop()
    : null;
  const ballPlotUrl = jobId && ballPlotFilename
    ? getFileUrl(jobId, ballPlotFilename)
    : null;

  // Wrist trajectory plot
  const plotFilename = report?.outputs?.plot
    ? report.outputs.plot.split(/[\\/]/).pop()
    : null;
  const plotUrl = jobId && plotFilename
    ? getFileUrl(jobId, plotFilename)
    : null;

  // Phase screenshots
  const phaseScreenshots = report?.outputs?.phase_screenshots ?? {};
  const screenshotEntries = Object.entries(phaseScreenshots).filter(([, path]) => path);

  return (
    <PageWrapper className="bg-golf-navy">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="font-display text-4xl font-bold">
            Swing <span className="text-gradient">Analysis</span>
          </h1>
          <p className="text-white/40 mt-2">
            Upload your golf swing video and get an AI-powered biomechanical report.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {/* IDLE */}
          {phase === "idle" && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="max-w-2xl mx-auto space-y-6"
            >
              <VideoDropzone onFile={setFile} />
              <motion.button
                whileHover={file ? { scale: 1.03, boxShadow: "0 0 32px rgba(22,163,74,0.5)" } : {}}
                whileTap={file ? { scale: 0.97 } : {}}
                onClick={handleAnalyze}
                disabled={!file}
                className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
                  file
                    ? "bg-golf-green text-white shadow-glow hover:bg-green-500"
                    : "bg-white/5 text-white/30 cursor-not-allowed"
                }`}
              >
                Analyze My Swing
              </motion.button>
              <p className="text-center text-xs text-white/25">
                Analysis takes 30–120 seconds depending on video length.
              </p>
            </motion.div>
          )}

          {/* ANALYZING */}
          {phase === "analyzing" && (
            <motion.div
              key="analyzing"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="flex flex-col items-center"
            >
              <AnalysisProgress status={status} progress={progress} />
            </motion.div>
          )}

          {/* ERROR */}
          {phase === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="max-w-lg mx-auto"
            >
              <div className="glass rounded-2xl p-8 text-center space-y-6 border border-red-500/30">
                {/* Error golf ball */}
                <div className="relative mx-auto w-16 h-16">
                  <div className="golf-ball w-16 h-16 opacity-50" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <AlertCircle size={28} className="text-red-400" />
                  </div>
                </div>

                <div>
                  <h3 className="font-display font-bold text-xl text-red-400 mb-2">
                    Analysis Failed
                  </h3>
                  <p className="text-white/50 text-sm leading-relaxed">
                    {errorMsg || "An unexpected error occurred during analysis."}
                  </p>
                </div>

                {/* Common troubleshooting */}
                <div className="glass rounded-xl p-4 text-left space-y-2 text-xs text-white/40">
                  <p className="font-semibold text-white/60">Common causes:</p>
                  <p>• Missing ML packages: <code className="text-golf-green">pip install scikit-learn opencv-python mediapipe</code></p>
                  <p>• Unsupported video format (try MP4)</p>
                  <p>• Backend not running on port 8000</p>
                  <p>• Video too short or corrupted</p>
                </div>

                <div className="flex gap-3 justify-center">
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={handleAnalyze}
                    className="flex items-center gap-2 px-6 py-3 bg-golf-green/20 border border-golf-green/40 text-golf-green rounded-xl font-semibold text-sm hover:bg-golf-green/30 transition-all"
                  >
                    <RefreshCw size={14} /> Retry Analysis
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={handleReset}
                    className="flex items-center gap-2 px-6 py-3 glass border border-white/10 text-white/60 rounded-xl text-sm hover:text-white hover:border-white/30 transition-all"
                  >
                    <RotateCcw size={14} /> Upload Different Video
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}

          {/* DONE */}
          {phase === "done" && report && (
            <motion.div
              key="done"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-10"
            >
              {/* Top bar: score + actions */}
              <div className="glass rounded-2xl p-6 flex flex-col lg:flex-row items-center gap-8">
                <SwingScoreRing
                  score={report.fault_analysis.overall_score ?? 0}
                  quality={report.fault_analysis.swing_quality}
                  faultSummary={report.fault_analysis.fault_details?.summary}
                />
                <div className="flex-1 space-y-4">
                  <div className="flex flex-wrap gap-3 items-center">
                    <h2 className="font-display text-2xl font-bold">Analysis Complete</h2>
                    <span className="text-xs text-white/40 glass px-3 py-1 rounded-full">
                      {report.fault_analysis.fault_details?.summary?.total_faults ?? 0} faults found
                    </span>
                  </div>
                  <p className="text-white/50 text-sm">
                    Video: <span className="text-white/70">{report.video.split(/[\\/]/).pop()}</span>
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {report && jobId && <ReportDownload report={report} jobId={jobId} />}

                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={handleReset}
                      className="flex items-center gap-2 px-5 py-3 glass border border-white/10 rounded-xl text-sm text-white/60 hover:text-white hover:border-white/30 transition-all"
                    >
                      <RotateCcw size={14} /> Analyze Another
                    </motion.button>
                  </div>
                </div>
              </div>

              {/* Quick stats row */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  {
                    icon: Target,
                    label: "Faults Found",
                    value: `${report.fault_analysis.fault_details?.summary?.total_faults ?? 0}`,
                    sub: `${report.fault_analysis.fault_details?.summary?.critical_count ?? 0} critical`,
                    color: "text-red-400",
                  },
                  {
                    icon: TrendingUp,
                    label: "Swing Score",
                    value: `${report.fault_analysis.overall_score ?? 0}/100`,
                    sub: report.fault_analysis.swing_quality,
                    color: "text-golf-green",
                  },
                  {
                    icon: Clock,
                    label: "Phases Analyzed",
                    value: `${Object.keys(report.phase_ranges).length}`,
                    sub: `${Object.values(report.phase_ranges).flat().reduce((a, b) => Math.max(a, b), 0)} frames`,
                    color: "text-blue-400",
                  },
                  {
                    icon: Camera,
                    label: "Tracking",
                    value: report.ball_tracking?.enabled ? "Active" : "ML Fallback",
                    sub: report.ball_tracking?.status?.replace("_", " ") ?? "N/A",
                    color: "text-amber-400",
                  },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="glass rounded-xl p-4 border border-white/5"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <stat.icon size={14} className="text-white/30" />
                      <span className="text-[10px] text-white/40 uppercase tracking-wider font-semibold">{stat.label}</span>
                    </div>
                    <div className={`font-display font-bold text-lg ${stat.color}`}>{stat.value}</div>
                    <div className="text-[10px] text-white/30 mt-0.5">{stat.sub}</div>
                  </motion.div>
                ))}
              </div>

              {/* Phase timeline */}
              <div className="glass rounded-2xl p-6">
                <PhaseTimeline
                  phaseRanges={report.phase_ranges}
                  phaseFaultSummary={report.phase_fault_summary}
                  fps={30}
                  videoRef={videoRef as React.RefObject<HTMLVideoElement>}
                />
              </div>

              {/* Two-column layout */}
              <div className="grid lg:grid-cols-5 gap-6">
                {/* Faults (wider) */}
                <div className="lg:col-span-3 glass rounded-2xl p-6 space-y-4">
                  <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
                    Fault Analysis
                  </h3>
                  <FaultCards faultDetails={report.fault_analysis.fault_details} />
                </div>

                {/* Side: perf + annotated video */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="glass rounded-2xl p-6">
                    <PerformanceMetrics
                      performance={report.performance_prediction}
                      ballTracking={report.ball_tracking}
                    />
                  </div>

                  {videoUrl && (
                    <VideoPlayer
                      ref={videoRef}
                      videoUrl={videoUrl}
                      phaseRanges={report.phase_ranges}
                      fps={30}
                      jobId={jobId ?? undefined}
                      filename={videoFilename ?? undefined}
                    />
                  )}
                </div>
              </div>

              {/* Ball trajectory */}
              <BallTrajectoryChart
                trajectory={report.ball_tracking?.trajectory_2d ?? []}
                phaseRanges={report.phase_ranges}
                fps={30}
                ballTracking={report.ball_tracking}
              />

              {/* Phase screenshots */}
              {screenshotEntries.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-2xl p-6 space-y-4"
                >
                  <div className="flex items-center gap-2">
                    <Camera size={14} className="text-white/40" />
                    <span className="text-sm font-semibold text-white/60 uppercase tracking-widest">Phase Snapshots</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {screenshotEntries.map(([phase, path]) => {
                      const filename = path.split(/[\\/]/).pop();
                      const url = jobId && filename ? `/api/files/${jobId}/${filename}` : null;
                      if (!url) return null;
                      return (
                        <div key={phase} className="space-y-1.5">
                          <img
                            src={url}
                            alt={`${phase} screenshot`}
                            className="w-full aspect-video object-cover rounded-lg border border-white/10"
                          />
                          <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wide block text-center">
                            {phase.replace("_", " ")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}

              {/* Plot images */}
              <div className="grid md:grid-cols-2 gap-6">
                {plotUrl && (
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass rounded-2xl p-4 space-y-3"
                  >
                    <div className="flex items-center gap-2">
                      <Image size={14} className="text-white/40" />
                      <span className="text-xs text-white/40 font-semibold uppercase tracking-wider">
                        Wrist Trajectory Plot
                      </span>
                    </div>
                    <img
                      src={plotUrl}
                      alt="Swing analysis plot"
                      className="w-full rounded-lg"
                    />
                  </motion.div>
                )}
                {ballPlotUrl && (
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="glass rounded-2xl p-4 space-y-3"
                  >
                    <div className="flex items-center gap-2">
                      <Target size={14} className="text-white/40" />
                      <span className="text-xs text-white/40 font-semibold uppercase tracking-wider">
                        Ball Trajectory Plot
                      </span>
                    </div>
                    <img
                      src={ballPlotUrl}
                      alt="Ball trajectory plot"
                      className="w-full rounded-lg"
                    />
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageWrapper>
  );
}
