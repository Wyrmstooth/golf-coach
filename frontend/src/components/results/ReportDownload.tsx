import { useState } from "react";
import { motion } from "framer-motion";
import { Download, FileText, Loader2 } from "lucide-react";
import {
  pdf,
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Image as PDFImage,
} from "@react-pdf/renderer";
import type { AnalysisReport } from "../../api/analysis";

// ---------- PDF Styles ----------
const styles = StyleSheet.create({
  page: {
    backgroundColor: "#0f172a",
    color: "#ffffff",
    fontFamily: "Helvetica",
    padding: 36,
  },
  header: {
    borderBottomWidth: 2,
    borderBottomColor: "#16a34a",
    paddingBottom: 12,
    marginBottom: 20,
  },
  title: { fontSize: 24, fontFamily: "Helvetica-Bold", color: "#16a34a", marginBottom: 4 },
  subtitle: { fontSize: 10, color: "#94a3b8" },
  sectionTitle: {
    fontSize: 13,
    fontFamily: "Helvetica-Bold",
    color: "#16a34a",
    marginBottom: 8,
    marginTop: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#1e293b",
    paddingBottom: 4,
  },
  row: { flexDirection: "row", marginBottom: 6 },
  cell: { flex: 1, fontSize: 9, color: "#cbd5e1", padding: 6, backgroundColor: "#1e293b", marginRight: 4 },
  cellHeader: { flex: 1, fontSize: 9, fontFamily: "Helvetica-Bold", color: "#16a34a", padding: 6, backgroundColor: "#052e16", marginRight: 4 },
  faultBox: { backgroundColor: "#1e293b", padding: 8, marginBottom: 6, borderRadius: 4 },
  faultTitle: { fontSize: 10, fontFamily: "Helvetica-Bold", color: "#ffffff", marginBottom: 2 },
  faultDesc: { fontSize: 8, color: "#94a3b8", marginBottom: 2 },
  faultFix: { fontSize: 8, color: "#16a34a" },
  critical: { color: "#ef4444" },
  major:    { color: "#f97316" },
  minor:    { color: "#eab308" },
  scoreBox: { backgroundColor: "#052e16", padding: 16, borderRadius: 8, alignItems: "center", marginBottom: 16 },
  scoreNum: { fontSize: 48, fontFamily: "Helvetica-Bold", color: "#16a34a" },
  scoreLabel: { fontSize: 12, color: "#94a3b8" },
  metric: { flex: 1, backgroundColor: "#1e293b", padding: 10, marginRight: 4, borderRadius: 4, alignItems: "center" },
  metricValue: { fontSize: 20, fontFamily: "Helvetica-Bold", color: "#ca8a04" },
  metricLabel: { fontSize: 8, color: "#94a3b8", marginTop: 2 },
});

// ---------- PDF Document ----------
function GolfReport({ report, analysisDate }: { report: AnalysisReport; analysisDate: string }) {
  const score = report.fault_analysis.overall_score ?? 0;
  const quality = report.fault_analysis.swing_quality;
  const faults = report.fault_analysis.fault_details?.faults ?? [];
  const perf = report.performance_prediction;
  const ballDist = report.ball_tracking?.distance_estimation;
  const phases = Object.entries(report.phase_ranges);
  const summary = report.phase_fault_summary;

  const videoName = report.video.split(/[\\/]/).pop() ?? "video.mp4";

  return (
    <Document>
      {/* Page 1 – Cover */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>GolfCoach AI — Swing Analysis Report</Text>
          <Text style={styles.subtitle}>{videoName} · {analysisDate}</Text>
        </View>

        {/* Score */}
        <View style={styles.scoreBox}>
          <Text style={styles.scoreNum}>{score.toFixed(0)}</Text>
          <Text style={styles.scoreLabel}>Overall Swing Score / 100</Text>
          <Text style={{ fontSize: 14, color: "#16a34a", marginTop: 4, fontFamily: "Helvetica-Bold" }}>{quality}</Text>
        </View>

        {/* Summary table */}
        <Text style={styles.sectionTitle}>Fault Summary</Text>
        <View style={styles.row}>
          <Text style={styles.cellHeader}>Severity</Text>
          <Text style={styles.cellHeader}>Count</Text>
        </View>
        {(["critical", "major", "minor"] as const).map((sev) => (
          <View style={styles.row} key={sev}>
            <Text style={[styles.cell, styles[sev]]}>{sev.toUpperCase()}</Text>
            <Text style={styles.cell}>{report.fault_analysis.fault_details?.summary?.[`${sev}_count`] ?? 0}</Text>
          </View>
        ))}

        {/* Performance */}
        <Text style={styles.sectionTitle}>Performance Prediction</Text>
        <View style={styles.row}>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{perf?.BallSpeed?.toFixed(0) ?? "—"}</Text>
            <Text style={styles.metricLabel}>Ball Speed (mph)</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{(ballDist?.distance_yards ?? perf?.Distance)?.toFixed(0) ?? "—"}</Text>
            <Text style={styles.metricLabel}>Distance (yds)</Text>
          </View>
          <View style={[styles.metric, { marginRight: 0 }]}>
            <Text style={styles.metricValue}>{(ballDist?.carry_yards ?? perf?.Carry)?.toFixed(0) ?? "—"}</Text>
            <Text style={styles.metricLabel}>Carry (yds)</Text>
          </View>
        </View>
      </Page>

      {/* Page 2 – Phase Breakdown */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Phase Breakdown</Text>
          <Text style={styles.subtitle}>{videoName}</Text>
        </View>
        <View style={styles.row}>
          {(["Phase", "Frames", "Max Severity", "Total Faults", "Top Fault"] as const).map((h) => (
            <Text key={h} style={styles.cellHeader}>{h}</Text>
          ))}
        </View>
        {phases.map(([phase, [start, end]]) => {
          const s = summary[phase];
          const total = (s?.counts.critical ?? 0) + (s?.counts.major ?? 0) + (s?.counts.minor ?? 0);
          return (
            <View style={styles.row} key={phase}>
              <Text style={styles.cell}>{phase.replace("_", " ")}</Text>
              <Text style={styles.cell}>{start}–{end}</Text>
              <Text style={[styles.cell, styles[(s?.max_severity as "critical" | "major" | "minor") ?? "minor"] ?? {}]}>{s?.max_severity ?? "none"}</Text>
              <Text style={styles.cell}>{total}</Text>
              <Text style={styles.cell}>{s?.top_fault_titles?.[0] ?? "—"}</Text>
            </View>
          );
        })}
      </Page>

      {/* Page 3 – Fault Details */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Fault Details</Text>
          <Text style={styles.subtitle}>All detected swing faults with corrective guidance</Text>
        </View>
        {faults.length === 0 ? (
          <Text style={{ color: "#16a34a", fontSize: 14, marginTop: 20 }}>No faults detected — excellent swing!</Text>
        ) : (
          faults.map((f, i) => (
            <View style={styles.faultBox} key={i}>
              <Text style={[styles.faultTitle, styles[(f.severity as "critical" | "major" | "minor")] ?? {}]}>
                [{f.severity.toUpperCase()}] {f.title} — {f.phase.replace("_", " ")}
              </Text>
              <Text style={styles.faultDesc}>{f.description} (Measured: {f.value.toFixed(1)}°, Expected: {f.expected})</Text>
              <Text style={styles.faultFix}>Fix: {f.fix}</Text>
            </View>
          ))
        )}
      </Page>

      {/* Page 4 – Ball Tracking */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Ball Tracking & Distance</Text>
          <Text style={styles.subtitle}>Module 3 — Vision-based or ML-predicted distance</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.cellHeader}>Metric</Text>
          <Text style={styles.cellHeader}>Value</Text>
        </View>
        {[
          ["Tracking Status", report.ball_tracking?.status ?? "—"],
          ["Method", ballDist?.method ?? "—"],
          ["Confidence", ballDist ? `${ballDist.confidence.toFixed(0)}%` : "—"],
          ["Carry Distance", ballDist ? `${ballDist.carry_yards.toFixed(1)} yds` : "—"],
          ["Total Distance", ballDist ? `${ballDist.distance_yards.toFixed(1)} yds` : "—"],
          ["Trajectory Points", String(report.ball_tracking?.trajectory_2d?.length ?? 0)],
        ].map(([k, v]) => (
          <View style={styles.row} key={k}>
            <Text style={styles.cell}>{k}</Text>
            <Text style={styles.cell}>{v}</Text>
          </View>
        ))}
      </Page>
    </Document>
  );
}

// ---------- Component ----------
interface Props {
  report: AnalysisReport;
}

export default function ReportDownload({ report }: Props) {
  const [generating, setGenerating] = useState(false);

  const handleDownload = async () => {
    setGenerating(true);
    try {
      const date = new Date().toLocaleDateString("en-US", {
        year: "numeric", month: "long", day: "numeric",
      });
      const blob = await pdf(<GolfReport report={report} analysisDate={date} />).toBlob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "GolfCoach_Analysis_Report.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.04, boxShadow: "0 0 24px rgba(202,138,4,0.4)" }}
      whileTap={{ scale: 0.97 }}
      onClick={handleDownload}
      disabled={generating}
      className="flex items-center gap-2.5 px-6 py-3 bg-golf-gold/10 border border-golf-gold/40 text-golf-gold rounded-xl hover:bg-golf-gold/20 transition-all duration-200 font-semibold text-sm disabled:opacity-60"
    >
      {generating ? (
        <Loader2 size={16} className="animate-spin" />
      ) : (
        <FileText size={16} />
      )}
      {generating ? "Generating PDF..." : "Download Full Report"}
      {!generating && <Download size={14} className="text-golf-gold/60" />}
    </motion.button>
  );
}
