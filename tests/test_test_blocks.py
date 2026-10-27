"""Unit tests for Test Blocks helpers and the MCP tool surface."""

from types import SimpleNamespace

from testzeus_mcp_server.test_blocks import (
    SDK_HINT,
    builder_status,
    is_test_blocks_test,
    manager,
    not_ready_run_error,
    summarize_builder,
    validate_step_type,
    verify_summary,
)


class TestHelpers:
    def test_is_test_blocks_test(self):
        assert is_test_blocks_test(SimpleNamespace(is_test_blocks=True))
        assert is_test_blocks_test(SimpleNamespace(executor="test_blocks", data={}))
        assert is_test_blocks_test(
            SimpleNamespace(executor="hercules", authoring_mode="box_graph", data={})
        )
        assert not is_test_blocks_test(
            SimpleNamespace(executor="hercules", authoring_mode="legacy", data={})
        )
        assert not is_test_blocks_test(None)

    def test_not_ready_run_error(self):
        ready = SimpleNamespace(
            id="readyid12345678", is_test_blocks=True, builder_status="ready", data={}
        )
        draft = SimpleNamespace(
            id="draftid12345678", is_test_blocks=True, builder_status="authoring", data={}
        )
        gherkin = SimpleNamespace(
            id="gherkin1234567", is_test_blocks=False, executor="hercules", data={}
        )
        assert not_ready_run_error([ready, gherkin]) is None
        message = not_ready_run_error([draft, gherkin])
        assert message.startswith("Error:")
        assert "draftid12345678" in message
        assert "verify_test_blocks" in message

    def test_builder_status_falls_back_to_data(self):
        assert builder_status(SimpleNamespace(data={"builder_status": "invalid"})) == "invalid"

    def test_manager_requires_sdk_surface(self):
        try:
            manager(None)
            raise AssertionError("expected error")
        except ValueError as exc:
            assert "authenticated" in str(exc)
        try:
            manager(SimpleNamespace())
            raise AssertionError("expected error")
        except ValueError as exc:
            assert SDK_HINT in str(exc)
        tb = object()
        assert manager(SimpleNamespace(test_blocks=tb)) is tb

    def test_validate_step_type(self):
        assert validate_step_type(None) is None
        assert validate_step_type("backend") == "backend"
        assert validate_step_type("mobile") == "mobile"
        try:
            validate_step_type("gherkin")
            raise AssertionError("expected error")
        except ValueError as exc:
            assert "step_type" in str(exc)

    def test_summarize_and_verify(self):
        payload = {
            "id": "t1",
            "name": "n",
            "builder_status": "authoring",
            "block_graph_hash": "h",
            "blocks": [
                {
                    "id": "a",
                    "kind": "intent",
                    "label": "one",
                    "step_type": "backend",
                    "implementation": {"verificationStatus": "verified"},
                    "authoring": {},
                },
                {
                    "id": "b",
                    "kind": "intent",
                    "label": "two",
                    "implementation": {"verificationStatus": "failed"},
                    "authoring": {"isAssert": True},
                },
            ],
            "validation": {"errors": [{"code": "UNVERIFIED", "message": "fix"}]},
        }
        summary = summarize_builder(payload)
        assert summary["id"] == "t1" and len(summary["steps"]) == 2
        assert "UNVERIFIED" in summary["errors"][0]
        assert verify_summary(payload)["status"] == "failed"


class TestServerSurface:
    def test_create_test_points_at_test_blocks(self):
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
        assert "create_test_blocks instead" in content
        assert "async def create_test_blocks" in content
        assert "async def add_test_blocks_step" in content
        assert "async def verify_test_blocks" in content
        assert "async def save_test_blocks" in content
        assert "async def live_run_test_blocks" in content
        assert "async def get_test_blocks_run_status" in content
        assert "builder_status" in content
