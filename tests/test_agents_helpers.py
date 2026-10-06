import pytest
from agents.coder.tools import CoderTools
from agents.security.agent import SecurityAgent
from agents.tester.agent import TestingAgent as AgentTesterClass
from agents.reviewer.agent import ReviewAgent


def test_coder_diff_stats():
    tools = CoderTools(".")
    sample_diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
-old_code()
+new_code_1()
+new_code_2()
 unchanged()"""
    stats = tools.compute_diff_stats(sample_diff)
    assert stats["additions"] == 2
    assert stats["deletions"] == 1
    assert stats["total_changes"] == 3


def test_security_shannon_entropy():
    # Uniform text has lower entropy than randomized high-entropy API key
    low_entropy = SecurityAgent.calculate_shannon_entropy("aaaaaaaa")
    high_entropy = SecurityAgent.calculate_shannon_entropy("sk_live_51N8x92KLq92jL0P19z82hK")
    assert low_entropy == 0.0
    assert high_entropy > 3.0


def test_tester_metrics_formatter():
    summary = AgentTesterClass.format_test_metrics_summary(passed_count=48, failed_count=2, duration_sec=3.45)
    assert "48/50 tests passed (96.0%) in 3.45s" in summary


def test_reviewer_conventional_title():
    assert ReviewAgent.validate_conventional_title("feat(auth): add JWT token rotation") is True
    assert ReviewAgent.validate_conventional_title("fix: checkout bug") is True
    assert ReviewAgent.validate_conventional_title("invalid pr title format") is False
