import pytest
import os
import shutil
import tempfile
from memory.manager import ProjectMemoryManager
from memory.models import (
    ArchitectureRecord, DecisionRecord, TaskHistoryRecord,
    DeveloperPreferenceRecord, DecisionStatus, TaskStatus, PreferenceCategory
)

@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

def test_memory_initialization_and_seeding(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    overview = manager.get_overview()
    
    assert overview.total_architecture_components >= 3
    assert overview.total_decisions >= 2
    assert overview.total_tasks_recorded >= 1
    assert overview.total_preferences >= 3

def test_architecture_memory(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    rec = ArchitectureRecord(
        id="arch-test-module",
        component_name="Test Component",
        technology_stack=["Python", "Pytest"],
        entrypoints=["tests/test_memory.py"],
        conventions=["Mocking", "Fixtures"],
        description="Testing component memory operations.",
        dependencies=[]
    )
    manager.architecture.add_or_update(rec)
    manager.save_to_storage()

    # Re-load from storage to check persistence
    manager2 = ProjectMemoryManager(root_dir=temp_dir)
    found = manager2.architecture.get_by_id("arch-test-module")
    assert found is not None
    assert found.component_name == "Test Component"

def test_decision_memory(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    dec = DecisionRecord(
        id="adr-test-001",
        title="ADR Test: Use JSON for Memory Storage",
        status=DecisionStatus.ACCEPTED,
        context="We need local persistent memory without complex DB servers.",
        decision="Store memory as JSON files in .memory/store.json",
        consequences=["Zero external dependencies", "Human readable"]
    )
    manager.decisions.add_decision(dec)
    manager.save_to_storage()

    manager2 = ProjectMemoryManager(root_dir=temp_dir)
    results = manager2.decisions.search_decisions("JSON")
    matching = [r for r in results if r.id == "adr-test-001"]
    assert len(matching) == 1
    assert matching[0].title == "ADR Test: Use JSON for Memory Storage"

def test_task_memory(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    task = TaskHistoryRecord(
        id="task-test-101",
        task_title="Implement Project Memory",
        task_request="Do Phase 13 Project Memory",
        agent_name="Coder Agent",
        status=TaskStatus.COMPLETED,
        files_changed=["memory/manager.py"],
        fix_summary="Built memory stores and FastAPI endpoints."
    )
    manager.tasks.record_task(task)
    manager.save_to_storage()

    manager2 = ProjectMemoryManager(root_dir=temp_dir)
    tasks = manager2.tasks.search_tasks("Phase 13")
    assert len(tasks) >= 1
    assert tasks[0].id == "task-test-101"

def test_preference_memory(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    pref = DeveloperPreferenceRecord(
        id="pref-test-tab",
        category=PreferenceCategory.CODING_STYLE,
        key="Tab Width",
        value="2 spaces",
        description="Standard tab width for TypeScript/JSON"
    )
    manager.preferences.add_or_update_preference(pref)
    manager.save_to_storage()

    manager2 = ProjectMemoryManager(root_dir=temp_dir)
    prefs = manager2.preferences.search_preferences("Tab Width")
    assert len(prefs) >= 1
    assert prefs[0].value == "2 spaces"

def test_llm_context_synthesis(temp_dir):
    manager = ProjectMemoryManager(root_dir=temp_dir)
    context_str = manager.get_llm_context("Fix bug")
    assert "Project Memory Context" in context_str
    assert "FastAPI" in context_str or "Python" in context_str
