import dagster as dg
from dagster_duckdb import DuckDBResource


monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")


def import_url_to_duckdb(url: str, database_resource: DuckDBResource, table_name: str):
    with duckdb.get_connection() as conn:
        row_count = conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from read_csv_auto('{url}')
            )
            """
        ).fetchone()
        assert row_count is not None
        row_count = row_count[0]


@dg.asset(
        # TODO make snowflake
        kinds={"duckdb"},
        # key likely different? 
        key=["target", "main", "raw_customers"],
        automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1")
    )  # every Monday at midnight)
def raw_customers(duckdb: DuckDBResource) -> None:
    # function will need to change.
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_customers",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_orders"],
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # every Monday at midnight
)
def raw_orders(duckdb: DuckDBResource) -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_orders",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_payments"],
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # every Monday at midnight
)
def raw_payments(duckdb: DuckDBResource) -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_payments",
    )


@dg.asset(
    deps=["stg_orders"],
    kinds={"duckdb"},
    partitions_def=monthly_partition,
    automation_condition=dg.AutomationCondition.eager(),
    description="Monthly sales performance",
)
def monthly_orders(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    table_name = "jaffle_platform.main.monthly_orders"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                partition_date varchar,
                status varchar,
                order_num double
            );

            delete from {table_name} where partition_date = '{month_to_fetch}';

            insert into {table_name}
            select
                '{month_to_fetch}' as partition_date,
                status,
                count(*) as order_num
            from jaffle_platform.main.stg_orders
            where strftime(order_date, '%Y-%m') = '{month_to_fetch}'
            group by '{month_to_fetch}', status;
            """
        )

        preview_query = (
            f"select * from {table_name} where partition_date = '{month_to_fetch}';"
        )
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
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    table_name = "jaffle_platform.main.raw_customers"

    with duckdb.get_connection() as conn:
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
