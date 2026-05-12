import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Video, X, CheckCircle, Film } from "lucide-react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export default function VideoDropzone({ onFile, disabled }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length === 0) return;
      const file = accepted[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      onFile(file);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "video/*": [".mp4", ".mov", ".avi", ".mkv"] },
    maxFiles: 1,
    disabled,
  });

  const clear = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!selectedFile ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
          >
            <div
              {...getRootProps()}
              className={`relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300 p-10 sm:p-14 text-center ${
                isDragActive
                  ? "border-golf-green bg-golf-green/[0.06] shadow-glow"
                  : "border-white/[0.12] hover:border-golf-green/50 hover:bg-golf-green/[0.03]"
              } ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}
            >
              <input {...getInputProps()} />
              {isDragActive && (
                <motion.div
                  className="absolute inset-0 rounded-2xl border-2 border-golf-green/60"
                  animate={{ scale: [1, 1.02, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                />
              )}
              <div className="flex flex-col items-center gap-4">
                <motion.div
                  animate={isDragActive ? { scale: 1.15, rotate: [0, -8, 8, 0] } : { scale: 1 }}
                  transition={{ duration: 0.4 }}
                  className="w-18 h-18 rounded-full bg-golf-green/10 ring-1 ring-golf-green/20 flex items-center justify-center"
                >
                  <Film size={32} className="text-golf-green" />
                </motion.div>
                <div>
                  <p className="text-lg font-semibold">
                    {isDragActive ? "Drop it here!" : "Drop your swing video"}
                  </p>
                  <p className="text-sm text-white/40 mt-1.5">
                    or <span className="text-golf-green font-medium underline decoration-golf-green/30 underline-offset-2">browse files</span>
                  </p>
                  <p className="text-xs text-white/25 mt-3">MP4, MOV, AVI &middot; up to 500MB</p>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="preview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass rounded-2xl overflow-hidden"
          >
            <div className="relative">
              {previewUrl && (
                <video
                  src={previewUrl}
                  className="w-full h-52 object-cover"
                  muted
                  playsInline
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-golf-navy/95 via-transparent to-transparent" />
              <button
                onClick={clear}
                disabled={disabled}
                className="absolute top-3 right-3 w-9 h-9 glass rounded-full flex items-center justify-center hover:bg-red-500/20 transition-colors border border-white/[0.08]"
              >
                <X size={15} />
              </button>
              <div className="absolute bottom-0 left-0 right-0 p-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-golf-green/15 ring-1 ring-golf-green/20 flex items-center justify-center flex-shrink-0">
                  <Video size={16} className="text-golf-green" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{selectedFile.name}</p>
                  <p className="text-xs text-white/40">
                    {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
                  </p>
                </div>
                <CheckCircle size={18} className="text-golf-green flex-shrink-0" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
