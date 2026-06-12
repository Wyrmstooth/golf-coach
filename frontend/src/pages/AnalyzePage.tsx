import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, Image, Target, AlertCircle, RefreshCw, Clock, TrendingUp, Camera, ShieldCheck, Sparkles, Settings2 } from "lucide-react";

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
import { validateVideo } from "../api/admin";
import type { VideoValidation } from "../api/admin";

type Phase = "idle" | "validating" | "validated" | "analyzing" | "done" | "error";

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [validation, setValidation] = useState<VideoValidation | null>(null);
  const { jobId, setJobId, report, reset } = useAppStore();
  const { status, progress, error: jobError } = useAnalysisJob(jobId);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [searchParams] = useSearchParams();
  const didLoadJob = useRef(false);

  // Analysis options toggles
  const [showOptions, setShowOptions] = useState(false);
  const [optBallTracking, setOptBallTracking] = useState(true);
  const [optPerformance, setOptPerformance] = useState(true);
  const [optVideoRender, setOptVideoRender] = useState(true);

  // Load past analysis from URL param (works with both hash and regular routing)
  useEffect(() => {
    if (didLoadJob.current) return;
    // Try react-router search params first, then fall back to parsing the hash
    let jobParam = searchParams.get("job");
    if (!jobParam) {
      const hash = window.location.hash;
      const hashParams = new URLSearchParams(hash.includes("?") ? hash.split("?")[1] : "");
      jobParam = hashParams.get("job");
    }
    if (jobParam && !jobId) {
      didLoadJob.current = true;
      setJobId(jobParam);
      setPhase("analyzing");
    }
  }, [searchParams, jobId, setJobId]);

  // Transition phases based on analysis status (in useEffect, not render body)
  useEffect(() => {
    if (phase === "analyzing" && status === "done" && report) {
      setPhase("done");
    }
    if (phase === "analyzing" && status === "error") {
      setPhase("error");
      if (!errorMsg) {
        setErrorMsg(
          typeof jobError === "string"
            ? jobError
            : jobError?.message ?? "Analysis failed. The backend may be missing required ML packages."
        );
      }
    }
  }, [phase, status, report, jobError, errorMsg]);

  const handleAnalyze = async () => {
    if (!file) return;
    reset();
    setErrorMsg(null);
    setValidation(null);

    setPhase("validating");
    try {
      const v = await validateVideo(file);
      setValidation(v);
      setPhase("validated");

      await new Promise((r) => setTimeout(r, 800));

      setPhase("analyzing");
      const { job_id } = await uploadVideo(file, {
        skipBallTracking: !optBallTracking,
        skipPerformance: !optPerformance,
        skipVideoRender: !optVideoRender,
      });
      setJobId(job_id);
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail ?? err?.message;
      setErrorMsg(
        detail ?? "Failed to process video. Make sure the backend is running on port 8000."
      );
      setPhase("error");
    }
  };

  const handleReset = () => {
    reset();
    setFile(null);
    setErrorMsg(null);
    setValidation(null);
    setPhase("idle");
  };

  const videoFilename = report?.outputs?.annotated_video
    ? report.outputs.annotated_video.split(/[\\/]/).pop()
    : undefined;
  const videoUrl = report?.outputs?.annotated_video_data_uri
    ?? (report?.outputs?.annotated_video && jobId
      ? getFileUrl(jobId, report.outputs.annotated_video.split(/[\\/]/).pop() ?? report.outputs.annotated_video)
      : null);

  const ballPlotUrl = report?.outputs?.ball_plot_data_uri
    ?? (report?.outputs?.ball_plot && jobId
      ? getFileUrl(jobId, report.outputs.ball_plot.split(/[\\/]/).pop() ?? report.outputs.ball_plot)
      : null);

  const plotUrl = report?.outputs?.plot_data_uri
    ?? (report?.outputs?.plot && jobId
      ? getFileUrl(jobId, report.outputs.plot.split(/[\\/]/).pop() ?? report.outputs.plot)
      : null);

  const phaseScreenshots = report?.outputs?.phase_screenshot_data_uris ?? report?.outputs?.phase_screenshots ?? {};
  const screenshotEntries = Object.entries(phaseScreenshots).filter(([, path]) => path);

  return (
    <PageWrapper className="bg-golf-navy">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 sm:mb-10"
        >
          <h1 className="font-display text-3xl sm:text-4xl font-bold">
            Swing <span className="text-gradient">Analysis</span>
          </h1>
          <p className="text-white/45 mt-2 text-sm sm:text-base">
            Upload your golf swing video and get an AI-powered biomechanical report.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {(phase === "idle" || phase === "validating" || phase === "validated") && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="max-w-2xl mx-auto space-y-6"
            >
              {phase === "idle" && (
                <>
                  <VideoDropzone onFile={setFile} />

                  {/* ── Analysis Options ── */}
                  <div className="glass rounded-xl border border-white/[0.06] overflow-hidden">
                    <button
                      onClick={() => setShowOptions(!showOptions)}
                      className="w-full flex items-center justify-between px-5 py-3 text-sm text-white/40 hover:text-white/60 transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        <Settings2 size={13} />
                        Analysis Options
                      </span>
                      <motion.span
                        animate={{ rotate: showOptions ? 180 : 0 }}
                        className="text-white/25 text-xs"
                      >
                        ▼
                      </motion.span>
                    </button>
                    {showOptions && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="px-5 pb-4 space-y-3"
                      >
                        <label className="flex items-center justify-between cursor-pointer">
                          <span className="text-xs text-white/50">Ball Tracking</span>
                          <button
                            onClick={() => setOptBallTracking(!optBallTracking)}
                            className={`relative w-9 h-5 rounded-full transition-colors ${optBallTracking ? "bg-golf-green" : "bg-white/[0.12]"}`}
                          >
                            <motion.div
                              animate={{ x: optBallTracking ? 16 : 2 }}
                              className="w-3.5 h-3.5 rounded-full bg-white absolute top-0.5"
                            />
                          </button>
                        </label>
                        <label className="flex items-center justify-between cursor-pointer">
                          <span className="text-xs text-white/50">Performance Predictor</span>
                          <button
                            onClick={() => setOptPerformance(!optPerformance)}
                            className={`relative w-9 h-5 rounded-full transition-colors ${optPerformance ? "bg-golf-green" : "bg-white/[0.12]"}`}
                          >
                            <motion.div
                              animate={{ x: optPerformance ? 16 : 2 }}
                              className="w-3.5 h-3.5 rounded-full bg-white absolute top-0.5"
                            />
                          </button>
                        </label>
                        <label className="flex items-center justify-between cursor-pointer">
                          <span className="text-xs text-white/50">Annotated Video</span>
                          <button
                            onClick={() => setOptVideoRender(!optVideoRender)}
                            className={`relative w-9 h-5 rounded-full transition-colors ${optVideoRender ? "bg-golf-green" : "bg-white/[0.12]"}`}
                          >
                            <motion.div
                              animate={{ x: optVideoRender ? 16 : 2 }}
                              className="w-3.5 h-3.5 rounded-full bg-white absolute top-0.5"
                            />
                          </button>
                        </label>
                      </motion.div>
                    )}
                  </div>

                  <motion.button
                    whileHover={file ? { scale: 1.03, boxShadow: "0 0 36px rgba(16,185,129,0.5)" } : {}}
                    whileTap={file ? { scale: 0.97 } : {}}
                    onClick={handleAnalyze}
                    disabled={!file}
                    className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
                      file
                        ? "btn-primary shadow-glow"
                        : "bg-white/[0.04] text-white/25 cursor-not-allowed border border-white/[0.06]"
                    }`}
                  >
                    <span className="flex items-center justify-center gap-2">
                      <Sparkles size={20} />
                      Analyze My Swing
                    </span>
                  </motion.button>
                  <p className="text-center text-xs text-white/30">
                    Video is first validated to confirm it contains a golf swing. Full analysis takes 30–120 seconds.
                  </p>
                </>
              )}

              {phase === "validating" && (
                <div className="glass rounded-2xl p-8 text-center space-y-5">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-12 h-12 mx-auto border-2 border-golf-green/30 border-t-golf-green rounded-full"
                  />
                  <div>
                    <h3 className="font-display font-bold text-lg mb-1">Validating Video</h3>
                    <p className="text-white/45 text-sm">
                      Checking if your video contains a golf swing with detectable poses and keypoints...
                    </p>
                  </div>
                </div>
              )}

              {phase === "validated" && validation && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="glass rounded-2xl p-6 text-center space-y-4 border border-golf-green/20"
                >
                  <div className="w-14 h-14 mx-auto rounded-full bg-golf-green/10 ring-1 ring-golf-green/20 flex items-center justify-center">
                    <ShieldCheck size={28} className="text-golf-green" />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-lg text-golf-green mb-1">Video Valid</h3>
                    <p className="text-white/45 text-sm">
                      Golf swing detected. {validation.pose_detection_ratio && `Pose confidence: ${(validation.pose_detection_ratio * 100).toFixed(0)}% · `}
                      {validation.frame_count} frames · {validation.duration_sec}s
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-xs text-white/35">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-golf-green/30 border-t-golf-green rounded-full"
                    />
                    Starting full analysis...
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

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

          {phase === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="max-w-lg mx-auto"
            >
              <div className="glass rounded-2xl p-8 text-center space-y-6 border border-red-500/20">
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
                  <p className="text-white/55 text-sm leading-relaxed">
                    {errorMsg || "An unexpected error occurred during analysis."}
                  </p>
                </div>

                <div className="glass rounded-xl p-4 text-left space-y-2 text-xs text-white/45">
                  <p className="font-semibold text-white/55">Common causes:</p>
                  <p>· Missing ML packages: <code className="text-golf-green">pip install scikit-learn opencv-python mediapipe</code></p>
                  <p>· Unsupported video format (try MP4)</p>
                  <p>· Backend not running on port 8000</p>
                  <p>· Video too short or corrupted</p>
                </div>

                <div className="flex gap-3 justify-center">
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={handleAnalyze}
                    className="flex items-center gap-2 px-6 py-3 bg-golf-green/15 border border-golf-green/30 text-golf-green rounded-xl font-semibold text-sm hover:bg-golf-green/25 transition-all"
                  >
                    <RefreshCw size={14} /> Try Again
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={handleReset}
                    className="flex items-center gap-2 px-6 py-3 glass text-white/55 rounded-xl text-sm hover:text-white hover:border-white/[0.18] transition-all"
                  >
                    <RotateCcw size={14} /> New Video
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}

          {phase === "done" && report && (
            <motion.div
              key="done"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-8"
            >
              {/* ── Hero Card ── */}
              <div className="glass rounded-2xl p-6 sm:p-8 flex flex-col lg:flex-row items-center gap-8">
                <SwingScoreRing
                  score={report.fault_analysis.overall_score ?? 0}
                  quality={report.fault_analysis.swing_quality}
                  faultSummary={report.fault_analysis.fault_details?.summary}
                />
                <div className="flex-1 space-y-4 text-center lg:text-left">
                  <div>
                    <h2 className="font-display text-2xl sm:text-3xl font-bold">
                      Swing <span className="text-gradient">Report</span>
                    </h2>
                    <p className="text-white/35 text-xs sm:text-sm mt-1">
                      {report.video.split(/[\\/]/).pop()} &middot; AI-powered biomechanical analysis
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3 justify-center lg:justify-start">
                    {report && jobId && <ReportDownload report={report} jobId={jobId} />}
                    <motion.button
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={handleReset}
                      className="flex items-center gap-2 px-5 py-3 glass text-sm text-white/55 hover:text-white hover:border-white/[0.18] rounded-xl transition-all"
                    >
                      <RotateCcw size={14} /> Analyze Another
                    </motion.button>
                  </div>
                </div>
              </div>

              {/* ── Quick Stats ── */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  {
                    icon: TrendingUp,
                    label: "Swing Score",
                    value: report.fault_analysis.overall_score ?? 0,
                    unit: "/100",
                    sub: report.fault_analysis.swing_quality,
                    color: "text-golf-green",
                    bg: "bg-golf-green/5",
                  },
                  {
                    icon: Target,
                    label: "Faults Found",
                    value: report.fault_analysis.fault_details?.summary?.total_faults ?? 0,
                    unit: "",
                    sub: `${report.fault_analysis.fault_details?.summary?.critical_count ?? 0} critical`,
                    color: "text-red-400",
                    bg: "bg-red-500/5",
                  },
                  {
                    icon: Clock,
                    label: "Swing Phases",
                    value: Object.keys(report.phase_ranges).length,
                    unit: "",
                    sub: `${Object.values(report.phase_ranges).flat().reduce((a, b) => Math.max(a, b), 0)} total frames`,
                    color: "text-blue-400",
                    bg: "bg-blue-500/5",
                  },
                  {
                    icon: Camera,
                    label: "Ball Tracking",
                    value: report.ball_tracking?.enabled ? "Active" : "Off",
                    unit: "",
                    sub: report.ball_tracking?.status?.replace(/_/g, " ") ?? "N/A",
                    color: report.ball_tracking?.status === "success" ? "text-golf-green" : "text-amber-400",
                    bg: report.ball_tracking?.status === "success" ? "bg-golf-green/5" : "bg-amber-500/5",
                  },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className={`glass rounded-xl p-5 ${stat.bg} border border-white/[0.06]`}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <stat.icon size={15} className={stat.color} />
                      <span className="text-[10px] text-white/40 uppercase tracking-wider font-semibold">{stat.label}</span>
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className={`font-display font-bold text-2xl ${stat.color}`}>{stat.value}</span>
                      {stat.unit && <span className="text-white/25 text-xs">{stat.unit}</span>}
                    </div>
                    <div className="text-[10px] text-white/30 mt-1 capitalize">{stat.sub}</div>
                  </motion.div>
                ))}
              </div>

              {/* ── Video Player ── */}
              {videoUrl && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Camera size={15} className="text-white/30" />
                    <h3 className="text-xs font-semibold text-white/45 uppercase tracking-widest">Annotated Video</h3>
                  </div>
                  <VideoPlayer
                    ref={videoRef}
                    videoUrl={videoUrl}
                    phaseRanges={report.phase_ranges}
                    fps={30}
                    jobId={jobId ?? undefined}
                    filename={videoFilename ?? undefined}
                  />
                </section>
              )}

              {/* ── Phase Timeline ── */}
              <section className="glass rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-5">
                  <Clock size={15} className="text-white/30" />
                  <h3 className="text-xs font-semibold text-white/45 uppercase tracking-widest">Phase Breakdown</h3>
                </div>
                <PhaseTimeline
                  phaseRanges={report.phase_ranges}
                  phaseFaultSummary={report.phase_fault_summary}
                  fps={30}
                  videoRef={videoRef as React.RefObject<HTMLVideoElement>}
                />
              </section>

              {/* ── Fault Analysis + Performance ── */}
              <div className="grid lg:grid-cols-5 gap-6">
                <section className="lg:col-span-3 glass rounded-2xl p-6 space-y-5">
                  <div className="flex items-center gap-2">
                    <Target size={15} className="text-white/30" />
                    <h3 className="text-xs font-semibold text-white/45 uppercase tracking-widest">Fault Analysis</h3>
                  </div>
                  <FaultCards faultDetails={report.fault_analysis.fault_details} />
                </section>
                <section className="lg:col-span-2 space-y-5">
                  <div className="glass rounded-2xl p-6">
                    <PerformanceMetrics
                      performance={report.performance_prediction}
                      ballTracking={report.ball_tracking}
                    />
                  </div>
                </section>
              </div>

              {/* ── Ball Trajectory Chart ── */}
              <BallTrajectoryChart
                trajectory={report.ball_tracking?.trajectory_2d ?? []}
                phaseRanges={report.phase_ranges}
                fps={30}
                ballTracking={report.ball_tracking}
              />

              {/* ── Plot Images ── */}
              {(plotUrl || ballPlotUrl) && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Image size={15} className="text-white/30" />
                    <h3 className="text-xs font-semibold text-white/45 uppercase tracking-widest">Trajectory Plots</h3>
                  </div>
                  <div className="grid md:grid-cols-2 gap-5">
                    {plotUrl && (
                      <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass rounded-2xl p-5 space-y-3 group cursor-pointer hover:border-white/[0.14] transition-all"
                      >
                        <div className="flex items-center gap-2">
                          <Image size={14} className="text-white/30" />
                          <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wider">Wrist Trajectory</span>
                          <span className="text-[9px] text-white/20 ml-auto opacity-0 group-hover:opacity-100 transition-opacity">Click to expand</span>
                        </div>
                        <div className="relative rounded-xl overflow-hidden bg-white/[0.02] border border-white/[0.06]">
                          <img
                            src={plotUrl}
                            alt="Swing analysis plot"
                            className="w-full h-auto object-contain"
                            style={{ maxHeight: "420px" }}
                          />
                        </div>
                      </motion.div>
                    )}
                    {ballPlotUrl && (
                      <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="glass rounded-2xl p-5 space-y-3 group cursor-pointer hover:border-white/[0.14] transition-all"
                      >
                        <div className="flex items-center gap-2">
                          <Target size={14} className="text-white/30" />
                          <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wider">Ball Trajectory</span>
                          <span className="text-[9px] text-white/20 ml-auto opacity-0 group-hover:opacity-100 transition-opacity">Click to expand</span>
                        </div>
                        <div className="relative rounded-xl overflow-hidden bg-white/[0.02] border border-white/[0.06]">
                          <img
                            src={ballPlotUrl}
                            alt="Ball trajectory plot"
                            className="w-full h-auto object-contain"
                            style={{ maxHeight: "420px" }}
                          />
                        </div>
                      </motion.div>
                    )}
                  </div>
                </section>
              )}

              {/* ── Phase Screenshots ── */}
              {screenshotEntries.length > 0 && (
                <motion.section
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-2xl p-6 space-y-4"
                >
                  <div className="flex items-center gap-2">
                    <Camera size={15} className="text-white/30" />
                    <h3 className="text-xs font-semibold text-white/45 uppercase tracking-widest">Phase Snapshots</h3>
                    <span className="text-[9px] text-white/25 ml-auto">{screenshotEntries.length} phases</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {screenshotEntries.map(([phase, path]) => {
                      if (!path) return null;
                      return (
                        <div key={phase} className="space-y-2">
                          <div className="relative rounded-lg overflow-hidden border border-white/[0.08] hover:border-white/[0.15] group/card transition-all">
                            <img
                              src={path}
                              alt={`${phase} screenshot`}
                              className="w-full aspect-video object-cover"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover/card:opacity-100 transition-opacity" />
                          </div>
                          <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wide block text-center">
                            {phase.replace(/_/g, " ")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </motion.section>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageWrapper>
  );
}
