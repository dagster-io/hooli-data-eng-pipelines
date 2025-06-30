from dagster_snowflake import SnowflakeResource
from dagster_duckdb import DuckDBResource
import dagster as dg
from hooli_etl_pipeline.defs.resources import get_env, get_database_kind, DataImportResource
import pandas as pd

monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")


@dg.asset(
        kinds={get_database_kind()},
        # key likely different? 
        key=["target", "main", "raw_customers"],
        automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1")
    )  # every Monday at midnight)
def raw_customers(database: DuckDBResource, data_importer: DataImportResource) -> None:
    data_importer.import_url_to_database(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        table_name="RAW_CUSTOMERS",
        database_resource=database,
    )


@dg.asset(
    kinds={get_database_kind()},
    key=["target", "main", "raw_orders"],
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # every Monday at midnight
)
def raw_orders(database: DuckDBResource, data_importer: DataImportResource) -> None:
    data_importer.import_url_to_database(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        table_name="RAW_ORDERS",
        database_resource=database,
    )


@dg.asset(
    kinds={get_database_kind()},
    key=["target", "main", "raw_payments"],
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # every Monday at midnight
)
def raw_payments(database: DuckDBResource, data_importer: DataImportResource) -> None:
    data_importer.import_url_to_database(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
        table_name="RAW_PAYMENTS",
        database_resource=database,
    )


@dg.asset(
    deps=["stg_orders"],
    kinds={get_database_kind()},
    partitions_def=monthly_partition,
    automation_condition=dg.AutomationCondition.eager(),
    description="Monthly sales performance",
)
def monthly_orders(context: dg.AssetExecutionContext, database: DuckDBResource):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    context.log.info(f"Fetching data for month: {month_to_fetch}")
    table_name = "monthly_orders"

    # Choose the correct month extraction expression for each backend
    if isinstance(database, SnowflakeResource):
        month_expr = "TO_VARCHAR(CAST(order_date AS DATE), 'YYYY-MM')"
    else:
        month_expr = "strftime(cast(order_date as date), '%Y-%m')"

    with database.get_connection() as conn:
        conn = conn.cursor() if isinstance(database, SnowflakeResource) else conn
        conn.execute(
            f"""
            create table if not exists {table_name} (
                partition_date varchar,
                status varchar,
                order_num double
            )
            """
        )
        conn.execute(
            f"delete from {table_name} where partition_date = '{month_to_fetch}'"
        )
        conn.execute(
            f"""
            insert into {table_name}
            select
                '{month_to_fetch}' as partition_date,
                status,
                count(*) as order_num
            from stg_orders
            where {month_expr} = '{month_to_fetch}'
            group by '{month_to_fetch}', status
            """
        )
        preview_query = (
            f"select * from {table_name} where partition_date = '{month_to_fetch}';"
        )
        if isinstance(database, SnowflakeResource):
            cursor = conn.execute(preview_query)
            columns = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            preview_df = pd.DataFrame(data, columns=columns)
        else:
            preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where partition_date = '{month_to_fetch}'
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )


@dg.asset_check(
    asset=raw_customers,
    description="Check if there are any null customer_ids in the joined data",
)
def missing_dimension_check(database: DuckDBResource) -> dg.AssetCheckResult:
    table_name = "RAW_CUSTOMERS"

    with database.get_connection() as conn:
        conn = (
            conn.cursor() if isinstance(database, SnowflakeResource) else conn
        )
        query_result = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where id is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(
            passed=count == 0, metadata={"customer_id is null": count}
        )
