"""Triggers for the engineering agents: the weekly improvement review."""

import os
import time

import dagster as dg
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hooli_agents import settings


bug_fix_job = dg.define_asset_job("bug_fix_job", selection=["bug_fixer", "bug_fixer_reply", "bug_fixer_outcome"])
pr_review_job = dg.define_asset_job("pr_review_job", selection=["pr_reviewer", "pr_reviewer_reply", "pr_reviewer_outcome"])
improvement_review_job = dg.define_asset_job(
    "improvement_review_job",
    selection=[
        "improvement_advisor",
        "improvement_advisor_reply",
        "improvement_advisor_outcome",
    ],
)


def _slack() -> WebClient:
    return WebClient(token=os.environ["SLACK_BOT_TOKEN"])


BRANCH_SKIP = "Branch deployment: the full deployment's sensors handle announcements and approvals."


def _in_branch_deployment() -> bool:
    """Dagster+ sets this in branch deployments, where a second copy of each sensor would double-post."""
    return os.environ.get("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "").lower() in ("1", "true")


def _periodic_review(context: dg.SensorEvaluationContext, name: str, period_hours: float, text: str):
    """Fire once per period (the first tick fires at once), announcing in Slack and tagging the thread."""
    now = time.time()
    last = float(context.cursor) if context.cursor else 0.0
    if now - last < period_hours * 3600:
        return dg.SkipReason(f"Next {name} in {round((last + period_hours * 3600 - now) / 3600, 1)}h.")
    channel = settings.get("slack_channel")
    try:
        posted = _slack().chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        context.log.error(f"Could not post to Slack channel {channel}: {e.response.get('error')}")
        return dg.SkipReason("Slack post failed.")
    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(
                run_key=f"{name}-{int(now)}",
                tags={"slack/channel": channel, "slack/thread_ts": posted["ts"]},
            )
        ],
        cursor=str(now),
    )


@dg.sensor(
    name="improvement_review_trigger",
    job=improvement_review_job,
    minimum_interval_seconds=3600,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def improvement_review_trigger(context: dg.SensorEvaluationContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    return _periodic_review(
        context,
        "improvement review",
        float(settings.get("improvement_period_hours", 168)),
        ":bar_chart: Improvement review started. Checking retries, deprecated APIs, freshness, automation and alerts.",
    )
