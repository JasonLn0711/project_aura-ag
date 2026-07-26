from __future__ import annotations

from aura.agent.contracts import OperatingMode, WorkflowTemplate


WORKFLOW_TEMPLATES = (
    WorkflowTemplate(
        "feature",
        1,
        "從零實作功能",
        "/feature",
        OperatingMode.IMPLEMENT,
        "standard",
        ("repository", "objective", "acceptance_criteria"),
        ("repository_preflight", "worktree_grant"),
        "full",
        ("implementation_reviewable", "required_tests_recorded"),
        True,
    ),
    WorkflowTemplate(
        "bug",
        1,
        "修正 bug",
        "/bug",
        OperatingMode.IMPLEMENT,
        "standard",
        ("repository", "symptom", "reproduction_status"),
        ("repository_preflight", "worktree_grant"),
        "focused_then_full",
        ("root_cause_recorded", "regression_test_or_reason"),
        True,
    ),
    WorkflowTemplate(
        "ask",
        1,
        "詢問 Repository，不修改",
        "/ask",
        OperatingMode.ASK_EXPLAIN,
        "quick",
        ("repository", "question"),
        ("read_only",),
        "source_citations",
        ("observed_code_separated_from_inference",),
        False,
    ),
    WorkflowTemplate(
        "architecture",
        1,
        "分析架構",
        "/architecture",
        OperatingMode.REVIEW_DIAGNOSE,
        "expert",
        ("repository", "scope"),
        ("artifact_only_write",),
        "architecture_review",
        ("repository_map", "runtime_flow", "risks"),
        False,
    ),
    WorkflowTemplate(
        "test",
        1,
        "執行與修正測試",
        "/test",
        OperatingMode.IMPLEMENT,
        "standard",
        ("repository", "test_command"),
        ("repository_preflight", "worktree_grant", "recording_gate"),
        "focused_then_full",
        ("failures_classified", "repair_loops_at_most_two"),
        True,
    ),
    WorkflowTemplate(
        "security",
        1,
        "資安與 Prompt-injection Review",
        "/security",
        OperatingMode.REVIEW_DIAGNOSE,
        "expert",
        ("repository", "review_scope"),
        ("artifact_only_write", "instruction_trust"),
        "security",
        ("findings_have_evidence", "scope_is_explicit"),
        False,
    ),
    WorkflowTemplate(
        "pii",
        1,
        "PII／Red-team 報告",
        "/pii",
        OperatingMode.REVIEW_DIAGNOSE,
        "expert",
        ("repository", "data_scope"),
        ("artifact_only_write", "transfer_preview"),
        "pii_red_team",
        ("data_flow_map", "redacted_export"),
        False,
    ),
    WorkflowTemplate(
        "queue",
        1,
        "管理排程與歷史任務",
        "/queue",
        OperatingMode.ASK_EXPLAIN,
        "quick",
        ("repository",),
        ("local_catalog_only",),
        "catalog_integrity",
        ("queue_change_persisted",),
        False,
        provider_required=False,
    ),
    WorkflowTemplate(
        "package",
        1,
        "Technical Architecture Package",
        "/package",
        OperatingMode.REVIEW_DIAGNOSE,
        "expert",
        ("repository", "base_commit"),
        ("artifact_only_write", "recording_gate"),
        "architecture_package",
        ("package_validated", "missing_evidence_registered"),
        False,
    ),
    WorkflowTemplate(
        "docs",
        1,
        "README／ADR／SDD",
        "/docs",
        OperatingMode.IMPLEMENT,
        "standard",
        ("repository", "document_objective"),
        ("repository_preflight", "worktree_grant"),
        "documentation",
        ("source_backed", "links_validated"),
        True,
    ),
    WorkflowTemplate(
        "meeting",
        1,
        "從已確認會議 Action 建立任務",
        "/meeting",
        OperatingMode.IMPLEMENT,
        "standard",
        ("repository", "confirmed_aura_evidence"),
        ("evidence_freshness", "transfer_preview", "worktree_grant"),
        "evidence_backed",
        ("evidence_link_retained", "canonical_text_unchanged"),
        True,
    ),
    WorkflowTemplate(
        "publish",
        1,
        "建立 Commit／Push Branch／Open PR",
        "/publish",
        OperatingMode.PUBLISH,
        "standard",
        ("repository", "validated_run", "publication_target"),
        ("publish_preflight", "freshness", "secret_scan"),
        "publication",
        ("agent_branch_only", "publication_evidence_retained"),
        True,
    ),
)


class WorkflowRegistry:
    def __init__(self, templates: tuple[WorkflowTemplate, ...] = WORKFLOW_TEMPLATES):
        self._templates = {template.template_id: template for template in templates}
        if len(self._templates) != len(templates):
            raise ValueError("Workflow template IDs must be unique.")

    def get(self, template_id: str) -> WorkflowTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow template: {template_id}") from exc

    def resolve_command(self, command: str) -> WorkflowTemplate:
        normalized = command.strip().split(maxsplit=1)[0].lower()
        for template in self._templates.values():
            if template.command == normalized:
                return template
        raise KeyError(f"Unknown workflow command: {normalized}")

    def all(self) -> tuple[WorkflowTemplate, ...]:
        return tuple(self._templates.values())

    def suggestions(self, recent_template_ids: tuple[str, ...] = ()) -> tuple[WorkflowTemplate, ...]:
        ordered = tuple(
            template
            for template_id in recent_template_ids
            if (template := self._templates.get(template_id)) is not None
        )
        defaults = tuple(
            self._templates[template_id]
            for template_id in ("feature", "bug", "ask", "architecture")
        )
        return tuple(dict.fromkeys((*ordered, *defaults)))[:4]
