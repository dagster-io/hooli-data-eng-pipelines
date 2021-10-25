from typing import Tuple

from dagster import AssetKey, In, List, Out, Output, op, usable_as_dagster_type
from dagster.core.types.decorator import usable_as_dagster_type
from pandas import DataFrame

from .id_range_for_time import HackerNewsApiIdRange

ACTION_FIELD_NAMES = [
    "id",
    "parent",
    "time",
    "type",
    "by",
    "text",
    "kids",
    # "dead",
    "score",
    "title",
    "descendants",
    "url",
]


@usable_as_dagster_type
class HNItemsDataFrame(DataFrame):
    pass


@usable_as_dagster_type
class HNCommentsDataFrame(DataFrame):
    pass


@usable_as_dagster_type
class HNStoriesDataFrame(DataFrame):
    pass


@op(
    out={
        "items": Out(io_manager_key="parquet_io_manager", dagster_type=HNItemsDataFrame)
    },
    required_resource_keys={"hn_client"},
    description="Downloads all of the items for the id range passed in as input and creates a DataFrame with all the entries.",
)
def download_items(context, id_range: HackerNewsApiIdRange) -> Output:
    """
    Downloads all of the items for the id range passed in as input and creates a DataFrame with
    all the entries.
    """
    start_id, end_id = id_range

    context.log.info(
        f"Downloading range {start_id} up to {end_id}: {end_id - start_id} items."
    )

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(context.resources.hn_client.fetch_item_by_id(context, item_id))
        if len(rows) % 100 == 0:
            context.log.info(f"Downloaded {len(rows)} items!")

    non_none_rows = [row for row in rows if row is not None]

    return Output(
        HNItemsDataFrame(DataFrame(non_none_rows).drop_duplicates(subset=["id"])),
        "items",
        metadata={
            "Non-empty items": len(non_none_rows),
            "Empty items": rows.count(None),
        },
    )


@op(
    out={
        "comments_df": Out(
            dagster_type=HNCommentsDataFrame,
            io_manager_key="warehouse_io_manager",
            metadata={"table": "hackernews.comments"},
        ),
    },
    description="Creates a dataset of all items that are comments",
)
def build_comments(_context, items: HNItemsDataFrame) -> HNCommentsDataFrame:
    items = items.where(items["type"] == "comment")[ACTION_FIELD_NAMES]
    items["user_id"] = items["by"]
    del items["by"]

    yield Output(HNCommentsDataFrame(items), "comments_df")


@op(
    out={
        "stories_df": Out(
            dagster_type=HNStoriesDataFrame,
            io_manager_key="warehouse_io_manager",
            metadata={"table": "hackernews.stories"},
        ),
    },
    description="Creates a dataset of all items that are stories",
)
def build_stories(_context, items: HNItemsDataFrame) -> HNStoriesDataFrame:
    items = items.where(items["type"] == "story")[ACTION_FIELD_NAMES]
    items["user_id"] = items["by"]
    del items["by"]

    yield Output(HNStoriesDataFrame(items), "stories")


@op(
    ins={"tables": In(List[DataFrame], description="Tables to update in Snowflake")},
    out={
        "updated_tables": Out(
            List[DataFrame],
            description="Updated Snowflake tables",
            asset_key=AssetKey("hacker_news_tables"),
        )
    },
    description="Updates tables in Snowflake",
)
def update_tables(tables: List[DataFrame]) -> List[DataFrame]:
    yield Output(tables, metadata={"n_tables_updated": len(tables)})
