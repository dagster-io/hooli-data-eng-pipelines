# Dynamic Asset Checks Framework

This project provides a flexible, extensible system for defining and evaluating **data quality checks** dynamically, based on YAML configuration.

Checks are applied to Dagster assets, leveraging Pandas for evaluation and supporting a wide variety of conditions, metrics, and patterns — including **custom SQL, predictive anomaly detection, correlation checks, value set validations, and type checks**.

✅ Easy YAML configuration  
✅ Grouped or non-grouped checks  
✅ Optional blocking of downstream materialization  
✅ Dynamic time window filtering (days, hours, minutes)  
✅ Built-in pattern matching for common field types

---

## ✨ How It Works

- Define your checks in YAML (one or many per asset).
- Checks automatically register as Dagster `asset_check` functions.
- Checks support dynamic filtering, historical evaluation, and rich metadata output.
- You can enforce static thresholds, anomaly detection, predicted values, field patterns, and more.

---

## 🛠 YAML Configuration Format

Each check block follows this structure:

| Field | Required? | Description |
|:---|:---|:---|
| `asset` | ✅ | Name of the asset (e.g., `RAW_DATA.users`) |
| `check_name` | ✅ | Unique name for the check |
| `type` | ✅ | Type of check (`static_threshold`, `percent_delta`, `anomaly_detection`, `predicted_range`, `custom`, `correlation_check`, `value_set_check`, `type_check`, `freshness`) |
| `metric` | ✅* | Metric to compute (e.g., `mean:revenue`, `null_pct:email`) |
| `pattern` | Optional | For `pattern_match_pct`, use a built-in pattern or custom regex |
| `allowed_values` | Optional | For `value_set_check`, list of valid field values |
| `expected_type` | Optional | For `type_check`, expected field type (`int`, `float`, `string`, `timestamp`) |
| `threshold` | Optional | Static or anomaly threshold |
| `threshold_pct` | Optional | For percent_delta checks |
| `min` / `max` | Optional | Static minimum or maximum allowed value |
| `history` | Optional | How much historical data to retrieve (for anomalies, predictions) |
| `confidence` | Optional | Prediction confidence (0.9, 0.95, 0.99) or sensitivity (`Low`, `Normal`, `High`) |
| `where` | Optional | SQL-like filter to apply before evaluating the check |
| `group_by` | Optional | Group checks by a column's values |
| `allowed_failures` | Optional | Allowed number of groups that can fail |
| `blocking` | Optional | Prevent downstream materialization if check fails |
| `custom_sql` | Optional | Custom query condition (rows violating this are counted) |
| `time_range` | Optional | Dynamic time filtering (last N days, hours, minutes) |

---

## 📚 Supported Metric Types

| Metric | Meaning |
|:---|:---|
| `num_rows` | Number of rows |
| `null_pct:col` | Percent NULL in column |
| `null_count:col` | Raw NULL count |
| `non_null_count:col` | Non-NULL row count |
| `distinct_count:col` | Unique values count |
| `mean:col`, `median:col`, `mode:col` | Statistical metrics |
| `sum:col`, `min:col`, `max:col`, `stddev:col`, `variance:col` | Aggregates |
| `range:col` | Max - Min |
| `positive_pct:col`, `negative_pct:col`, `zero_pct:col` | Value sign analysis |
| `pattern_match_pct:col` | Pattern conformance |
| `duplicate_pct:col` | Percent duplicated values |
| `max_length:col`, `min_length:col`, `avg_length:col` | String length stats |
| `distribution_change:col` | Field value distribution change |

---

## 🧠 Built-In Pattern Names (for `pattern` field)

| Pattern | Meaning |
|:---|:---|
| `email` | Email address validation |
| `uuid` | UUID format |
| `zip_code` | US ZIP code (5 digits, optional 4-digit extension) |
| `us_state_code` | Two-letter US State abbreviations |
| `us_phone_number` | US phone numbers with or without formatting |
| `us_ssn` | US Social Security Number (`123-45-6789`) |
| `credit_card` | Visa, MasterCard, Amex, Discover formats |
| `ipv4` | IPv4 address (`192.168.0.1`) |
| `ipv6` | IPv6 address |
| `mac_address` | MAC address |
| `iso_date` | ISO Date format (`YYYY-MM-DD`) |
| `iso_datetime` | ISO DateTime (`YYYY-MM-DDTHH:MM:SS`) |
| `hex_color` | Hexadecimal color (`#FFFFFF`) |

---

## 📋 Example YAML Snippet

```yaml
checks:

  # Validate new users in the last 7 days
  - asset: RAW_DATA.users
    check_name: new_users_last_7_days
    type: static_threshold
    metric: num_rows
    time_range:
      column: created_at
      days_back: 7
    min: 1000
    blocking: true

  # Check valid email formats
  - asset: RAW_DATA.users
    check_name: valid_email_format_check
    type: static_threshold
    metric: pattern_match_pct:email_address
    pattern: email
    min: 90

  # Ensure order IDs are UUIDs
  - asset: RAW_DATA.orders
    check_name: order_id_uuid_format_check
    type: static_threshold
    metric: pattern_match_pct:order_id
    pattern: uuid
    min: 99

  # Check correlation between subtotal and tax
  - asset: RAW_DATA.orders
    check_name: subtotal_to_tax_correlation
    type: correlation_check
    column_x: subtotal
    column_y: tax_charged
    min_correlation: 0.8

  # Validate data types
  - asset: RAW_DATA.users
    check_name: created_at_must_be_timestamp
    type: type_check
    metric: type_check:created_at
    expected_type: timestamp
