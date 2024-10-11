from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    asset,
    asset_check,
    AssetCheckResult,
    Definitions,
    with_source_code_references,
)
from dagster._core.definitions.tags import build_kind_tag
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud
from pandas import DataFrame, read_html, get_dummies, to_numeric
from sklearn.linear_model import LinearRegression as Regression

@asset(
    kinds={"Kubernetes", "S3"},
)
def country_stats() -> DataFrame:
    df = read_html("https://tinyurl.com/mry64ebh", flavor='html5lib')[0]
    df.columns = ["country", "Population (1 July 2022)", "Population (1 July 2023)", "Change", "UN Continental Region[1]", "UN Statistical Subregion[1]"]
    df = df.drop(columns=["Change"])
    df = df.rename(columns={
        "UN Continental Region[1]": "continent",
        "UN Statistical Subregion[1]": "region",
        "Population (1 July 2022)": "pop_2022",
        "Population (1 July 2023)": "pop_2023",
        }
    )
    df["pop_change"] = ((to_numeric(df["pop_2023"]) / to_numeric(df["pop_2022"])) - 1)*100
    return df

@asset_check(
       asset=country_stats 
)
def check_country_stats(country_stats):
    return AssetCheckResult(passed=True)

@asset(
    kinds={"Kubernetes", "S3"}
)
def change_model(country_stats: DataFrame) -> Regression:
    data = country_stats.dropna(subset=["pop_change"])
    dummies = get_dummies(data[["continent"]])
    return Regression().fit(dummies, data["pop_change"])

@asset(
    kinds={"Kubernetes", "S3"}
)
def continent_stats(country_stats: DataFrame, change_model: Regression) -> DataFrame:
    result = country_stats.groupby("continent").sum()
    result["pop_change_factor"] = change_model.coef_
    return result

defs = Definitions(
    assets=link_code_references_to_git_if_cloud(
        with_source_code_references([country_stats, continent_stats, change_model]),
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_basics/definitions.py",
        ),
    ), 
    asset_checks=[check_country_stats]
)

