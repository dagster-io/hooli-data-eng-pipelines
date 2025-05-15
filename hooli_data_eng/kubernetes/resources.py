import dagster as dg
from dagster_k8s import PipesK8sClient


resource_def = {
    "LOCAL": {
        "pipes_k8s_client": dg.ResourceDefinition.none_resource(),
    },
    "BRANCH": {
        "pipes_k8s_client": PipesK8sClient(),
    },
    "PROD": {
        "pipes_k8s_client": PipesK8sClient(),
    },
}
