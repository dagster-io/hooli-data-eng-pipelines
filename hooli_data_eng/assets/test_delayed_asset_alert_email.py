
from hooli_data_eng.resources.sensor_smtp import local_email_alert, ses_email_alert
import os
from dagster import build_freshness_policy_sensor_context, FreshnessPolicy, AssetKey, build_resources

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


context = build_freshness_policy_sensor_context(
    sensor_name="test_delay_sensor",
    asset_key=AssetKey("test_asset"),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=1),
    previous_minutes_late=1,
    minutes_late=5
)


with build_resources({
    "email": local_email_alert.configured({
        "smtp_email_to": ["test@test.com"],
        "smtp_email_from": "no-reply@test.com"
    })    
}) as resources:
    resources.email.send_email_alert(context)

with build_resources({
    "email": ses_email_alert.configured({
        "smtp_host": "email-smtp.us-west-2.amazonaws.com",
        "smtp_username": SMTP_USERNAME,
        "smtp_password": SMTP_PASSWORD,
        "smtp_email_from": "lopp@elementl.com",
        "smtp_email_to": ["lopp@elementl.com"]
    })
}) as resources:
    resources.email.send_email_alert(context)


