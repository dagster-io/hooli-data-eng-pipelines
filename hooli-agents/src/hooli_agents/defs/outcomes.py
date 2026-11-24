"""A structured outcome for each agent run: a summary, what was filed, what was refused, and decisions for a person."""

import re

import dagster as dg

from hooli_agents import ledger

AGENTS = ["improvement_advisor"]  # the others use the shipped outcome asset


def _text(result) -> str:
    if isinstance(result, dict):
        return str(result.get("final_answer") or result.get("answer") or result)
    return str(result)


def _decisions(text: str) -> list[str]:
    found = re.search(r"decisions for you:?\s*(.*)\Z", text, re.IGNORECASE | re.DOTALL)
    if not found:
        return []
    items = [re.sub(r"^[\s\-*•\d.)]+", "", line).strip() for line in found.group(1).splitlines()]
    return [i for i in items if i and i.lower() not in ("none", "none.")][:3]


def _summary(text: str) -> str:
    head = re.split(r"decisions for you", text, flags=re.IGNORECASE)[0].strip()
    return head[:700] + ("…" if len(head) > 700 else "")


def _drafts_markdown(filed: list[dict], would_file: list[dict]) -> str:
    """The full text of what was filed, or what would have been filed in practice mode, for reading in the UI."""
    parts = []
    for row in would_file:
        parts.append(f"## {row.get('title', '(untitled)')}\n\n_Practice mode, not filed ({row.get('place', '')})._\n\n{row.get('body', '')}")
    for row in filed:
        link = f" {row['url']}" if row.get("url") else ""
        parts.append(f"## {row.get('title', row.get('kind', 'filed'))}\n\n_Filed ({row.get('kind', '')}).{link}_")
    return "\n\n---\n\n".join(parts) or "Nothing was filed or drafted."


def _outcome_asset(agent: str) -> dg.AssetsDefinition:
    @dg.asset(
        name=f"{agent}_outcome",
        ins={"result": dg.AssetIn(key=agent)},
        group_name="engineering_agents",
        description=f"What the {agent} run did: a summary, what it filed, what was refused, and decisions for a person.",
    )
    def outcome(context: dg.AssetExecutionContext, result) -> dg.Output:
        text = _text(result)
        start = context.instance.get_run_stats(context.run_id).start_time or 0
        rows = ledger.since(start)
        filed = [r for r in rows if r["kind"] not in ("refused", "would_file")]
        would_file = [r for r in rows if r["kind"] == "would_file"]
        refused = [r for r in rows if r["kind"] == "refused"]
        decisions = _decisions(text)
        status = "filed" if filed else "practice" if would_file else "blocked" if refused else "nothing_new"
        return dg.Output(
            value={
                "status": status,
                "text": text,
                "filed": filed,
                "would_file": would_file,
                "refused": refused,
                "decisions_for_you": decisions,
            },
            metadata={
                "status": status,
                "summary": dg.MetadataValue.md(_summary(text)),
                "drafts": dg.MetadataValue.md(_drafts_markdown(filed, would_file)),
                "filed": dg.MetadataValue.json(filed),
                "would_file": dg.MetadataValue.json(would_file),
                "refused": dg.MetadataValue.json(refused),
                "decisions_for_you": dg.MetadataValue.json(decisions),
                "filed_count": len(filed),
            },
        )

    return outcome


outcome_assets = [_outcome_asset(a) for a in AGENTS]
