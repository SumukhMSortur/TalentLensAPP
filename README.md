# TalentLens AI

AI-powered Action Quality Assessment system for exercise video analysis. Compares athlete (ideal form) vs user (non-athlete) performance using MediaPipe pose detection, joint angle analysis, and scoring algorithms.

## Supported Exercises

- `squat`
- `push-up`
- `pull Up`

## Project Layout

```
├── backend/
│   └── server.py              # FastAPI REST API server
├── frontend/
│   ├── index.html             # Professional SPA frontend
│   ├── styles.css             # Dark-theme design system
│   └── app.js                 # Frontend application logic
├── src/
│   ├── pose/
│   │   └── pose_extractor.py  # MediaPipe pose detection & annotated video rendering
│   ├── features/
│   │   └── feature_extractor.py  # Angle extraction, symmetry, body-line metrics
│   ├── scoring/
│   │   └── score_calculator.py   # Depth/form/consistency/symmetry scoring
│   ├── comparison/
│   │   └── comparison_service.py # DTW + cosine similarity, frame-level feedback
│   └── analytics/
│       └── model_performance.py  # Nearest-centroid classifier, action prediction
├── dataset/
│   ├── videos/                # Input workout videos grouped by action
│   ├── poses/                 # Cached pose landmark arrays
│   └── features/              # Cached feature records
├── outputs/                   # Generated annotated videos and reports
├── main.py                    # Batch pipeline runner (CLI)
├── requirements.txt           # Python dependencies
└── README.md
```

## Requirements

- Python 3.10.x recommended
- Windows PowerShell or VS Code terminal recommended
- OpenCV build that can write browser-playable MP4 files

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Application

### Start the Backend + Frontend

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000/app/** in your browser.

### How to Use

1. Upload an **Athlete (Reference)** video — showing ideal exercise form
2. Upload a **User** video — showing the performance to evaluate
3. Select the **exercise type** from the dropdown
4. Click **Analyze & Compare**
5. View the results: similarity score, side-by-side annotated videos, per-joint error analysis, and detailed score breakdown

### Run the Batch Pipeline (CLI)

```powershell
python main.py
```

This processes all videos in `dataset/videos/` and generates an HTML report at `outputs/results_report.html`.

## UI Features

- **Side-by-side comparison**: Athlete vs User videos with pose annotations
- **Toggle**: Switch between annotated and original video views
- **Animated score ring**: Overall similarity score with gradient animation
- **Metrics dashboard**: Joint angle difference, movement smoothness, temporal consistency
- **Detailed breakdown**: Depth, form, consistency, symmetry scores with progress bars
- **Joint error chart**: Per-joint deviation visualized as bar charts
- **Action classification**: Probability bars for predicted exercise type
- **Dark premium theme**: Glassmorphism cards, gradient accents, micro-animations

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/actions` | List available exercise types |
| POST | `/api/compare` | Upload 2 videos + run comparison pipeline |
| GET | `/api/results/{job_id}` | Retrieve cached results |
| GET | `/api/model-metrics` | Model performance metrics |

## Notes

- `streamlit_app.py` is the legacy UI — no longer used
- `config.py` currently exists but is empty
- `setup_dataset.py` is an optional dataset copy helper
- `view_features.py` reads saved feature records and plots angle series
