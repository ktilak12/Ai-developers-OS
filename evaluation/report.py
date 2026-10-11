import html
from evaluation.models import ComparativeScorecard


class BenchmarkReportGenerator:
    """
    Generates human-readable Markdown scorecards and reports comparing Agent v1 vs Agent v2.
    Sanitizes dynamic fields to prevent HTML and script injection in markdown renderers.
    """

    @staticmethod
    def generate_markdown_report(scorecard: ComparativeScorecard) -> str:
        v1 = scorecard.v1_baseline
        v2 = scorecard.v2_orchestrated

        safe_eval_id = html.escape(str(scorecard.evaluation_id))
        safe_created_at = html.escape(str(scorecard.created_at))

        lines = [
            f"# SWE Benchmark Evaluation Report ({safe_eval_id})",
            f"**Evaluated Tasks:** {scorecard.tasks_evaluated_count} | **Timestamp:** {safe_created_at}",
            "",
            "## 🏆 Executive Summary",
            f"- **Task Completion Rate:** Agent v1: `{v1.completion_rate_pct}%` ➡️ Agent v2: `{v2.completion_rate_pct}%` (**+{scorecard.completion_improvement_pct}% gain**)",
            f"- **Test Suite Success Rate:** Agent v1: `{v1.avg_test_success_rate}%` ➡️ Agent v2: `{v2.avg_test_success_rate}%` (**+{scorecard.test_success_improvement_pct}% gain**)",
            f"- **Security Audit Score:** Agent v1: `{v1.avg_security_score}/100` ➡️ Agent v2: `{v2.avg_security_score}/100` (**+{scorecard.security_score_improvement_pct} points**)",
            f"- **Planning Accuracy:** Agent v1: `{v1.avg_planning_accuracy}%` ➡️ Agent v2: `{v2.avg_planning_accuracy}%`",
            f"- **Code Correctness:** Agent v1: `{v1.avg_code_correctness}%` ➡️ Agent v2: `{v2.avg_code_correctness}%`",
            "",
            "## 📊 Comparative Performance Matrix",
            "| Dimension | Agent v1 (Single LLM) | Agent v2 (AI Developer OS) | Delta / Impact |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Completion Rate** | {v1.completion_rate_pct}% | {v2.completion_rate_pct}% | **+{scorecard.completion_improvement_pct}%** |",
            f"| **Test Pass Rate** | {v1.avg_test_success_rate}% | {v2.avg_test_success_rate}% | **+{scorecard.test_success_improvement_pct}%** |",
            f"| **Security Audit** | {v1.avg_security_score}/100 | {v2.avg_security_score}/100 | **+{scorecard.security_score_improvement_pct}** |",
            f"| **Planning Accuracy** | {v1.avg_planning_accuracy}% | {v2.avg_planning_accuracy}% | **+{round(v2.avg_planning_accuracy - v1.avg_planning_accuracy, 1)}%** |",
            f"| **Code Correctness** | {v1.avg_code_correctness}% | {v2.avg_code_correctness}% | **+{round(v2.avg_code_correctness - v1.avg_code_correctness, 1)}%** |",
            f"| **Tool Calling Accuracy** | {v1.avg_tool_accuracy}% | {v2.avg_tool_accuracy}% | **+{round(v2.avg_tool_accuracy - v1.avg_tool_accuracy, 1)}%** |",
            f"| **Avg Duration (sec)** | {v1.avg_duration_sec}s | {v2.avg_duration_sec}s | **Self-healing retry overhead** |",
            f"| **Total Token Cost** | ${v1.total_cost_usd} | ${v2.total_cost_usd} | **More targeted context via GraphRAG** |",
            "",
            "## 🎯 Task Breakdown Sample",
        ]

        for item in scorecard.task_breakdown[:5]:
            safe_task_id = html.escape(str(item.get("task_id", "")))
            safe_title = html.escape(str(item.get("title", "")))
            safe_cat = html.escape(str(item.get("category", "")))
            safe_diff = html.escape(str(item.get("difficulty", "")))

            lines.append(f"### `{safe_task_id}`: {safe_title}")
            lines.append(f"- **Category:** {safe_cat} | **Difficulty:** {safe_diff}")
            lines.append(f"- **Agent v1:** Completed: {item['v1']['completed']} | Tests: {item['v1']['test_success_rate']}% | Security: {item['v1']['security_score']}")
            lines.append(f"- **Agent v2:** Completed: {item['v2']['completed']} | Tests: {item['v2']['test_success_rate']}% | Security: {item['v2']['security_score']}")
            lines.append("")

        return "\n".join(lines)
