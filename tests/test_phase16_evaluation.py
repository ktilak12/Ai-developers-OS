import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from evaluation.dataset import get_all_benchmark_tasks, get_benchmark_task_by_id, SWE_BENCHMARK_20_TASKS
from evaluation.evaluator import SWEEvaluator
from evaluation.report import BenchmarkReportGenerator

client = TestClient(app)


def test_swe_benchmark_dataset_integrity():
    tasks = get_all_benchmark_tasks()
    assert len(tasks) == 20
    assert len(SWE_BENCHMARK_20_TASKS) == 20

    # Ensure uniqueness of task IDs
    task_ids = [t.task_id for t in tasks]
    assert len(set(task_ids)) == 20

    for task in tasks:
        assert task.task_id.startswith("swe-")
        assert len(task.title) > 0
        assert len(task.description) > 0
        assert len(task.target_files) > 0
        assert len(task.expected_tools) > 0

    # Single task lookup
    task_01 = get_benchmark_task_by_id("swe-01")
    assert task_01 is not None
    assert task_01.task_id == "swe-01"

    # Non-existent task lookup
    assert get_benchmark_task_by_id("swe-non-existent") is None


def test_swe_evaluator_comparative_scorecard():
    temp_dir = tempfile.mkdtemp()
    try:
        evaluator = SWEEvaluator(temp_dir)
        scorecard = evaluator.run_benchmark(task_ids=["swe-01", "swe-02", "swe-03"])

        assert scorecard.tasks_evaluated_count == 3
        assert scorecard.v1_baseline.completion_rate_pct < scorecard.v2_orchestrated.completion_rate_pct
        assert scorecard.v2_orchestrated.avg_test_success_rate > scorecard.v1_baseline.avg_test_success_rate
        assert scorecard.v2_orchestrated.avg_security_score > scorecard.v1_baseline.avg_security_score
        assert len(scorecard.task_breakdown) == 3

        # Markdown Report Generation
        md_report = BenchmarkReportGenerator.generate_markdown_report(scorecard)
        assert "# SWE Benchmark Evaluation Report" in md_report
        assert "Agent v1 (Single LLM)" in md_report
        assert "Agent v2 (AI Developer OS)" in md_report
        assert "swe-01" in md_report
    finally:
        shutil.rmtree(temp_dir)


def test_evaluation_api_endpoints():
    # 1. /api/evaluation/benchmark/tasks
    res_tasks = client.get("/api/evaluation/benchmark/tasks")
    assert res_tasks.status_code == 200
    data_tasks = res_tasks.json()
    assert data_tasks["status"] == "success"
    assert data_tasks["total"] == 20

    # 2. /api/evaluation/benchmark/tasks/{task_id}
    res_single = client.get("/api/evaluation/benchmark/tasks/swe-01")
    assert res_single.status_code == 200
    assert res_single.json()["task_id"] == "swe-01"

    # 3. /api/evaluation/benchmark/scorecard
    res_scorecard = client.get("/api/evaluation/benchmark/scorecard")
    assert res_scorecard.status_code == 200
    sc_data = res_scorecard.json()
    assert "evaluation_id" in sc_data
    assert "v1_baseline" in sc_data
    assert "v2_orchestrated" in sc_data

    # 4. /api/evaluation/benchmark/run
    res_run = client.post("/api/evaluation/benchmark/run", json={"task_ids": ["swe-01", "swe-02"]})
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["tasks_evaluated_count"] == 2

    # 5. /api/evaluation/benchmark/report
    res_report = client.get("/api/evaluation/benchmark/report")
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert "markdown" in report_data
    assert len(report_data["markdown"]) > 100


def test_evaluation_api_error_handling():
    # 1. Non-existent task returns 404
    res_404 = client.get("/api/evaluation/benchmark/tasks/swe-unknown-999")
    assert res_404.status_code == 404

    # 2. Oversized task ID returns 400
    res_oversized = client.get(f"/api/evaluation/benchmark/tasks/{'x' * 65}")
    assert res_oversized.status_code == 400

    # 3. Invalid task_ids list type returns 400
    res_bad_type = client.post("/api/evaluation/benchmark/run", json={"task_ids": "not_a_list"})
    assert res_bad_type.status_code in (400, 422)
