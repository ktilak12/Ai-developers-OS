"""
CI/CD Agent — AI Developer OS
Generates, validates, and manages GitHub Actions workflow YAML files.
Uses LLM for intelligent, project-specific workflow generation.
"""
from __future__ import annotations

import os
import re
import textwrap
from typing import Dict, Any, List, Optional

from llm.provider import get_llm_provider, LLMMessage

CICD_SYSTEM_PROMPT = """You are a GitHub Actions expert for the AI Developer OS platform.
Your job is to generate production-grade, secure GitHub Actions YAML workflows.

Rules:
1. Always pin action versions (e.g., actions/checkout@v4, not @main)
2. Use secrets for all credentials — never hardcode
3. Add caching for dependencies (npm, pip, cargo, go modules, maven)
4. Include separate jobs for: lint, test, build, security scan, and deploy
5. Use matrix strategies for multi-version testing when appropriate
6. Add concurrency groups to cancel stale runs on the same branch
7. Separate workflows for CI (push/PR) and CD (main merge / release)
8. Output only valid YAML — no explanations, no markdown fences
"""


class CICDAgent:
    """
    CI/CD Workflow Agent: Generates GitHub Actions workflows for any detected stack.
    Supports Python, Node.js/TypeScript, Go, Rust, Java (Maven/Gradle), and C/C++.
    """

    SUPPORTED_LANGUAGES = ["python", "typescript", "javascript", "go", "rust", "java", "cpp"]

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    # ------------------------------------------------------------------
    # Language / Framework Detection
    # ------------------------------------------------------------------
    def detect_stack(self) -> Dict[str, Any]:
        """Detects the project's language and framework stack from project files."""
        stack: Dict[str, Any] = {
            "languages": [],
            "frameworks": [],
            "test_commands": [],
            "build_commands": [],
            "package_managers": [],
        }

        root = self.root_dir

        # Python
        if os.path.exists(os.path.join(root, "pyproject.toml")) or \
           os.path.exists(os.path.join(root, "requirements.txt")):
            stack["languages"].append("python")
            stack["test_commands"].append("pytest")
            stack["package_managers"].append("pip")
            # Check for FastAPI / Django / Flask
            for req_file in ["requirements.txt", "pyproject.toml"]:
                req_path = os.path.join(root, req_file)
                if os.path.exists(req_path):
                    content = self._read_safe(req_path)
                    if "fastapi" in content.lower():
                        stack["frameworks"].append("fastapi")
                    if "django" in content.lower():
                        stack["frameworks"].append("django")
                    if "flask" in content.lower():
                        stack["frameworks"].append("flask")

        # Node / TypeScript
        pkg_json = os.path.join(root, "apps", "web", "package.json")
        if os.path.exists(pkg_json):
            stack["languages"].append("typescript")
            stack["package_managers"].append("npm")
            content = self._read_safe(pkg_json)
            if "next" in content.lower():
                stack["frameworks"].append("nextjs")
                stack["build_commands"].append("npm run build")
                stack["test_commands"].append("npm test")

        # Go
        if os.path.exists(os.path.join(root, "go.mod")):
            stack["languages"].append("go")
            stack["test_commands"].append("go test ./...")
            stack["build_commands"].append("go build ./...")
            stack["package_managers"].append("go modules")

        # Rust
        if os.path.exists(os.path.join(root, "Cargo.toml")):
            stack["languages"].append("rust")
            stack["test_commands"].append("cargo test")
            stack["build_commands"].append("cargo build --release")
            stack["package_managers"].append("cargo")

        # Java
        if os.path.exists(os.path.join(root, "pom.xml")):
            stack["languages"].append("java")
            stack["test_commands"].append("mvn test")
            stack["build_commands"].append("mvn package -DskipTests")
            stack["package_managers"].append("maven")
            stack["frameworks"].append("maven")
        elif os.path.exists(os.path.join(root, "build.gradle")) or \
             os.path.exists(os.path.join(root, "build.gradle.kts")):
            stack["languages"].append("java")
            stack["test_commands"].append("gradle test")
            stack["build_commands"].append("gradle build -x test")
            stack["package_managers"].append("gradle")
            stack["frameworks"].append("gradle")

        return stack

    # ------------------------------------------------------------------
    # Workflow Generation
    # ------------------------------------------------------------------
    def generate_ci_workflow(
        self,
        branch: str = "main",
        stack: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a CI workflow (triggered on push and pull_request).
        Uses LLM for project-specific customization, falls back to templates.
        """
        if stack is None:
            stack = self.detect_stack()

        # Try LLM generation first
        llm_yaml = self._generate_with_llm(stack, workflow_type="ci", branch=branch)
        if llm_yaml:
            return {
                "status": "success",
                "workflow_type": "ci",
                "trigger": "push / pull_request",
                "languages": stack["languages"],
                "frameworks": stack["frameworks"],
                "yaml": llm_yaml,
                "source": "llm",
                "output_path": ".github/workflows/ci.yml",
            }

        # Fallback: build from templates
        yaml_parts = [self._header_ci(branch)]
        for lang in stack["languages"]:
            yaml_parts.append(self._job_for_language(lang, stack))
        yaml_parts.append(self._security_job())

        final_yaml = "\n".join(yaml_parts)

        return {
            "status": "success",
            "workflow_type": "ci",
            "trigger": "push / pull_request",
            "languages": stack["languages"],
            "frameworks": stack["frameworks"],
            "yaml": final_yaml,
            "source": "template",
            "output_path": ".github/workflows/ci.yml",
        }

    def generate_cd_workflow(
        self,
        deploy_target: str = "docker",
        stack: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a CD workflow (triggered on push to main / release tags).
        """
        if stack is None:
            stack = self.detect_stack()

        llm_yaml = self._generate_with_llm(
            stack, workflow_type="cd", deploy_target=deploy_target
        )
        if llm_yaml:
            return {
                "status": "success",
                "workflow_type": "cd",
                "trigger": "push to main / release tag",
                "deploy_target": deploy_target,
                "yaml": llm_yaml,
                "source": "llm",
                "output_path": ".github/workflows/cd.yml",
            }

        # Fallback template
        yaml = self._template_cd(deploy_target, stack)
        return {
            "status": "success",
            "workflow_type": "cd",
            "trigger": "push to main / release tag",
            "deploy_target": deploy_target,
            "yaml": yaml,
            "source": "template",
            "output_path": ".github/workflows/cd.yml",
        }

    def write_workflow_file(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Writes the generated workflow YAML to .github/workflows/."""
        rel_path = result.get("output_path", ".github/workflows/ci.yml")
        full_path = os.path.join(self.root_dir, rel_path)

        # Security: ensure path stays within root
        real_full = os.path.realpath(full_path)
        if not real_full.startswith(self.root_dir):
            return {"status": "error", "message": "Path traversal detected."}

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(result["yaml"])

        return {
            "status": "success",
            "written_to": rel_path,
            "size_bytes": len(result["yaml"].encode()),
        }

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------
    def _generate_with_llm(
        self,
        stack: Dict[str, Any],
        workflow_type: str = "ci",
        branch: str = "main",
        deploy_target: str = "docker",
    ) -> Optional[str]:
        languages = ", ".join(stack.get("languages", [])) or "unknown"
        frameworks = ", ".join(stack.get("frameworks", [])) or "none detected"
        test_cmds = ", ".join(stack.get("test_commands", [])) or "none"
        build_cmds = ", ".join(stack.get("build_commands", [])) or "none"
        pkg_managers = ", ".join(stack.get("package_managers", [])) or "none"

        if workflow_type == "ci":
            prompt = f"""Generate a GitHub Actions CI workflow YAML for this project:

Languages: {languages}
Frameworks: {frameworks}
Package managers: {pkg_managers}
Test commands: {test_cmds}
Build commands: {build_cmds}
Primary branch: {branch}

Requirements:
- Trigger on push and pull_request to {branch}
- Add dependency caching for each package manager
- Run linting, tests, and build in separate jobs
- Include a security scan job using appropriate tools (bandit for Python, npm audit for Node, cargo audit for Rust, etc.)
- Pin all action versions to @v4 or latest stable
- Add concurrency group to cancel redundant runs
- Use ubuntu-latest runners

Output only the complete YAML, no explanations.
"""
        else:
            prompt = f"""Generate a GitHub Actions CD workflow YAML for this project:

Languages: {languages}
Frameworks: {frameworks}
Deploy target: {deploy_target}
Primary branch: {branch}

Requirements:
- Trigger on push to main AND on release tag (v*)
- Build Docker image and push to GitHub Container Registry (ghcr.io)
- Use GITHUB_TOKEN for registry authentication
- Run database migrations as a separate step
- Add a manual approval step before production deploy
- Pin all action versions

Output only the complete YAML, no explanations.
"""

        try:
            response = self.llm.chat(
                messages=[LLMMessage(role="user", content=prompt)],
                system_prompt=CICD_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=4096,
            )

            text = response.content.strip()
            if response.provider == "stub" or "[StubProvider]" in text or not text:
                return None

            # Strip markdown fences
            text = re.sub(r'^```yaml\n?', '', text, flags=re.MULTILINE)
            text = re.sub(r'\n?```$', '', text, flags=re.MULTILINE)
            text = text.strip()

            # Basic validation
            if "on:" not in text and "jobs:" not in text:
                return None

            return text

        except Exception:
            return None

    # ------------------------------------------------------------------
    # Template fallbacks
    # ------------------------------------------------------------------
    def _header_ci(self, branch: str) -> str:
        return textwrap.dedent(f"""\
            name: CI

            on:
              push:
                branches: ["{branch}"]
              pull_request:
                branches: ["{branch}"]

            concurrency:
              group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
              cancel-in-progress: true
        """)

    def _job_for_language(self, lang: str, stack: Dict[str, Any]) -> str:
        if lang == "python":
            return textwrap.dedent("""\
                jobs:
                  python-ci:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
                      - uses: actions/setup-python@v5
                        with:
                          python-version: "3.12"
                          cache: pip
                      - run: pip install -r requirements.txt
                      - run: pip install pylint mypy bandit
                      - run: pylint **/*.py --exit-zero
                      - run: mypy . --ignore-missing-imports --exit-zero
                      - run: pytest --tb=short
                      - run: bandit -r . -ll --exit-zero
            """)
        elif lang in ("typescript", "javascript"):
            return textwrap.dedent("""\
                  node-ci:
                    runs-on: ubuntu-latest
                    defaults:
                      run:
                        working-directory: apps/web
                    steps:
                      - uses: actions/checkout@v4
                      - uses: actions/setup-node@v4
                        with:
                          node-version: "20"
                          cache: npm
                          cache-dependency-path: apps/web/package-lock.json
                      - run: npm ci
                      - run: npm run lint --if-present
                      - run: npm run build
                      - run: npm test --if-present
                      - run: npm audit --audit-level=high
            """)
        elif lang == "go":
            return textwrap.dedent("""\
                  go-ci:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
                      - uses: actions/setup-go@v5
                        with:
                          go-version: "1.22"
                          cache: true
                      - run: go vet ./...
                      - run: go test ./... -race -coverprofile=coverage.out
                      - run: go build ./...
            """)
        elif lang == "rust":
            return textwrap.dedent("""\
                  rust-ci:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
                      - uses: dtolnay/rust-toolchain@stable
                        with:
                          components: clippy, rustfmt
                      - uses: Swatinem/rust-cache@v2
                      - run: cargo fmt --check
                      - run: cargo clippy -- -D warnings
                      - run: cargo test
                      - run: cargo audit --ignore RUSTSEC-0000-0000
            """)
        elif lang == "java":
            return textwrap.dedent("""\
                  java-ci:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
                      - uses: actions/setup-java@v4
                        with:
                          java-version: "17"
                          distribution: temurin
                          cache: maven
                      - run: mvn test
                      - run: mvn package -DskipTests
            """)
        return ""

    def _security_job(self) -> str:
        return textwrap.dedent("""\
              security-scan:
                runs-on: ubuntu-latest
                needs: []
                steps:
                  - uses: actions/checkout@v4
                  - name: Run Trivy vulnerability scanner
                    uses: aquasecurity/trivy-action@master
                    with:
                      scan-type: fs
                      scan-ref: .
                      severity: CRITICAL,HIGH
                      exit-code: 1
        """)

    def _template_cd(self, deploy_target: str, stack: Dict[str, Any]) -> str:
        return textwrap.dedent(f"""\
            name: CD

            on:
              push:
                branches: ["main"]
              release:
                types: [published]

            concurrency:
              group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
              cancel-in-progress: false

            env:
              REGISTRY: ghcr.io
              IMAGE_NAME: ${{{{ github.repository }}}}

            jobs:
              build-and-push:
                runs-on: ubuntu-latest
                permissions:
                  contents: read
                  packages: write
                steps:
                  - uses: actions/checkout@v4

                  - name: Log in to GitHub Container Registry
                    uses: docker/login-action@v3
                    with:
                      registry: ${{{{ env.REGISTRY }}}}
                      username: ${{{{ github.actor }}}}
                      password: ${{{{ secrets.GITHUB_TOKEN }}}}

                  - name: Extract Docker metadata
                    id: meta
                    uses: docker/metadata-action@v5
                    with:
                      images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
                      tags: |
                        type=ref,event=branch
                        type=semver,pattern={{{{version}}}}
                        type=sha,prefix=sha-

                  - name: Build and push Docker image
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      push: true
                      tags: ${{{{ steps.meta.outputs.tags }}}}
                      labels: ${{{{ steps.meta.outputs.labels }}}}
                      cache-from: type=gha
                      cache-to: type=gha,mode=max

              deploy:
                needs: build-and-push
                runs-on: ubuntu-latest
                environment:
                  name: production
                  url: https://your-production-url.example.com
                steps:
                  - name: Deploy to production
                    run: echo "Add your deployment steps here (e.g., kubectl, docker-compose pull, etc.)"
        """)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _read_safe(self, path: str, max_bytes: int = 65536) -> str:
        """Reads a file safely within root directory."""
        try:
            real_path = os.path.realpath(path)
            if not real_path.startswith(self.root_dir):
                return ""
            with open(real_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_bytes)
        except Exception:
            return ""
