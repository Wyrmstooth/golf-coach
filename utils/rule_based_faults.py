"""
Rule-based golf swing fault detector based on geometric biomechanical thresholds.
Implements methods from:
  Sun, Gaoyue. "Golf Swing Correction Based on Deep Learning Body Posture Recognition."
  PRIS 2021. https://doi.org/10.1145/3480651.3480713

Uses concrete joint-angle thresholds instead of pure ML, giving interpretable,
phase-specific fault detection.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple, Optional
import numpy as np

# ── MediaPipe landmark indices ──────────────────────────────────────────────
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

# ── Thresholds from paper ───────────────────────────────────────────────────
ARM_ANGLE_MIN = 160.0
ARM_ANGLE_MAX = 180.0
LEG_ANGLE_MIN = 160.0
LEG_ANGLE_MAX = 180.0
HEAD_DISP_MAX = 0.03  # Normalized frame units (≈ 3% of frame)
WRIST_DIST_MAX = 0.05  # Normalized frame units (≈ 5% of frame)
SPINE_GRADIENT_MAX_DELTA = 0.15


def _distance(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1[:2] - p2[:2]))


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex b, in degrees."""
    ba = a[:2] - b[:2]
    bc = c[:2] - b[:2]
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return 0.0
    cosine = np.dot(ba, bc) / denom
    return math.degrees(math.acos(np.clip(cosine, -1.0, 1.0)))


def _midpoint(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    return (p1[:2] + p2[:2]) / 2


def _spine_gradient(landmarks: np.ndarray) -> float:
    """Gradient of spine line (nose → midpoint of ankles)."""
    nose = landmarks[NOSE][:2]
    legs_mid = _midpoint(landmarks[LEFT_ANKLE], landmarks[RIGHT_ANKLE])
    dx = nose[0] - legs_mid[0]
    dy = nose[1] - legs_mid[1]
    if abs(dx) < 1e-6:
        return 0.0
    return float(dy / dx)


class RuleBasedFaultDetector:
    """
    Detect swing faults using geometric rules derived from golf biomechanics.
    
    Runs per-phase (ADDRESS, BACKSWING, TOP, DOWNSWING, IMPACT, FOLLOW_THROUGH)
    and produces human-readable fault descriptions with severity ratings.
    """

    def detect(
        self,
        landmarks_sequence: List[Optional[np.ndarray]],
        phase_ranges: Dict[str, Tuple[int, int]],
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> Dict:
        """
        Run rule-based fault detection across all phases.
        
        Returns dict with same shape as ML fault detector for easy swapping:
          { overall_score, swing_quality, details: { faults, by_phase, by_severity, summary } }
        """
        faults: List[Dict] = []
        by_phase: Dict[str, List[Dict]] = {p: [] for p in phase_ranges}
        raw_scores = []

        # ── Phase-by-phase analysis ─────────────────────────────────────────
        for phase, (start, end) in phase_ranges.items():
            phase_faults, phase_score = self._analyze_phase(
                landmarks_sequence, phase, start, end, frame_width, frame_height
            )
            faults.extend(phase_faults)
            by_phase[phase] = phase_faults
            raw_scores.append(phase_score)

        # ── Cross-phase analysis ────────────────────────────────────────────
        cross_faults = self._cross_phase_analysis(landmarks_sequence, phase_ranges)
        faults.extend(cross_faults)
        for f in cross_faults:
            by_phase[f["phase"]].append(f)

        # ── Scoring ─────────────────────────────────────────────────────────
        # Score: 0 = perfect, 100 = terrible. Each fault contributes.
        total_faults = len(faults)
        critical = sum(1 for f in faults if f["severity"] == "critical")
        major = sum(1 for f in faults if f["severity"] == "major")
        minor = sum(1 for f in faults if f["severity"] == "minor")

        # Weighted penalty: critical=15, major=8, minor=3
        score = min(100, critical * 15 + major * 8 + minor * 3)
        quality = self._quality_label(score)

        return {
            "overall_score": round(score, 1),
            "swing_quality": quality,
            "details": {
                "faults": faults,
                "by_phase": by_phase,
                "by_severity": {
                    "critical": [f for f in faults if f["severity"] == "critical"],
                    "major": [f for f in faults if f["severity"] == "major"],
                    "minor": [f for f in faults if f["severity"] == "minor"],
                },
                "summary": {
                    "total_faults": total_faults,
                    "critical_count": critical,
                    "major_count": major,
                    "minor_count": minor,
                },
            },
            "messages": self._build_messages(faults),
            "critical_faults": [f["title"] for f in faults if f["severity"] == "critical"],
        }

    def _analyze_phase(
        self,
        landmarks_sequence: List[Optional[np.ndarray]],
        phase: str,
        start: int,
        end: int,
        frame_width: int,
        frame_height: int,
    ) -> Tuple[List[Dict], float]:
        """Analyze a single phase and return (faults, phase_score)."""
        faults = []
        phase_score = 0.0

        # Collect valid landmarks in this phase
        phase_landmarks = []
        for i in range(start, min(end + 1, len(landmarks_sequence))):
            lm = landmarks_sequence[i]
            if lm is not None and len(lm) >= 33:
                phase_landmarks.append(lm)

        if len(phase_landmarks) < 1:
            return faults, 0.0

        # Use median landmarks for stability
        median_lm = np.median(np.stack(phase_landmarks), axis=0)

        # ── 1. Arm angles ─────────────────────────────────────────────────
        for side, shoulder, elbow, wrist in [
            ("Left", LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
            ("Right", RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
        ]:
            angle = _angle(median_lm[shoulder], median_lm[elbow], median_lm[wrist])
            if angle < ARM_ANGLE_MIN - 10:
                faults.append(self._fault(
                    phase, "critical" if angle < 120 else "major",
                    f"{side} Arm Too Bent",
                    f"{side} arm angle is {angle:.1f}°. Standard is {ARM_ANGLE_MIN}°–{ARM_ANGLE_MAX}°. A bent arm reduces swing power and consistency.",
                    f"Keep the {side.lower()} arm straighter during the {phase.lower().replace('_', ' ')}.",
                    f"Straight Arm Drill: Practice half-swings with a towel under the {side.lower()} armpit to maintain extension.",
                    "arm_angle", angle, f"{ARM_ANGLE_MIN}°–{ARM_ANGLE_MAX}°"
                ))
                phase_score += 15 if angle < 120 else 8
            elif angle > ARM_ANGLE_MAX + 5:
                faults.append(self._fault(
                    phase, "minor",
                    f"{side} Arm Hyperextended",
                    f"{side} arm angle is {angle:.1f}°. Slightly beyond the standard range.",
                    f"Relax the {side.lower()} arm slightly to maintain natural extension.",
                    "Posture Drill: Stand tall and let arms hang naturally to find the correct extension.",
                    "arm_angle", angle, f"{ARM_ANGLE_MIN}°–{ARM_ANGLE_MAX}°"
                ))
                phase_score += 3

        # ── 2. Leg angles ─────────────────────────────────────────────────
        for side, hip, knee, ankle in [
            ("Left", LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
            ("Right", RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
        ]:
            angle = _angle(median_lm[hip], median_lm[knee], median_lm[ankle])
            if angle < LEG_ANGLE_MIN - 10:
                faults.append(self._fault(
                    phase, "critical" if angle < 130 else "major",
                    f"{side} Leg Too Bent",
                    f"{side} leg angle is {angle:.1f}°. Standard is {LEG_ANGLE_MIN}°–{LEG_ANGLE_MAX}°. Excessive knee flex causes weight shift issues.",
                    f"Straighten the {side.lower()} leg to improve weight transfer and balance.",
                    "Balance Drill: Practice swings with feet together to feel correct leg angles.",
                    "leg_angle", angle, f"{LEG_ANGLE_MIN}°–{LEG_ANGLE_MAX}°"
                ))
                phase_score += 15 if angle < 130 else 8
            elif angle > LEG_ANGLE_MAX + 5:
                faults.append(self._fault(
                    phase, "minor",
                    f"{side} Leg Locked",
                    f"{side} leg angle is {angle:.1f}°. Slightly beyond standard range.",
                    f"Maintain a slight flex in the {side.lower()} knee for stability.",
                    "Flex Drill: Setup with a slight knee bend and maintain it throughout the swing.",
                    "leg_angle", angle, f"{LEG_ANGLE_MIN}°–{LEG_ANGLE_MAX}°"
                ))
                phase_score += 3

        # ── 3. Wrist distance (except ADDRESS) ────────────────────────────
        if phase != "ADDRESS":
            wrist_dist = _distance(median_lm[LEFT_WRIST], median_lm[RIGHT_WRIST])
            if wrist_dist > WRIST_DIST_MAX:
                faults.append(self._fault(
                    phase, "major" if wrist_dist > 0.08 else "minor",
                    "Wrists Too Far Apart",
                    f"Wrist distance is {wrist_dist:.3f} (normalized). Should be near zero during {phase.lower().replace('_', ' ')}.",
                    "Keep hands closer together, maintaining the triangle formed by arms and shoulders.",
                    "Connection Drill: Place a small ball between forearms and swing without dropping it.",
                    "wrist_distance", wrist_dist, f"< {WRIST_DIST_MAX}"
                ))
                phase_score += 8 if wrist_dist > 0.08 else 3

        # ── 4. Spine gradient stability (per phase) ───────────────────────
        grad = _spine_gradient(median_lm)
        # Store for cross-phase comparison
        self._last_spine_gradient = getattr(self, "_last_spine_gradient", {})
        self._last_spine_gradient[phase] = grad

        return faults, phase_score

    def _cross_phase_analysis(
        self,
        landmarks_sequence: List[Optional[np.ndarray]],
        phase_ranges: Dict[str, Tuple[int, int]],
    ) -> List[Dict]:
        """Analyze movements between phases (head displacement, spine stability)."""
        faults = []

        # ── Head displacement: BACKSWING → TOP ────────────────────────────
        if "BACKSWING" in phase_ranges and "TOP" in phase_ranges:
            bs_start, bs_end = phase_ranges["BACKSWING"]
            top_start, top_end = phase_ranges["TOP"]
            bs_nose = self._get_nose(landmarks_sequence, bs_start, bs_end)
            top_nose = self._get_nose(landmarks_sequence, top_start, top_end)
            if bs_nose is not None and top_nose is not None:
                disp = float(np.linalg.norm(bs_nose - top_nose))
                if disp > HEAD_DISP_MAX:
                    faults.append(self._fault(
                        "BACKSWING", "major" if disp > 0.06 else "minor",
                        "Excessive Head Movement",
                        f"Head moved {disp:.3f} (normalized) from backswing to top. Head should stay stable.",
                        "Keep your head still during the backswing. Imagine a glass of water on your head.",
                        "Steady Head Drill: Practice backswings while focusing on a fixed point on the ball.",
                        "head_displacement", disp, f"< {HEAD_DISP_MAX}"
                    ))

        # ── Spine gradient stability across phases ────────────────────────
        grads = getattr(self, "_last_spine_gradient", {})
        if len(grads) >= 2:
            phases_ordered = [p for p in ["ADDRESS", "BACKSWING", "TOP", "DOWNSWING", "IMPACT", "FOLLOW_THROUGH"] if p in grads]
            for i in range(1, len(phases_ordered)):
                prev_phase = phases_ordered[i - 1]
                curr_phase = phases_ordered[i]
                delta = abs(grads[curr_phase] - grads[prev_phase])
                if delta > SPINE_GRADIENT_MAX_DELTA:
                    faults.append(self._fault(
                        curr_phase, "major" if delta > 0.25 else "minor",
                        "Spine Angle Unstable",
                        f"Spine line changed by {delta:.3f} from {prev_phase.lower().replace('_', ' ')} to {curr_phase.lower().replace('_', ' ')}. Spine should remain stable.",
                        "Maintain consistent spine tilt throughout the swing. Don't stand up or dip.",
                        "Posture Drill: Practice swings with your backside against a wall to maintain spine angle.",
                        "spine_gradient", delta, f"< {SPINE_GRADIENT_MAX_DELTA}"
                    ))

        return faults

    def _get_nose(self, landmarks_sequence: List[Optional[np.ndarray]], start: int, end: int) -> Optional[np.ndarray]:
        """Get median nose position in a phase range."""
        positions = []
        for i in range(start, min(end + 1, len(landmarks_sequence))):
            lm = landmarks_sequence[i]
            if lm is not None and len(lm) > NOSE:
                positions.append(lm[NOSE][:2])
        if not positions:
            return None
        return np.median(np.stack(positions), axis=0)

    def _fault(
        self, phase: str, severity: str, title: str, description: str,
        fix: str, drill: str, feature: str, value: float, expected: str
    ) -> Dict:
        return {
            "phase": phase,
            "severity": severity,
            "title": title,
            "description": description,
            "fix": fix,
            "drill": drill,
            "feature": feature,
            "value": round(value, 2),
            "expected": expected,
        }

    def _quality_label(self, score: float) -> str:
        if score >= 55:
            return "Poor"
        if score >= 38:
            return "Needs Work"
        if score >= 25:
            return "Good"
        return "Excellent"

    def _build_messages(self, faults: List[Dict]) -> List[str]:
        """Build human-readable summary messages."""
        messages = []
        critical = [f for f in faults if f["severity"] == "critical"]
        major = [f for f in faults if f["severity"] == "major"]
        minor = [f for f in faults if f["severity"] == "minor"]

        if critical:
            messages.append(f"🔴 {len(critical)} critical fault(s) detected. These significantly affect swing performance.")
        if major:
            messages.append(f"🟠 {len(major)} major issue(s) found. Address these for noticeable improvement.")
        if minor:
            messages.append(f"🟡 {len(minor)} minor adjustment(s) recommended.")
        if not faults:
            messages.append("✅ Great swing! No significant faults detected.")

        return messages
