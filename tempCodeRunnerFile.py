import os
import sys
import webbrowser
import logging
from html import escape
from pathlib import Path

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.features.feature_extractor import FeatureExtractor
from src.pose.pose_extractor import PoseExtractor
from src.scoring.score_calculator import ScoreCalculator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def _relative_video_path(report_file, path_value):
    return Path(os.path.relpath(path_value, start=report_file.parent)).as_posix()


def build_results_report(video_records, score_lookup, report_path):
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    cards = []
    for video_record in video_records:
        key = (video_record["action"], video_record["base_name"])
        score = score_lookup.get(key)
        if score is None:
            continue

        original_video = _relative_video_path(report_file, video_record["video_path"])
        output_video = _relative_video_path(report_file, video_record["output_video_path"])
        title = escape(f"{video_record['action']} / {video_record['base_name']}")

        cards.append(
            f"""
            <section class="card">
              <h2>{title}</h2>
              <p class="meta">
                Reps: <strong>{score['rep_count']}</strong>
                <span>Final Score: <strong>{score['final_score']}</strong></span>
              </p>
              <div class="videos">
                <div>
                  <h3>Original Video</h3>
                  <video controls preload="metadata" playsinline>
                    <source src="{escape(original_video)}" type="video/mp4" />
                    Your browser could not play the original video.
                  </video>
                </div>
                <div>
                  <h3>Annotated Video</h3>
                  <video controls preload="metadata" playsinline>
                    <source src="{escape(output_video)}" type="video/mp4" />
                    Your browser could not play the annotated video.
                    <a href="{escape(output_video)}">Open the MP4 directly</a>.
                  </video>
                </div>
              </div>
            </section>
            """
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TalentLens AI Results</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f1ea;
      --card: #fffdf8;
      --ink: #1f2933;
      --muted: #52606d;
      --accent: #c05621;
      --border: #e6ded0;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #f7f3eb 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    p {{
      color: var(--muted);
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
      margin-top: 20px;
      box-shadow: 0 10px 30px rgba(31, 41, 51, 0.06);
    }}
    .meta {{
      display: flex;
      gap: 18px;
      flex-wrap: wrap;
      margin-bottom: 16px;
      color: var(--ink);
    }}
    .videos {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 18px;
    }}
    h2, h3 {{
      margin-top: 0;
    }}
    h3 {{
      color: var(--accent);
      margin-bottom: 10px;
    }}
    video {{
      width: 100%;
      border-radius: 12px;
      background: #000;
      border: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <main>
    <h1>TalentLens AI Results</h1>
    <p>Each result includes the original input video, the annotated pose video, and its score.</p>
    {''.join(cards) if cards else '<p>No matching video results were found.</p>'}
  </main>
</body>
</html>
"""

    report_file.write_text(html, encoding="utf-8")
    return str(report_file)


def open_results_report(report_path):
    absolute_path = Path(report_path).resolve()

    try:
        if hasattr(os, "startfile"):
            os.startfile(str(absolute_path))
            return True

        return webbrowser.open(absolute_path.as_uri())
    except OSError:
        return False


def main():
    dataset_path = "dataset/videos"
    pose_path = "dataset/poses"
    feature_path = "dataset/features"
    output_path = "outputs/pose_samples"
    report_path = "outputs/results_report.html"
    limit_per_action = 2

    print("\nTalentLens AI pipeline starting")
    print(f"Input videos : {dataset_path}")
    print(f"Pose output  : {pose_path}")
    print(f"Feature data : {feature_path}")
    print(f"Video output : {output_path}")

    pose_extractor = PoseExtractor(model_complexity=1)
    processed_videos = pose_extractor.extract_dataset(
        dataset_path=dataset_path,
        save_path=pose_path,
        output_root=output_path,
        limit_per_action=limit_per_action,
    )

    if not processed_videos:
        print("\nNo videos were processed. Check dataset/videos/<action>/")
        return

    feature_extractor = FeatureExtractor()
    processed_features = feature_extractor.process_dataset(
        pose_path=pose_path,
        save_path=feature_path,
        selected_videos=processed_videos,
    )

    scorer = ScoreCalculator()
    score_results = scorer.process_dataset(
        feature_path=feature_path,
        selected_videos=processed_features,
    )

    score_lookup = {
        (result["action"], result["base_name"]): result for result in score_results
    }

    cached_pose_count = sum(1 for item in processed_videos if item.get("cached"))
    generated_pose_count = len(processed_videos) - cached_pose_count
    cached_feature_count = sum(1 for item in processed_features if item.get("cached"))
    generated_feature_count = len(processed_features) - cached_feature_count

    print("\nPipeline summary")
    for video_record in processed_videos:
        key = (video_record["action"], video_record["base_name"])
        score = score_lookup.get(key)
        if score is None:
            continue

        print(
            f"- {video_record['action']}/{video_record['base_name']}: "
            f"reps={score['rep_count']}, score={score['final_score']}, "
            f"output={video_record['output_video_path']}"
        )

    print(
        f"\nPose stage    : reused {cached_pose_count}, generated {generated_pose_count}"
    )
    print(
        f"Feature stage : reused {cached_feature_count}, generated {generated_feature_count}"
    )

    report_file = build_results_report(processed_videos, score_lookup, report_path)
    print(f"\nResults report created: {report_file}")
    if open_results_report(report_file):
        print("Results report opened automatically.")
    else:
        print("Could not open the report automatically. Open it manually in your browser.")

if __name__ == "__main__":
    main()
