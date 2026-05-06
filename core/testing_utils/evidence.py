from constants.evidence import (
    EVIDENCE_MODE_FAILURE_ONLY,
    EVIDENCE_MODE_FULL,
    EVIDENCE_MODE_SCREENSHOT_ONLY,
)


def should_capture_trace(evidence_mode: str, collect_all_evidence: bool) -> bool:
    return collect_all_evidence or evidence_mode in {
        EVIDENCE_MODE_FULL,
        EVIDENCE_MODE_FAILURE_ONLY,
    }


def should_record_video(evidence_mode: str, collect_all_evidence: bool) -> bool:
    return collect_all_evidence or evidence_mode in {
        EVIDENCE_MODE_FULL,
        EVIDENCE_MODE_FAILURE_ONLY,
    }


def should_attach_test_evidence(evidence_mode: str, collect_all_evidence: bool, test_failed: bool) -> bool:
    if collect_all_evidence or evidence_mode == EVIDENCE_MODE_FULL:
        return True
    if evidence_mode in {EVIDENCE_MODE_FAILURE_ONLY, EVIDENCE_MODE_SCREENSHOT_ONLY}:
        return test_failed
    return False
