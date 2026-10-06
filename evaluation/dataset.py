from typing import List, Optional
from evaluation.models import SWEBenchmarkTask, BenchmarkTaskCategory, DifficultyLevel


SWE_BENCHMARK_20_TASKS: List[SWEBenchmarkTask] = [
    SWEBenchmarkTask(
        task_id="swe-01",
        title="Fix checkout race condition when coupon expired during card hold",
        description="Prevent applying discount if coupon expires between checkout initiation and stripe payment authorization.",
        category=BenchmarkTaskCategory.BUG_FIX,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/routes/checkout.py", "services/coupon.py"],
        expected_tools=["rag.query", "ast.search_symbols", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Test test_expired_coupon_during_hold raises 400 error and refunds transaction."
    ),
    SWEBenchmarkTask(
        task_id="swe-02",
        title="Implement JWT refresh token rotation with blacklist revocation",
        description="Issue rotating single-use refresh tokens stored in hashed Redis set; invalidate token family on reuse detection.",
        category=BenchmarkTaskCategory.SECURITY,
        difficulty=DifficultyLevel.HARD,
        target_files=["apps/api/auth/tokens.py", "services/redis_session.py"],
        expected_tools=["docs.search_best_practices", "fs.read_file", "coder.generate_diff", "security.scan_ast", "sandbox.run_test"],
        test_criteria="Test test_refresh_token_reuse_invalidates_all_sessions passes."
    ),
    SWEBenchmarkTask(
        task_id="swe-03",
        title="Resolve SQL injection vulnerability in search filter query builder",
        description="Convert string concatenation in search query builder to parameterized SQLAlchemy binds.",
        category=BenchmarkTaskCategory.SECURITY,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["services/search_builder.py", "apps/api/routes/search.py"],
        expected_tools=["security.check_secrets", "security.scan_ast", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Test test_sql_injection_payloads_safely_escaped passes 0 findings."
    ),
    SWEBenchmarkTask(
        task_id="swe-04",
        title="Optimize N+1 query in order history pagination endpoint",
        description="Use joinedload / selectinload for customer order items relationship to drop database roundtrips from O(N) to O(1).",
        category=BenchmarkTaskCategory.PERFORMANCE,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/routes/orders.py", "models/order.py"],
        expected_tools=["ast.search_symbols", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Query counter asserts <= 2 SQL statements executed for 50 orders."
    ),
    SWEBenchmarkTask(
        task_id="swe-05",
        title="Refactor legacy monolithic auth service to modular RBAC middleware",
        description="Extract permission checks into reusable FastAPI Depends role guard supporting ADMIN, DEVELOPER, and VIEWER.",
        category=BenchmarkTaskCategory.REFACTOR,
        difficulty=DifficultyLevel.HARD,
        target_files=["apps/api/middleware/rbac.py", "apps/api/routes/admin.py"],
        expected_tools=["rag.query", "fs.read_file", "coder.generate_diff", "reviewer.analyze_diff", "sandbox.run_test"],
        test_criteria="All protected endpoints return 403 Forbidden for unauthorized roles."
    ),
    SWEBenchmarkTask(
        task_id="swe-06",
        title="Add idempotency key header support for payment intent creation",
        description="Check and store Idempotency-Key header with 24-hour TTL in cache to deduplicate duplicate retry requests.",
        category=BenchmarkTaskCategory.API_DESIGN,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/routes/payments.py", "services/idempotency.py"],
        expected_tools=["fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Concurrent identical requests return original cached response with 200 OK."
    ),
    SWEBenchmarkTask(
        task_id="swe-07",
        title="Handle unhandled edge case in websocket disconnection heartbeat timeout",
        description="Catch DisconnectError and cleanly prune inactive client socket handles from connection manager pool.",
        category=BenchmarkTaskCategory.BUG_FIX,
        difficulty=DifficultyLevel.EASY,
        target_files=["apps/api/ws/connection_manager.py"],
        expected_tools=["fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Memory leak test asserts active_connections count reaches 0 on client drop."
    ),
    SWEBenchmarkTask(
        task_id="swe-08",
        title="Implement distributed rate limiter using sliding window Redis counter",
        description="Limit API consumers to 100 requests per minute per IP address with sliding window timestamp zset.",
        category=BenchmarkTaskCategory.FEATURE,
        difficulty=DifficultyLevel.HARD,
        target_files=["apps/api/middleware/rate_limit.py", "services/redis_client.py"],
        expected_tools=["docs.search_best_practices", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Request 101 within 60s returns 429 Too Many Requests with Retry-After header."
    ),
    SWEBenchmarkTask(
        task_id="swe-09",
        title="Sanitize unsanitized HTML input in user profile markdown renderer (XSS)",
        description="Integrate bleach / DOMPurify sanitization stripping <script>, <iframe>, and onerror event handlers.",
        category=BenchmarkTaskCategory.SECURITY,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["services/markdown_sanitizer.py", "apps/api/routes/profile.py"],
        expected_tools=["security.scan_ast", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Test test_xss_vectors_stripped strips javascript: pseudoprotocol."
    ),
    SWEBenchmarkTask(
        task_id="swe-10",
        title="Migrate synchronous file upload to asynchronous signed S3 upload URLs",
        description="Generate presigned S3 PUT URLs with 15-minute expiration instead of buffering multipart bodies on API server.",
        category=BenchmarkTaskCategory.FEATURE,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/routes/uploads.py", "services/s3_storage.py"],
        expected_tools=["rag.query", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="API returns valid signed URL without reading file payload into server RAM."
    ),
    SWEBenchmarkTask(
        task_id="swe-11",
        title="Fix deadlock during concurrent inventory decrement under high traffic",
        description="Acquire row-level SELECT FOR UPDATE in deterministic ascending SKU order to prevent cyclic locks.",
        category=BenchmarkTaskCategory.BUG_FIX,
        difficulty=DifficultyLevel.HARD,
        target_files=["services/inventory.py", "apps/api/routes/orders.py"],
        expected_tools=["ast.search_symbols", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Concurrent threads test executes 20 concurrent checkouts without DeadlockDetectedError."
    ),
    SWEBenchmarkTask(
        task_id="swe-12",
        title="Implement structured audit logging for administrative mutations",
        description="Record actor_id, IP, action, resource_id, and timestamp in structured JSON format for SOC2 compliance.",
        category=BenchmarkTaskCategory.FEATURE,
        difficulty=DifficultyLevel.EASY,
        target_files=["apps/api/middleware/audit.py", "services/logger.py"],
        expected_tools=["fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Audit log handler records structured log entries with valid schema."
    ),
    SWEBenchmarkTask(
        task_id="swe-13",
        title="Prevent timing attacks in password hash verification with constant-time compare",
        description="Replace standard string equality == with hmac.compare_digest in authentication token validator.",
        category=BenchmarkTaskCategory.SECURITY,
        difficulty=DifficultyLevel.EASY,
        target_files=["apps/api/auth/security.py"],
        expected_tools=["security.scan_ast", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Timing analysis confirms uniform execution delta across character mismatches."
    ),
    SWEBenchmarkTask(
        task_id="swe-14",
        title="Implement cursor-based pagination for high-volume notification feed",
        description="Switch offset-based limit/offset to opaque base64 timestamp cursors to eliminate pagination drift.",
        category=BenchmarkTaskCategory.PERFORMANCE,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/routes/notifications.py"],
        expected_tools=["fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="New notification inserts do not cause duplicate items on page scroll."
    ),
    SWEBenchmarkTask(
        task_id="swe-15",
        title="Fix memory leak in background worker task queue event listener",
        description="Properly unregister event emitter listeners in asyncio task teardown handler.",
        category=BenchmarkTaskCategory.BUG_FIX,
        difficulty=DifficultyLevel.HARD,
        target_files=["services/worker_queue.py", "services/events.py"],
        expected_tools=["rag.query", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Heap profile test asserts no detached listeners remain after 1,000 tasks."
    ),
    SWEBenchmarkTask(
        task_id="swe-16",
        title="Add OpenAPI schema validation and automated request body parsing",
        description="Configure Pydantic v2 model strict mode and custom 422 error handlers with field-level error messages.",
        category=BenchmarkTaskCategory.API_DESIGN,
        difficulty=DifficultyLevel.EASY,
        target_files=["apps/api/schemas/common.py", "apps/api/main.py"],
        expected_tools=["fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Invalid schema payloads return uniform 422 with validation detail array."
    ),
    SWEBenchmarkTask(
        task_id="swe-17",
        title="Refactor global state singleton into dependency injection container",
        description="Replace global database session singleton with scoped FastAPI dependency injection providers.",
        category=BenchmarkTaskCategory.REFACTOR,
        difficulty=DifficultyLevel.HARD,
        target_files=["core/dependencies.py", "apps/api/main.py"],
        expected_tools=["ast.search_symbols", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Mock database sessions can be injected during testing without modifying production globals."
    ),
    SWEBenchmarkTask(
        task_id="swe-18",
        title="Implement circuit breaker pattern for external payment gateway outages",
        description="Trip circuit breaker to OPEN state after 5 consecutive timeouts within 30 seconds; serve fallback queue.",
        category=BenchmarkTaskCategory.PERFORMANCE,
        difficulty=DifficultyLevel.HARD,
        target_files=["services/circuit_breaker.py", "services/payment_gateway.py"],
        expected_tools=["docs.search_best_practices", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Subsequent requests fail-fast within 1ms during circuit OPEN state."
    ),
    SWEBenchmarkTask(
        task_id="swe-19",
        title="Fix CSRF vulnerability on cross-origin session termination endpoint",
        description="Enforce SameSite=Strict on session cookies and require X-CSRF-Token header on POST /logout.",
        category=BenchmarkTaskCategory.SECURITY,
        difficulty=DifficultyLevel.MEDIUM,
        target_files=["apps/api/auth/csrf.py", "apps/api/routes/auth.py"],
        expected_tools=["security.scan_ast", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Cross-origin unauthorized POST request rejected with 403 Invalid CSRF Token."
    ),
    SWEBenchmarkTask(
        task_id="swe-20",
        title="Implement zero-downtime database migration for user schema split",
        description="Execute expand-and-contract pattern with dual-writing to migrate user metadata to separate profile table.",
        category=BenchmarkTaskCategory.REFACTOR,
        difficulty=DifficultyLevel.HARD,
        target_files=["migrations/versions/split_user.py", "services/user_service.py"],
        expected_tools=["rag.query", "fs.read_file", "coder.generate_diff", "sandbox.run_test"],
        test_criteria="Reads and writes succeed seamlessly during migration phase."
    ),
]


def get_all_benchmark_tasks() -> List[SWEBenchmarkTask]:
    return SWE_BENCHMARK_20_TASKS


def get_benchmark_task_by_id(task_id: str) -> Optional[SWEBenchmarkTask]:
    for t in SWE_BENCHMARK_20_TASKS:
        if t.task_id == task_id:
            return t
    return None
