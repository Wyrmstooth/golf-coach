export interface AddressFeedback {
  status: "ok" | "no_pose" | "error";
  angles: Record<string, number>;
  corrections: string[];
  overall: string;
  /** Base64 JPEG with MediaPipe skeleton drawn – present when status === "ok" */
  annotated_frame?: string;
}

export class LiveAddressSocket {
  private ws: WebSocket | null = null;
  private onMessage: (feedback: AddressFeedback) => void;

  constructor(onMessage: (feedback: AddressFeedback) => void) {
    this.onMessage = onMessage;
  }

  connect(): void {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname;
    const url = `${protocol}//${host}:8000/api/live/address`;
    this.ws = new WebSocket(url);
    this.ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data) as AddressFeedback;
        this.onMessage(data);
      } catch {
        // ignore parse errors
      }
    };
  }

  sendFrame(base64DataUri: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ frame: base64DataUri }));
    }
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
