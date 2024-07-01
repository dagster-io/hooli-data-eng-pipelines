from dagster import asset, asset_check, AssetCheckResult, Definitions
from dagster._core.definitions.metadata import with_source_code_references
from pandas import DataFrame, read_html, get_dummies, to_numeric
from sklearn.linear_model import LinearRegression as Regression

@asset
def country_stats() -> DataFrame:
    df = read_html("https://tinyurl.com/mry64ebh", flavor='html5lib')[0]
    df.columns = ["country", "continent", "region", "pop_2022", "pop_2023", "pop_change"]
    df["pop_change"] = ((to_numeric(df["pop_2023"]) / to_numeric(df["pop_2022"])) - 1)*100
    return df

@asset_check(
       asset=country_stats 
)
def check_country_stats(country_stats):
    return AssetCheckResult(success=True)

@asset
def change_model(country_stats: DataFrame) -> Regression:
    data = country_stats.dropna(subset=["pop_change"])
    dummies = get_dummies(data[["continent"]])
    return Regression().fit(dummies, data["pop_change"])

@asset
def continent_stats(country_stats: DataFrame, change_model: Regression) -> DataFrame:
    result = country_stats.groupby("continent").sum()
    result["pop_change_factor"] = change_model.coef_
    return result

defs = Definitions(
    assets=with_source_code_references([country_stats, continent_stats, change_model]), 
    asset_checks=[check_country_stats]
)

