from dagster import FreshnessPolicySensorContext, freshness_policy_sensor, AssetSelection, AssetKey
from dagster._utils.alert import (
    EMAIL_MESSAGE,
    send_email_via_ssl
)
from dagster._core.errors import DagsterInvalidDefinitionError
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union
import datetime 
import ssl
import smtplib
import os

assets_to_monitor = AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])) | AssetSelection.keys(AssetKey(["ANALYTICS", "daily_order_summary"]))

@freshness_policy_sensor(asset_selection=assets_to_monitor)
def asset_delay_alert_sensor(context: FreshnessPolicySensorContext):
    if context.minutes_late is None or context.previous_minutes_late is None:
        return

    if context.minutes_late >= 2 and context.previous_minutes_late < 2:
        send_email_alert(
            context = context,
            email_username= os.getenv("SMTP_USERNAME"),
            email_from = "lopp@elementl.com",
            email_to=["lopp@elementl.com"],
            email_password=os.getenv("SMTP_PASSWORD"),
            smtp_host="email-smtp.us-west-2.amazonaws.com",
            smtp_type="STARTTLS",
            smtp_port=587
        )
    
    return


def send_email_via_starttls(
    email_from: str,
    email_password: str,
    email_username: str,
    email_to: Sequence[str],
    message: str,
    smtp_host: str,
    smtp_port: int,
):
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(email_username, email_password)
        server.sendmail(email_from, email_to, message)

def _default_delay_email_body(context) -> str:
    return "<br>".join(
        [
            f"Asset { context.asset_key } late!",
            f"Late by: { context.minutes_late } minutes"
        ]
    )

def _default_delay_email_subject(context) -> str:
    return f"Dagster Asset Late: { context.asset_key }" 

def send_email_alert(
    context: FreshnessPolicySensorContext,
    email_from: str,
    email_username: str,
    email_password: str,
    email_to: Sequence[str],
    email_body_fn: Callable[["FreshnessPolicySensorContext"], str] = _default_delay_email_body,
    email_subject_fn: Callable[["FreshnessPolicySensorContext"], str] = _default_delay_email_subject,
    smtp_host: str = "smtp.gmail.com",
    smtp_type: str = "SSL",
    smtp_port: Optional[int] = None,
):
    email_body = email_body_fn(context)
    message = EMAIL_MESSAGE.format(
        email_to=",".join(email_to),
        email_from=email_from,
        email_subject=email_subject_fn(context),
        email_body=email_body,
        randomness=datetime.datetime.now(),
    )

    if smtp_type == "SSL":
        send_email_via_ssl(
            email_from, email_password, email_to, message, smtp_host, smtp_port=smtp_port or 465
        )
    elif smtp_type == "STARTTLS":
        send_email_via_starttls(
            email_from, email_password, email_username, email_to, message, smtp_host, smtp_port=smtp_port or 587
        )
    else:
        raise DagsterInvalidDefinitionError(f'smtp_type "{smtp_type}" is not supported.')
