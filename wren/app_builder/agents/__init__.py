"""Wren App Builder Agents — specialized agents for the build pipeline.

Agent pipeline for complex app generation:
  ArchitectAgent → PlannerAgent → WriterAgent → ReviewerAgent → (loop)

Each agent is a self-contained async class that can run standalone
or wired into the BuildOrchestrator.
"""

from wren.app_builder.agents.architect_agent import (
    ArchitectAgent,
    ArchitectureDesign,
    ComponentSpec,
    DataModelSpec,
    RouteSpec,
)

from wren.app_builder.agents.planner_agent import (
    PlannerAgent,
    ImplementationPlan,
    FilePlan,
)

from wren.app_builder.agents.writer_agent import (
    WriterAgent,
    GenerationSession,
    GeneratedFileResult,
)

from wren.app_builder.agents.reviewer_agent import (
    ReviewerAgent,
    ReviewReport,
    ReviewIssue,
)

from wren.app_builder.agents.context_analyzer import (
    ProjectContextAnalyzer,
    DependencyGraph,
    FileNode,
    ExportInfo,
    ImportInfo,
)

__all__ = [
    # Architect
    "ArchitectAgent",
    "ArchitectureDesign",
    "ComponentSpec",
    "DataModelSpec",
    "RouteSpec",
    # Planner
    "PlannerAgent",
    "ImplementationPlan",
    "FilePlan",
    # Writer
    "WriterAgent",
    "GenerationSession",
    "GeneratedFileResult",
    # Reviewer
    "ReviewerAgent",
    "ReviewReport",
    "ReviewIssue",
    # Context Analyzer
    "ProjectContextAnalyzer",
    "DependencyGraph",
    "FileNode",
    "ExportInfo",
    "ImportInfo",
]
