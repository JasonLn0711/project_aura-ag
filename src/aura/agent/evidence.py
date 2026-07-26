from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from aura.agent.contracts import AuraEvidenceContext
from aura.agent.policy import path_has_sensitive_component
from aura.claim_review import load_claims


FULL_TRANSCRIPT_CLAIM_ID = "__full_transcript__"


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read AURA evidence artifact: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"AURA evidence artifact must be an object: {path.name}")
    return value


@dataclass(frozen=True)
class EvidenceSelection:
    meeting_id: str
    claim_id: str
    text: str
    review_status: str
    support_status: str
    source_segment_ids: tuple[str, ...]
    snippets: tuple[dict[str, Any], ...]
    stale: bool
    eligible: bool
    reasons: tuple[str, ...]
    source_digest: str
    transcript_hash: str = ""
    transcript_revision: int | None = None
    summary_hash: str | None = None
    evidence_created_at: str = ""
    source_spans: tuple[tuple[int, int], ...] = ()
    source_kind: str = "action_item"
    transfer_scope: str = "selected_segments"
    redaction_report_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_context(self) -> AuraEvidenceContext:
        if not self.eligible:
            raise ValueError("Only eligible confirmed evidence can create a context.")
        return AuraEvidenceContext(
            context_id=self.source_digest,
            meeting_id=self.meeting_id,
            source_kind=self.source_kind,
            source_item_id=self.claim_id,
            source_text=self.text,
            review_status=self.review_status,
            support_status=self.support_status,
            source_segment_ids=self.source_segment_ids,
            source_spans=self.source_spans,
            transcript_hash=self.transcript_hash,
            transcript_revision=self.transcript_revision,
            summary_hash=self.summary_hash,
            evidence_created_at=self.evidence_created_at,
            transfer_scope=self.transfer_scope,
            redaction_report_id=self.redaction_report_id,
        )


class AuraEvidenceAdapter:
    """Read-only view over canonical AURA session artifacts."""

    def __init__(self, session_dir: str | Path):
        self.session_dir = Path(session_dir).expanduser().resolve()
        if path_has_sensitive_component(self.session_dir):
            raise ValueError("AURA evidence cannot be read from a sensitive path.")
        if not self.session_dir.is_dir():
            raise ValueError("AURA session directory is unavailable.")

    def list_action_candidates(self) -> tuple[dict[str, object], ...]:
        actions: tuple[dict[str, object], ...] = tuple(
            {
                "claim_id": str(claim.get("claim_id") or ""),
                "text": str(claim.get("text") or ""),
                "review_status": str(claim.get("review_status") or "unreviewed"),
                "support_status": str(claim.get("support_status") or "unknown"),
            }
            for claim in load_claims(self.session_dir)
            if claim.get("field") == "action_items" and claim.get("claim_id")
        )
        session = _read_object(self.session_dir / "session.json")
        segments_payload = _read_object(self.session_dir / "segments.json")
        segments = segments_payload.get("segments", [])
        transcript_ready = (
            bool(session.get("meeting_id"))
            and bool(session.get("transcript_sha256"))
            and isinstance(segments, list)
            and any(
                isinstance(item, dict) and str(item.get("text") or "").strip()
                for item in segments
            )
        )
        full_transcript: dict[str, object] = {
            "claim_id": FULL_TRANSCRIPT_CLAIM_ID,
            "text": "完整逐字稿（文件級傳送範圍）",
            "review_status": "document_scope",
            "support_status": "source_transcript",
            "eligible": transcript_ready,
            "requires_document_confirmation": True,
            "meeting_title": str(
                session.get("title") or session.get("meeting_id") or ""
            ),
        }
        return actions + (full_transcript,)

    def local_audio_span(
        self,
        *,
        start_ms: int,
        end_ms: int,
        track: str = "mixed",
    ) -> dict[str, Any]:
        if start_ms < 0 or end_ms <= start_ms:
            raise ValueError("Audio span must satisfy 0 <= start_ms < end_ms.")
        session = _read_object(self.session_dir / "session.json")
        tracks = session.get("audio_tracks")
        if not isinstance(tracks, dict) or track not in tracks:
            raise KeyError(track)
        value = tracks[track]
        path_value = value.get("path") if isinstance(value, dict) else value
        path = Path(str(path_value)).expanduser()
        if not path.is_absolute():
            path = self.session_dir / path
        path = path.resolve(strict=True)
        if path != self.session_dir and not path.is_relative_to(self.session_dir):
            raise ValueError("The selected audio track is outside the AURA session.")
        if not path.is_file():
            raise ValueError("The selected local audio track is unavailable.")
        return {
            "path": path,
            "start_ms": int(start_ms),
            "end_ms": int(end_ms),
        }

    def select_confirmed_action(self, claim_id: str) -> EvidenceSelection:
        session = _read_object(self.session_dir / "session.json")
        summary = _read_object(self.session_dir / "summary.json")
        segments_payload = _read_object(self.session_dir / "segments.json")
        segments = segments_payload.get("segments", [])
        if not isinstance(segments, list):
            raise ValueError("segments.json must contain a segments list.")
        segment_by_id = {
            str(item.get("segment_id")): item
            for item in segments
            if isinstance(item, dict) and item.get("segment_id")
        }
        claim = next(
            (
                item
                for item in load_claims(self.session_dir)
                if str(item.get("claim_id") or "") == claim_id
                and item.get("field") == "action_items"
            ),
            None,
        )
        if claim is None:
            raise KeyError(claim_id)

        meeting_id = str(session.get("meeting_id") or "")
        transcript_hash = str(session.get("transcript_sha256") or "")
        summary_transcript_hash = str(summary.get("transcript_sha256") or "")
        summary_file_hash = hashlib.sha256(
            (self.session_dir / "summary.json").read_bytes()
        ).hexdigest()
        source_ids = tuple(str(value) for value in claim.get("source_segment_ids", []))
        freshness_reasons: list[str] = []
        if not meeting_id or str(summary.get("meeting_id") or "") != meeting_id:
            freshness_reasons.append("meeting_id_mismatch")
        if not transcript_hash or transcript_hash != summary_transcript_hash:
            freshness_reasons.append("transcript_hash_mismatch")
        if str(session.get("summary_status") or "").lower() == "invalidated":
            freshness_reasons.append("summary_invalidated")
        unresolved = [segment_id for segment_id in source_ids if segment_id not in segment_by_id]
        if unresolved:
            freshness_reasons.append("source_segments_missing")

        eligibility_reasons = list(freshness_reasons)
        review_status = str(claim.get("review_status") or "unreviewed")
        support_status = str(claim.get("support_status") or "unknown")
        if review_status != "confirmed":
            eligibility_reasons.append("review_not_confirmed")
        if support_status == "unsupported":
            eligibility_reasons.append("support_status_unsupported")
        if not source_ids:
            eligibility_reasons.append("source_segments_required")

        snippets = tuple(
            {
                "segment_id": segment_id,
                "start_ms": int(segment_by_id[segment_id].get("start_ms") or 0),
                "end_ms": int(segment_by_id[segment_id].get("end_ms") or 0),
                "speaker": str(segment_by_id[segment_id].get("speaker") or ""),
                "text": str(segment_by_id[segment_id].get("text") or ""),
            }
            for segment_id in source_ids
            if segment_id in segment_by_id
        )
        digest_input = json.dumps(
            {
                "meeting_id": meeting_id,
                "claim_id": claim_id,
                "transcript_sha256": transcript_hash,
                "source_segment_ids": source_ids,
                "snippets": snippets,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return EvidenceSelection(
            meeting_id=meeting_id,
            claim_id=claim_id,
            text=str(claim.get("text") or ""),
            review_status=review_status,
            support_status=support_status,
            source_segment_ids=source_ids,
            snippets=snippets,
            stale=bool(freshness_reasons),
            eligible=not eligibility_reasons,
            reasons=tuple(dict.fromkeys(eligibility_reasons)),
            source_digest=hashlib.sha256(digest_input).hexdigest(),
            transcript_hash=transcript_hash,
            transcript_revision=(
                int(session["transcript_revision"])
                if session.get("transcript_revision") is not None
                else None
            ),
            summary_hash=summary_file_hash,
            evidence_created_at=str(
                claim.get("created_at")
                or summary.get("created_at")
                or session.get("created_at")
                or ""
            ),
            source_spans=tuple(
                (
                    int(snippet["start_ms"]),
                    int(snippet["end_ms"]),
                )
                for snippet in snippets
            ),
        )

    def select_full_transcript(self) -> EvidenceSelection:
        session = _read_object(self.session_dir / "session.json")
        segments_payload = _read_object(self.session_dir / "segments.json")
        segments = segments_payload.get("segments", [])
        if not isinstance(segments, list):
            raise ValueError("segments.json must contain a segments list.")
        snippets = tuple(
            {
                "segment_id": str(item.get("segment_id") or f"segment-{index}"),
                "start_ms": int(item.get("start_ms") or 0),
                "end_ms": int(item.get("end_ms") or 0),
                "speaker": str(item.get("speaker") or ""),
                "text": str(item.get("text") or ""),
            }
            for index, item in enumerate(segments, start=1)
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        )
        meeting_id = str(session.get("meeting_id") or "")
        transcript_hash = str(session.get("transcript_sha256") or "")
        reasons = []
        if not meeting_id:
            reasons.append("meeting_id_required")
        if not transcript_hash:
            reasons.append("transcript_hash_required")
        if not snippets:
            reasons.append("transcript_segments_required")
        transcript = "\n".join(str(item["text"]) for item in snippets)
        digest = hashlib.sha256(
            json.dumps(
                {
                    "meeting_id": meeting_id,
                    "transcript_sha256": transcript_hash,
                    "snippets": snippets,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return EvidenceSelection(
            meeting_id=meeting_id,
            claim_id=FULL_TRANSCRIPT_CLAIM_ID,
            text=transcript,
            review_status="document_scope",
            support_status="source_transcript",
            source_segment_ids=tuple(
                str(item["segment_id"]) for item in snippets
            ),
            snippets=snippets,
            stale=False,
            eligible=not reasons,
            reasons=tuple(reasons),
            source_digest=digest,
            transcript_hash=transcript_hash,
            transcript_revision=(
                int(session["transcript_revision"])
                if session.get("transcript_revision") is not None
                else None
            ),
            evidence_created_at=str(session.get("created_at") or ""),
            source_spans=tuple(
                (int(item["start_ms"]), int(item["end_ms"]))
                for item in snippets
            ),
            source_kind="full_transcript",
            transfer_scope="full_transcript",
        )
