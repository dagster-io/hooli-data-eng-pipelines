import dagster as dg
from dagster_k8s import PipesK8sClient

CONTAINER_REGISTRY = (
    "764506304434.dkr.ecr.us-west-2.amazonaws.com/hooli-data-science-prod"
)


# This k8s pipes asset only runs in prod, see utils/example_container
# The dependency on predicted_orders is not a real dependency since the script does not rely
# or use that upstream Snowflake table, it is used here for illustrative purposes
@dg.asset(
    deps=[dg.AssetKey(["FORECASTING","predicted_orders"])],
    kinds={"kubernetes", "S3"},
)
def k8s_pod_asset(
    context: dg.AssetExecutionContext,
    pipes_k8s_client: PipesK8sClient,
) -> dg.MaterializeResult:
    # The kubernetes pod spec for the computation we want to run
    # with resource limits and requests set.
    pod_spec = {
        "containers": [
            {
                "name": "pipes-example",
                "image": f"{CONTAINER_REGISTRY}:latest-pipes-example",
                "resources": {
                    "requests": {
                        "memory": "64Mi",
                        "cpu": "250m",
                    },
                    "limits": {
                        "memory": "128Mi",
                        "cpu": "500m",
                    },
                },
            },
        ]
    }

    # Arbitrary json-serializable data you want access to from the `PipesSession`
    # in the k8s pod container. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    return pipes_k8s_client.run(
        context=context,
        namespace="data-eng-prod",
        base_pod_spec=pod_spec,
        extras=extras,
    ).get_materialize_result()
