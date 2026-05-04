import json
import unittest

from ui_mvp.analysis import build_frame_stats, summarize_frame_results
from ui_mvp.reporting import build_report_html, build_report_json
from ui_mvp.schemas import AnalysisResult, EvidenceAsset, MediaMetadata


class UiMvpTests(unittest.TestCase):
    def test_frame_stats_count_buckets(self):
        frame_results = [
            {"frame_index": 0, "fake_probability": 0.1},
            {"frame_index": 1, "fake_probability": 0.55},
            {"frame_index": 2, "fake_probability": 0.9},
        ]
        stats = build_frame_stats(frame_results)
        self.assertEqual(stats["real_frames"], 1)
        self.assertEqual(stats["uncertain_frames"], 1)
        self.assertEqual(stats["fake_frames"], 1)

    def test_summary_uses_checkpoint_warning_path(self):
        frame_results = [{"frame_index": 0, "fake_probability": 0.5}]
        verdict, confidence, risk_level, summary, flagged = summarize_frame_results(frame_results, ["missing checkpoint"])
        self.assertEqual(verdict, "Needs configured model checkpoint")
        self.assertEqual(risk_level, "uncertain")
        self.assertEqual(flagged, [])
        self.assertAlmostEqual(confidence, 0.5)
        self.assertIn("pending checkpoint", summary.lower())

    def test_report_builders_emit_content(self):
        result = AnalysisResult(
            analysis_id="abc123",
            input_type="video",
            filename="clip.mp4",
            filesize=1024,
            verdict="Likely Fake",
            confidence_score=0.87,
            risk_level="likely_fake",
            summary_text="Likely manipulated.",
            flagged_frame_indices=[1, 3],
            frame_stats={"sampled_frames": 2, "fake_frames": 2, "uncertain_frames": 0, "real_frames": 0},
            evidence_paths=[EvidenceAsset(label="Frame timeline", kind="timeline", description="Sampled frames.")],
            created_at="2026-04-10T00:00:00Z",
            model_used="XCEPTION",
            media_metadata=MediaMetadata(
                filename="clip.mp4",
                filesize=1024,
                extension=".mp4",
                media_kind="video",
                duration_seconds=3.0,
                fps=24.0,
                frame_count=72,
                width=1280,
                height=720,
            ),
            frame_results=[{"frame_index": 0, "timestamp_label": "00:00", "fake_probability": 0.87, "risk_label": "Likely Fake"}],
        )
        report_json = build_report_json(result)
        report_html = build_report_html(result)
        self.assertEqual(json.loads(report_json)["analysis_id"], "abc123")
        self.assertIn("Deepfake Analysis Report", report_html)
        self.assertIn("Likely Fake", report_html)


if __name__ == "__main__":
    unittest.main()
