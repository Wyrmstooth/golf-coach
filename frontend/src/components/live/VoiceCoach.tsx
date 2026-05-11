import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, VolumeX, Mic, ChevronDown } from "lucide-react";

interface Props {
  feedback: { corrections?: string[]; overall?: string; status?: string } | null;
  connected: boolean;
}

function cleanText(text: string): string {
  return text.replace(/[•\-–—*]/g, "").replace(/\s+/g, " ").trim();
}

export default function VoiceCoach({ feedback, connected }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [lastSpoken, setLastSpoken] = useState<string | null>(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  const spokeRef = useRef<Set<string>>(new Set());
  const lastFeedbackRef = useRef<string | null>(null);

  useEffect(() => {
    const handleVoices = () => {
      const available = speechSynthesis.getVoices();
      setVoices(available);
      if (!selectedVoice && available.length > 0) {
        const english = available.filter(
          (v) => v.lang.startsWith("en") && v.localService
        );
        setSelectedVoice(english[0] ?? available[0]);
      }
    };
    handleVoices();
    speechSynthesis.addEventListener("voiceschanged", handleVoices);
    return () => speechSynthesis.removeEventListener("voiceschanged", handleVoices);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!enabled || !text) return;
      const cleaned = cleanText(text);
      if (cleaned.length < 2) return;

      if (spokeRef.current.has(cleaned)) return;
      spokeRef.current.add(cleaned);

      // Clean up old entries (keep last 10)
      const entries = Array.from(spokeRef.current);
      if (entries.length > 10) {
        spokeRef.current = new Set(entries.slice(-10));
      }

      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      if (selectedVoice) utterance.voice = selectedVoice;

      utterance.onstart = () => {
        setSpeaking(true);
        setLastSpoken(cleaned);
      };
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);

      speechSynthesis.speak(utterance);
    },
    [enabled, selectedVoice]
  );

  useEffect(() => {
    if (!feedback || !enabled || !connected) return;

    const status = feedback.status;
    const overall = feedback.overall;
    const corrections = feedback.corrections ?? [];

    // Speak overall status changes
    if (overall && overall !== lastFeedbackRef.current) {
      lastFeedbackRef.current = overall;
      if (overall === "GOOD ADDRESS") {
        speak("Good address position. Hold it right there.");
      } else if (overall !== "DETECTING...") {
        speak(`Adjust position. ${corrections.length} correction${corrections.length !== 1 ? "s" : ""} needed.`);
      }
    }

    // Speak individual corrections (only new ones)
    if (corrections.length > 0) {
      corrections.slice(0, 2).forEach((c) => {
        if (c && c.trim()) speak(c);
      });
    }
  }, [feedback, enabled, connected, speak]);

  // Re-speak last on toggle on
  useEffect(() => {
    if (enabled && lastSpoken) {
      spokeRef.current.clear();
    }
  }, [enabled]);

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setEnabled((e) => !e)}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
            enabled
              ? "bg-golf-green/20 border border-golf-green/30 text-golf-green"
              : "glass border border-white/10 text-white/40 hover:text-white/70"
          }`}
          title={enabled ? "Voice feedback on" : "Voice feedback off"}
        >
          {enabled ? (
            <motion.div
              animate={speaking ? { scale: [1, 1.18, 1] } : { scale: 1 }}
              transition={{ duration: 0.8, repeat: speaking ? Infinity : 0 }}
            >
              <Volume2 size={14} />
            </motion.div>
          ) : (
            <VolumeX size={14} />
          )}
          <span className="hidden sm:inline">
            {enabled ? (speaking ? "Speaking..." : "Voice On") : "Voice Off"}
          </span>
        </motion.button>

        {/* Voice picker */}
        {enabled && voices.length > 1 && (
          <>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setVoiceOpen((o) => !o)}
              className="flex items-center gap-1 px-2.5 py-2 rounded-xl text-xs glass border border-white/10 text-white/40 hover:text-white/70 transition-colors"
            >
              <span className="truncate max-w-[60px] hidden sm:inline">
                {selectedVoice?.name.split(" ").slice(0, 2).join(" ") ?? "Voice"}
              </span>
              <ChevronDown size={10} />
            </motion.button>

            <AnimatePresence>
              {voiceOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.97 }}
                  className="absolute left-0 top-full mt-1 w-56 max-h-52 overflow-y-auto glass rounded-xl border border-white/10 py-1 z-50 shadow-xl"
                >
                  {voices
                    .filter((v) => v.lang.startsWith("en"))
                    .map((v) => (
                      <button
                        key={v.name}
                        onClick={() => {
                          setSelectedVoice(v);
                          setVoiceOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-xs transition-colors truncate ${
                          selectedVoice?.name === v.name
                            ? "text-golf-green bg-golf-green/10"
                            : "text-white/50 hover:text-white/80 hover:bg-white/5"
                        }`}
                      >
                        {v.name}
                      </button>
                    ))}
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>

      {/* Last spoken bubble */}
      <AnimatePresence>
        {enabled && lastSpoken && speaking && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2 glass rounded-xl px-3 py-2 flex items-start gap-2 border border-golf-green/15"
          >
            <Mic size={12} className="text-golf-green mt-0.5 flex-shrink-0" />
            <p className="text-xs text-white/60 leading-relaxed line-clamp-2">
              {lastSpoken}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
