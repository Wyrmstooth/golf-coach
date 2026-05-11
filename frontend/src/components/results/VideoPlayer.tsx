import { forwardRef, useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Play, Pause, Download, Loader2 } from "lucide-react";

interface Props {
  videoUrl: string;
  phaseRanges: Record<string, [number, number]>;
  fps?: number;
  jobId?: string;
  filename?: string;
}

const PHASE_COLORS: Record<string, string> = {
  ADDRESS:        "#6b7280",
  BACKSWING:      "#3b82f6",
  TOP:            "#f59e0b",
  DOWNSWING:      "#22c55e",
  IMPACT:         "#ef4444",
  FOLLOW_THROUGH: "#a855f7",
};

const VideoPlayer = forwardRef<HTMLVideoElement, Props>(
  ({ videoUrl, phaseRanges, fps = 30, filename }, ref) => {
    const [playing, setPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [videoError, setVideoError] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const internalRef = useRef<HTMLVideoElement | null>(null);
    const videoRef = (ref as React.RefObject<HTMLVideoElement | null>) ?? internalRef;

    const handleVideoError = () => {
      setVideoError(true);
    };

    const handleDownload = useCallback(async () => {
      setDownloading(true);
      try {
        const res = await fetch(videoUrl);
        if (!res.ok) throw new Error("Download failed");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename ?? "annotated_swing.mp4";
        a.click();
        URL.revokeObjectURL(url);
      } catch {
        // fallback: open in new tab
        window.open(videoUrl, "_blank");
      } finally {
        setDownloading(false);
      }
    }, [videoUrl, filename]);

    const handlePlayPause = () => {
      if (!videoRef.current) return;
      if (playing) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    };

    const handleTimeUpdate = () => {
      if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
    };

    const handleDurationChange = () => {
      if (videoRef.current) setDuration(videoRef.current.duration);
    };

    const seekTo = (t: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = t;
      }
    };

    const progressPct = duration ? (currentTime / duration) * 100 : 0;

    // Build phase tick marks on the scrubber
    const totalFrames = duration * fps || 1;
    const phaseTicks = Object.entries(phaseRanges).map(([phase, [start]]) => ({
      phase,
      pct: (start / totalFrames) * 100,
      color: PHASE_COLORS[phase] ?? "#fff",
      timeAtStart: start / fps,
    }));

    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl overflow-hidden"
      >
        {/* Video */}
        <div className="relative bg-black">
          {videoError ? (
            <div className="w-full aspect-video flex items-center justify-center bg-black/80 text-white/40 text-sm">
              <div className="text-center space-y-2">
                <p>Annotated video unavailable</p>
                <p className="text-xs text-white/20">Try analyzing again or use a different video format</p>
              </div>
            </div>
          ) : (
            <video
              ref={videoRef}
              src={videoUrl}
              className="w-full max-h-[500px] object-contain"
              onTimeUpdate={handleTimeUpdate}
              onDurationChange={handleDurationChange}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              onError={handleVideoError}
              crossOrigin="anonymous"
            />
          )}
          {/* Center play overlay */}
          {!playing && !videoError && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={handlePlayPause}
              className="absolute inset-0 flex items-center justify-center bg-black/40"
            >
              <div className="w-16 h-16 rounded-full bg-golf-green/80 flex items-center justify-center shadow-glow backdrop-blur-sm">
                <Play size={28} className="text-white ml-1" />
              </div>
            </motion.button>
          )}
        </div>

        {/* Controls */}
        <div className="px-4 pb-4 pt-3 space-y-2">
          {/* Scrubber with phase ticks */}
          <div className="relative">
            <div
              className="relative h-2 bg-white/10 rounded-full cursor-pointer overflow-visible"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const pct = (e.clientX - rect.left) / rect.width;
                seekTo(pct * duration);
              }}
            >
              {/* Progress fill */}
              <div
                className="absolute left-0 top-0 h-full bg-golf-green rounded-full transition-all duration-150"
                style={{ width: `${progressPct}%` }}
              />
              {/* Phase tick marks */}
              {phaseTicks.map(({ phase, pct, color, timeAtStart }) => (
                <button
                  key={phase}
                  title={`${phase.replace("_", " ")} (${timeAtStart.toFixed(1)}s)`}
                  onClick={(e) => {
                    e.stopPropagation();
                    seekTo(timeAtStart);
                  }}
                  className="absolute top-1/2 -translate-y-1/2 w-1 h-4 rounded-sm cursor-pointer hover:scale-125 transition-transform"
                  style={{ left: `${pct}%`, backgroundColor: color, zIndex: 10 }}
                />
              ))}
            </div>
          </div>

          {/* Time and controls row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={handlePlayPause}
                className="w-8 h-8 glass rounded-lg flex items-center justify-center hover:bg-golf-green/20 transition-colors"
              >
                {playing ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
              </button>
              <span className="text-xs text-white/40 font-mono">
                {currentTime.toFixed(1)}s / {duration.toFixed(1)}s
              </span>
            </div>

            <button
              onClick={handleDownload}
              disabled={downloading}
              className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white transition-colors px-3 py-1.5 glass rounded-lg disabled:opacity-50"
            >
              {downloading ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Download size={12} />
              )}
              {downloading ? "Saving..." : "Download"}
            </button>
          </div>

          {/* Phase legend */}
          <div className="flex flex-wrap gap-2 pt-1">
            {Object.entries(PHASE_COLORS).map(([phase, color]) => (
              <button
                key={phase}
                onClick={() => {
                  const range = phaseRanges[phase];
                  if (range) seekTo(range[0] / fps);
                }}
                className="flex items-center gap-1 text-[10px] text-white/40 hover:text-white/80 transition-colors"
              >
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                {phase.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    );
  }
);

VideoPlayer.displayName = "VideoPlayer";

export default VideoPlayer;
