import dagster as dg

####################################################################################################
#                                     Mocked Databricks model                                      #
####################################################################################################


@dg.asset(
    key_prefix="databricks",
    group_name="ingestion",
    description="Ledger loaded ",
    kinds={"databricks"},
    automation_condition=dg.AutomationCondition.on_cron("0 12 * * *"),
)
def revenue():
    pass


@dg.asset(
    key_prefix="databricks",
    group_name="ingestion",
    description="Ledger loaded ",
    kinds={"databricks"},
    automation_condition=dg.AutomationCondition.on_cron("0 12 * * *"),
)
def economic_indicators():
    pass


@dg.asset(
    key_prefix="databricks",
    group_name="ingestion",
    description="Ledger loaded ",
    kinds={"databricks"},
    automation_condition=dg.AutomationCondition.on_cron("0 12 * * *"),
)
def news_sentiment():
    pass


####################################################################################################
#                                        Mocked dbt models                                         #
####################################################################################################

# Customers


@dg.asset(
    deps=[dg.AssetKey(["replication", "customers", "customers"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_customers():
    pass


@dg.asset(
    deps=[dg.AssetKey(["replication", "customers", "orders"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_orders():
    pass


@dg.asset(
    deps=[dg.AssetKey(["replication", "customers", "payments"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_payments():
    pass


@dg.asset(
    deps=[stg_customers],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def dim_customers():
    pass


@dg.asset(
    deps=[stg_orders],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def fct_orders():
    pass


@dg.asset(
    deps=[stg_payments],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def fct_payments():
    pass


# Inventory


@dg.asset(
    deps=[dg.AssetKey(["replication", "inventory", "inventory_items"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_inventory_items():
    pass


@dg.asset(
    deps=[dg.AssetKey(["replication", "inventory", "warehouses"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_warehouses():
    pass


@dg.asset(
    deps=[dg.AssetKey(["replication", "inventory", "suppliers"])],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def stg_suppliers():
    pass


@dg.asset(
    deps=[stg_inventory_items],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def fct_inventory():
    pass


@dg.asset(
    deps=[stg_warehouses],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def fct_warehouses():
    pass


@dg.asset(
    deps=[stg_suppliers],
    automation_condition=dg.AutomationCondition.eager(),
    group_name="transformation",
    kinds={"dbt"},
)
def fct_suppliers():
    pass
