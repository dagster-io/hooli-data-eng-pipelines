from dagster import FreshnessPolicySensorContext, freshness_policy_sensor, AssetSelection, AssetKey, build_resources, ResourceDefinition, EnvVar
from hooli_data_eng.resources.sensor_smtp import LocalEmailAlert, SESEmailAlert

import os

def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

alert_resources = {
    "LOCAL": LocalEmailAlert(smtp_email_to=["data@awesome.com"], smtp_email_from="no-reply@awesome.com"),
    "PROD": SESEmailAlert(
        smtp_host="email-smtp.us-west-2.amazonaws.com", 
        smtp_email_from="lopp@elementl.com", 
        smtp_email_to= ["lopp@elementl.com"], 
        smtp_username=EnvVar("SMTP_USERNAME"), 
        smtp_password=EnvVar("SMTP_PASSWORD")
    ), 
    "BRANCH": ResourceDefinition.none_resource()
}

assets_to_monitor = AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])) | AssetSelection.keys(AssetKey(["ANALYTICS", "daily_order_summary"]))

@freshness_policy_sensor(asset_selection=assets_to_monitor)
def asset_delay_alert_sensor(context: FreshnessPolicySensorContext, email: alert_resources[get_env()]):
    if context.minutes_late is None or context.previous_minutes_late is None:
        return

    if context.minutes_late >= 2 and context.previous_minutes_late < 2:
        email.send_email_alert(context)
    
    return