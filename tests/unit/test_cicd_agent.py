"""
Unit tests for CICDAgent — AI Developer OS
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cicd.agent import CICDAgent


class TestCICDStackDetection:
    def test_detect_python_stack(self):
        agent = CICDAgent(root_dir=os.path.abspath("."))
        stack = agent.detect_stack()
        assert "python" in stack["languages"]
        assert "pytest" in stack["test_commands"]
        assert "pip" in stack["package_managers"]

    def test_detect_typescript_stack(self):
        agent = CICDAgent(root_dir=os.path.abspath("."))
        stack = agent.detect_stack()
        assert "typescript" in stack["languages"]
        assert "npm" in stack["package_managers"]
        assert "nextjs" in stack["frameworks"]


class TestCICDWorkflowGeneration:
    def setup_method(self):
        self.agent = CICDAgent(root_dir=os.path.abspath("."))

    def test_generate_ci_workflow_success(self):
        res = self.agent.generate_ci_workflow(branch="main")
        assert res["status"] == "success"
        assert res["workflow_type"] == "ci"
        assert "name: CI" in res["yaml"]
        assert "actions/checkout@v4" in res["yaml"]
        assert res["output_path"] == ".github/workflows/ci.yml"

    def test_generate_ci_workflow_contains_security_scan(self):
        res = self.agent.generate_ci_workflow(branch="main")
        # Template should include security scan or bandit/trivy
        assert "security" in res["yaml"].lower() or "bandit" in res["yaml"].lower()

    def test_generate_cd_workflow_success(self):
        res = self.agent.generate_cd_workflow(deploy_target="docker")
        assert res["status"] == "success"
        assert res["workflow_type"] == "cd"
        assert "name: CD" in res["yaml"]
        assert "build-and-push" in res["yaml"]
        assert res["output_path"] == ".github/workflows/cd.yml"

    def test_workflow_output_path_is_safe(self):
        res = self.agent.generate_ci_workflow()
        assert not res["output_path"].startswith("/")
        assert ".." not in res["output_path"]

    def test_write_workflow_to_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_agent = CICDAgent(root_dir=tmpdir)
            wf = temp_agent.generate_ci_workflow()
            write_res = temp_agent.write_workflow_file(wf)
            assert write_res["status"] == "success"
            written_file = os.path.join(tmpdir, wf["output_path"])
            assert os.path.exists(written_file)
            with open(written_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "name: CI" in content
