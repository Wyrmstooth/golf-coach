import { useState } from "react";
import { motion } from "framer-motion";
import { Download, FileText, Loader2 } from "lucide-react";
import {
  pdf,
  Document,
  Page,
  Text,
  View,
  Image,
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
  title:    { fontSize: 24, fontFamily: "Helvetica-Bold", color: "#16a34a", marginBottom: 4 },
  subtitle: { fontSize: 10, color: "#94a3b8" },
  sectionTitle: {
    fontSize: 13, fontFamily: "Helvetica-Bold", color: "#16a34a",
    marginBottom: 8, marginTop: 16, borderBottomWidth: 1,
    borderBottomColor: "#1e293b", paddingBottom: 4,
  },
  row:        { flexDirection: "row", marginBottom: 4 },
  cell:       { flex: 1, fontSize: 9, color: "#cbd5e1", padding: 6, backgroundColor: "#1e293b", marginRight: 4 },
  cellHeader: { flex: 1, fontSize: 9, fontFamily: "Helvetica-Bold", color: "#16a34a", padding: 6, backgroundColor: "#052e16", marginRight: 4 },
  faultBox:   { backgroundColor: "#1e293b", padding: 8, marginBottom: 6, borderRadius: 4 },
  faultTitle: { fontSize: 10, fontFamily: "Helvetica-Bold", color: "#ffffff", marginBottom: 2 },
  faultDesc:  { fontSize: 8, color: "#94a3b8", marginBottom: 2 },
  faultFix:   { fontSize: 8, color: "#16a34a" },
  faultMeasurement: { fontSize: 8, color: "#cbd5e1", marginBottom: 2 },
  critical: { color: "#ef4444" },
  major:    { color: "#f97316" },
  minor:    { color: "#eab308" },
  scoreBox:   { backgroundColor: "#052e16", padding: 16, borderRadius: 8, alignItems: "center", marginBottom: 16 },
  scoreNum:   { fontSize: 48, fontFamily: "Helvetica-Bold", color: "#16a34a" },
  scoreLabel: { fontSize: 12, color: "#94a3b8" },
  metric:      { flex: 1, backgroundColor: "#1e293b", padding: 10, marginRight: 4, borderRadius: 4, alignItems: "center" },
  metricValue: { fontSize: 20, fontFamily: "Helvetica-Bold", color: "#ca8a04" },
  metricLabel: { fontSize: 8, color: "#94a3b8", marginTop: 2 },
  footer:     { position: "absolute", bottom: 20, left: 36, right: 36, flexDirection: "row", justifyContent: "space-between", borderTopWidth: 1, borderTopColor: "#1e293b", paddingTop: 8 },
  footerText: { fontSize: 7, color: "#475569" },

  // ── Phase section — stacked layout (image full-width on top, faults below) ───
  phaseSection:  { marginBottom: 20, borderWidth: 1, borderColor: "#1e293b", borderRadius: 6 },
  phaseHeader:   { fontSize: 12, fontFamily: "Helvetica-Bold", color: "#ffffff", backgroundColor: "#052e16", padding: 10, borderRadius: 4 },
  phaseScore:    { fontSize: 9, color: "#16a34a", fontFamily: "Helvetica-Bold" },
  // A4 usable width = 595 - 2*36 = 523pt
  phaseImg:      { width: 523, height: 270 },
  phaseImgPlaceholder: { width: 523, height: 50, backgroundColor: "#1e293b", justifyContent: "center", alignItems: "center" },
  phaseImgPlaceholderText: { fontSize: 8, color: "#475569" },
  imgCaption:    { fontSize: 7, color: "#64748b", paddingLeft: 8, paddingBottom: 6, backgroundColor: "#0a1628" },
  phaseFaults:   { padding: 8 },
  noFaults:      { fontSize: 9, color: "#16a34a", padding: 6 },
  warningBox:    { backgroundColor: "#f9731620", padding: 8, borderRadius: 4, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: "#f97316" },
  successBox:    { backgroundColor: "#16a34a15", padding: 8, borderRadius: 4, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: "#16a34a" },
});

const PHASE_ORDER  = ["ADDRESS", "BACKSWING", "TOP", "DOWNSWING", "IMPACT", "FOLLOW_THROUGH"];
const PHASE_LABELS: Record<string, string> = {
  ADDRESS: "Address", BACKSWING: "Backswing", TOP: "Top of Swing",
  DOWNSWING: "Downswing", IMPACT: "Impact", FOLLOW_THROUGH: "Follow Through",
};
const SEV_BORDER: Record<string, string> = {
  critical: "#ef4444", major: "#f97316", minor: "#eab308", none: "#16a34a",
};

// ---------- PDF Document ----------
interface GolfReportProps {
  report: AnalysisReport;
  analysisDate: string;
  phaseImages: Record<string, string>;
}

function GolfReport({ report, analysisDate, phaseImages }: GolfReportProps) {
  const score    = report.fault_analysis.overall_score ?? 0;
  const quality  = report.fault_analysis.swing_quality;
  const perf     = report.performance_prediction;
  const ballDist = report.ball_tracking?.distance_estimation;
  const phases   = Object.entries(report.phase_ranges);
  const summary  = report.phase_fault_summary;
  const byPhase  = report.fault_analysis.fault_details?.by_phase ?? {};

  const videoName   = report.video.split(/[\\/]/).pop() ?? "video.mp4";
  const totalFaults = report.fault_analysis.fault_details?.summary?.total_faults ?? 0;

  // Split 6 phases across two pages (3 each)
  const phaseGroups = [PHASE_ORDER.slice(0, 3), PHASE_ORDER.slice(3)];

  return (
    <Document>
      {/* ── Page 1 – Cover + Summary ── */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>GolfCoach AI — Swing Analysis Report</Text>
          <Text style={styles.subtitle}>{videoName} · {analysisDate}</Text>
        </View>

        <View style={styles.scoreBox}>
          <Text style={styles.scoreNum}>{score.toFixed(0)}</Text>
          <Text style={styles.scoreLabel}>Overall Swing Score / 100</Text>
          <Text style={{ fontSize: 14, color: "#16a34a", marginTop: 4, fontFamily: "Helvetica-Bold" }}>{quality}</Text>
        </View>

        <Text style={styles.sectionTitle}>Fault Summary</Text>
        <View style={styles.row}>
          {["Severity", "Count", "Percentage"].map(h => <Text key={h} style={styles.cellHeader}>{h}</Text>)}
        </View>
        {(["critical", "major", "minor"] as const).map(sev => {
          const count = report.fault_analysis.fault_details?.summary?.[`${sev}_count`] ?? 0;
          return (
            <View style={styles.row} key={sev}>
              <Text style={[styles.cell, styles[sev]]}>{sev.toUpperCase()}</Text>
              <Text style={styles.cell}>{count}</Text>
              <Text style={styles.cell}>{totalFaults > 0 ? ((count / totalFaults) * 100).toFixed(0) : 0}%</Text>
            </View>
          );
        })}

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

        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 1 of 5</Text>
        </View>
      </Page>

      {/* ── Page 2 – Phase Breakdown Table ── */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Phase Breakdown</Text>
          <Text style={styles.subtitle}>{videoName} · {analysisDate}</Text>
        </View>
        <View style={styles.row}>
          {["Phase", "Frames", "Severity", "Faults", "Score", "Top Fault"].map(h => (
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
              <Text style={[styles.cell, styles[(s?.max_severity as "critical"|"major"|"minor")] ?? {}]}>{s?.max_severity ?? "none"}</Text>
              <Text style={styles.cell}>{total}</Text>
              <Text style={styles.cell}>{s?.score?.toFixed(0) ?? "—"}/100</Text>
              <Text style={styles.cell}>{s?.top_fault_titles?.[0] ?? "—"}</Text>
            </View>
          );
        })}
        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 2 of 5</Text>
        </View>
      </Page>

      {/* ── Pages 3 & 4 – Per-Phase Screenshots + Fault Details (3 phases each page) ── */}
      {phaseGroups.map((group, pageIdx) => (
        <Page key={pageIdx} size="A4" style={styles.page}>
          <View style={styles.header}>
            <Text style={styles.title}>Fault Analysis by Phase {pageIdx === 0 ? "(1/2)" : "(2/2)"}</Text>
            <Text style={styles.subtitle}>
              Full-frame annotated screenshots — coloured boxes highlight the exact body region where each fault occurs
            </Text>
          </View>

          {group.map(phase => {
            const phaseFaults = byPhase[phase] ?? [];
            const phaseLabel  = PHASE_LABELS[phase] ?? phase.replace("_", " ");
            const phaseSum    = summary[phase];
            const phaseScore  = phaseSum?.score;
            const maxSev      = phaseSum?.max_severity ?? "none";
            const imgDataUri  = phaseImages[phase];
            const midFrame    = report.phase_ranges[phase]
              ? Math.floor((report.phase_ranges[phase][0] + report.phase_ranges[phase][1]) / 2)
              : null;

            return (
              <View
                key={phase}
                style={[styles.phaseSection, { borderLeftWidth: 4, borderLeftColor: SEV_BORDER[maxSev] ?? "#16a34a" }]}
                wrap={false}
              >
                {/* Phase header */}
                <View style={[styles.phaseHeader, { flexDirection: "row", justifyContent: "space-between", alignItems: "center" }]}>
                  <Text>{phaseLabel}</Text>
                  {phaseScore !== undefined && (
                    <Text style={styles.phaseScore}>Score: {phaseScore.toFixed(0)}/100</Text>
                  )}
                </View>

                {/* Full-width annotated screenshot */}
                {imgDataUri ? (
                  <Image src={imgDataUri} style={styles.phaseImg} />
                ) : (
                  <View style={styles.phaseImgPlaceholder}>
                    <Text style={styles.phaseImgPlaceholderText}>Screenshot not available</Text>
                  </View>
                )}
                <Text style={styles.imgCaption}>Frame {midFrame ?? "—"} · {phaseLabel}</Text>

                {/* Fault cards below the screenshot */}
                <View style={styles.phaseFaults}>
                  {phaseFaults.length === 0 ? (
                    <View style={styles.successBox}>
                      <Text style={styles.noFaults}>✓ No faults detected in this phase</Text>
                    </View>
                  ) : (
                    phaseFaults.map((f, i) => (
                      <View
                        key={i}
                        style={[styles.faultBox, { borderLeftWidth: 2, borderLeftColor: SEV_BORDER[f.severity] ?? "#16a34a" }]}
                      >
                        <Text style={[styles.faultTitle, styles[(f.severity as "critical"|"major"|"minor")] ?? {}]}>
                          [{f.severity.toUpperCase()}] {f.title}
                        </Text>
                        <Text style={styles.faultDesc}>{f.description}</Text>
                        <Text style={styles.faultMeasurement}>Measured: {f.value.toFixed(1)}° | Expected: {f.expected}</Text>
                        <Text style={styles.faultFix}>Fix: {f.fix}</Text>
                      </View>
                    ))
                  )}
                </View>
              </View>
            );
          })}

          <View style={styles.footer}>
            <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
            <Text style={styles.footerText}>Page {pageIdx + 3} of 5</Text>
          </View>
        </Page>
      ))}

      {/* ── Page 5 – Ball Tracking & Distance ── */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Ball Tracking & Distance Estimation</Text>
          <Text style={styles.subtitle}>Module 3 — Vision-based or ML-predicted distance analysis</Text>
        </View>

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
          ["Tracking Status",  report.ball_tracking?.status ?? "—"],
          ["Method",           ballDist?.method ?? "—"],
          ["Confidence",       ballDist ? `${ballDist.confidence.toFixed(0)}%` : "—"],
          ["Carry Distance",   ballDist ? `${ballDist.carry_yards.toFixed(1)} yds` : "—"],
          ["Total Distance",   ballDist ? `${ballDist.distance_yards.toFixed(1)} yds` : "—"],
          ["ML Ball Speed",    perf ? `${perf.BallSpeed.toFixed(0)} mph` : "—"],
          ["Trajectory Points",String(report.ball_tracking?.trajectory_2d?.length ?? 0)],
        ].map(([k, v]) => (
          <View style={styles.row} key={k}>
            <Text style={styles.cell}>{k}</Text>
            <Text style={styles.cell}>{v}</Text>
          </View>
        ))}

        {ballDist?.notes && (
          <View style={{ marginTop: 12 }}>
            <Text style={styles.sectionTitle}>Notes</Text>
            <Text style={{ fontSize: 9, color: "#94a3b8" }}>{ballDist.notes}</Text>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>GolfCoach AI — Automated Swing Analysis Report</Text>
          <Text style={styles.footerText}>Page 5 of 5</Text>
        </View>
      </Page>
    </Document>
  );
}

// ---------- Helper: fetch PNG → base64 data URI ----------
async function fetchAsDataUri(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload  = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

// ---------- Component ----------
interface Props2 {
  report: AnalysisReport;
  jobId?: string;
}

export default function ReportDownload({ report, jobId }: Props2) {
  const [generating, setGenerating] = useState(false);

  const handleDownload = async () => {
    setGenerating(true);
    try {
      const date = new Date().toLocaleDateString("en-US", {
        year: "numeric", month: "long", day: "numeric",
      });

      // Fetch phase screenshots as base64 data URIs (only when jobId is present)
      const phaseImages: Record<string, string> = {};
      if (jobId) {
        const phaseScreenshots = report.outputs?.phase_screenshots ?? {};
        const entries = await Promise.all(
          Object.entries(phaseScreenshots).map(async ([phase, filename]) => {
            const dataUri = await fetchAsDataUri(`/api/files/${jobId}/${filename}`);
            return [phase, dataUri] as [string, string | null];
          })
        );
        for (const [phase, dataUri] of entries) {
          if (dataUri) phaseImages[phase] = dataUri;
        }
      }

      const blob = await pdf(
        <GolfReport report={report} analysisDate={date} phaseImages={phaseImages} />
      ).toBlob();
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
