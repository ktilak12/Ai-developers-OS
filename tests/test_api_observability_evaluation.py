import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_api_observability_endpoints():
    # 1. Metrics
    res = client.get("/api/observability/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "task_success_rate" in metrics
    assert "total_tasks_executed" in metrics
    assert "avg_execution_time_sec" in metrics

    # 2. Traces list
    traces_res = client.get("/api/observability/traces")
    assert traces_res.status_code == 200
    traces_data = traces_res.json()
    assert traces_data["status"] == "success"
    assert traces_data["total"] >= 1
    trace_id = traces_data["traces"][0]["workflow_id"]

    # 3. Trace detail
    detail_res = client.get(f"/api/observability/traces/{trace_id}")
    assert detail_res.status_code == 200
    trace = detail_res.json()
    assert trace["workflow_id"] == trace_id
    assert len(trace["spans"]) >= 1


def test_api_evaluation_endpoints():
    # 1. Get 20 benchmark tasks
    tasks_res = client.get("/api/evaluation/benchmark/tasks")
    assert tasks_res.status_code == 200
    data = tasks_res.json()
    assert data["status"] == "success"
    assert data["total"] == 20

    # 2. Get task detail
    task_res = client.get("/api/evaluation/benchmark/tasks/swe-01")
    assert task_res.status_code == 200
    task = task_res.json()
    assert task["task_id"] == "swe-01"
    assert task["category"] == "bug_fix"

    # 3. Scorecard
    scorecard_res = client.get("/api/evaluation/benchmark/scorecard")
    assert scorecard_res.status_code == 200
    scorecard = scorecard_res.json()
    assert "v1_baseline" in scorecard
    assert "v2_orchestrated" in scorecard
    assert scorecard["v2_orchestrated"]["completion_rate_pct"] > scorecard["v1_baseline"]["completion_rate_pct"]

    # 4. Run custom subset
    run_res = client.post("/api/evaluation/benchmark/run", json={"task_ids": ["swe-01", "swe-02"]})
    assert run_res.status_code == 200
    custom_scorecard = run_res.json()
    assert custom_scorecard["tasks_evaluated_count"] == 2

    # 5. Markdown Report
    report_res = client.get("/api/evaluation/benchmark/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert "markdown" in report_data
    assert "SWE Benchmark Evaluation Report" in report_data["markdown"]
