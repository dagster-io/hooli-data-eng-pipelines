"""Grade an agent's outcome against fixtures: which seeded problems it found, and how precise it was."""

import json
from pathlib import Path

import dagster as dg

from hooli_agents import settings

FIXTURES = Path(__file__).resolve().parents[3] / "eval" / "improvement_fixtures.json"


def _matches(text: str, fixture: dict) -> bool:
    low = text.lower()
    return any(all(word.lower() in low for word in group) for group in fixture["any"])


def grade(outcome: dict, fixtures: list[dict]) -> dict:
    """Match findings (filed, or practice-mode would-file) and the final note against the fixtures."""
    findings = outcome.get("filed", []) + outcome.get("would_file", [])
    texts = [f"{f.get('title', '')} {f.get('body', '')}" for f in findings]
    # In practice mode, or when tools filed nothing, the note is the only record of what was found.
    pool = texts or [outcome.get("text", "")]
    matched = [fx["id"] for fx in fixtures if any(_matches(t, fx) for t in pool)]
    useful = sum(1 for t in pool if any(_matches(t, fx) for fx in fixtures))
    return {
        "matched": matched,
        "missed": [fx["id"] for fx in fixtures if fx["id"] not in matched],
        "findings": len(pool) if texts else None,
        "findings_matching_a_fixture": useful if texts else None,
        "recall": round(len(matched) / len(fixtures), 2) if fixtures else None,
        "precision": round(useful / len(texts), 2) if texts else None,
    }


@dg.asset_check(
    asset="improvement_advisor_outcome",
    name="matches_fixtures",
    description="Whether the improvement advisor found enough of the problems seeded in the demo project.",
)
def improvement_advisor_matches_fixtures(improvement_advisor_outcome: dict) -> dg.AssetCheckResult:
    fixtures = json.loads(FIXTURES.read_text())["fixtures"]
    result = grade(improvement_advisor_outcome, fixtures)
    threshold = float(settings.get("grade_min_recall", 0.5))
    return dg.AssetCheckResult(
        passed=bool(result["recall"] is not None and result["recall"] >= threshold),
        severity=dg.AssetCheckSeverity.WARN,
        description=f"Found {len(result['matched'])} of {len(fixtures)} seeded problems (needs recall of at least {threshold}).",
        metadata={
            "recall": result["recall"] if result["recall"] is not None else dg.MetadataValue.null(),
            "precision": result["precision"] if result["precision"] is not None else dg.MetadataValue.null(),
            "matched_fixture": dg.MetadataValue.json(result["matched"]),
            "missed_fixture": dg.MetadataValue.json(result["missed"]),
        },
    )
