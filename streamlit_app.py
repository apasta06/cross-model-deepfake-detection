from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ui_mvp.analysis import AnalysisError, analyze_media, save_uploaded_file, validate_upload
from ui_mvp.config import BASE_DIR, MAX_UPLOAD_SIZE_MB, MODEL_OPTIONS, RETENTION_MESSAGE, RISK_COLORS, SUPPORTED_INPUT_FORMATS
from ui_mvp.reporting import build_report_html, build_report_json, suggested_report_name
from ui_mvp.schemas import HistoryRecord
from ui_mvp.storage import append_history, load_history, update_report_path, write_report_file


st.set_page_config(
    page_title="Deepfake Forensics MVP",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #0d1117 0%, #111827 45%, #0f172a 100%); color: #f3f4f6; }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .hero-card {
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: rgba(15, 23, 42, 0.72);
            backdrop-filter: blur(8px);
            min-height: 130px;
        }
        .hero-label { color: #9ca3af; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }
        .hero-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem; }
        .section-card {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: rgba(17, 24, 39, 0.85);
            margin-top: 1rem;
        }
        .privacy-banner {
            border-left: 4px solid #38bdf8;
            background: rgba(2, 132, 199, 0.12);
            padding: 0.9rem 1rem;
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, color: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="hero-label">{label}</div>
          <div class="hero-value" style="color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_color(risk_level: str) -> str:
    return RISK_COLORS.get(risk_level, "#E5E7EB")


def discover_checkpoints(selected_model: str) -> list[Path]:
    pattern_map = {
        "XCEPTION": "Xception*.pt",
        "MESO4": "Meso4*.pt",
        "MESOINCEPTION4": "MesoInception4*.pt",
        "EFFICIENTB0": "Efficient*.pt",
    }
    pattern = pattern_map.get(selected_model)
    if not pattern:
        return []

    search_dirs = [
        BASE_DIR / "smoke_outputs",
        BASE_DIR / "Unimodal" / "weights" / "video",
        BASE_DIR / "Unimodal" / "weights" / "audio",
        BASE_DIR,
    ]
    discovered: list[Path] = []
    for folder in search_dirs:
        if folder.exists():
            discovered.extend(folder.glob(pattern))
    unique = []
    seen = set()
    for path in discovered:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return sorted(unique)


def main() -> None:
    inject_theme()
    st.title("Deepfake Forensics MVP")
    st.caption("Upload media, run a local analysis, review frame-level signals, and export an audit-ready report.")
    st.markdown(f'<div class="privacy-banner">{RETENTION_MESSAGE}</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("Run Setup")
        selected_model = st.selectbox(
            "Select Type / Model",
            list(MODEL_OPTIONS.keys()),
            format_func=lambda key: f"{key} - {MODEL_OPTIONS[key]}",
        )
        discovered_checkpoints = discover_checkpoints(selected_model)
        checkpoint_options = ["Manual path entry"]
        checkpoint_options.extend(str(path) for path in discovered_checkpoints)
        if selected_model == "MESO4":
            smoke_checkpoint = BASE_DIR / "smoke_outputs" / "best_MESO4_VIDEO.pt"
            if smoke_checkpoint.exists() and str(smoke_checkpoint) not in checkpoint_options:
                checkpoint_options.insert(1, str(smoke_checkpoint))
        selected_checkpoint = st.selectbox(
            "Available checkpoints",
            checkpoint_options,
            help="Choose a discovered checkpoint or keep manual entry selected.",
        )
        checkpoint_text = st.text_input(
            "Checkpoint path",
            value="" if selected_checkpoint == "Manual path entry" else selected_checkpoint,
            help="Optional. Supply a compatible .pt checkpoint for model-backed scoring.",
        )
        if discovered_checkpoints:
            st.caption(f"Auto-detected {len(discovered_checkpoints)} checkpoint(s) for {selected_model}.")
        if selected_model == "MESO4":
            st.caption("Smoke-test checkpoint search includes `smoke_outputs/best_MESO4_VIDEO.pt`.")
        st.caption(f"Supported uploads: {', '.join(SUPPORTED_INPUT_FORMATS)}")
        st.caption(f"Maximum upload size: {MAX_UPLOAD_SIZE_MB} MB")

    uploaded_file = st.file_uploader("Upload Media", type=[ext.lstrip(".") for ext in SUPPORTED_INPUT_FORMATS])

    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
        st.session_state.latest_media_bytes = None
        st.session_state.latest_media_name = None
        st.session_state.latest_report_path = None

    if uploaded_file is not None:
        st.subheader("1. Upload Media")
        file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
        st.write(f"Filename: `{uploaded_file.name}`")
        st.write(f"Size: `{file_size_mb:.2f} MB`")
        st.write(f"Format: `{Path(uploaded_file.name).suffix.lower()}`")
        effective_checkpoint_text = checkpoint_text.strip()
        if selected_checkpoint != "Manual path entry":
            effective_checkpoint_text = selected_checkpoint

        if effective_checkpoint_text and not Path(effective_checkpoint_text).expanduser().exists():
            st.warning("The checkpoint path does not exist. The run will fall back to metadata-only review mode.")
        elif effective_checkpoint_text:
            st.info(f"Using checkpoint: `{effective_checkpoint_text}`")
        else:
            st.info("No checkpoint selected. The run will use metadata-only review mode.")

        if st.button("2. Run Analysis", type="primary", use_container_width=True):
            tmp_path = save_uploaded_file(uploaded_file)
            try:
                validate_upload(tmp_path, MAX_UPLOAD_SIZE_MB)
                checkpoint_path = Path(effective_checkpoint_text).expanduser() if effective_checkpoint_text else None
                with st.spinner("Running analysis. Large videos can take around a minute on CPU..."):
                    result = analyze_media(tmp_path, selected_model, checkpoint_path)
                append_history(HistoryRecord.from_result(result))
                st.session_state.latest_result = result
                st.session_state.latest_media_bytes = uploaded_file.getvalue()
                st.session_state.latest_media_name = uploaded_file.name
                st.session_state.latest_report_path = None
                st.success("Analysis complete. Results are shown below in section 3.")
            except AnalysisError as exc:
                st.error(str(exc))
            except Exception as exc:  # pragma: no cover
                st.error(f"Analysis failed: {exc}")
            finally:
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass

    result = st.session_state.latest_result
    if result:
        st.subheader("3. View Results")
        hero_left, hero_mid, hero_right = st.columns([1.2, 1, 1])
        with hero_left:
            render_metric_card("Final Verdict", result.verdict, risk_color(result.risk_level))
        with hero_mid:
            render_metric_card("Confidence", f"{result.confidence_score:.1%}", "#E5E7EB")
        with hero_right:
            render_metric_card("Overall Risk", result.risk_level.replace("_", " ").title(), risk_color(result.risk_level))

        viewer_col, evidence_col = st.columns([1.8, 1.2])
        with viewer_col:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### Forensic Viewer")
            if result.input_type == "video":
                st.video(st.session_state.latest_media_bytes)
            else:
                st.image(st.session_state.latest_media_bytes, caption=result.filename, use_container_width=True)

            if result.frame_results:
                frame_df = pd.DataFrame(result.frame_results)
                selected_index = st.slider(
                    "Frame-by-frame review",
                    min_value=0,
                    max_value=max(len(result.frame_results) - 1, 0),
                    value=0,
                )
                selected_row = frame_df.iloc[selected_index]
                st.write(
                    f"Frame `{int(selected_row['frame_index'])}` at `{selected_row['timestamp_label']}` "
                    f"has fake probability `{selected_row['fake_probability']:.1%}`."
                )
                st.bar_chart(frame_df.set_index("timestamp_label")["fake_probability"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with evidence_col:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### Explanation & Evidence")
            st.write(result.summary_text)
            for asset in result.evidence_paths:
                st.markdown(f"**{asset.label}**")
                st.write(asset.description)
            if result.warnings:
                st.warning("\n".join(result.warnings))
            st.markdown("</div>", unsafe_allow_html=True)

        lower_left, lower_right = st.columns([1.1, 1])
        with lower_left:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### Analysis Dashboard")
            stats_df = pd.DataFrame(
                [
                    {"Category": "Likely fake frames", "Count": result.frame_stats.get("fake_frames", 0)},
                    {"Category": "Uncertain frames", "Count": result.frame_stats.get("uncertain_frames", 0)},
                    {"Category": "Likely real frames", "Count": result.frame_stats.get("real_frames", 0)},
                ]
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Field": "Filename", "Value": result.filename},
                        {"Field": "Model", "Value": result.model_used},
                        {"Field": "Created", "Value": result.created_at},
                        {"Field": "Input type", "Value": result.input_type},
                        {"Field": "Frame samples", "Value": result.frame_stats.get("sampled_frames", 0)},
                        {"Field": "Duration (s)", "Value": result.media_metadata.duration_seconds},
                        {"Field": "FPS", "Value": result.media_metadata.fps},
                        {"Field": "Resolution", "Value": f"{result.media_metadata.width} x {result.media_metadata.height}"},
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.bar_chart(stats_df.set_index("Category"), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with lower_right:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### Report Generation")
            json_report = build_report_json(result)
            html_report = build_report_html(result)

            st.download_button(
                "Download JSON report",
                data=json_report,
                file_name=suggested_report_name(result, "json"),
                mime="application/json",
                use_container_width=True,
            )
            st.download_button(
                "Download HTML report",
                data=html_report,
                file_name=suggested_report_name(result, "html"),
                mime="text/html",
                use_container_width=True,
            )

            if st.button("Save HTML report to local audit store", use_container_width=True):
                report_name = suggested_report_name(result, "html")
                report_path = write_report_file(report_name, html_report)
                update_report_path(result.analysis_id, str(report_path))
                st.session_state.latest_report_path = str(report_path)
                st.success(f"Saved report to {report_path}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("4. History & Auditing")
    history = load_history(limit=20)
    if history:
        history_df = pd.DataFrame(history)
        history_df["filesize_mb"] = (history_df["filesize"] / (1024 * 1024)).round(2)
        st.dataframe(
            history_df[
                [
                    "created_at",
                    "filename",
                    "input_type",
                    "model_used",
                    "verdict",
                    "confidence_score",
                    "risk_level",
                    "filesize_mb",
                    "report_path",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No prior analyses yet. Run your first upload to start the audit trail.")


if __name__ == "__main__":
    main()
