from dagster import FreshnessPolicySensorContext, freshness_policy_sensor, AssetSelection, AssetKey, build_resources, ResourceDefinition
from hooli_data_eng.resources.sensor_smtp import local_email_alert, ses_email_alert

import os

def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

alert_resources = {
    "LOCAL": {
        "email": local_email_alert.configured({
            "smtp_email_to": ["data@awesome.com"],
            "smtp_email_from": "no-reply@awesome.com"
        })
    },
    "PROD": {
        "email": ses_email_alert.configured({
            "smtp_email_to": ["lopp@elementl.com"],
            "smtp_email_from": "lopp@elementl.com",
            "smtp_host": "email-smtp.us-west-2.amazonaws.com",
            "smtp_username": {"env": "SMTP_USERNAME"},
            "smtp_password": {"env": "SMTP_PASSWORD"},
        })
    },
    "BRANCH": {
        "email": ResourceDefinition.none_resource()
    }
}

assets_to_monitor = AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])) | AssetSelection.keys(AssetKey(["ANALYTICS", "daily_order_summary"]))

@freshness_policy_sensor(asset_selection=assets_to_monitor)
def asset_delay_alert_sensor(context: FreshnessPolicySensorContext):
    if context.minutes_late is None or context.previous_minutes_late is None:
        return

    if context.minutes_late >= 2 and context.previous_minutes_late < 2:
        with build_resources(
            alert_resources[get_env()]
        ) as resources:
            resources.email.send_email_alert(context)
    
    return