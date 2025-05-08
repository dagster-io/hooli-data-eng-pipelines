import yaml
from pathlib import Path
from hooli_data_eng.checks_dsl.engine import validate_check_config, generate_asset_check_function, handle_schema_change_check, handle_freshness_check

def load_checks_from_yaml(path: str):
    yaml_path = Path(path)
    if not yaml_path.exists():
        return []  # ✅ return empty list

    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)

    if not config or "checks" not in config:
        return []  # ✅ return empty list

    all_checks = []

    for check in config["checks"]:
        if check.get("type") == "schema_change":
            all_checks.extend(handle_schema_change_check(check))
        elif check.get("type") == "freshness":
            all_checks.extend(handle_freshness_check(check))
        else:
            validate_check_config(check)
            check_fn = generate_asset_check_function(check)
            all_checks.append(check_fn)

    return all_checks