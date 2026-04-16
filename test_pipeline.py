"""Quick test of analysis pipeline on good and bad swings"""
import sys, os
sys.path.insert(0, '.')
from analyze_video import MLSwingAnalyzer

analyzer = MLSwingAnalyzer()

good_videos = ['test_videos/good_swings/3.mp4', 'test_videos/good_swings/7.mp4']
bad_videos = ['test_videos/bad_swings/bad-10.mp4', 'test_videos/bad_swings/bad-12.mp4', 'test_videos/bad_swings/bad-16.mp4']

results = []
for label, videos in [('GOOD', good_videos), ('BAD', bad_videos)]:
    for video in videos:
        if not os.path.exists(video):
            print(f"  Skipping {video} (not found)")
            continue
        name = os.path.basename(video)
        print(f'\n{"="*60}')
        print(f'{label} SWING: {name}')
        print(f'{"="*60}')
        report = analyzer.analyze_video(video, output_dir='output/test_tmp', skip_video_render=True, verbose=False)
        fa = report["fault_analysis"]
        score = fa["overall_score"]
        quality = fa["swing_quality"]
        msgs = fa["messages"]
        phases = report.get("phase_ranges", {})
        print(f'  Score: {score:.1f}/100  Quality: {quality}  Faults: {len(msgs)}')
        for p, (s, e) in phases.items():
            print(f'    {p:20s}: {s:4d}-{e:4d} ({e-s:3d} frames)')
        for msg in msgs:
            print(f'  {msg}')
        results.append((label, name, score, len(msgs), quality))

print(f'\n\n{"="*60}')
print('SUMMARY')
print(f'{"="*60}')
print(f'{"Type":<6} {"Video":<20} {"Score":>6} {"Faults":>7} {"Quality":<12}')
print('-' * 60)
for label, name, score, faults, quality in results:
    print(f'{label:<6} {name:<20} {score:6.1f} {faults:7d} {quality:<12}')
