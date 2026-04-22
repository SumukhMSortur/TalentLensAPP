# TalentLens AI

TalentLens AI is a Python exercise-analysis pipeline for workout videos. It reads clips from `dataset/videos/`, runs MediaPipe pose detection, extracts angle-based features, counts reps, scores each clip, writes annotated MP4s, and generates a local HTML report.

## Supported exercises

- `squat`
- `push-up`
- `pull Up`

## Project layout

- `main.py` - pipeline entry point and HTML report builder
- `src/pose/pose_extractor.py` - pose extraction and annotated video generation
- `src/features/feature_extractor.py` - feature extraction and CSV export
- `src/scoring/score_calculator.py` - score calculation
- `dataset/videos/` - input workout videos grouped by action
- `dataset/poses/` - cached pose arrays
- `dataset/features/` - cached feature records and CSV tables
- `outputs/pose_samples/` - annotated MP4 outputs
- `outputs/results_report.html` - generated report
- `setup_dataset.py` - optional dataset copy helper
- `view_features.py` - optional feature visualization helper

## Requirements

- Python 3.10.x recommended
- Windows PowerShell or VS Code terminal recommended
- Enough disk space for `dataset/` and generated outputs
- An OpenCV build that can write browser-playable MP4 files

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the pipeline

```powershell
python main.py
```

The pipeline expects:

- input videos in `dataset/videos/<action>/`
- pose caches in `dataset/poses/`
- feature caches in `dataset/features/`
- annotated videos in `outputs/pose_samples/`
- the final report at `outputs/results_report.html`

## Expected result

- The console prints rep counts and scores for processed videos.
- Annotated MP4s are written under `outputs/pose_samples/`.
- A local report is written to `outputs/results_report.html`.

## Sharing the project

Share these if someone should reproduce the project from source:

- `main.py`
- `src/`
- `requirements.txt`
- `dataset/videos/`

Share these too if you want to avoid recomputation and keep results closer to your machine:

- `dataset/poses/`
- `dataset/features/`
- `outputs/pose_samples/`
- `outputs/results_report.html`

Do not share:

- `.venv/`
- `.venv-1/`
- `venv/`
- `__pycache__/`
- `.git/`
- `UCF101.rar`
- `workoutfitness-video.zip`

## Notes

- No `.env` file or environment variables are required.
- `config.py` currently exists but is empty.
- `setup_dataset.py` is optional and now accepts a source path instead of relying on a hardcoded machine-specific path.
- `view_features.py` reads the current saved feature-record format and plots the extracted angle series.

## Common issues

`PermissionError: [Errno 13] Permission denied: 'outputs\\results_report.html'`

- Close the report in your browser or editor, then rerun `python main.py`.

Feature visualization fails on saved `.npy` files

- Use the updated `view_features.py`, which loads pickled feature records with `allow_pickle=True`.

Annotated MP4 generation fails on another machine

- This is usually a codec or OpenCV build issue. Sharing pre-generated files from `outputs/pose_samples/` is the safest workaround.

## One-command quick start

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install -r requirements.txt; python main.py
```
