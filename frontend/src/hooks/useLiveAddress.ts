import { useCallback, useEffect, useRef, useState } from "react";
import { LiveAddressSocket, type AddressFeedback } from "../api/live";

export function useLiveAddress() {
  const [feedback, setFeedback] = useState<AddressFeedback | null>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<LiveAddressSocket | null>(null);

  const connect = useCallback(() => {
    const sock = new LiveAddressSocket((fb) => setFeedback(fb));
    sock.connect();
    socketRef.current = sock;
    setConnected(true);
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
    socketRef.current = null;
    setConnected(false);
    setFeedback(null);
  }, []);

  const sendFrame = useCallback((dataUri: string) => {
    socketRef.current?.sendFrame(dataUri);
  }, []);

  useEffect(() => () => { socketRef.current?.disconnect(); }, []);

  return { feedback, connected, connect, disconnect, sendFrame };
}
