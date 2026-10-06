import os
import shutil
import tempfile
import pytest
from evaluation.dataset import get_all_benchmark_tasks, get_benchmark_task_by_id
from evaluation.models import DifficultyLevel, BenchmarkTaskCategory
from evaluation.evaluator import SWEEvaluator
from evaluation.report import BenchmarkReportGenerator


def test_swe_benchmark_dataset():
    tasks = get_all_benchmark_tasks()
    assert len(tasks) == 20
    
    # Test lookup
    task_01 = get_benchmark_task_by_id("swe-01")
    assert task_01 is not None
    assert task_01.category == BenchmarkTaskCategory.BUG_FIX
    assert "coupon" in task_01.title.lower()
    assert len(task_01.target_files) >= 1
    assert len(task_01.expected_tools) >= 1

    # Verify category coverage
    categories = {t.category for t in tasks}
    assert BenchmarkTaskCategory.BUG_FIX in categories
    assert BenchmarkTaskCategory.SECURITY in categories
    assert BenchmarkTaskCategory.PERFORMANCE in categories
    assert BenchmarkTaskCategory.REFACTOR in categories
    assert BenchmarkTaskCategory.API_DESIGN in categories


def test_swe_evaluator_and_scorecard():
    temp_dir = tempfile.mkdtemp()
    try:
        storage_path = os.path.join(temp_dir, "test_benchmarks.json")
        evaluator = SWEEvaluator(temp_dir, storage_path=storage_path)

        # Initial seed check
        scorecard = evaluator.get_latest_scorecard()
        assert scorecard is not None
        assert scorecard.tasks_evaluated_count == 20
        assert scorecard.v2_orchestrated.completion_rate_pct > scorecard.v1_baseline.completion_rate_pct
        assert scorecard.v2_orchestrated.avg_test_success_rate > scorecard.v1_baseline.avg_test_success_rate
        assert scorecard.v2_orchestrated.avg_security_score > scorecard.v1_baseline.avg_security_score
        assert len(scorecard.task_breakdown) == 20

        # Custom subset run
        subset_scorecard = evaluator.run_benchmark(task_ids=["swe-01", "swe-02"])
        assert subset_scorecard.tasks_evaluated_count == 2
        assert len(subset_scorecard.task_breakdown) == 2

        # Generate markdown report
        report_md = BenchmarkReportGenerator.generate_markdown_report(scorecard)
        assert "# SWE Benchmark Evaluation Report" in report_md
        assert "Agent v1" in report_md
        assert "Agent v2" in report_md
        assert "Completion Rate" in report_md
    finally:
        shutil.rmtree(temp_dir)
