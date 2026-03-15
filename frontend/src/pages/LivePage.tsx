import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Camera, CameraOff, Activity, Video } from "lucide-react";

import PageWrapper from "../components/layout/PageWrapper";
import CameraFeed from "../components/live/CameraFeed";
import AddressMetrics from "../components/live/AddressMetrics";
import LiveSwingRecorder from "../components/live/LiveSwingRecorder";
import { useLiveAddress } from "../hooks/useLiveAddress";

type Tab = "address" | "swing";

export default function LivePage() {
  const [tab, setTab] = useState<Tab>("address");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const { feedback, connected, connect, disconnect, sendFrame } = useLiveAddress();

  const startCamera = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: "user" },
        audio: false,
      });
      setStream(s);
      setCameraError(null);
    } catch (err: any) {
      setCameraError(err?.message ?? "Camera access denied.");
    }
  };

  const stopCamera = () => {
    stream?.getTracks().forEach((t) => t.stop());
    setStream(null);
    disconnect();
  };

  const toggleCamera = () => {
    if (stream) stopCamera();
    else startCamera();
  };

  // When tab === address and camera is on, connect WS
  useEffect(() => {
    if (tab === "address" && stream && !connected) {
      connect();
    }
    if (tab !== "address" && connected) {
      disconnect();
    }
  }, [tab, stream, connected, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => () => { stream?.getTracks().forEach((t) => t.stop()); }, [stream]);

  return (
    <PageWrapper className="bg-golf-navy">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-display text-4xl font-bold">
            Live <span className="text-gradient">Feedback</span>
          </h1>
          <p className="text-white/40 mt-2">
            Real-time posture correction and swing analysis using your webcam.
          </p>
        </motion.div>

        {/* Tab toggle */}
        <div className="flex gap-2 mb-8 glass p-1 rounded-xl w-fit">
          {[
            { id: "address" as Tab, label: "Address Check", icon: Activity },
            { id: "swing" as Tab, label: "Record Swing", icon: Video },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                tab === id
                  ? "bg-golf-green text-white shadow-glow"
                  : "text-white/50 hover:text-white"
              }`}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Camera column */}
          <div className="lg:col-span-2 space-y-4">
            {/* Camera toggle */}
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">Camera Feed</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.97 }}
                onClick={toggleCamera}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  stream
                    ? "bg-red-500/20 border border-red-500/40 text-red-400 hover:bg-red-500/30"
                    : "bg-golf-green/20 border border-golf-green/40 text-golf-green hover:bg-golf-green/30 shadow-glow"
                }`}
              >
                {stream ? <CameraOff size={15} /> : <Camera size={15} />}
                {stream ? "Stop Camera" : "Start Camera"}
              </motion.button>
            </div>

            {cameraError && (
              <div className="glass rounded-xl px-4 py-3 text-red-400 text-sm border border-red-500/30">
                {cameraError}
              </div>
            )}

            <CameraFeed
              stream={stream}
              mirrored
              onFrame={tab === "address" && connected ? sendFrame : undefined}
              frameInterval={200}
            />

            {tab === "swing" && (
              <LiveSwingRecorder stream={stream} />
            )}
          </div>

          {/* Right panel */}
          <div className="space-y-4">
            {tab === "address" ? (
              <>
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
                  Real-time Feedback
                </h3>
                <AddressMetrics feedback={feedback} connected={connected} />
                <div className="glass rounded-xl p-4 text-xs text-white/40 space-y-1 leading-relaxed">
                  <p className="font-semibold text-white/60">How to use:</p>
                  <p>1. Start your camera</p>
                  <p>2. Stand in your address position, facing the camera</p>
                  <p>3. Get real-time feedback on your spine, knee, and arm angles</p>
                  <p>4. Adjust until all metrics show green</p>
                </div>
              </>
            ) : (
              <div className="glass rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
                  How to Record
                </h3>
                <div className="space-y-3 text-xs text-white/50 leading-relaxed">
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-golf-green">1.</span>
                    <span>Start your camera and position it to capture your full swing</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-golf-green">2.</span>
                    <span>Click "Start Recording" — a 3-second countdown will begin</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-golf-green">3.</span>
                    <span>Perform your swing during the 5-second recording window</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-golf-green">4.</span>
                    <span>Your video is sent for AI analysis — results appear in ~2 minutes</span>
                  </div>
                </div>
                <div className="glass-green rounded-xl p-3 text-xs text-golf-green/70">
                  Tip: For best results, set up the camera at hip height, 8–12 feet away, facing you from the side.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
