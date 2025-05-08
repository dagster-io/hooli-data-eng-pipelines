import hashlib
import json
import dagster as dg
from hooli_data_eng.dbt.resources import dbt_project


def get_current_dbt_code_version(asset_key: dg.AssetKey) -> str:
    with open(dbt_project.manifest_path) as f:
        manifest = json.load(f)

    model_name = asset_key.path[-1]
    model_sql = manifest["nodes"][f"model.dbt_project.{model_name}"]["raw_code"]

    return hashlib.sha1(model_sql.encode("utf-8")).hexdigest()
