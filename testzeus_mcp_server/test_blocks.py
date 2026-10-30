"""Test Blocks helpers for the MCP server.

A Test Blocks test (``executor == "test_blocks"``) is an ordered list of steps.
Steps cannot be written through the tests collection: every change goes through
``client.test_blocks`` (SDK >= 0.0.28). A test only becomes ``ready`` after
verify then save.
"""

from typing import Any

SDK_HINT = "Test Blocks tools need testzeus-sdk>=0.0.28. Upgrade with: pip install -U testzeus-sdk"
STEP_TYPES = ("browser", "mobile", "backend", "soql", "apex", "http")
RUNNABLE_VERIFICATION = ("verified", "inferred", "transcribed")


def manager(client: Any) -> Any:
    if client is None:
        raise ValueError("Not authenticated")
    tb = getattr(client, "test_blocks", None)
    if tb is None:
        raise ValueError(SDK_HINT)
    return tb


def is_test_blocks_test(test: Any) -> bool:
    if test is None:
        return False
    if getattr(test, "is_test_blocks", None) is True:
        return True
    data = getattr(test, "data", None) or {}
    executor = str(getattr(test, "executor", None) or data.get("executor") or "").strip().lower()
    mode = (
        str(getattr(test, "authoring_mode", None) or data.get("authoring_mode") or "")
        .strip()
        .lower()
    )
    return executor in ("test_blocks", "test_builder") or mode == "box_graph"


def builder_status(test: Any) -> str:
    data = getattr(test, "data", None) or {}
    return str(getattr(test, "builder_status", None) or data.get("builder_status") or "")


def not_ready_run_error(tests: list[Any]) -> str | None:
    """Error when run_test / create_test_run_group would queue an unverified Test Blocks test."""
    blocked = [
        test for test in tests if is_test_blocks_test(test) and builder_status(test) != "ready"
    ]
    if not blocked:
        return None
    ids = ", ".join(str(getattr(test, "id", "?")) for test in blocked)
    return (
        f"Error: Test Blocks test(s) {ids} are not ready to run. "
        "Verify every step, then save (verify_test_blocks + save_test_blocks), "
        "or use live_run_test_blocks which enforces readiness."
    )


def test_identity(test: Any) -> dict[str, Any]:
    return {
        "id": getattr(test, "id", None),
        "name": getattr(test, "name", None),
        "executor": getattr(test, "executor", None),
        "origin": getattr(test, "origin", None),
        "authoring_mode": getattr(test, "authoring_mode", None),
        "builder_status": getattr(test, "builder_status", None),
        "testing_type": getattr(test, "testing_type", None),
        "execution_mode": getattr(test, "execution_mode", None),
        "test_feature": getattr(test, "test_feature", None),
        "environment": getattr(test, "environment", None),
        "test_data": getattr(test, "test_data", None),
        "tags": getattr(test, "tags", None),
    }


def summarize_builder(payload: dict[str, Any]) -> dict[str, Any]:
    """Compact mutation response: ids, status, ordered steps, validation errors."""
    blocks = payload.get("blocks") or []
    steps = []
    for block in blocks:
        if str(block.get("kind") or "intent") not in ("", "intent"):
            continue
        steps.append(
            {
                "id": block.get("id"),
                "label": block.get("label"),
                "step_type": block.get("step_type") or "browser",
                "verification": (block.get("implementation") or {}).get("verificationStatus")
                or "unverified",
                "assert": bool((block.get("authoring") or {}).get("isAssert")),
            }
        )
    validation = payload.get("validation") or {}
    return {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "builder_status": payload.get("builder_status"),
        "block_graph_hash": payload.get("block_graph_hash"),
        "environment": payload.get("environment"),
        "environment_url_key": payload.get("environment_url_key"),
        "steps": steps,
        "errors": [
            f"{issue.get('code')}: {issue.get('message')}"
            for issue in validation.get("errors") or []
        ],
    }


def verify_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = summarize_builder(payload)
    failed = [
        step for step in summary["steps"] if step["verification"] not in RUNNABLE_VERIFICATION
    ]
    summary["status"] = "failed" if failed else "verified"
    summary["failed_steps"] = failed
    return summary


def validate_step_type(step_type: str | None) -> str | None:
    if step_type is None:
        return None
    if step_type not in STEP_TYPES:
        raise ValueError(
            f"Invalid step_type '{step_type}'. Must be one of: {', '.join(STEP_TYPES)}"
        )
    return step_type
