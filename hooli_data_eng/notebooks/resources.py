from dagstermill import ConfigurableLocalOutputNotebookIOManager


# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

resource_def = {
    "LOCAL": {
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
    },
    "BRANCH": {
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
    },
    "PROD": {
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),}
}
