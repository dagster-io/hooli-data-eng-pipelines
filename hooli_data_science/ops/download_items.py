from typing import Tuple

from dagster import Out, Output, op
from pandas import DataFrame


ACTION_FIELD_NAMES = [
    "id",
    "parent",
    "time",
    "type",
    "by",
    "text",
    "kids",
    "dead",
    "score",
    "title",
    "descendants",
    "url",
]


@op(
    out={"items": Out(io_manager_key="parquet_io_manager", dagster_type=DataFrame)},
    required_resource_keys={"hn_client"},
    description="Downloads all of the items for the id range passed in as input and creates a DataFrame with all the entries.",
)
def download_items(context, id_range: Tuple[int, int]) -> Output:
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
        DataFrame(non_none_rows).drop_duplicates(subset=["id"]),
        "items",
        metadata={
            "Non-empty items": len(non_none_rows),
            "Empty items": rows.count(None),
        },
    )


@op(
    out=Out(
        io_manager_key="warehouse_io_manager",
        metadata={"table": "hackernews.comments"},
    ),
    description="Creates a dataset of all items that are comments",
)
def build_comments(context, items: DataFrame) -> DataFrame:
    return items.where(items["type"] == "comment")[ACTION_FIELD_NAMES]


@op(
    out=Out(
        io_manager_key="warehouse_io_manager",
        metadata={"table": "hackernews.stories"},
    ),
    description="Creates a dataset of all items that are stories",
)
def build_stories(context, items: DataFrame) -> DataFrame:
    return items.where(items["type"] == "story")[ACTION_FIELD_NAMES]
