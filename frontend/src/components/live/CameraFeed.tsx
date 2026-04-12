import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CameraOff, Crosshair } from "lucide-react";

interface Props {
  stream: MediaStream | null;
  mirrored?: boolean;
  onFrame?: (dataUri: string) => void;
  frameInterval?: number;
  /** Base64 JPEG returned by the server with MediaPipe skeleton drawn on it */
  annotatedFrame?: string | null;
}

export default function CameraFeed({
  stream,
  mirrored = true,
  onFrame,
  frameInterval = 200,
  annotatedFrame,
}: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch(() => {});
    }
    return () => {
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [stream]);

  useEffect(() => {
    if (!onFrame || !stream) return;

    intervalRef.current = setInterval(() => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState < 2) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Mirror the captured frame to match visual display — server draws
      // skeleton on the mirrored frame so the overlay lines up correctly.
      if (mirrored) {
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(video, -canvas.width, 0);
        ctx.restore();
      } else {
        ctx.drawImage(video, 0, 0);
      }

      onFrame(canvas.toDataURL("image/jpeg", 0.6));
    }, frameInterval);

    return () => clearInterval(intervalRef.current);
  }, [stream, onFrame, mirrored, frameInterval]);

  if (!stream) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass rounded-2xl flex items-center justify-center h-72 text-white/20"
      >
        <div className="flex flex-col items-center gap-3">
          <CameraOff size={36} />
          <p className="text-sm">Camera not active</p>
          <p className="text-xs text-white/15">Press "Start Camera" to begin</p>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="relative glass rounded-2xl overflow-hidden bg-black/40">
      {/* Raw video feed — hidden behind skeleton overlay when pose is detected */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-auto rounded-2xl block"
        style={{
          transform: mirrored ? "scaleX(-1)" : "none",
          // Fade out when the annotated frame is available so the skeleton
          // overlay takes over cleanly without a double-image.
          opacity: annotatedFrame ? 0 : 1,
          transition: "opacity 0.35s ease",
        }}
      />

      {/* Skeleton overlay — server-rendered frame with MediaPipe joints drawn */}
      <AnimatePresence>
        {annotatedFrame && (
          <motion.img
            key="skeleton"
            src={annotatedFrame}
            className="absolute inset-0 w-full h-full object-cover rounded-2xl"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            alt="pose skeleton"
          />
        )}
      </AnimatePresence>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* LIVE badge */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 glass px-2.5 py-1 rounded-full text-xs font-semibold z-10">
        <motion.div
          className="w-2 h-2 rounded-full bg-red-500"
          animate={{ opacity: [1, 0.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
        LIVE
      </div>

      {/* Skeleton tracking indicator */}
      <AnimatePresence>
        {annotatedFrame && (
          <motion.div
            key="tracking"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute top-3 right-3 flex items-center gap-1.5 glass-green px-2.5 py-1 rounded-full text-xs font-semibold text-golf-green z-10"
          >
            <Crosshair size={11} />
            Tracking
          </motion.div>
        )}
      </AnimatePresence>

      {/* Guide overlay when no skeleton yet — help user position themselves */}
      <AnimatePresence>
        {!annotatedFrame && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center pointer-events-none z-10"
          >
            <div
              className="border-2 border-white/15 rounded-2xl"
              style={{ width: "35%", height: "78%", borderStyle: "dashed" }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
