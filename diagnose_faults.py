"""
Comprehensive fault diagnosis: extract CaddieSet features for ALL swings
and compare good vs bad distributions to calibrate thresholds.
"""
import sys, os, json, csv
import numpy as np
sys.path.insert(0, '.')

from analyze_video import MLSwingAnalyzer

analyzer = MLSwingAnalyzer()

good_dir = 'good_swings'
bad_dir = 'bad_swings'
test_good = 'test_videos/good_swings'
test_bad = 'test_videos/bad_swings'

# Collect all videos
good_videos = sorted([os.path.join(good_dir, f) for f in os.listdir(good_dir) if f.endswith('.mp4')])
bad_videos = sorted([os.path.join(bad_dir, f) for f in os.listdir(bad_dir) if f.endswith('.mp4')])

# Also add test videos if not already included
for f in os.listdir(test_good):
    p = os.path.join(test_good, f)
    if p.endswith('.mp4') and p not in good_videos:
        good_videos.append(p)
for f in os.listdir(test_bad):
    p = os.path.join(test_bad, f)
    if p.endswith('.mp4') and p not in bad_videos:
        bad_videos.append(p)

# Key features to track (phase-prefixed)
KEY_FEATURES = [
    '0-SPINE-ANGLE', '0-SHOULDER-ANGLE', '0-LEFT-LEG-ANGLE', '0-RIGHT-ARM-ANGLE',
    '0-HIP-SHIFTED', '0-HIP-ROTATION',
    '1-SPINE-ANGLE', '1-HIP-SHIFTED', '1-HIP-ROTATION', '1-RIGHT-ARM-ANGLE',
    '2-LEFT-ARM-ANGLE', '2-RIGHT-ARM-ANGLE',
    '3-RIGHT-ARM-ANGLE', '3-HIP-ROTATION', '3-HIP-SHIFTED',
    '4-SPINE-ANGLE', '4-RIGHT-ARM-ANGLE', '4-LEFT-LEG-ANGLE', '4-HIP-SHIFTED',
    '5-RIGHT-ARM-ANGLE', '5-SPINE-ANGLE',
]

all_data = []  # (label, name, features_dict, score, faults_count, messages)

def process_video(video_path, label):
    name = os.path.basename(video_path)
    try:
        report = analyzer.analyze_video(
            video_path, output_dir='output/diag_tmp', skip_video_render=True, verbose=False
        )
    except Exception as e:
        print(f"  ERROR processing {name}: {e}")
        return None
    
    fa = report["fault_analysis"]
    score = fa["overall_score"] or 0
    quality = fa["swing_quality"]
    msgs = fa["messages"]
    
    # We need the raw caddieset features - extract them
    # Re-extract since report doesn't contain raw features
    from utils.trajectory_extractor import TrajectoryExtractor
    from utils.swing_phase_analyzer import SwingPhaseAnalyzer
    from training.caddieset_feature_extractor import CaddieSetFeatureExtractor
    import cv2
    
    te = analyzer.trajectory_extractor
    pa = analyzer.phase_analyzer
    ce = analyzer.caddieset_extractor
    
    # Clear cached
    te.cached_landmarks = []
    frame_data = te.extract_from_video(str(video_path), verbose=False, preprocess=False)
    phase_ranges, sw_s, sw_e, wy, sm = pa.detect_phases(frame_data)
    
    cap = cv2.VideoCapture(str(video_path))
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    caddieset = ce.extract_from_landmarks(te.cached_landmarks, phase_ranges, fh, fw)
    
    return {
        'label': label,
        'name': name,
        'score': float(score),
        'quality': quality,
        'num_faults': len(msgs),
        'messages': msgs,
        'features': caddieset,
        'phases': {k: [int(v[0]), int(v[1])] for k, v in phase_ranges.items()},
    }

print("Processing GOOD swings...")
good_results = []
for i, v in enumerate(good_videos):
    print(f"  [{i+1}/{len(good_videos)}] {os.path.basename(v)}")
    r = process_video(v, 'GOOD')
    if r:
        good_results.append(r)

print(f"\nProcessing BAD swings...")
bad_results = []
for i, v in enumerate(bad_videos):
    print(f"  [{i+1}/{len(bad_videos)}] {os.path.basename(v)}")
    r = process_video(v, 'BAD')
    if r:
        bad_results.append(r)

# ====== ANALYSIS ======
print(f"\n\n{'='*80}")
print(f"RESULTS: {len(good_results)} good, {len(bad_results)} bad swings processed")
print(f"{'='*80}")

# Score distributions
good_scores = [r['score'] for r in good_results]
bad_scores = [r['score'] for r in bad_results]
print(f"\nSCORE DISTRIBUTIONS:")
print(f"  GOOD: min={min(good_scores):.1f} max={max(good_scores):.1f} mean={np.mean(good_scores):.1f} median={np.median(good_scores):.1f}")
print(f"  BAD:  min={min(bad_scores):.1f} max={max(bad_scores):.1f} mean={np.mean(bad_scores):.1f} median={np.median(bad_scores):.1f}")

# Fault counts
good_faults = [r['num_faults'] for r in good_results]
bad_faults = [r['num_faults'] for r in bad_results]
print(f"\nFAULT COUNT DISTRIBUTIONS:")
print(f"  GOOD: min={min(good_faults)} max={max(good_faults)} mean={np.mean(good_faults):.1f}")
print(f"  BAD:  min={min(bad_faults)} max={max(bad_faults)} mean={np.mean(bad_faults):.1f}")

# Per-video summary
print(f"\n{'Type':<6} {'Video':<20} {'Score':>6} {'Faults':>7} {'Quality':<12} Fault Types")
print('-' * 100)
for r in good_results:
    fault_types = '; '.join([m.split(']')[1].split(':')[0].strip() if ']' in m else m[:40] for m in r['messages'][:3]])
    print(f"{'GOOD':<6} {r['name']:<20} {r['score']:6.1f} {r['num_faults']:7d} {r['quality']:<12} {fault_types}")
for r in bad_results:
    fault_types = '; '.join([m.split(']')[1].split(':')[0].strip() if ']' in m else m[:40] for m in r['messages'][:3]])
    print(f"{'BAD':<6} {r['name']:<20} {r['score']:6.1f} {r['num_faults']:7d} {r['quality']:<12} {fault_types}")

# Feature distributions comparison
print(f"\n\n{'='*80}")
print("KEY FEATURE DISTRIBUTIONS (GOOD vs BAD)")
print(f"{'='*80}")
print(f"{'Feature':<25} {'Good Mean':>10} {'Good Std':>10} {'Bad Mean':>10} {'Bad Std':>10} {'Separation':>10}")
print('-' * 80)

for feat in KEY_FEATURES:
    good_vals = [r['features'].get(feat) for r in good_results if r['features'].get(feat) is not None]
    bad_vals = [r['features'].get(feat) for r in bad_results if r['features'].get(feat) is not None]
    
    if not good_vals or not bad_vals:
        continue
    
    good_vals = [v for v in good_vals if not np.isnan(v)]
    bad_vals = [v for v in bad_vals if not np.isnan(v)]
    
    if not good_vals or not bad_vals:
        continue
    
    gm, gs = np.mean(good_vals), np.std(good_vals)
    bm, bs = np.mean(bad_vals), np.std(bad_vals)
    
    # Cohen's d for separation
    pooled_std = np.sqrt((gs**2 + bs**2) / 2) if (gs + bs) > 0 else 1
    cohens_d = (bm - gm) / pooled_std if pooled_std > 0 else 0
    
    print(f"{feat:<25} {gm:10.1f} {gs:10.1f} {bm:10.1f} {bs:10.1f} {cohens_d:10.2f}")

# Print raw values per video for top discriminating features
print(f"\n\n{'='*80}")
print("RAW VALUES FOR TOP FEATURES (per video)")
print(f"{'='*80}")

top_features = [
    '3-RIGHT-ARM-ANGLE', '4-RIGHT-ARM-ANGLE', '5-RIGHT-ARM-ANGLE',
    '4-SPINE-ANGLE', '4-HIP-SHIFTED', '4-LEFT-LEG-ANGLE',
    '0-SPINE-ANGLE', '1-HIP-SHIFTED', '3-HIP-SHIFTED',
]

header = f"{'Type':<6} {'Video':<16}"
for feat in top_features:
    short = feat.replace('-ANGLE', '').replace('RIGHT-ARM', 'R-ARM').replace('LEFT-LEG', 'L-LEG').replace('SPINE', 'SP').replace('HIP-SHIFTED', 'HIP-S')
    header += f" {short:>12}"
print(header)
print('-' * (22 + 13 * len(top_features)))

for r in good_results + bad_results:
    row = f"{r['label']:<6} {r['name']:<16}"
    for feat in top_features:
        val = r['features'].get(feat)
        if val is not None and not np.isnan(val):
            row += f" {val:12.1f}"
        else:
            row += f" {'N/A':>12}"
    print(row)

# Save full data as JSON for further analysis
output = {
    'good': [{k: v for k, v in r.items() if k != 'features'} | {'features': {k: float(v) if v is not None and not np.isnan(v) else None for k, v in r['features'].items()}} for r in good_results],
    'bad': [{k: v for k, v in r.items() if k != 'features'} | {'features': {k: float(v) if v is not None and not np.isnan(v) else None for k, v in r['features'].items()}} for r in bad_results],
}
with open('output/fault_diagnosis.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f"\nFull data saved to output/fault_diagnosis.json")
