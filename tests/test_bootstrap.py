from dicom_release_compare.models import ChangeItem, DiffReport, DiffRun
from dicom_release_compare.pipeline import pipeline_overview


def test_pipeline_has_expected_stages():
    steps = [s.name for s in pipeline_overview()]
    assert steps == [
        "fetch",
        "parse",
        "normalize",
        "align",
        "diff",
        "semantic",
        "score",
        "report",
        "publish",
    ]


def test_diff_report_model_creation():
    report = DiffReport(run=DiffRun(run_id="run_1", base_release="2024e", target_release="2026a"))
    assert report.run.base_release == "2024e"
    assert report.changes == []


def test_change_item_score_bounds():
    item = ChangeItem(
        change_id="chg1",
        part="03",
        entity="attribute",
        change_type="modified",
        classification="Technical",
        score=50,
    )
    assert item.score == 50
