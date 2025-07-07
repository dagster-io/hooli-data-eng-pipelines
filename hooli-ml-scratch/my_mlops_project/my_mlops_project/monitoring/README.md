# Monitoring

To enable monitoring as part of a scheduled Databricks workflow, please:
- Create the inference table that you want to monitor and was passed in as an initialization parameter.
- Update all the TODOs in the [monitoring resource file](../resources/monitoring-resource.yml).
- Uncomment the monitoring workflow from the main Databricks Asset Bundles file [databricks.yml](../databricks.yml).

For more details, refer to [my_mlops_project/resources/README.md](../resources/README.md). 
The implementation supports monitoring of batch inference tables directly.
For real time inference tables, unpacking is required before monitoring can be attached.
