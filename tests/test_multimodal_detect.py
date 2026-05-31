import unittest

from api.multimodal_detect import fuse_scores


class MultimodalDetectTests(unittest.TestCase):
    def test_fusion_rvra_when_both_modalities_clean(self):
        result = fuse_scores(video_score=0.2, audio_score=0.3)

        self.assertEqual(result.classification, "Real Video & Real Audio (RVRA)")
        self.assertEqual(result.alert_level, "AUTHENTIC")
        self.assertTrue(result.audio_available)
        self.assertAlmostEqual(result.fused_score, 0.25)

    def test_fusion_fvra_when_only_video_is_fake(self):
        result = fuse_scores(video_score=0.8, audio_score=0.3)

        self.assertEqual(result.classification, "Fake Video & Real Audio (FVRA)")
        self.assertEqual(result.alert_level, "PARTIAL FORGERY (Visual Identity Swap)")
        self.assertTrue(result.audio_available)
        self.assertAlmostEqual(result.fused_score, 0.55)

    def test_fusion_rvfa_when_only_audio_is_fake(self):
        result = fuse_scores(video_score=0.2, audio_score=0.8)

        self.assertEqual(result.classification, "Real Video & Fake Audio (RVFA)")
        self.assertEqual(result.alert_level, "PARTIAL FORGERY (Acoustic Voice Clone)")
        self.assertTrue(result.audio_available)
        self.assertAlmostEqual(result.fused_score, 0.5)

    def test_fusion_fvfa_when_both_modalities_are_fake(self):
        result = fuse_scores(video_score=0.8, audio_score=0.8)

        self.assertEqual(result.classification, "Fake Video & Fake Audio (FVFA)")
        self.assertEqual(result.alert_level, "TOTAL MULTIMODAL SYNTHESIS")
        self.assertTrue(result.audio_available)
        self.assertAlmostEqual(result.fused_score, 0.8)

    def test_fusion_uses_visual_only_fallback_when_audio_missing(self):
        result = fuse_scores(video_score=0.7, audio_score=None)

        self.assertEqual(result.classification, "Video Analysis (Audio Missing/Degraded)")
        self.assertEqual(result.alert_level, "FAKE")
        self.assertFalse(result.audio_available)
        self.assertAlmostEqual(result.fused_score, 0.7)


if __name__ == "__main__":
    unittest.main()
