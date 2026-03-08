"""
🏌️ Golf Coach - Interactive Streamlit App
Professional golf swing analysis with live pose correction
"""

import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
import tempfile
import time
from PIL import Image
import json

# Import our refactored modules
from analyze_video import MLSwingAnalyzer

# Page config
st.set_page_config(
    page_title="🏌️ GolfCoach AI",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E8449;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #27AE60;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #1E8449;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #27AE60;
    }
</style>
""", unsafe_allow_html=True)


class AddressPoseCorrector:
    """ADDRESS Phase pose correction using MediaPipe"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5
        )
    
    def check_address_posture(self, landmarks):
        """
        Check ADDRESS position posture and return corrections
        
        Key points for ADDRESS:
        - Spine angle: ~30-40° forward lean
        - Knee bend: ~140-160°
        - Arm straight: Left arm ~160-180°
        - Weight distribution: Balanced
        """
        lm = landmarks.landmark
        
        def get_angle(p1, p2, p3):
            a = np.array([lm[p1].x, lm[p1].y])
            b = np.array([lm[p2].x, lm[p2].y])
            c = np.array([lm[p3].x, lm[p3].y])
            
            ba = a - b
            bc = c - b
            
            cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
            angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
            return angle
        
        # Calculate key angles
        spine_angle = get_angle(11, 23, 25)  # shoulder-hip-knee (approximation)
        left_knee = get_angle(23, 25, 27)
        right_knee = get_angle(24, 26, 28)
        left_arm = get_angle(11, 13, 15)
        
        # Check posture
        corrections = []
        status = "✅ GOOD"
        
        # Spine angle check (should be bent forward)
        if spine_angle > 165:
            corrections.append("⚠️ Stand more upright - spine too bent")
            status = "⚠️ NEEDS ADJUSTMENT"
        elif spine_angle < 150:
            corrections.append("⚠️ Bend forward more from hips")
            status = "⚠️ NEEDS ADJUSTMENT"
        
        # Knee bend check
        avg_knee = (left_knee + right_knee) / 2
        if avg_knee > 170:
            corrections.append("⚠️ Bend knees more (athletic stance)")
            status = "⚠️ NEEDS ADJUSTMENT"
        elif avg_knee < 130:
            corrections.append("⚠️ Less knee bend - too low")
            status = "⚠️ NEEDS ADJUSTMENT"
        
        # Left arm check (should be relatively straight)
        if left_arm < 150:
            corrections.append("⚠️ Straighten left arm more")
            status = "⚠️ NEEDS ADJUSTMENT"
        
        if not corrections:
            corrections.append("✅ Perfect ADDRESS position!")
        
        return {
            'status': status,
            'spine_angle': spine_angle,
            'left_knee': left_knee,
            'right_knee': right_knee,
            'left_arm': left_arm,
            'corrections': corrections
        }


def main():
    # Header
    st.markdown('<div class="main-header">🏌️ Golf Coach Pro ⛳</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        mode = st.radio(
            "Select Mode:",
            ["📹 Video Analysis", "🎥 Live ADDRESS Pose Check", "🏌️ Live Swing Analysis"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.info("""
        **Golf Coach AI
        
        - 📹 **Video Analysis**: Full swing phase detection
        - 🎥 **Live Mode**: Real-time ADDRESS posture correction
        - 🎯 **6 Phases**: ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH
        """)
    
    # Main content
    if mode == "📹 Video Analysis":
        video_analysis_mode()
    elif mode == "🎥 Live ADDRESS Pose Check":
        live_address_mode()
    else:
        live_swing_mode()


def video_analysis_mode():
    """Video upload and analysis"""
    st.header("📹 Video Analysis Mode")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Golf Swing Video")
        
        # File uploader
        video_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'mov', 'avi'],
            help="Upload your golf swing video for analysis"
        )
        
        # Sample videos
        st.markdown("**Or use a sample video:**")
        sample_videos = list(Path('.').glob('[0-9].mp4'))
        if sample_videos:
            sample_choice = st.selectbox(
                "Sample videos",
                ["None"] + [v.name for v in sample_videos]
            )
            if sample_choice != "None":
                video_file = sample_choice
        
        if video_file:
            # Display video
            if isinstance(video_file, str):
                # Sample video
                st.video(video_file)
                video_path = video_file
            else:
                # Uploaded video
                st.video(video_file)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(video_file.read())
                    video_path = tmp_file.name
            
            # Analyze button
            if st.button("🚀 Analyze Swing", type="primary"):
                with st.spinner("🔍 Analyzing swing phases, detecting faults, and predicting performance..."):
                    # Run full ML analysis
                    output_dir = "output"
                    Path(output_dir).mkdir(exist_ok=True)
                    
                    try:
                        analyzer = MLSwingAnalyzer()
                        report = analyzer.analyze_video(video_path, output_dir, verbose=False)
                        
                        st.success("✅ Analysis complete!")
                        
                        # Show results in col2
                        with col2:
                            st.subheader("📊 Analysis Results")
                            
                            # Phase breakdown
                            st.markdown("### Swing Phases")
                            for phase, (start, end) in report['phase_ranges'].items():
                                duration = end - start + 1
                                st.markdown(f"**{phase}**: frames {start}-{end} ({duration} frames)")
                            
                            # Fault Analysis
                            if report['fault_analysis']['overall_score'] is not None:
                                st.markdown("### Fault Analysis")
                                score = report['fault_analysis']['overall_score']
                                
                                # Color-coded overall score
                                if score < 20:
                                    st.success(f"🏆 Fault Score: {score:.1f}/100 - Excellent!")
                                elif score < 50:
                                    st.info(f"⚡ Fault Score: {score:.1f}/100 - Good with room to improve")
                                elif score < 75:
                                    st.warning(f"⚠️ Fault Score: {score:.1f}/100 - Needs work")
                                else:
                                    st.error(f"🔴 Fault Score: {score:.1f}/100 - Significant issues")
                                
                                # Structured fault data
                                fault_details = report['fault_analysis'].get('fault_details', {}) or {}
                                by_severity = fault_details.get('by_severity', {}) or {}
                                by_phase = fault_details.get('by_phase', {}) or {}
                                phase_summary = report.get('phase_fault_summary') or {}
                                
                                # Phase overview strip (quick glance across 6 phases)
                                if phase_summary:
                                    st.markdown("#### Phase Overview")
                                    phase_order = [
                                        "ADDRESS",
                                        "BACKSWING",
                                        "TOP",
                                        "DOWNSWING",
                                        "IMPACT",
                                        "FOLLOW_THROUGH",
                                    ]
                                    severity_colors = {
                                        "none": "#27ae60",      # green
                                        "minor": "#f1c40f",     # yellow
                                        "major": "#e67e22",     # orange
                                        "critical": "#e74c3c",  # red
                                    }
                                    cards_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
                                    for phase_name in phase_order:
                                        summary = phase_summary.get(phase_name, {})
                                        max_sev = (summary.get("max_severity") or "none").lower()
                                        color = severity_colors.get(max_sev, "#7f8c8d")
                                        counts = summary.get("counts", {}) or {}
                                        total_issues = sum(int(v) for v in counts.values())
                                        label = f"{phase_name}<br/><span style='font-size:11px;'>{total_issues} issue{'s' if total_issues != 1 else ''}</span>"
                                        cards_html += (
                                            f"<div style='flex:1 1 90px;padding:8px;"
                                            f"background-color:{color};color:white;border-radius:6px;"
                                            f"text-align:center;font-size:12px;'>"
                                            f"{label}</div>"
                                        )
                                    cards_html += "</div>"
                                    st.markdown(cards_html, unsafe_allow_html=True)

                                # Display faults by severity (global view)
                                critical = by_severity.get('critical', [])
                                if critical:
                                    st.markdown("**🔴 Critical Issues (all phases):**")
                                    for fault in critical[:3]:  # Show top 3
                                        st.error(f"**{fault.get('phase', '')}** - {fault.get('title', '')}: {fault.get('fix', '')}")
                                
                                major = by_severity.get('major', [])
                                if major:
                                    st.markdown("**🟠 Major Issues (all phases):**")
                                    for fault in major[:3]:
                                        st.warning(f"**{fault.get('phase', '')}** - {fault.get('title', '')}: {fault.get('fix', '')}")
                                
                                minor = by_severity.get('minor', [])
                                if minor:
                                    st.markdown("**🟡 Minor Issues (all phases):**")
                                    for fault in minor[:2]:
                                        st.info(f"**{fault.get('phase', '')}** - {fault.get('title', '')}")
                                
                                # Per-phase detail panels
                                if phase_summary or by_phase:
                                    st.markdown("### Phase-by-phase Issues")
                                    phase_order = [
                                        "ADDRESS",
                                        "BACKSWING",
                                        "TOP",
                                        "DOWNSWING",
                                        "IMPACT",
                                        "FOLLOW_THROUGH",
                                    ]
                                    severity_labels = {
                                        "none": "No issues",
                                        "minor": "Minor",
                                        "major": "Major",
                                        "critical": "Critical",
                                    }
                                    severity_emoji = {
                                        "critical": "🔴",
                                        "major": "🟠",
                                        "minor": "🟡",
                                    }
                                    
                                    for phase_name in phase_order:
                                        faults_for_phase = by_phase.get(phase_name, []) or []
                                        summary = phase_summary.get(phase_name, {})
                                        max_sev = (summary.get("max_severity") or "none").lower()
                                        score = summary.get("score")
                                        header_suffix = severity_labels.get(max_sev, "No data")
                                        header = f"{phase_name} – {header_suffix}"
                                        if score is not None and score > 0:
                                            header += f" (score {score:.0f}/100)"
                                        
                                        # Expand problem phases by default, others collapsed
                                        expanded = bool(faults_for_phase and max_sev in ("critical", "major"))
                                        with st.expander(header, expanded=expanded):
                                            if not faults_for_phase:
                                                st.markdown("✅ No significant issues detected in this phase.")
                                            else:
                                                for fault in faults_for_phase:
                                                    sev = (fault.get("severity") or "minor").lower()
                                                    emoji = severity_emoji.get(sev, "⚠️")
                                                    title = fault.get("title", "")
                                                    description = fault.get("description", "")
                                                    fix = fault.get("fix", "")
                                                    expected = fault.get("expected")
                                                    value = fault.get("value")

                                                    st.markdown(f"{emoji} **{title}**")
                                                    if description:
                                                        st.markdown(f"- **Issue**: {description}")
                                                    if fix:
                                                        st.markdown(f"- **Fix**: {fix}")
                                                    if expected is not None:
                                                        try:
                                                            st.caption(f"Expected: {expected} (observed {float(value):.1f})")
                                                        except Exception:
                                                            st.caption(f"Expected: {expected}")

                                # Fallback to old format if no detailed faults
                                if not critical and not major and not minor and not (phase_summary or by_phase):
                                    old_faults = report['fault_analysis'].get('critical_faults', [])
                                    if old_faults:
                                        st.markdown("**Issues Found:**")
                                        for fault in old_faults:
                                            st.warning(fault)
                                    elif score < 30:
                                        st.success("✅ No significant faults detected!")
                            
                            # Performance Prediction
                            if report['performance_prediction']:
                                st.markdown("### Performance Prediction")
                                perf = report['performance_prediction']
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Ball Speed", f"{perf['BallSpeed']:.1f} mph")
                                    st.metric("Distance", f"{perf['Distance']:.1f} yards")
                                with col_b:
                                    st.metric("Carry", f"{perf['Carry']:.1f} yards")
                                    st.metric("Confidence", f"{perf['confidence']:.1f}%")

                            # Ball Tracking & Trajectory (Module 3)
                            ball = report.get('ball_tracking')
                            if ball and ball.get('enabled'):
                                st.markdown("### Ball Tracking & Trajectory")
                                status = ball.get('status', 'unknown')
                                dist = ball.get('distance_estimation') or {}

                                if status == "success":
                                    st.success("Vision-based ball tracking successful.")
                                elif status == "partial":
                                    st.warning("Ball tracking partially reliable – using ML-based fallback for distance.")
                                elif status == "failed":
                                    st.error("Ball tracking failed – using ML-based distance only.")
                                else:
                                    st.info(f"Ball tracking status: {status}")

                                if dist:
                                    st.metric("Carry (Module 3)", f"{dist.get('carry_yards', 0):.1f} yards")
                                    st.metric("Distance (Module 3)", f"{dist.get('distance_yards', 0):.1f} yards")
                                    st.caption(f"Method: {dist.get('method', 'unknown')} (confidence {dist.get('confidence', 0):.1f}%)")

                                files = (ball.get('files') or {})
                                if files.get('plot') and Path(files['plot']).exists():
                                    st.markdown("#### Ball Trajectory Plot")
                                    st.image(files['plot'], use_container_width=True)
                                    st.caption("Horizontal and vertical ball displacement over time, with colored bands showing swing phases.")

                                if files.get('csv') and Path(files['csv']).exists():
                                    with open(files['csv'], 'rb') as f_csv:
                                        st.download_button(
                                            "⬇️ Download Ball Trajectory (CSV)",
                                            f_csv.read(),
                                            file_name=f"{Path(video_path).stem}_ball_traj.csv",
                                            mime="text/csv",
                                        )
                            
                            # Analysis Plot
                            if Path(report['outputs']['plot']).exists():
                                st.markdown("### Analysis Plot")
                                st.image(report['outputs']['plot'], use_container_width=True)
                            
                            # Annotated Video
                            if Path(report['outputs']['annotated_video']).exists():
                                st.markdown("### Annotated Video")
                                st.video(report['outputs']['annotated_video'])
                                
                                with open(report['outputs']['annotated_video'], 'rb') as f:
                                    st.download_button(
                                        "⬇️ Download Analyzed Video",
                                        f.read(),
                                        file_name=f"{Path(video_path).stem}_analyzed.mp4",
                                        mime="video/mp4"
                                    )
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if not video_file:
            st.info("👈 Upload a video or select a sample to begin analysis")


def live_address_mode():
    """Live webcam mode for ADDRESS pose checking"""
    st.header("🎥 Live ADDRESS Pose Correction")
    
    st.info("""
    **📌 ADDRESS Position Tips:**
    - Stand with feet shoulder-width apart
    - Bend from hips (not waist)
    - Slight knee bend (athletic stance)
    - Arms hanging naturally
    - Weight balanced on balls of feet
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📷 Camera Feed")
        
        # Camera controls
        run_camera = st.checkbox("▶️ Start Camera", value=False)
        
        if run_camera:
            # Placeholder for video
            frame_placeholder = st.empty()
            
            # Pose corrector
            corrector = AddressPoseCorrector()
            
            # Open webcam
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Stats placeholder
            with col2:
                st.markdown("### 📊 Live Feedback")
                status_placeholder = st.empty()
                metrics_placeholder = st.empty()
                corrections_placeholder = st.empty()
            
            try:
                while run_camera:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("❌ Failed to access camera")
                        break
                    
                    # Mirror frame
                    frame = cv2.flip(frame, 1)
                    
                    # Process with MediaPipe
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = corrector.pose.process(rgb)
                    
                    if results.pose_landmarks:
                        # Draw skeleton
                        corrector.mp_drawing.draw_landmarks(
                            frame,
                            results.pose_landmarks,
                            corrector.mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=corrector.mp_style.get_default_pose_landmarks_style()
                        )
                        
                        # Check posture
                        feedback = corrector.check_address_posture(results.pose_landmarks)
                        
                        # Update status
                        with col2:
                            if feedback['status'] == "✅ GOOD":
                                status_placeholder.success(feedback['status'])
                            else:
                                status_placeholder.warning(feedback['status'])
                            
                            # Metrics
                            metrics_placeholder.markdown(f"""
                            <div class="metric-card" style="background-color: #2c3e50; color: white; padding: 15px; border-radius: 8px;">
                            <b style="color: #3498db;">Spine Angle:</b> <span style="color: #ecf0f1;">{feedback['spine_angle']:.1f}°</span> (Target: 150-165°)<br>
                            <b style="color: #3498db;">Left Knee:</b> <span style="color: #ecf0f1;">{feedback['left_knee']:.1f}°</span> (Target: 140-160°)<br>
                            <b style="color: #3498db;">Right Knee:</b> <span style="color: #ecf0f1;">{feedback['right_knee']:.1f}°</span> (Target: 140-160°)<br>
                            <b style="color: #3498db;">Left Arm:</b> <span style="color: #ecf0f1;">{feedback['left_arm']:.1f}°</span> (Target: >150°)
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Corrections
                            corrections_html = "<div style='background-color: #34495e; color: white; padding: 15px; border-radius: 8px; margin-top: 10px;'>"
                            corrections_html += "<b style='color: #f39c12; font-size: 1.1em;'>Corrections:</b><br><br>"
                            for c in feedback['corrections']:
                                if "✅" in c:
                                    corrections_html += f"<div style='color: #2ecc71; margin: 5px 0;'>{c}</div>"
                                else:
                                    corrections_html += f"<div style='color: #e74c3c; margin: 5px 0;'>{c}</div>"
                            corrections_html += "</div>"
                            corrections_placeholder.markdown(corrections_html, unsafe_allow_html=True)
                        
                        # Add status to frame
                        cv2.putText(frame, feedback['status'], (20, 50),
                                   cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 0), 3)
                    else:
                        status_placeholder.warning("⚠️ No pose detected")
                    
                    # Display frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                    
                    # Small delay
                    time.sleep(0.03)
            
            finally:
                cap.release()
        else:
            st.info("👆 Click 'Start Camera' to begin ADDRESS pose checking")
    
    with col2:
        if not run_camera:
            st.markdown("### 📊 Live Feedback")
            st.info("Camera not started yet")


def live_swing_mode():
    """Live webcam mode for full swing analysis"""
    st.header("🏌️ Live Swing Analysis")
    
    st.info("""
    **📌 Instructions:**
    - Stand in front of camera with full swing visible
    - Click "Start Recording" and perform your swing
    - Recording lasts 5 seconds
    - Analysis will detect phases, faults, and predict performance
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📷 Live Recording")
        
        # Recording controls
        start_recording = st.button("🎥 Start Recording (5 sec)", type="primary")
        
        if start_recording:
            # Placeholder for video
            frame_placeholder = st.empty()
            progress_placeholder = st.empty()
            
            # Temp file for recording
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                video_path = tmp_file.name
            
            # Open webcam
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Get video properties
            fps = 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            
            # Record for 5 seconds
            recording_duration = 5
            frames_to_record = fps * recording_duration
            
            st.info("🎥 Recording started... Perform your swing!")
            
            try:
                for i in range(frames_to_record):
                    ret, frame = cap.read()
                    if not ret:
                        st.error("❌ Failed to access camera")
                        break
                    
                    # Mirror frame
                    frame = cv2.flip(frame, 1)
                    
                    # Write frame
                    out.write(frame)
                    
                    # Display frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                    
                    # Progress
                    progress = (i + 1) / frames_to_record
                    progress_placeholder.progress(progress)
                    
                    # Small delay
                    time.sleep(1/fps)
                
                out.release()
                cap.release()
                
                st.success("✅ Recording complete! Analyzing swing...")
                
                # Analyze the recorded video
                output_dir = "output"
                Path(output_dir).mkdir(exist_ok=True)
                
                analyzer = MLSwingAnalyzer()
                report = analyzer.analyze_video(video_path, output_dir, verbose=False)
                
                st.success("✅ Analysis complete!")
                
                # Show results in col2
                with col2:
                    st.subheader("📊 Analysis Results")
                    
                    # Phase breakdown
                    st.markdown("### Swing Phases")
                    for phase, (start, end) in report['phase_ranges'].items():
                        duration = end - start + 1
                        st.markdown(f"**{phase}**: frames {start}-{end} ({duration} frames)")
                    
                    # Fault Analysis
                    if report['fault_analysis']['overall_score'] is not None:
                        st.markdown("### Fault Analysis")
                        score = report['fault_analysis']['overall_score']
                        
                        # Color-coded score
                        if score < 20:
                            st.success(f"🏆 Fault Score: {score:.1f}/100 - Excellent!")
                        elif score < 50:
                            st.info(f"⚡ Fault Score: {score:.1f}/100 - Good with room to improve")
                        elif score < 75:
                            st.warning(f"⚠️ Fault Score: {score:.1f}/100 - Needs work")
                        else:
                            st.error(f"🔴 Fault Score: {score:.1f}/100 - Significant issues")
                        
                        # Display faults by severity if available
                        fault_details = report['fault_analysis'].get('fault_details', {})
                        by_severity = fault_details.get('by_severity', {})
                        
                        # Critical faults
                        critical = by_severity.get('critical', [])
                        if critical:
                            st.markdown("**🔴 Critical Issues:**")
                            for fault in critical[:3]:
                                st.error(f"**{fault.get('phase', '')}** - {fault.get('title', '')}: {fault.get('fix', '')}")
                        
                        # Major faults
                        major = by_severity.get('major', [])
                        if major:
                            st.markdown("**🟠 Major Issues:**")
                            for fault in major[:3]:
                                st.warning(f"**{fault.get('phase', '')}** - {fault.get('title', '')}: {fault.get('fix', '')}")
                        
                        # Minor faults
                        minor = by_severity.get('minor', [])
                        if minor:
                            st.markdown("**🟡 Minor Issues:**")
                            for fault in minor[:2]:
                                st.info(f"**{fault.get('phase', '')}** - {fault.get('title', '')}")
                        
                        # Fallback to old format
                        if not critical and not major and not minor:
                            old_faults = report['fault_analysis'].get('critical_faults', [])
                            if old_faults:
                                st.markdown("**Issues Found:**")
                                for fault in old_faults:
                                    st.warning(fault)
                            elif score < 30:
                                st.success("✅ No significant faults detected!")
                    
                    # Performance Prediction
                    if report['performance_prediction']:
                        st.markdown("### Performance Prediction")
                        perf = report['performance_prediction']
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Ball Speed", f"{perf['BallSpeed']:.1f} mph")
                            st.metric("Distance", f"{perf['Distance']:.1f} yards")
                        with col_b:
                            st.metric("Carry", f"{perf['Carry']:.1f} yards")
                            st.metric("Confidence", f"{perf['confidence']:.1f}%")

                    # Ball Tracking & Trajectory (Module 3)
                    ball = report.get('ball_tracking')
                    if ball and ball.get('enabled'):
                        st.markdown("### Ball Tracking & Trajectory")
                        status = ball.get('status', 'unknown')
                        dist = ball.get('distance_estimation') or {}

                        if status == "success":
                            st.success("Vision-based ball tracking successful.")
                        elif status == "partial":
                            st.warning("Ball tracking partially reliable – using ML-based fallback for distance.")
                        elif status == "failed":
                            st.error("Ball tracking failed – using ML-based distance only.")
                        else:
                            st.info(f"Ball tracking status: {status}")

                        if dist:
                            st.metric("Carry (Module 3)", f"{dist.get('carry_yards', 0):.1f} yards")
                            st.metric("Distance (Module 3)", f"{dist.get('distance_yards', 0):.1f} yards")
                            st.caption(f"Method: {dist.get('method', 'unknown')} (confidence {dist.get('confidence', 0):.1f}%)")

                        files = (ball.get('files') or {})
                        if files.get('plot') and Path(files['plot']).exists():
                            st.markdown("#### Ball Trajectory Plot")
                            st.image(files['plot'], use_container_width=True)

                        if files.get('csv') and Path(files['csv']).exists():
                            with open(files['csv'], 'rb') as f_csv:
                                st.download_button(
                                    "⬇️ Download Ball Trajectory (CSV)",
                                    f_csv.read(),
                                    file_name="live_ball_traj.csv",
                                    mime="text/csv",
                                )
                    
                    # Analysis Plot
                    if Path(report['outputs']['plot']).exists():
                        st.markdown("### Analysis Plot")
                        st.image(report['outputs']['plot'], use_container_width=True)
                    
                    # Recorded Video
                    st.markdown("### Your Recorded Swing")
                    st.video(video_path)
                    
                    # Annotated Video
                    if Path(report['outputs']['annotated_video']).exists():
                        st.markdown("### Annotated Video")
                        st.video(report['outputs']['annotated_video'])
                        
                        with open(report['outputs']['annotated_video'], 'rb') as f:
                            st.download_button(
                                "⬇️ Download Analyzed Video",
                                f.read(),
                                file_name="live_swing_analyzed.mp4",
                                mime="video/mp4"
                            )
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                cap.release()
                out.release()
        else:
            st.info("👆 Click 'Start Recording' to begin live swing analysis")
    
    with col2:
        if not start_recording:
            st.markdown("### 📊 Analysis Results")
            st.info("Recording not started yet")


if __name__ == "__main__":
    main()
