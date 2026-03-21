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
  row: { flexDirection: "row", marginBottom: 4 },
  cell: { flex: 1, fontSize: 9, color: "#cbd5e1", padding: 6, backgroundColor: "#1e293b", marginRight: 4 },
  cellHeader: { flex: 1, fontSize: 9, fontFamily: "Helvetica-Bold", color: "#16a34a", padding: 6, backgroundColor: "#052e16", marginRight: 4 },
  faultBox: { backgroundColor: "#1e293b", padding: 8, marginBottom: 6, borderRadius: 4 },
  faultTitle: { fontSize: 10, fontFamily: "Helvetica-Bold", color: "#ffffff", marginBottom: 2 },
  faultDesc: { fontSize: 8, color: "#94a3b8", marginBottom: 2 },
  faultFix: { fontSize: 8, color: "#16a34a" },
  faultMeasurement: { fontSize: 8, color: "#cbd5e1", marginBottom: 2 },
  critical: { color: "#ef4444" },
  major:    { color: "#f97316" },
  minor:    { color: "#eab308" },
  scoreBox: { backgroundColor: "#052e16", padding: 16, borderRadius: 8, alignItems: "center", marginBottom: 16 },
  scoreNum: { fontSize: 48, fontFamily: "Helvetica-Bold", color: "#16a34a" },
  scoreLabel: { fontSize: 12, color: "#94a3b8" },
  metric: { flex: 1, backgroundColor: "#1e293b", padding: 10, marginRight: 4, borderRadius: 4, alignItems: "center" },
  metricValue: { fontSize: 20, fontFamily: "Helvetica-Bold", color: "#ca8a04" },
  metricLabel: { fontSize: 8, color: "#94a3b8", marginTop: 2 },
  footer: { position: "absolute", bottom: 20, left: 36, right: 36, flexDirection: "row", justifyContent: "space-between", borderTopWidth: 1, borderTopColor: "#1e293b", paddingTop: 8 },
  footerText: { fontSize: 7, color: "#475569" },
  phaseHeader: { fontSize: 12, fontFamily: "Helvetica-Bold", color: "#ffffff", backgroundColor: "#052e16", padding: 8, marginTop: 12, marginBottom: 4, borderRadius: 4 },
  phaseScore: { fontSize: 9, color: "#16a34a", fontFamily: "Helvetica-Bold" },
  noFaults: { fontSize: 9, color: "#16a34a", padding: 8 },
  warningBox: { backgroundColor: "#f9731620", padding: 8, borderRadius: 4, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: "#f97316" },
  successBox: { backgroundColor: "#16a34a15", padding: 8, borderRadius: 4, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: "#16a34a" },
});

const PHASE_ORDER = ["ADDRESS", "BACKSWING", "TOP", "DOWNSWING", "IMPACT", "FOLLOW_THROUGH"];
const PHASE_LABELS: Record<string, string> = {
  ADDRESS: "Address",
  BACKSWING: "Backswing",
  TOP: "Top of Swing",
  DOWNSWING: "Downswing",
  IMPACT: "Impact",
  FOLLOW_THROUGH: "Follow Through",
};

// ---------- PDF Document ----------
function GolfReport({ report, analysisDate }: { report: AnalysisReport; analysisDate: string }) {
  const score = report.fault_analysis.overall_score ?? 0;
  const quality = report.fault_analysis.swing_quality;
  const faults = report.fault_analysis.fault_details?.faults ?? [];
  const perf = report.performance_prediction;
  const ballDist = report.ball_tracking?.distance_estimation;
  const phases = Object.entries(report.phase_ranges);
  const summary = report.phase_fault_summary;
  const byPhase = report.fault_analysis.fault_details?.by_phase ?? {};

  const videoName = report.video.split(/[\\/]/).pop() ?? "video.mp4";
  const totalFaults = report.fault_analysis.fault_details?.summary?.total_faults ?? 0;

  return (
    <Document>
      {/* Page 1 – Cover + Summary */}
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

        {/* Fault summary table */}
        <Text style={styles.sectionTitle}>Fault Summary</Text>
        <View style={styles.row}>
          <Text style={styles.cellHeader}>Severity</Text>
          <Text style={styles.cellHeader}>Count</Text>
          <Text style={styles.cellHeader}>Percentage</Text>
        </View>
        {(["critical", "major", "minor"] as const).map((sev) => {
          const count = report.fault_analysis.fault_details?.summary?.[`${sev}_count`] ?? 0;
          return (
            <View style={styles.row} key={sev}>
              <Text style={[styles.cell, styles[sev]]}>{sev.toUpperCase()}</Text>
              <Text style={styles.cell}>{count}</Text>
              <Text style={styles.cell}>{totalFaults > 0 ? ((count / totalFaults) * 100).toFixed(0) : 0}%</Text>
            </View>
          );
        })}

        {/* Performance metrics */}
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

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 1 of 4</Text>
        </View>
      </Page>

      {/* Page 2 – Phase Breakdown */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Phase Breakdown</Text>
          <Text style={styles.subtitle}>{videoName} · {analysisDate}</Text>
        </View>
        <View style={styles.row}>
          {(["Phase", "Frames", "Severity", "Faults", "Score", "Top Fault"] as const).map((h) => (
            <Text key={h} style={styles.cellHeader}>{h}</Text>
          ))}
        </View>
        {phases.map(([phase, [start, end]]) => {
          const s = summary[phase];
          const total = (s?.counts.critical ?? 0) + (s?.counts.major ?? 0) + (s?.counts.minor ?? 0);
          return (
            <View style={styles.row} key={phase}>
              <Text style={styles.cell}>{PHASE_LABELS[phase] ?? phase.replace("_", " ")}</Text>
              <Text style={styles.cell}>{start}–{end}</Text>
              <Text style={[styles.cell, styles[(s?.max_severity as "critical" | "major" | "minor") ?? "minor"] ?? {}]}>{s?.max_severity ?? "none"}</Text>
              <Text style={styles.cell}>{total}</Text>
              <Text style={styles.cell}>{s?.score?.toFixed(0) ?? "—"}/100</Text>
              <Text style={styles.cell}>{s?.top_fault_titles?.[0] ?? "—"}</Text>
            </View>
          );
        })}

        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 2 of 4</Text>
        </View>
      </Page>

      {/* Page 3 – Per-Phase Fault Details */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Detailed Fault Analysis by Phase</Text>
          <Text style={styles.subtitle}>All detected faults grouped by swing phase with corrective guidance</Text>
        </View>

        {PHASE_ORDER.map((phase) => {
          const phaseFaults = byPhase[phase] ?? [];
          const phaseLabel = PHASE_LABELS[phase] ?? phase.replace("_", " ");
          const phaseSum = summary[phase];
          const phaseScore = phaseSum?.score;

          return (
            <View key={phase} wrap={false}>
              <View style={styles.phaseHeader}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text>{phaseLabel}</Text>
                  {phaseScore !== undefined && (
                    <Text style={styles.phaseScore}>Score: {phaseScore.toFixed(0)}/100</Text>
                  )}
                </View>
              </View>

              {phaseFaults.length === 0 ? (
                <View style={styles.successBox}>
                  <Text style={styles.noFaults}>✓ No faults detected in this phase</Text>
                </View>
              ) : (
                phaseFaults.map((f, i) => (
                  <View style={styles.faultBox} key={i}>
                    <Text style={[styles.faultTitle, styles[(f.severity as "critical" | "major" | "minor")] ?? {}]}>
                      [{f.severity.toUpperCase()}] {f.title}
                    </Text>
                    <Text style={styles.faultDesc}>{f.description}</Text>
                    <Text style={styles.faultMeasurement}>
                      Measured: {f.value.toFixed(1)}° | Expected: {f.expected}
                    </Text>
                    <Text style={styles.faultFix}>Fix: {f.fix}</Text>
                  </View>
                ))
              )}
            </View>
          );
        })}

        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 3 of 4</Text>
        </View>
      </Page>

      {/* Page 4 – Ball Tracking & Distance */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Ball Tracking & Distance Estimation</Text>
          <Text style={styles.subtitle}>Module 3 — Vision-based or ML-predicted distance analysis</Text>
        </View>

        {/* Tracking status */}
        {report.ball_tracking?.enabled ? (
          <View style={styles.successBox}>
            <Text style={{ fontSize: 10, color: "#16a34a", fontFamily: "Helvetica-Bold" }}>
              ✓ Ball tracking was active for this analysis
            </Text>
          </View>
        ) : (
          <View style={styles.warningBox}>
            <Text style={{ fontSize: 10, color: "#f97316", fontFamily: "Helvetica-Bold", marginBottom: 2 }}>
              ⚠ Ball tracking was not available
            </Text>
            <Text style={{ fontSize: 8, color: "#94a3b8" }}>
              Distance estimation used ML pose-based prediction as fallback.
            </Text>
          </View>
        )}

        <View style={styles.row}>
          <Text style={styles.cellHeader}>Metric</Text>
          <Text style={styles.cellHeader}>Value</Text>
        </View>
        {[
          ["Tracking Status", report.ball_tracking?.status ?? "—"],
          ["Tracking Enabled", report.ball_tracking?.enabled ? "Yes" : "No"],
          ["Method", ballDist?.method ?? "—"],
          ["Confidence", ballDist ? `${ballDist.confidence.toFixed(0)}%` : "—"],
          ["Carry Distance", ballDist ? `${ballDist.carry_yards.toFixed(1)} yds` : "—"],
          ["Total Distance", ballDist ? `${ballDist.distance_yards.toFixed(1)} yds` : "—"],
          ["ML Ball Speed", perf ? `${perf.BallSpeed.toFixed(0)} mph` : "—"],
          ["Trajectory Points", String(report.ball_tracking?.trajectory_2d?.length ?? 0)],
        ].map(([k, v]) => (
          <View style={styles.row} key={k}>
            <Text style={styles.cell}>{k}</Text>
            <Text style={styles.cell}>{v}</Text>
          </View>
        ))}

        {/* Notes */}
        {ballDist?.notes && (
          <View style={{ marginTop: 12 }}>
            <Text style={styles.sectionTitle}>Notes</Text>
            <Text style={{ fontSize: 9, color: "#94a3b8" }}>{ballDist.notes}</Text>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 4 of 4</Text>
        </View>
      </Page>
    </Document>
  );
}

// ---------- Component ----------
interface Props2 {
  report: AnalysisReport;
}

export default function ReportDownload({ report }: Props2) {
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
