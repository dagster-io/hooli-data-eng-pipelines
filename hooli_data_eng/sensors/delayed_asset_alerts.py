# Removed in Dagster 1.7.0 in favor of asset freshness checks

# from dagster import FreshnessPolicySensorContext, freshness_policy_sensor, AssetSelection, AssetKey, build_resources, ResourceDefinition, EnvVar
# from hooli_data_eng.resources.sensor_smtp import EmailAlert

# import os

# assets_to_monitor = AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])) | AssetSelection.keys(AssetKey(["ANALYTICS", "weekly_order_summary"]))

# @freshness_policy_sensor(asset_selection=assets_to_monitor)
# def asset_delay_alert_sensor(context: FreshnessPolicySensorContext, email: EmailAlert):
#     if context.minutes_late is None or context.previous_minutes_late is None:
#         return

#     if context.minutes_late >= 2 and context.previous_minutes_late < 2:
#         email.send_email_alert(context)
    
#     return