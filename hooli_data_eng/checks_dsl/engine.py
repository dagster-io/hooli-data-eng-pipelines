import pandas as pd
import numpy as np
import re
import statistics
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Any, Optional
from datetime import datetime
from dagster import (
    AssetKey,
    AssetCheckResult,
    DagsterEventType,
    EventRecordsFilter,
    asset_check,
    FreshnessPolicy,
    MetadataValue,
    build_column_schema_change_checks,
    build_last_update_freshness_checks, 
    build_time_partition_freshness_checks

)
import jsonschema
import scipy.stats as stats

# --- Your REQUIRED code -- keep this exactly as you requested ---

CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "check_name": {"type": "string"},
        "type": {"type": "string"},
        "metric": {"type": "string"},
        "min": {"type": "number"},
        "max": {"type": "number"},
        "threshold": {"type": "number"},
        "threshold_pct": {"type": "number"},
        "confidence": {
            "anyOf": [
                {"type": "number"},
                {"type": "string"}
            ]
        },
        "history": {"type": "integer"},
        "where": {"type": "string"},
        "group_by": {"type": "string"},
        "allowed_failures": {"type": "integer"},
        "blocking": {"type": "boolean"},
        "assets": {
            "type": "array",
            "items": {"type": "string"}
        },
        "maximum_lag_minutes": {"type": "number"},
        "maximum_lag_minutes_by_partition": {"type": "number"}
    },
    "required": ["type"],
}

BUILT_IN_PATTERNS = {
    "email": r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$",
    "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89ab][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
    "zip_code": r"^\d{5}(-\d{4})?$",
    "us_state_code": r"^(A[LKZR]|C[AOT]|D[EC]|FL|GA|HI|I[ADLN]|K[SY]|LA|M[EHDAINSOT]|N[HCDEJMVSY]|O[HKR]|P[ARW]|RI|S[CD]|T[NX]|UT|V[AIT]|W[AIVY])$",
    "us_phone_number": r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
    "us_ssn": r"^\d{3}-\d{2}-\d{4}$",
    "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$",
    "ipv4": r"^(\d{1,3}\.){3}\d{1,3}$",
    "ipv6": r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$",
    "mac_address": r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$",
    "iso_date": r"^\d{4}-\d{2}-\d{2}$",
    "iso_datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    "hex_color": r"^#(?:[0-9a-fA-F]{3}){1,2}$",
}

BENFORD_EXPECTED = {
    1: 0.301,
    2: 0.176,
    3: 0.125,
    4: 0.097,
    5: 0.079,
    6: 0.067,
    7: 0.058,
    8: 0.051,
    9: 0.046,
}

BENFORD_SECOND_DIGIT_EXPECTED = {
    0: 0.1197,
    1: 0.1139,
    2: 0.1088,
    3: 0.1043,
    4: 0.1003,
    5: 0.0967,
    6: 0.0934,
    7: 0.0904,
    8: 0.0876,
    9: 0.0850,
}

def validate_check_config(config: Dict[str, Any]) -> None:
    jsonschema.validate(instance=config, schema=CHECK_SCHEMA)

def handle_schema_change_check(check: Dict[str, Any]) -> List:
    seen = set()
    unique_asset_keys = []
    for asset in check.get("assets", []):
        key = tuple(asset.split("."))
        if key not in seen:
            seen.add(key)
            unique_asset_keys.append(AssetKey(key))

    return build_column_schema_change_checks(assets=unique_asset_keys)

# Function to handle freshness checks from YAML
def handle_freshness_check(check: dict):
    checks = []
    assets = check.get("assets", [])

    for asset in assets:
        asset_key = AssetKey(asset.split("."))

        if "maximum_lag_minutes" in check:
            checks.extend(
                build_last_update_freshness_checks(
                    assets=[asset_key],
                    maximum_lag_minutes=check["maximum_lag_minutes"]
                )
            )

        if "maximum_lag_minutes_by_partition" in check:
            raise NotImplementedError(
                "Dynamic partition freshness checks are not supported yet. "
                "Attach a FreshnessPolicy directly on your asset instead."
            )

    return checks





def apply_filters(df: pd.DataFrame, where: str = None, group_by: str = None, time_range: dict = None) -> Dict[str, pd.DataFrame]:
    """
    Applies optional WHERE, GROUP BY, and TIME RANGE filters to a dataframe.

    If @now/@today are used in WHERE, or time_range is specified, local_dict context is passed to df.query().
    """
    context_vars = {}

    # If time_range exists, build the context_vars first
    if time_range:
        column = time_range.get("column")
        if not column:
            raise ValueError("time_range must specify a 'column' field.")

        context_vars = get_contextual_now(df, column)

        now = context_vars["now"]

        if "minutes_back" in time_range:
            delta = pd.Timedelta(minutes=time_range["minutes_back"])
        elif "hours_back" in time_range:
            delta = pd.Timedelta(hours=time_range["hours_back"])
        else:
            raise ValueError("time_range must specify either 'minutes_back' or 'hours_back'.")

        min_time = now - delta

        # Apply the time range filter
        df = df[df[column] >= min_time]

    # If WHERE exists, apply it next
    if where:
        df = df.query(where, local_dict=context_vars)

    # If GROUP BY exists, group
    if group_by:
        return dict(tuple(df.groupby(group_by)))

    return {"__all__": df}


def compute_entropy(series: pd.Series) -> float:
    value_counts = series.value_counts(normalize=True)
    return -(value_counts * np.log2(value_counts)).sum()

def evaluate_entropy_check(df, column, min_entropy, max_entropy):


    counts = df[column].value_counts(normalize=True)
    entropy = stats.entropy(counts, base=2)  # base-2 for bits

    passed = True
    if min_entropy is not None and entropy < min_entropy:
        passed = False
    if max_entropy is not None and entropy > max_entropy:
        passed = False

    # 🔥 Fix: Cast to native float
    return AssetCheckResult(
        passed=passed,
        metadata={
            "entropy": float(entropy),
            "min_entropy": float(min_entropy) if min_entropy is not None else None,
            "max_entropy": float(max_entropy) if max_entropy is not None else None,
        }
    )


def evaluate_benford_law(df: pd.DataFrame, column: str, threshold: float = 0.05, digit_position: int = 1):
    # Step 1: Preprocess the column
    series = df[column].dropna().astype(str).str.strip()

    # Filter to only numeric-like strings
    series = series[series.str.isnumeric()]

    if series.empty:
        return AssetCheckResult(
            passed=True,
            metadata={"note": "No valid numeric entries to evaluate Benford's Law"}
        )

    if digit_position == 1:
        first_digits = series.str[0].astype(int)
        expected = BENFORD_EXPECTED
    elif digit_position == 2:
        first_digits = series.str[1].astype(int)
        expected = BENFORD_SECOND_DIGIT_EXPECTED
    else:
        raise ValueError(f"Unsupported digit position: {digit_position}")

    # Step 2: Actual distribution
    actual_counts = first_digits.value_counts(normalize=True).to_dict()

    # Step 3: Compare actual vs expected
    deviations = {digit: abs(actual_counts.get(digit, 0) - expected.get(digit, 0)) for digit in expected.keys()}
    max_deviation = max(deviations.values())

    passed = max_deviation <= threshold

    return AssetCheckResult(
        passed=passed,
        metadata={
            "max_deviation": max_deviation,
            "threshold": threshold,
            "deviations_by_digit": deviations,
            "observed_distribution": actual_counts,
            "expected_distribution": expected,
        }
    )


def evaluate_benford_second_digit(df: pd.DataFrame, column: str, threshold: float = 0.05) -> AssetCheckResult:
    # Step 1: Extract second digits
    second_digits = df[column].dropna().astype(str).str.lstrip('-0').str[1:2]
    second_digits = second_digits[second_digits.isin(list('0123456789'))].astype(int)

    if second_digits.empty:
        return AssetCheckResult(
            passed=True,
            metadata={"note": "No valid entries to evaluate second-digit Benford's Law"}
        )

    # Step 2: Actual distribution
    actual_counts = second_digits.value_counts(normalize=True).to_dict()

    # Step 3: Compare actual vs expected
    deviations = {digit: abs(actual_counts.get(digit, 0) - BENFORD_SECOND_DIGIT_EXPECTED[digit]) for digit in range(0, 10)}
    max_deviation = max(deviations.values())

    passed = max_deviation <= threshold

    return AssetCheckResult(
        passed=passed,
        metadata={
            "max_deviation": max_deviation,
            "threshold": threshold,
            "deviations_by_digit": deviations,
            "observed_distribution": actual_counts,
            "expected_distribution": BENFORD_SECOND_DIGIT_EXPECTED,
        }
    )

def get_contextual_now(df: pd.DataFrame, datetime_col: str = None) -> Dict[str, pd.Timestamp]:
    """
    Returns timezone-matched versions of @now and @today for use in pandas query local_dict.
    If the datetime_col is tz-aware, now/today will be tz-aware too. Otherwise, tz-naive.
    """
    if datetime_col and datetime_col in df.columns:
        non_null = df[datetime_col].dropna()
        sample = non_null.iloc[0] if not non_null.empty else None

        if isinstance(sample, pd.Timestamp) and sample.tzinfo is not None:
            now = pd.Timestamp.now(tz=sample.tzinfo)
            today = now.normalize()
            return {"now": now, "today": today}
    
    # Default to naive if no column or no tz-awareness
    now = pd.Timestamp.now().replace(tzinfo=None)
    today = now.normalize()
    return {"now": now, "today": today}


def get_z_value(confidence) -> float:
    sensitivity_mapping = {
        "Low": 1.645,     # ~90% confidence
        "Normal": 1.96,   # ~95% confidence
        "High": 2.576,    # ~99% confidence
    }
    numeric_mapping = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }

    if isinstance(confidence, str):
        return sensitivity_mapping.get(confidence.capitalize(), 1.96)
    elif isinstance(confidence, (float, int)):
        return numeric_mapping.get(float(confidence), 1.96)
    else:
        raise ValueError(f"Unsupported confidence type: {confidence}")

def compute_group_metric(df: pd.DataFrame, metric: str, pattern_override: str = None) -> float:
    import re

    if metric == "num_rows":
        return len(df)

    if ":" not in metric:
        raise ValueError(f"Unsupported metric format: {metric}")

    metric_type, column = metric.split(":", 1)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataframe")

    if metric_type == "mean":
        return df[column].mean()
    elif metric_type == "median":
        return df[column].median()
    elif metric_type == "mode":
        return df[column].mode().iloc[0] if not df[column].mode().empty else None
    elif metric_type == "sum":
        return df[column].sum()
    elif metric_type == "min":
        return df[column].min()
    elif metric_type == "max":
        return df[column].max()
    elif metric_type == "stddev":
        return df[column].std()
    elif metric_type == "variance":
        return df[column].var()
    elif metric_type == "range":
        return df[column].max() - df[column].min()
    elif metric_type == "distinct_count":
        return df[column].nunique()
    elif metric_type == "null_pct":
        return df[column].isnull().mean() * 100
    elif metric_type == "null_count":
        return df[column].isnull().sum()
    elif metric_type == "non_null_count":
        return df[column].notnull().sum()
    elif metric_type == "empty_string_pct":
        return (df[column] == "").mean() * 100
    elif metric_type == "zero_pct":
        return (df[column] == 0).mean() * 100
    elif metric_type == "positive_pct":
        return (df[column] > 0).mean() * 100
    elif metric_type == "negative_pct":
        return (df[column] < 0).mean() * 100
    elif metric_type == "max_length":
        return df[column].astype(str).map(len).max()
    elif metric_type == "min_length":
        return df[column].astype(str).map(len).min()
    elif metric_type == "avg_length":
        return df[column].astype(str).map(len).mean()
    if metric_type == "distribution_change":
        current_dist = df[column].value_counts(normalize=True)
        return current_dist.to_dict()  # return the full distribution, not scalar yet
    elif metric_type == "pattern_match_pct":
        pattern_string = None
        if pattern_override:
            if pattern_override in BUILT_IN_PATTERNS:
                pattern_string = BUILT_IN_PATTERNS[pattern_override]
            else:
                pattern_string = pattern_override
        else:
            pattern_string = BUILT_IN_PATTERNS["email"]  # Default fallback

        pattern = re.compile(pattern_string)
        return df[column].astype(str).map(lambda x: bool(pattern.match(x))).mean() * 100
    elif metric_type == "duplicate_pct":
        return (df[column].duplicated(keep=False)).mean() * 100
    elif metric_type == "value_set":
        # The allowed values list must come from somewhere else (handled at check-time)
        raise NotImplementedError("value_set needs 'allowed_values' at runtime. Should not call compute_group_metric directly.")
    elif metric_type == "type_check":
        # The expected type must come from check config — not here
        raise NotImplementedError("type_check needs 'expected_type' at runtime. Should not call compute_group_metric directly.")
    else:
        raise ValueError(f"Unsupported metric type: {metric_type}")


def evaluate_static_threshold(latest_value, min_value=None, max_value=None) -> bool:
    if isinstance(min_value, str):
        min_value = datetime.fromisoformat(min_value)
    if isinstance(max_value, str):
        max_value = datetime.fromisoformat(max_value)

    if isinstance(latest_value, pd.Timestamp):
        latest_value = latest_value.to_pydatetime()
    elif isinstance(latest_value, datetime):
        pass
    else:
        latest_value = float(latest_value)

    if min_value is not None and latest_value < min_value:
        return False
    if max_value is not None and latest_value > max_value:
        return False
    return True

def get_historical_values(context, asset: str, metric: str, history: int, group_key: Optional[str] = None) -> List[float]:
    records = context.instance.get_event_records(
        EventRecordsFilter(event_type=DagsterEventType.ASSET_CHECK_EVALUATION, asset_key=AssetKey(asset)),
        limit=history,
    )
    values = []
    for record in records:
        check_result = record.asset_check_evaluation
        if group_key:
            if group_key in check_result.metadata and metric in check_result.metadata[group_key]:
                values.append(check_result.metadata[group_key][metric])
        else:
            if metric in check_result.metadata:
                values.append(check_result.metadata[metric].value)
    return values

# --- The refactored generator ---

def generate_asset_check_function(parsed_check: Dict[str, Any]):
    print(f"🔪 Registering check '{parsed_check['check_name']}' for asset: {parsed_check['asset']}")
    validate_check_config(parsed_check)

    asset = parsed_check["asset"]
    check_name = parsed_check["check_name"]
    check_type = parsed_check.get("type", "anomaly_detection")
    metric = parsed_check.get("metric")
    history = parsed_check.get("history", 10)
    threshold = parsed_check.get("threshold", 2.0)
    min_value = parsed_check.get("min")
    max_value = parsed_check.get("max")
    threshold_pct = parsed_check.get("threshold_pct")
    confidence = parsed_check.get("confidence", 0.95)
    where = parsed_check.get("where")
    group_by = parsed_check.get("group_by")
    allowed_failures = parsed_check.get("allowed_failures", 0)
    pattern_override = parsed_check.get("pattern")
    custom_sql = parsed_check.get("custom_sql")
    blocking = parsed_check.get("blocking")

    if not blocking:
        blocking = False  # Only set blocking=True if explicitly requested

    @asset_check(name=check_name, asset=AssetKey(asset.split(".")) if "." in asset else AssetKey(asset),blocking=blocking)
    def dynamic_check(context, asset_data):
        df_map = apply_filters(asset_data, where=where, group_by=group_by, time_range=parsed_check.get("time_range"))

        is_grouped = group_by is not None
        failures = []
        metadata = {}
        z = get_z_value(confidence)

        for group_key, df in df_map.items():
            value = None
            passed = True
            group_metadata = {
                "total_rows": len(df),
            }

            if check_type == "custom":
                if not custom_sql:
                    raise ValueError(f"Custom check requires 'custom_sql' field for {check_name}")
                sql_to_run = custom_sql
                time_column = parsed_check.get("time_column")
                context_vars = get_contextual_now(df, time_column)
                failing_rows = df.query(sql_to_run, local_dict=context_vars)
                value = len(failing_rows)
                group_metadata.update({
                    "custom_sql": custom_sql,
                    "rows_failing_condition": value,
                })

            elif check_type == "entropy_check":
                column = metric.split(":")[1]
                result = evaluate_entropy_check(asset_data, column, min_value, max_value)
                return result

            elif check_type == "benford_law":
                parts = metric.split(":", 1)
                column = parts[1] if len(parts) > 1 else parts[0]
                return evaluate_benford_law(asset_data, column, threshold=threshold)

            elif check_type == "benford_second_digit_law":
                column = metric.split(":", 1)[1]
                return evaluate_benford_second_digit(asset_data, column, threshold=threshold)

            elif check_type == "constant_value_check":
                column = metric.split(":")[1]
                most_common_pct = (df[column].value_counts(normalize=True).max()) * 100
                value = most_common_pct
                passed = most_common_pct <= (threshold_pct if threshold_pct is not None else 99.9)
                group_metadata.update({
                    "most_common_pct": most_common_pct,
                    "threshold_pct": threshold_pct,
                })

            elif check_type == "correlation_check":
                column_x = parsed_check.get("column_x")
                column_y = parsed_check.get("column_y")
                min_corr = parsed_check.get("min_correlation")
                max_corr = parsed_check.get("max_correlation")
                if column_x not in df.columns or column_y not in df.columns:
                    raise ValueError(f"Columns {column_x} and/or {column_y} not found in asset data.")
                corr = df[[column_x, column_y]].dropna().corr().iloc[0, 1]
                value = corr
                group_metadata.update({
                    "column_x": column_x,
                    "column_y": column_y,
                    "correlation": corr,
                    "min_correlation": min_corr,
                    "max_correlation": max_corr,
                })
                if min_corr is not None and corr < min_corr:
                    passed = False
                if max_corr is not None and corr > max_corr:
                    passed = False

            elif check_type == "value_set_check":
                column = metric.split(":")[1]
                allowed_values = parsed_check.get("allowed_values")
                if not allowed_values:
                    raise ValueError(f"value_set_check requires 'allowed_values' field for {check_name}")
                valid_pct = (df[column].isin(allowed_values)).mean() * 100
                value = valid_pct
                passed = valid_pct >= (min_value if min_value is not None else 100)
                group_metadata.update({
                    "allowed_values": allowed_values,
                    "valid_pct": valid_pct,
                })

            elif check_type == "type_check":
                column = metric.split(":")[1]
                expected_type = parsed_check.get("expected_type")
                if not expected_type:
                    raise ValueError(f"type_check requires 'expected_type' field for {check_name}")
                if expected_type == "timestamp":
                    valid = pd.api.types.is_datetime64_any_dtype(df[column])
                elif expected_type == "int":
                    valid = pd.api.types.is_integer_dtype(df[column])
                elif expected_type == "float":
                    valid = pd.api.types.is_float_dtype(df[column])
                elif expected_type == "string":
                    valid = pd.api.types.is_string_dtype(df[column])
                elif expected_type == "bool":
                    valid = pd.api.types.is_bool_dtype(df[column])
                else:
                    raise ValueError(f"Unsupported expected_type: {expected_type}")
                value = bool(valid)
                passed = value
                group_metadata.update({
                    "expected_type": expected_type,
                    "type_valid": value,
                })

            # Compute metric if not already set
            if value is None and metric and check_type in ("static_threshold", "percent_delta", "anomaly_detection", "predicted_range"):
                value = compute_group_metric(df, metric, pattern_override=pattern_override)


            # Step 2: Evaluate historical logic
            if check_type not in ("constant_value_check","correlation_check", "value_set_check", "type_check", "custom"):
                hist_values = get_historical_values(context, asset, metric if check_type != "custom" else "num_failing_rows", history, group_key if is_grouped else None)

                if metric and metric.startswith("distribution_change:") and value is not None:
                    current_dist = pd.Series(value)
                    if hist_values:
                        historical = [pd.Series(hist) for hist in hist_values]
                        avg_hist = sum(historical) / len(historical)
                        all_keys = current_dist.index.union(avg_hist.index)
                        tvd = (current_dist.reindex(all_keys, fill_value=0) - avg_hist.reindex(all_keys, fill_value=0)).abs().sum() / 2.0
                        value = tvd
                    else:
                        value = 0.0
                    group_metadata.update({"distribution_tvd": value})

                if check_type == "static_threshold":
                    if value is None:
                        passed = False
                        group_metadata.update({"note": f"Metric value missing for '{check_name}'"})
                    else:
                        passed = evaluate_static_threshold(value, min_value=min_value, max_value=max_value)
                        group_metadata.update({
                            "min_threshold": min_value,
                            "max_threshold": max_value,
                        })

                elif check_type == "percent_delta":
                    if value is None:
                        passed = False
                        group_metadata.update({"note": f"Metric value missing for '{check_name}'"})
                    elif hist_values:
                        prev = hist_values[0]
                        delta_pct = abs(value - prev) / prev * 100 if prev else float("inf")
                        passed = delta_pct <= threshold_pct
                        group_metadata.update({
                            "previous": prev,
                            "latest": value,
                            "delta_pct": delta_pct,
                            "threshold_pct": threshold_pct,
                        })
                    else:
                        group_metadata.update({"note": "No prior value"})

                elif check_type == "anomaly_detection":
                    if value is None:
                        passed = False
                        group_metadata.update({"note": f"Metric value missing for '{check_name}'"})
                    elif len(hist_values) >= history:
                        mean = statistics.mean(hist_values)
                        stdev = statistics.stdev(hist_values)
                        lower = mean - threshold * stdev
                        upper = mean + threshold * stdev
                        passed = lower <= value <= upper
                        group_metadata.update({
                            "mean": mean,
                            "stdev": stdev,
                            "lower": lower,
                            "upper": upper,
                            "threshold_multiplier": threshold,
                        })
                    else:
                        group_metadata.update({"note": "Not enough history"})

                elif check_type == "predicted_range":
                    if value is None:
                        passed = False
                        group_metadata.update({"note": f"Metric value missing for '{check_name}'"})
                    elif len(hist_values) >= history:
                        X = np.arange(len(hist_values)).reshape(-1, 1)
                        y = np.array(hist_values)
                        model = LinearRegression().fit(X, y)
                        pred = model.predict(np.array([[len(hist_values)]])).item()
                        stdev = statistics.stdev(hist_values)
                        lower = pred - z * stdev
                        upper = pred + z * stdev
                        passed = lower <= value <= upper
                        group_metadata.update({
                            "predicted": pred,
                            "lower": lower,
                            "upper": upper,
                            "confidence_level": confidence,
                        })
                    else:
                        group_metadata.update({"note": "Not enough history"})
                else:
                    raise ValueError(f"Unsupported check type: {check_type}")

            group_metadata["passed"] = bool(passed)

            # Convert numpy types to native types
            for k, v in group_metadata.items():
                if isinstance(v, (np.integer, np.floating, np.bool_)):
                    group_metadata[k] = v.item()

            metadata[group_key] = group_metadata

            if not passed:
                failures.append(group_key)

        overall_passed = len(failures) <= allowed_failures

        if is_grouped:
            return AssetCheckResult(
                passed=overall_passed,
                metadata={
                    "group_results": metadata,
                    "failures": failures,
                    "allowed_failures": allowed_failures,
                },
            )
        else:
            return AssetCheckResult(
                passed=overall_passed,
                metadata=metadata["__all__"],
            )



    print(f"Finished defining check: {check_name}")
    return dynamic_check