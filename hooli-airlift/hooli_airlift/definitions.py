import os
import boto3
import dagster as dg

from hooli_airlift import assets  # noqa: TID252

from dagster_airlift.core import (
    AirflowInstance,
    build_defs_from_airflow_instance,
    assets_with_dag_mappings,
    load_airflow_dag_asset_specs,
    build_airflow_polling_sensor,
)
from dagster_airlift.mwaa import MwaaSessionAuthBackend

all_assets = dg.load_assets_from_modules([assets])

if os.environ.get("environment") == "development":
    session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE"))
else:
    session = boto3.Session(region_name="us-west-2")

boto_client = session.client("mwaa")

airflow_instance_hooli_01 = AirflowInstance(
    name="mwaa_hooli_airflow_01",
    auth_backend=MwaaSessionAuthBackend(
        mwaa_client=boto_client,
        env_name="hooli-airflow-01",
    ),
)

airflow_instance_hooli_02 = AirflowInstance(
    name="mwaa_hooli_airflow_02",
    auth_backend=MwaaSessionAuthBackend(
        mwaa_client=boto_client,
        env_name="hooli-airflow-02",
    ),
)

####################################################################################################
#                                         Airflow 02 - ML                                          #
####################################################################################################

ml_finance_dag_asset = next(
    iter(
        load_airflow_dag_asset_specs(
            airflow_instance=airflow_instance_hooli_02,
            dag_selector_fn=lambda dag: dag.dag_id == "ml_finance",
        )
    )
)

ml_finance_dag_asset = ml_finance_dag_asset.replace_attributes(
    deps=["finance_prediction_model"],
)

finance_prediction_model_asset_spec = dg.AssetSpec(
    key="finance_prediction_model",
    automation_condition=dg.AutomationCondition.eager(),
    deps=[
        dg.AssetKey(["databricks", "revenue"]),
        dg.AssetKey(["databricks", "economic_indicators"]),
        dg.AssetKey(["databricks", "news_sentiment"]),
    ],
    description="Financial prediction model using TensorFlow",
    group_name="ml",
    kinds={"airflow", "tensorflow"},
)

# TODO - unable to call `enrich_` when asset spec has `automation_condition` defined.
#
# enrich_airflow_mapped_assets(
#     [finance_prediction_model_asset_spec],
#     airflow_instance=airflow_instance_hooli_02,
#     source_code_retrieval_enabled=True,
# )


@dg.multi_asset(
    specs=[ml_finance_dag_asset, finance_prediction_model_asset_spec],
)
def finance_prediction_model():
    dag_id = "ml_finance"
    run_id = airflow_instance_hooli_02.trigger_dag(dag_id)
    airflow_instance_hooli_02.wait_for_run_completion(dag_id, run_id)
    if airflow_instance_hooli_02.get_run_state(dag_id, run_id) == "success":
        yield dg.MaterializeResult(asset_key=finance_prediction_model_asset_spec.key)
        yield dg.MaterializeResult(asset_key=ml_finance_dag_asset.key)
    else:
        raise Exception("Dag run failed.")


####################################################################################################
#                                      Airflow 02 - Reporting                                      #
####################################################################################################

reporting_dag_asset = next(
    iter(
        load_airflow_dag_asset_specs(
            airflow_instance=airflow_instance_hooli_02,
            dag_selector_fn=lambda dag: dag.dag_id == "wbr_reporting",
        )
    )
)

reporting_deps = [
    dg.AssetKey(["dim_customers"]),
    dg.AssetKey(["fct_inventory"]),
    dg.AssetKey(["fct_orders"]),
    dg.AssetKey(["fct_payments"]),
    dg.AssetKey(["fct_suppliers"]),
    dg.AssetKey(["fct_warehouses"]),
]

reporting_task_specs = [
    dg.AssetSpec(
        key="wbr_finance",
        deps=reporting_deps,
        automation_condition=dg.AutomationCondition.eager(),
        description="hooli-airflow-02 reporting: weekly business review, finance",
        group_name="reporting",
        kinds={"airflow"},
    ),
    dg.AssetSpec(
        key="wbr_performance",
        deps=reporting_deps,
        description="hooli-airflow-02 reporting: weekly business review, performance",
        automation_condition=dg.AutomationCondition.eager(),
        group_name="reporting",
        kinds={"airflow"},
    ),
    dg.AssetSpec(
        key="wbr_overview",
        deps=reporting_deps,
        description="hooli-airflow-02 reporting: weekly business review, overview",
        automation_condition=dg.AutomationCondition.eager(),
        group_name="reporting",
        kinds={"airflow"},
    ),
]

# TODO - unable to call `enrich_` when asset spec has `automation_condition` defined.
#
# enrich_airflow_mapped_assets(
#     reporting_task_specs,
#     airflow_instance=airflow_instance_hooli_02,
#     source_code_retrieval_enabled=True,
# )

reporting_dag_asset = reporting_dag_asset.replace_attributes(
    deps=["wbr_finance", "wbr_performance", "wbr_overview"],
)


@dg.multi_asset(
    specs=[reporting_dag_asset, *reporting_task_specs],
)
def wbr_reporting():
    dag_id = "wbr_reporting"
    run_id = airflow_instance_hooli_02.trigger_dag(dag_id)
    airflow_instance_hooli_02.wait_for_run_completion(dag_id, run_id)
    if airflow_instance_hooli_02.get_run_state(dag_id, run_id) == "success":
        for spec in reporting_task_specs:
            yield dg.MaterializeResult(asset_key=spec.key)
        yield dg.MaterializeResult(asset_key=reporting_dag_asset.key)
    else:
        raise Exception("Dag run failed.")


####################################################################################################
#                                             Sensors                                              #
####################################################################################################


sensor = build_airflow_polling_sensor(
    airflow_instance=airflow_instance_hooli_02,
    mapped_assets=[finance_prediction_model, wbr_reporting],
)

####################################################################################################
#                                           Definitions                                            #
####################################################################################################

AIRFLOW_DAG_TABLE_MAPPINGS = {
    "replicate_postgres_customers": [
        "customers",
        "orders",
        "payments",
    ],
    "replicate_postgres_inventory": [
        "inventory_items",
        "warehouses",
        "suppliers",
    ],
}

defs = dg.Definitions.merge(
    dg.Definitions(assets=[*all_assets, finance_prediction_model, wbr_reporting]),
    build_defs_from_airflow_instance(
        airflow_instance=airflow_instance_hooli_01,
        defs=dg.Definitions(
            assets=assets_with_dag_mappings(
                dag_mappings={
                    dag_id: [
                        dg.AssetSpec(
                            key=["replication", dag_id.split("_")[-1], table],
                            description=f"Postgres to Snowflake replication of {table} from Airflow environment `hooli-airflow-01`",
                            group_name="replication",
                            kinds={"snowflake"},
                        )
                        for table in tables
                    ]
                    for (dag_id, tables) in AIRFLOW_DAG_TABLE_MAPPINGS.items()
                }
            )
        ),
    ),
)


# If we were only _observing_ Airflow, then we could use the following. The reason we use `@multi_asset` is so that we can trigger Airflow to run downstream of our Dagster assets.
#
# build_defs_from_airflow_instance( airflow_instance=airflow_instance_hooli_02, defs=dg.Definitions( assets=[ *assets_with_dag_mappings( { "ml_finance": [ dg.AssetSpec( key="finance_prediction_model", deps=[ dg.AssetKey(["databricks", "revenue"]),
#                                 dg.AssetKey(["databricks", "economic_indicators"]),
#                                 dg.AssetKey(["databricks", "news_sentiment"]),
#                             ],
#                             description="Financial prediction model using TensorFlow",
#                             group_name="ml",
#                             kinds={"tensorflow"},
#                         )
#                     ]
#                 },
#             ),
#             *assets_with_task_mappings(
#                 dag_id="wbr_reporting",
#                 task_mappings={
#                     "generate_report_finance": [
#                         dg.AssetSpec(
#                             key="wbr_finance",
#                             deps=[dg.AssetKey("fct_payments")],
#                             description="Weekly business review: finance",
#                             group_name="reporting",
#                             kinds={"jupyter"},
#                         )
#                     ],
#                     "generate_report_performance": [
#                         dg.AssetSpec(
#                             key="wbr_performance",
#                             deps=[dg.AssetKey("fct_orders")],
#                             description="Weekly business review: performance",
#                             group_name="reporting",
#                             kinds={"jupyter"},
#                         )
#                     ],
#                     "generate_report_overview": [
#                         dg.AssetSpec(
#                             key="wbr_overview",
#                             deps=[
#                                 dg.AssetKey("dim_customers"),
#                                 dg.AssetKey("fct_payments"),
#                                 dg.AssetKey("fct_orders"),
#                             ],
#                             description="Weekly business review: overview",
#                             group_name="reporting",
#                             kinds={"jupyter"},
#                         )
#                     ],
#                 },
#             ),
#         ]
#     ),
# ),
