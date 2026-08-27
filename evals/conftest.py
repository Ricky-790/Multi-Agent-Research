import asyncio
import json

import pytest

from agents_service.graph import get_research_graph


def pytest_addoption(parser):
    parser.addoption(
        "--case",
        action="store",
        default="case_1.json",
        help="Dataset case file to run evals against",
    )


def get_golden_dataset(file_name: str) -> dict:
    with open(f"evals/datasets/{file_name}", "r") as f:
        return json.loads(f.read())


@pytest.fixture(scope="session")
def case_data(request) -> dict:
    file_name = request.config.getoption("--case")
    return get_golden_dataset(file_name)


@pytest.fixture(scope="session")
def query(case_data) -> str:
    return case_data["input"]["query"]


@pytest.fixture(scope="session")
def expected(case_data) -> dict:
    return case_data.get("expected", {})


@pytest.fixture(scope="session")
def pipeline_state(case_data) -> dict:
    initial_state = case_data.get("input")
    if initial_state is None:
        raise ValueError("No input found in dataset case")
    graph = get_research_graph()
    return asyncio.run(graph.ainvoke(initial_state))


@pytest.fixture(scope="session")
def research_plan(pipeline_state):
    return pipeline_state["plan"]


@pytest.fixture(scope="session")
def task_results(pipeline_state):
    return pipeline_state["task_results"]


@pytest.fixture(scope="session")
def report_outline(pipeline_state):
    return pipeline_state["report_outline"]


@pytest.fixture(scope="session")
def final_report(pipeline_state):
    return pipeline_state["final_report"]


@pytest.fixture(scope="session")
def query(case_data) -> str:
    return case_data["input"]["query"]
