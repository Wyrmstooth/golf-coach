import { useCallback, useEffect, useRef, useState } from "react";
import { LiveAddressSocket, type AddressFeedback } from "../api/live";

export function useLiveAddress() {
  const [feedback, setFeedback] = useState<AddressFeedback | null>(null);
  const [annotatedFrame, setAnnotatedFrame] = useState<string | null>(null);
  const [poseHoldMs, setPoseHoldMs] = useState(0);
  const [connected, setConnected] = useState(false);

  const socketRef = useRef<LiveAddressSocket | null>(null);
  const frameInFlightRef = useRef(false);
  // Timer to delay clearing metrics when pose is briefly lost
  const poseLostTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track when we entered a "good" position for the hold timer
  const goodSinceRef = useRef<number | null>(null);
  const holdIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const _stopHoldTimer = useCallback(() => {
    goodSinceRef.current = null;
    if (holdIntervalRef.current) { clearInterval(holdIntervalRef.current); holdIntervalRef.current = null; }
    setPoseHoldMs(0);
  }, []);

  const handleFeedback = useCallback((fb: AddressFeedback) => {
    frameInFlightRef.current = false;

    if (fb.status === "ok") {
      // Pose is visible – cancel any pending "pose lost" clear
      if (poseLostTimerRef.current) {
        clearTimeout(poseLostTimerRef.current);
        poseLostTimerRef.current = null;
      }

      // Update skeleton frame
      setAnnotatedFrame(fb.annotated_frame ?? null);
      setFeedback(fb);

      // Hold timer – only when position is actually good
      if (fb.overall === "GOOD ADDRESS") {
        if (goodSinceRef.current === null) {
          goodSinceRef.current = Date.now();
          holdIntervalRef.current = setInterval(() => {
            if (goodSinceRef.current !== null) {
              setPoseHoldMs(Date.now() - goodSinceRef.current);
            }
          }, 250);
        }
      } else {
        _stopHoldTimer();
      }
    } else if (fb.status === "no_pose") {
      // Skeleton gone
      setAnnotatedFrame(null);
      _stopHoldTimer();

      // Keep showing last metrics for 3 s before showing "no pose" state
      if (!poseLostTimerRef.current) {
        poseLostTimerRef.current = setTimeout(() => {
          setFeedback({ status: "no_pose", angles: {}, corrections: [], overall: "DETECTING..." });
          poseLostTimerRef.current = null;
        }, 3000);
      }
    }
  }, [_stopHoldTimer]);

  const connect = useCallback(() => {
    const sock = new LiveAddressSocket(handleFeedback);
    sock.connect();
    socketRef.current = sock;
    setConnected(true);
  }, [handleFeedback]);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
    socketRef.current = null;
    setConnected(false);
    setFeedback(null);
    setAnnotatedFrame(null);
    frameInFlightRef.current = false;
    _stopHoldTimer();
    if (poseLostTimerRef.current) { clearTimeout(poseLostTimerRef.current); poseLostTimerRef.current = null; }
  }, [_stopHoldTimer]);

  const sendFrame = useCallback((dataUri: string) => {
    if (frameInFlightRef.current) return;
    if (!socketRef.current) return;
    frameInFlightRef.current = true;
    socketRef.current.sendFrame(dataUri);
  }, []);

  useEffect(() => () => {
    socketRef.current?.disconnect();
    frameInFlightRef.current = false;
    if (poseLostTimerRef.current) clearTimeout(poseLostTimerRef.current);
    if (holdIntervalRef.current) clearInterval(holdIntervalRef.current);
  }, []);

  return { feedback, annotatedFrame, poseHoldMs, connected, connect, disconnect, sendFrame };
}
