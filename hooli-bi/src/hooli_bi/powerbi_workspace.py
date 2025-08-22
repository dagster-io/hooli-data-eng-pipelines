from dagster import EnvVar
from dagster_powerbi import PowerBIWorkspace, PowerBIServicePrincipal

# Connect using a service principal
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=EnvVar("AZURE_POWERBI_CLIENT_ID"),
        client_secret=EnvVar("AZURE_POWERBI_CLIENT_SECRET"),
        tenant_id=EnvVar("AZURE_POWERBI_TENANT_ID"),
    ),
    workspace_id=EnvVar("AZURE_POWERBI_WORKSPACE_ID"),
)
