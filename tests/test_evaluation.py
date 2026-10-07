from evals.reliability import summarize


def test_selected_score_bins_include_one_and_do_not_hide_service_errors():
    expected = {"sentiment": "positive", "emotion": "happy"}
    report = summarize({"split": "synthetic-test", "cases": [
        {"success": True, "expected": expected, "actual": {**expected, "confidence": 1}},
        {"success": True, "expected": expected, "actual": {"sentiment": "positive", "emotion": "neutral", "confidence": .95}},
        {"success": False, "expected": expected, "error": "SUMMARY_UNSUPPORTED"},
    ]})
    assert report["total"] == 3 and report["validated_responses"] == 2
    assert report["service_errors_excluded_from_bins"] == 1
    assert report["bins"][-1]["count"] == 2 and report["bins"][-1]["upper_inclusive"]
    assert report["bins"][-1]["joint_sentiment_emotion_agreement"]["correct"] == 1
    assert report["brier_score"] is None


def test_empty_score_bins_do_not_invent_observations():
    report = summarize({"split": "empty-test", "cases": []})
    assert report["validated_responses"] == 0
    assert all(row["count"] == 0 and row["mean_selected_score"] is None
               and row["joint_sentiment_emotion_agreement"] is None for row in report["bins"])
