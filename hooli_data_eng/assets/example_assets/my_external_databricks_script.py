from pandas import DataFrame, read_html, get_dummies, to_numeric
from sklearn.linear_model import LinearRegression as Regression

from dagster_pipes import (
    PipesDbfsContextLoader,
    PipesDbfsMessageWriter,
    open_dagster_pipes,
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


def change_model(country_stats: DataFrame) -> Regression:
    data = country_stats.dropna(subset=["pop_change"])
    dummies = get_dummies(data[["continent"]])
    return Regression().fit(dummies, data["pop_change"])


def continent_stats(country_stats: DataFrame, change_model: Regression) -> DataFrame:
    result = country_stats.groupby("continent").sum()
    result["pop_change_factor"] = change_model.coef_
    return result

if __name__ == "__main__":

    with open_dagster_pipes(
        context_loader=PipesDbfsContextLoader(),
        message_writer=PipesDbfsMessageWriter(),
    ) as pipes:
        
        # Generate country statistics
        country_data = country_stats()

        # Build a regression model to predict population change based on continent
        model = change_model(country_data)

        # Calculate statistics by continent and add the population change factor
        stats_by_continent = continent_stats(country_data, model)

        pipes.report_asset_materialization(
            asset_key="my_databricks_asset",
            metadata={
                "num_records": len(stats_by_continent),
                "columns": list(stats_by_continent.columns),
                "pop_change_mean": stats_by_continent["pop_change"].mean(),
                },
        )


### TODO - move open_dagster_pipes to the beginning of the script and
### record asset materialization events per function (country_stats, change_model, etc.)