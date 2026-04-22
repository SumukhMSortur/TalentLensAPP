import hashlib
import mimetypes
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.analytics.model_performance import ModelPerformanceAnalyzer
from src.comparison.comparison_service import (
    compare_sequences,
    process_video,
    render_comparison_annotations,
)
from src.features.feature_extractor import FeatureExtractor
from src.pose.pose_extractor import PoseExtractor
from src.scoring.score_calculator import ScoreCalculator


OUTPUT_ROOT = Path("outputs/streamlit_demo")
UPLOAD_ROOT = OUTPUT_ROOT / "uploads"
PROCESSED_ROOT = OUTPUT_ROOT / "processed"
RENDER_VERSION = "v2_body_only"


st.set_page_config(
    page_title="Talent Lens AI",
    page_icon="TL",
    layout="wide",
)


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --tl-ink: #17324d;
            --tl-muted: #4d5f73;
            --tl-soft: #6b7788;
            --tl-card: rgba(255, 252, 246, 0.92);
            --tl-panel: #20242f;
            --tl-panel-border: #353b4a;
            --tl-accent: #d1495b;
            --tl-accent-deep: #b93849;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(227, 193, 122, 0.25), transparent 30%),
                radial-gradient(circle at top right, rgba(78, 123, 166, 0.18), transparent 28%),
                linear-gradient(180deg, #f7f1e5 0%, #f1ece2 100%);
        }
        .stApp,
        .stApp p,
        .stApp span,
        .stApp label,
        .stApp div {
            color: var(--tl-ink);
        }
        .stApp h1,
        .stApp h2,
        .stApp h3 {
            color: var(--tl-ink);
        }
        .hero {
            padding: 1.4rem 1.6rem;
            border-radius: 24px;
            border: 1px solid rgba(44, 62, 80, 0.12);
            background: rgba(255, 252, 246, 0.88);
            box-shadow: 0 20px 45px rgba(44, 62, 80, 0.08);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.4rem;
            letter-spacing: 0.08em;
            color: var(--tl-ink);
        }
        .hero p {
            margin: 0.55rem 0 0;
            color: var(--tl-muted);
            font-size: 1rem;
        }
        .panel {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            border: 1px solid rgba(44, 62, 80, 0.12);
            background: rgba(255, 252, 246, 0.92);
            box-shadow: 0 10px 35px rgba(44, 62, 80, 0.06);
        }
        .metric-strip {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            border: 1px solid rgba(23, 50, 77, 0.12);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(242, 236, 226, 0.94));
            margin-bottom: 1rem;
        }
        .feedback-chip {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            margin: 0 0.5rem 0.5rem 0;
            border-radius: 999px;
            background: #17324d;
            color: white;
            font-size: 0.88rem;
        }
        .stFileUploader label,
        .stSelectbox label,
        .stToggle label,
        .stButton label {
            color: var(--tl-ink) !important;
            font-weight: 700 !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(180deg, #262833 0%, #20242f 100%) !important;
            border: 1px solid var(--tl-panel-border) !important;
            border-radius: 18px !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] * {
            color: #f7f4ee !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] span,
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: #d8dde8 !important;
        }
        .stFileUploader [data-testid="stFileUploaderFileName"] {
            color: var(--tl-ink) !important;
            font-weight: 600 !important;
        }
        .stFileUploader small {
            color: var(--tl-soft) !important;
        }
        .stButton > button {
            background: linear-gradient(135deg, #e05263 0%, var(--tl-accent) 100%) !important;
            color: #fffaf6 !important;
            border: 0 !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            box-shadow: 0 12px 25px rgba(209, 73, 91, 0.22);
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #cf4758 0%, var(--tl-accent-deep) 100%) !important;
            color: #ffffff !important;
        }
        .stButton > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(209, 73, 91, 0.18) !important;
        }
        .stMarkdown,
        .stCaption,
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {
            color: var(--tl-ink) !important;
        }
        .stCaption {
            color: var(--tl-muted) !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #232733 0%, #1d212b 100%) !important;
        }
        [data-testid="stSidebar"] * {
            color: #eef2f7 !important;
        }
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #eef2f7 !important;
        }
        [data-testid="stSidebar"] .stCaption {
            color: #c8d1dd !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
            color: #f7f9fc !important;
            font-weight: 700 !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            color: var(--tl-ink) !important;
            background: rgba(255, 252, 246, 0.92) !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            color: var(--tl-ink) !important;
            fill: var(--tl-ink) !important;
            opacity: 1 !important;
            -webkit-text-fill-color: var(--tl-ink) !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] span,
        [data-testid="stSelectbox"] div[data-baseweb="select"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            color: var(--tl-ink) !important;
            fill: var(--tl-ink) !important;
            opacity: 1 !important;
            -webkit-text-fill-color: var(--tl-ink) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            color: #10253a !important;
            background: #f7f3eb !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            color: #10253a !important;
            fill: #10253a !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #10253a !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] input,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            color: #10253a !important;
            fill: #10253a !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #10253a !important;
        }
        [data-testid="stSidebar"] [data-testid="stTickBar"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a,
        [data-testid="stSidebar"] svg {
            color: #d9e1ec !important;
            fill: #d9e1ec !important;
        }
        .stVideo + div,
        .stVideo label {
            color: var(--tl-ink) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_services():
    return {
        "pose_extractor": PoseExtractor(debug=False),
        "feature_extractor": FeatureExtractor(),
        "scorer": ScoreCalculator(),
        "model_analyzer": ModelPerformanceAnalyzer(),
    }


@st.cache_data(show_spinner=False)
def load_model_metrics():
    return get_services()["model_analyzer"].load_metrics()


def available_actions():
    video_root = Path("dataset/videos")
    if not video_root.exists():
        return ["squat", "push-up", "pull Up"]
    return [item.name for item in sorted(video_root.iterdir()) if item.is_dir()]


def persist_upload(upload, prefix):
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.name).suffix or ".mp4"
    payload = upload.getbuffer()
    digest = hashlib.md5(payload).hexdigest()[:10]
    output_path = UPLOAD_ROOT / f"{prefix}_{digest}{suffix}"
    if not output_path.exists():
        output_path.write_bytes(payload)
    return output_path


def build_frame_feedback_plot(frame_deviation):
    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(frame_deviation, color="#17324d", linewidth=2.0)
    ax.fill_between(range(len(frame_deviation)), frame_deviation, color="#d7a75b", alpha=0.22)
    ax.set_title("Frame-wise Deviation", color="#17324d")
    ax.set_xlabel("Aligned Frame")
    ax.set_ylabel("Deviation (deg)")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig


def build_joint_error_plot(per_joint_error):
    labels = list(per_joint_error.keys())
    values = list(per_joint_error.values())
    fig, ax = plt.subplots(figsize=(8, 3.2))
    colors = ["#70be78" if value < 8 else "#f0b14a" if value < 15 else "#d9534f" for value in values]
    ax.bar(labels, values, color=colors)
    ax.set_title("Average Joint Error", color="#17324d")
    ax.set_ylabel("Degrees")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def render_confusion_matrix(metrics):
    matrix = metrics.get("confusion_matrix")
    labels = metrics.get("labels")
    if not matrix or not labels:
        st.info("No confusion matrix available for the current model metrics source.")
        return

    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    image = ax.imshow(matrix, cmap="YlGnBu")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            ax.text(col_index, row_index, value, ha="center", va="center", color="#17324d")

    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)


def _video_format_for_path(video_path):
    suffix = Path(video_path).suffix.lower()
    if suffix in {".mp4", ".m4v"}:
        return "video/mp4"
    if suffix == ".webm":
        return "video/webm"
    if suffix in {".ogg", ".ogv"}:
        return "video/ogg"
    guessed_type, _ = mimetypes.guess_type(str(video_path))
    return guessed_type or "video/mp4"


def _browser_supported(video_path):
    return Path(video_path).suffix.lower() in {".mp4", ".m4v", ".webm", ".ogg", ".ogv"}


def display_video(video_path, fallback_video_path=None):
    target_path = Path(video_path)
    if not target_path.exists():
        st.error(f"Video file not found: {target_path}")
        return

    if _browser_supported(target_path):
        with open(target_path, "rb") as video_file:
            st.video(video_file.read(), format=_video_format_for_path(target_path))
        return

    if fallback_video_path:
        fallback_path = Path(fallback_video_path)
        if fallback_path.exists() and _browser_supported(fallback_path):
            st.info(
                f"`{target_path.suffix}` is not reliably browser-playable, so the app is showing the annotated MP4 instead."
            )
            with open(fallback_path, "rb") as video_file:
                st.video(video_file.read(), format=_video_format_for_path(fallback_path))
            return

    st.warning(
        f"This file uses `{target_path.suffix}` format, which many browsers do not play inline. "
        "Use the annotated MP4 view for reliable playback."
    )


def render_video_card(title, video_path, caption, metadata):
    with st.container(border=True):
        st.markdown(f"### {title}")
        fallback_path = metadata.get("comparison_video_path") or metadata.get("annotated_video_path")
        display_video(video_path, fallback_video_path=fallback_path)
        st.caption(caption)
        st.write(
            f"Action: `{metadata['prediction']['predicted_label']}` | "
            f"Confidence: `{metadata['prediction']['confidence'] * 100:.1f}%` | "
            f"Reps: `{metadata['rep_count']}`"
        )


def run_comparison(reference_path, user_path, action_name):
    services = get_services()
    process_kwargs = {
        "pose_extractor": services["pose_extractor"],
        "feature_extractor": services["feature_extractor"],
        "scorer": services["scorer"],
        "model_analyzer": services["model_analyzer"],
    }

    athlete_result = process_video(
        video_path=str(reference_path),
        action_name=action_name,
        role_name="Athlete",
        output_root=PROCESSED_ROOT / RENDER_VERSION,
        **process_kwargs,
    )
    user_result = process_video(
        video_path=str(user_path),
        action_name=action_name,
        role_name="User",
        output_root=PROCESSED_ROOT / RENDER_VERSION,
        **process_kwargs,
    )

    comparison_result = compare_sequences(
        athlete_result["angle_sequence"],
        user_result["angle_sequence"],
    )

    compared_user_video = (
        PROCESSED_ROOT
        / RENDER_VERSION
        / f"user_comparison_{Path(user_path).stem}_{RENDER_VERSION}.mp4"
    )
    render_comparison_annotations(
        processed_video=user_result,
        comparison_result=comparison_result,
        output_path=compared_user_video,
        pose_extractor=services["pose_extractor"],
    )
    user_result["comparison_video_path"] = str(compared_user_video)
    athlete_result["comparison_video_path"] = athlete_result["annotated_video_path"]

    return {
        "athlete": athlete_result,
        "user": user_result,
        "comparison": comparison_result,
    }


def sidebar_controls():
    with st.sidebar:
        st.markdown("## Comparison Setup")
        action_name = st.selectbox(
            "Movement category",
            options=available_actions(),
            help="Use the same action type for both videos so the comparison stays meaningful.",
        )
        show_original = st.toggle("Show Original Video", value=False)
        st.caption("Annotated videos are shown by default. Toggle this to review the raw uploads.")
    return action_name, show_original


def main():
    inject_styles()
    action_name, show_original = sidebar_controls()
    metrics = load_model_metrics()

    st.markdown(
        """
        <div class="hero">
            <h1>TALENT LENS AI</h1>
            <p>Side-by-side athlete vs user motion analysis with MediaPipe pose overlays, comparison scoring, and demo-ready performance dashboards.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploader_left, uploader_right = st.columns(2)
    with uploader_left:
        athlete_upload = st.file_uploader(
            "Athlete (Reference Video)",
            type=["mp4", "mov", "avi", "mkv"],
            key="athlete_upload",
        )
    with uploader_right:
        user_upload = st.file_uploader(
            "User / Non-Athlete Video",
            type=["mp4", "mov", "avi", "mkv"],
            key="user_upload",
        )

    run_requested = st.button("Process Comparison", type="primary", use_container_width=True)

    if run_requested:
        if not athlete_upload or not user_upload:
            st.warning("Upload both videos before running the comparison.")
        else:
            athlete_path = persist_upload(athlete_upload, "athlete")
            user_path = persist_upload(user_upload, "user")
            with st.spinner("Processing videos, extracting pose sequences, and building comparison overlays..."):
                st.session_state["comparison_payload"] = run_comparison(
                    reference_path=athlete_path,
                    user_path=user_path,
                    action_name=action_name,
                )

    payload = st.session_state.get("comparison_payload")
    if not payload:
        st.info("Upload two videos and click Process Comparison to generate the synchronized demo dashboard.")
        return

    athlete_result = payload["athlete"]
    user_result = payload["user"]
    comparison = payload["comparison"]

    left_column, right_column = st.columns(2)
    athlete_video_path = athlete_result["video_path"] if show_original else athlete_result["comparison_video_path"]
    user_video_path = user_result["video_path"] if show_original else user_result["comparison_video_path"]

    with left_column:
        render_video_card(
            "Athlete (Annotated)" if not show_original else "Athlete (Original)",
            athlete_video_path,
            "Reference benchmark video",
            athlete_result,
        )
    with right_column:
        render_video_card(
            "User (Annotated)" if not show_original else "User (Original)",
            user_video_path,
            "Comparison feedback is drawn directly on the user overlay",
            user_result,
        )

    st.markdown('<div class="metric-strip">', unsafe_allow_html=True)
    st.subheader("Similarity Score")
    st.metric("Similarity", f"{comparison['similarity_score']:.1f}%")
    st.progress(min(max(comparison["similarity_score"] / 100.0, 0.0), 1.0))
    st.write(f"Assessment: **{comparison['label']}**")
    feedback_html = "".join(
        f'<span class="feedback-chip">{message}</span>' for message in comparison["feedback_messages"]
    )
    st.markdown(feedback_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Performance Metrics")
    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("Joint Angle Difference", f"{comparison['joint_angle_difference']:.2f} deg")
    metric_b.metric("Movement Smoothness", f"{comparison['movement_smoothness']:.1f}")
    metric_c.metric("Temporal Consistency", f"{comparison['temporal_consistency']:.1f}")
    metric_d.metric("Average Posture Error", f"{comparison['average_posture_error']:.2f} deg")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.pyplot(build_frame_feedback_plot(comparison["frame_wise_deviation"]), use_container_width=True)
    with chart_right:
        st.pyplot(build_joint_error_plot(comparison["per_joint_error"]), use_container_width=True)

    st.subheader("Model Performance Dashboard")
    source_label = metrics.get("source", "unknown source")
    st.caption(f"Metrics source: {source_label}")

    dashboard_a, dashboard_b, dashboard_c = st.columns(3)
    accuracy_value = metrics.get("accuracy")
    loss_value = metrics.get("loss")
    confidence_value = user_result["prediction"]["confidence"]

    dashboard_a.metric("Accuracy", "N/A" if accuracy_value is None else f"{accuracy_value * 100:.2f}%")
    dashboard_b.metric("Loss", "N/A" if loss_value is None else f"{loss_value:.4f}")
    dashboard_c.metric("Prediction Confidence", f"{confidence_value * 100:.2f}%")

    probability_df = pd.DataFrame(
        {
            "Action": list(user_result["prediction"]["probabilities"].keys()),
            "Probability": list(user_result["prediction"]["probabilities"].values()),
        }
    ).sort_values("Probability", ascending=False)
    st.dataframe(probability_df, use_container_width=True, hide_index=True)

    with st.expander("Confusion Matrix", expanded=False):
        render_confusion_matrix(metrics)

    st.caption(
        "If no saved LSTM metrics file is present, the dashboard falls back to a nearest-centroid baseline built from the saved feature dataset."
    )


if __name__ == "__main__":
    main()
