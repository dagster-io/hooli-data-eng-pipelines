from dagster import FreshnessPolicySensorContext, ConfigurableResource
from dagster._utils.alert import EMAIL_MESSAGE, send_email_via_ssl
from dagster._core.errors import DagsterInvalidDefinitionError
from typing import Callable, Optional, Sequence
import datetime
import ssl
import smtplib
import os
from typing import List


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
            f"Late by: { context.minutes_late } minutes",
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
    email_body_fn: Callable[
        ["FreshnessPolicySensorContext"], str
    ] = _default_delay_email_body,
    email_subject_fn: Callable[
        ["FreshnessPolicySensorContext"], str
    ] = _default_delay_email_subject,
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
            email_from,
            email_password,
            email_to,
            message,
            smtp_host,
            smtp_port=smtp_port or 465,
        )
    elif smtp_type == "STARTTLS":
        send_email_via_starttls(
            email_from,
            email_password,
            email_username,
            email_to,
            message,
            smtp_host,
            smtp_port=smtp_port or 587,
        )
    else:
        raise DagsterInvalidDefinitionError(
            f'smtp_type "{smtp_type}" is not supported.'
        )


class SESEmailAlert(ConfigurableResource):
    smtp_host: str
    smtp_username: str
    smtp_password: str
    smtp_email_from: str
    smtp_email_to: List[str]

    def send_email_alert(self, context):

        return send_email_alert(
            context=context,
            email_username=self.smtp_username,
            email_from=self.smtp_email_from,
            email_to=self.smtp_email_to,
            email_password=self.smtp_password,
            smtp_host=self.smtp_host,
            smtp_type="STARTTLS",
            smtp_port=587,
        )


class LocalEmailAlert(ConfigurableResource):
    smtp_email_from: str
    smtp_email_to: List[str]

    def send_email_alert(self, context):
        email_body = _default_delay_email_body(context)
        message = EMAIL_MESSAGE.format(
            email_to=",".join(self.smtp_email_to),
            email_from=self.smtp_email_from,
            email_subject=_default_delay_email_subject(context),
            email_body=email_body,
            randomness=datetime.datetime.now(),
        )
        print(message)
        return
