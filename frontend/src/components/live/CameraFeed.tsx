import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { CameraOff } from "lucide-react";

interface Props {
  stream: MediaStream | null;
  mirrored?: boolean;
  onFrame?: (dataUri: string) => void;
  frameInterval?: number; // ms between captures
}

export default function CameraFeed({ stream, mirrored = true, onFrame, frameInterval = 200 }: Props) {
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
      <div className="glass rounded-2xl flex items-center justify-center h-72 text-white/30">
        <div className="flex flex-col items-center gap-3">
          <CameraOff size={36} />
          <p className="text-sm">Camera not active</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative glass rounded-2xl overflow-hidden">
      <motion.video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-auto rounded-2xl"
        style={{ transform: mirrored ? "scaleX(-1)" : "none" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      />
      <canvas ref={canvasRef} className="hidden" />
      {/* Live indicator */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 glass px-2.5 py-1 rounded-full text-xs font-semibold">
        <motion.div
          className="w-2 h-2 rounded-full bg-red-500"
          animate={{ opacity: [1, 0.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
        LIVE
      </div>
    </div>
  );
}
