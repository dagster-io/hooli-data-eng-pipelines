"""Enhanced Data Quality Checks with Automatic Processing Mode Selection.

Simplified API:
- data_source_type: "database" or "dataframe" (WHERE data comes from)
- Auto-detects whether to use SQL or fetch-to-dataframe (HOW to process)
- Auto-selects pandas/polars based on data size (IMPLEMENTATION DETAIL)
"""

from dataclasses import dataclass
from typing import Optional, Literal, List, Dict, Any, Union
import dagster as dg
from dagster import AssetKey, asset_check, AssetCheckResult, AssetCheckExecutionContext, MetadataValue, DagsterEventType, EventRecordsFilter
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import json
import os

import re
from scipy import stats
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# ENUMS FOR TYPE SAFETY AND BETTER DOCUMENTATION
# ═══════════════════════════════════════════════════════════════

class ComparisonOperator(str, Enum):
    """Comparison operators for validation checks."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class CorrelationMethod(str, Enum):
    """Statistical correlation methods."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"


class PredictionMethod(str, Enum):
    """Methods for time series prediction."""
    MOVING_AVERAGE = "moving_average"
    LINEAR_REGRESSION = "linear_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ARIMA = "arima"


class StatisticalTestMethod(str, Enum):
    """Statistical test methods for distribution analysis."""
    KS_TEST = "ks_test"
    CHI_SQUARE = "chi_square"


class AnomalyDetectionMethod(str, Enum):
    """Methods for anomaly detection."""
    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"


class ValidationType(str, Enum):
    """Types of cross-table validation."""
    ROW_COUNT = "row_count"
    COLUMN_VALUES = "column_values"
    AGGREGATE = "aggregate"


class AggregateFunction(str, Enum):
    """SQL aggregate functions."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


class DataSourceType(str, Enum):
    """Data source types for processing mode selection."""
    DATABASE = "database"
    DATAFRAME = "dataframe"


class SampleMethod(str, Enum):
    """Data sampling methods."""
    RANDOM = "random"
    TOP = "top"


# ═══════════════════════════════════════════════════════════════
# CHECK CONFIGURATION MODELS (Pydantic models for type safety)
# ═══════════════════════════════════════════════════════════════

class BaseCheckConfig(BaseModel):
    """Base configuration for all checks."""
    group_by: Optional[str] = Field(None, description="Column to group by for analysis")
    allowed_failures: int = Field(0, description="Number of groups allowed to fail")
    blocking: bool = Field(False, description="Whether this check is blocking (fails the pipeline)")
    name: Optional[str] = Field(None, description="Custom name for this check")


class RowCountCheckConfig(BaseCheckConfig):
    """Configuration for row count checks."""
    min_rows: int = Field(1, description="Minimum number of rows expected")
    max_rows: Optional[int] = Field(None, description="Maximum number of rows expected")


class NullCheckConfig(BaseCheckConfig):
    """Configuration for null value checks."""
    columns: List[str] = Field(..., description="Columns to check for null values")


class StaticThresholdConfig(BaseCheckConfig):
    """Configuration for static threshold checks."""
    metric: str = Field("num_rows", description="Metric to check (num_rows, sum, avg, etc.)")
    min_value: Optional[float] = Field(None, description="Minimum expected value")
    max_value: Optional[float] = Field(None, description="Maximum expected value")


class BenfordLawConfig(BaseCheckConfig):
    """Configuration for Benford's Law checks."""
    column: str = Field(..., description="Column to analyze for Benford's Law")
    threshold: float = Field(0.05, description="Significance threshold for the test")
    digit_position: int = Field(1, description="Digit position to analyze (1=first, 2=second, 12=first two)")
    min_samples: int = Field(100, description="Minimum samples required for reliable test")


class EntropyAnalysisConfig(BaseCheckConfig):
    """Configuration for entropy analysis checks."""
    column: str = Field(..., description="Column to analyze for entropy")
    min_entropy: Optional[float] = Field(None, description="Minimum expected entropy")
    max_entropy: Optional[float] = Field(None, description="Maximum expected entropy")


class CorrelationCheckConfig(BaseCheckConfig):
    """Configuration for correlation checks."""
    column_x: str = Field(..., description="First column for correlation analysis")
    column_y: str = Field(..., description="Second column for correlation analysis")
    min_correlation: Optional[float] = Field(None, description="Minimum expected correlation")
    max_correlation: Optional[float] = Field(None, description="Maximum expected correlation")
    method: CorrelationMethod = Field(CorrelationMethod.PEARSON, description="Correlation method")


class ValueSetValidationConfig(BaseCheckConfig):
    """Configuration for value set validation checks."""
    column: str = Field(..., description="Column to validate")
    allowed_values: List[str] = Field(..., description="Allowed values for the column")
    min_pct: float = Field(95.0, description="Minimum percentage of values that should be in allowed set")


class PatternMatchingConfig(BaseCheckConfig):
    """Configuration for pattern matching checks."""
    column: str = Field(..., description="Column to check for patterns")
    regex_pattern: Optional[str] = Field(None, description="Custom regex pattern")
    preset: Optional[str] = Field(None, description="Preset pattern (email, phone, etc.)")
    match_percentage: float = Field(95.0, description="Minimum percentage of values that should match")


class DataTypeCheckConfig(BaseCheckConfig):
    """Configuration for data type validation checks."""
    columns: List[Dict[str, str]] = Field(..., description="Column name and expected data type pairs")


class RangeCheckConfig(BaseCheckConfig):
    """Configuration for range validation checks."""
    columns: List[Dict[str, Any]] = Field(..., description="Column configurations with min/max values")


class UniquenessCheckConfig(BaseCheckConfig):
    """Configuration for uniqueness validation checks."""
    columns: List[Dict[str, Any]] = Field(..., description="Column configurations for uniqueness checks")


class PredictedRangeConfig(BaseCheckConfig):
    """Configuration for predicted range checks."""
    metric: str = Field(..., description="Metric to predict")
    method: PredictionMethod = Field(PredictionMethod.MOVING_AVERAGE, description="Prediction method")
    confidence: float = Field(0.95, description="Confidence level for prediction")
    history: int = Field(10, description="Number of historical data points to use")


class PercentDeltaConfig(BaseCheckConfig):
    """Configuration for percent delta checks."""
    metric: str = Field(..., description="Metric to compare")
    max_delta: float = Field(..., description="Maximum allowed percent change")
    history: int = Field(10, description="Number of historical data points to use")


class DistributionChangeConfig(BaseCheckConfig):
    """Configuration for distribution change checks."""
    metric: str = Field(..., description="Metric to analyze")
    method: StatisticalTestMethod = Field(StatisticalTestMethod.KS_TEST, description="Statistical test method")
    significance_level: float = Field(0.05, description="Significance level for the test")


class AnomalyDetectionConfig(BaseCheckConfig):
    """Configuration for anomaly detection checks."""
    metric: str = Field(..., description="Metric to analyze for anomalies")
    method: AnomalyDetectionMethod = Field(AnomalyDetectionMethod.Z_SCORE, description="Anomaly detection method")
    threshold: float = Field(2.0, description="Threshold for anomaly detection")
    history: int = Field(10, description="Number of historical data points to use")


class CrossTableValidationConfig(BaseCheckConfig):
    """Configuration for cross-table validation checks."""
    source_table: str = Field(..., description="Source table name")
    source_database: Optional[str] = Field(None, description="Source database resource key")
    join_columns: List[str] = Field(..., description="Columns to join on between source and destination")
    validation_type: ValidationType = Field(ValidationType.ROW_COUNT, description="Type of validation")
    aggregate_column: Optional[str] = Field(None, description="Column to aggregate (for aggregate validation)")
    aggregate_function: AggregateFunction = Field(AggregateFunction.SUM, description="Aggregate function")


class CustomSqlCheckConfig(BaseModel):
    """Configuration for custom SQL checks."""
    sql_query: str = Field(..., description="SQL query to execute")
    expected_result: Optional[Any] = Field(None, description="Expected result from the query")
    comparison: ComparisonOperator = Field(ComparisonOperator.EQUALS, description="Comparison operator")
    name: Optional[str] = Field(None, description="Custom name for this check")


class DataframeQueryCheckConfig(BaseModel):
    """Configuration for dataframe query checks."""
    query: str = Field(..., description="Dataframe query to execute")
    expected_result: Optional[Any] = Field(None, description="Expected result from the query")
    comparison: ComparisonOperator = Field(ComparisonOperator.EQUALS, description="Comparison operator")
    name: Optional[str] = Field(None, description="Custom name for this check")


class CustomDataframeCheckConfig(BaseModel):
    """Configuration for custom dataframe checks."""
    python_code: str = Field(..., description="Python code to execute on the dataframe")
    expected_result: Optional[Any] = Field(None, description="Expected result from the code")
    comparison: ComparisonOperator = Field(ComparisonOperator.EQUALS, description="Comparison operator")
    name: Optional[str] = Field(None, description="Custom name for this check")


class EnhancedDataQualityChecks(dg.Component, dg.Model, dg.Resolvable):
    """Enhanced data quality component with automatic processing mode selection.
    
    Key Design Principles:
    1. data_source_type only indicates WHERE data comes from
    2. Component automatically chooses SQL vs dataframe processing
    3. Pandas/Polars selection is automatic (never in YAML)
    4. Same YAML works for both simple and complex checks
    5. Uses nested YAML structure for clean, intuitive configuration
    """
    
    # Basic configuration - ONLY about data location
    assets: Optional[Dict[str, Any]] = Field(None, description="Multi-asset configuration dictionary")
    data_source_type: Optional[DataSourceType] = Field(None, description="Source of data: 'database' for SQL queries or 'dataframe' for pandas/polars dataframes")
    
    # Database-specific (when data_source_type="database")
    table_name: Optional[str] = Field(None, description="Database table name to query (e.g., 'schema.table_name')")
    database_resource_key: Optional[str] = Field(None, description="Dagster resource key for database connection (e.g., 'duckdb', 'postgres')")
    
    # Environment-aware configuration (optional - overrides table_name and database_resource_key)
    table_name_targets: Optional[Dict[str, str]] = Field(None, description="Environment-specific table names (e.g., {'dev': 'dev_table', 'prod': 'prod_table'})")
    database_resource_key_targets: Optional[Dict[str, str]] = Field(None, description="Environment-specific database resource keys (e.g., {'dev': 'dev_db', 'prod': 'prod_db'})")
    
    # Data sampling (for performance on large datasets)
    sample_size: Optional[int] = Field(None, description="Number of rows to sample for analysis (improves performance on large datasets)")
    sample_method: SampleMethod = Field(SampleMethod.RANDOM, description="Sampling method: 'random' for random sampling or 'top' for first N rows")
    
    # ═══════════════════════════════════════════════════════════════
    # WHERE CLAUSE FILTERING (Applied to all checks when possible)
    # ═══════════════════════════════════════════════════════════════
    where_clause: Optional[str] = Field(None, description="Custom SQL WHERE clause to filter data before analysis")
    time_filter_column: Optional[str] = Field(None, description="Column name for time-based filtering (used with hours_back/days_back)")
    hours_back: Optional[int] = Field(None, description="Filter data to last N hours (requires time_filter_column)")
    days_back: Optional[int] = Field(None, description="Filter data to last N days (requires time_filter_column)")

    # ═══════════════════════════════════════════════════════════════
    # NESTED CHECK CONFIGURATIONS (Support for multiple checks)
    # ═══════════════════════════════════════════════════════════════
    # Support for multiple custom SQL and dataframe query checks
    custom_sql_check: Optional[List[CustomSqlCheckConfig]] = Field(None, description="List of custom SQL checks to execute against the database")
    dataframe_query_check: Optional[List[DataframeQueryCheckConfig]] = Field(None, description="List of dataframe query checks to execute on pandas/polars dataframes")
    custom_dataframe_check: Optional[List[CustomDataframeCheckConfig]] = Field(None, description="List of custom Python code checks to execute on dataframes")
    
    # Nested check configurations for all check types
    row_count_check: Optional[List[RowCountCheckConfig]] = Field(None, description="List of row count validation checks (min/max rows, grouping)")
    null_check: Optional[List[NullCheckConfig]] = Field(None, description="List of null value checks for specified columns")
    static_threshold: Optional[List[StaticThresholdConfig]] = Field(None, description="List of static threshold checks for metrics (min/max values)")
    benford_law: Optional[List[BenfordLawConfig]] = Field(None, description="List of Benford's Law analysis checks for numerical distributions")
    entropy_analysis: Optional[List[EntropyAnalysisConfig]] = Field(None, description="List of Shannon entropy analysis checks for data diversity")
    correlation_check: Optional[List[CorrelationCheckConfig]] = Field(None, description="List of correlation analysis checks between column pairs")
    value_set_validation: Optional[List[ValueSetValidationConfig]] = Field(None, description="List of value set validation checks (allowed values for columns)")
    pattern_matching: Optional[List[PatternMatchingConfig]] = Field(None, description="List of regex pattern matching checks for text columns")
    data_type_check: Optional[List[DataTypeCheckConfig]] = Field(None, description="List of data type validation checks for columns")
    range_check: Optional[List[RangeCheckConfig]] = Field(None, description="List of range validation checks (min/max values for columns)")
    uniqueness_check: Optional[List[UniquenessCheckConfig]] = Field(None, description="List of uniqueness validation checks for column combinations")
    predicted_range: Optional[List[PredictedRangeConfig]] = Field(None, description="List of predicted range checks using historical data")
    percent_delta: Optional[List[PercentDeltaConfig]] = Field(None, description="List of percent delta checks comparing current vs historical values")
    distribution_change: Optional[List[DistributionChangeConfig]] = Field(None, description="List of distribution change checks using statistical tests")
    anomaly_detection: Optional[List[AnomalyDetectionConfig]] = Field(None, description="List of anomaly detection checks using various algorithms")
    cross_table_validation: Optional[List[CrossTableValidationConfig]] = Field(None, description="List of cross-table validation checks between source and destination tables")
    

    def __init__(self, **kwargs):
        """Initialize the component and resolve environment configuration."""
        # Call parent __init__ if it exists
        super().__init__(**kwargs)
        
        # Resolve environment-aware configuration
        self._resolve_environment_config()

    def __post_init__(self):
        """Post-initialization processing."""
        print(f"__post_init__ called for component with asset_key: {getattr(self, '_asset_name', 'N/A')}")
        
        # Apply intelligent defaults for table_name if asset_key follows schema.table pattern
        if hasattr(self, '_asset_name') and self._asset_name and '.' in self._asset_name and not self.table_name:
            self.table_name = self._asset_name
        

        
        # Set default data_source_type if not provided
        if self.data_source_type is None:
            # If no database resource is specified, default to dataframe mode
            if not self.database_resource_key_targets and self.database_resource_key == "duckdb":
                self.data_source_type = "dataframe"
            else:
                self.data_source_type = "database"
        
        # Validate configuration (but allow intelligent defaults to handle table_name)
        if self.data_source_type == "database" and not self.table_name and not getattr(self, '_asset_name', None):
            raise ValueError("table_name is required when data_source_type is 'database' and no asset_key is provided")

    def _resolve_environment_config(self):
        """Resolve environment-aware configuration based on deployment environment."""
        deployment_name = os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "")
        is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
        
        # Determine the target environment with explicit logic
        if is_branch_depl:
            # Branch deployment (takes precedence over deployment name)
            target = "branch"
        elif deployment_name:
            # All other deployments use their actual deployment name as target
            target = deployment_name
        else:
            # No deployment name and not a branch deployment = local development
            target = "local"
        
                # Resolve table_name from targets if available
        if self.table_name_targets and target in self.table_name_targets:
            self.table_name = self.table_name_targets[target]
        # If no table_name_targets or target not found, preserve the intelligent default
        # (table_name should already be set from __post_init__ if asset key follows schema.table pattern)
        
        # Resolve database_resource_key from targets if available
        if self.database_resource_key_targets and target in self.database_resource_key_targets:
            self.database_resource_key = self.database_resource_key_targets[target]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        """Build asset check definitions with automatic processing mode selection."""
        
        # Process multiple assets
        all_asset_checks = []
        for asset_name, asset_config in self.assets.items():
            # Create a temporary component instance for this asset
            temp_component = self._create_asset_component(asset_name, asset_config)
            asset_checks = temp_component._build_single_asset_checks()
            all_asset_checks.extend(asset_checks)
        return dg.Definitions(asset_checks=all_asset_checks)

    def _create_asset_component(self, asset_name: str, asset_config: dict):
        """Create a temporary component instance for a single asset."""
        
        # Get configuration values
        data_source_type = asset_config.get('data_source_type', 'database')
        table_name = asset_config.get('table_name')
        
        # Apply intelligent defaults for table_name if asset_name follows schema.table pattern
        if asset_name and '.' in asset_name and not table_name:
            table_name = asset_name
        
        # Set default data_source_type if not provided
        if data_source_type is None:
            # If no database resource is specified, default to dataframe mode
            database_resource_key = asset_config.get('database_resource_key')
            if not database_resource_key and not asset_config.get('database_resource_key_targets'):
                data_source_type = "dataframe"
            else:
                data_source_type = "database"
        
        # Create a new instance with the asset configuration
        component_data = {
            'data_source_type': data_source_type,
            'table_name': table_name,
            'sample_size': asset_config.get('sample_size'),
            'sample_method': asset_config.get('sample_method', 'random'),
            'where_clause': asset_config.get('where_clause'),
            'time_filter_column': asset_config.get('time_filter_column'),
            'hours_back': asset_config.get('hours_back'),
            'days_back': asset_config.get('days_back'),
            # Environment-aware configuration
            'table_name_targets': asset_config.get('table_name_targets'),
            'database_resource_key_targets': asset_config.get('database_resource_key_targets'),
        }
        
        # Only add database_resource_key if it's explicitly provided
        if asset_config.get('database_resource_key'):
            component_data['database_resource_key'] = asset_config.get('database_resource_key')
        
        # Process nested check configurations
        for check_name, check_config in asset_config.items():
            if check_name not in ['data_source_type', 'table_name', 'database_resource_key', 
                                'sample_size', 'sample_method', 'where_clause', 'time_filter_column', 
                                'hours_back', 'days_back', 'table_name_targets', 'database_resource_key_targets']:
                # This is a nested check configuration, apply directly
                if isinstance(check_config, dict):
                    self._apply_nested_check_config(component_data, check_name, check_config)
                else:
                    # Direct field assignment (for backward compatibility)
                    component_data[check_name] = check_config
        
        # Create a new instance with this data
        new_component = type(self)(**component_data)
        
        # Store the asset name and asset key for use in creating asset checks
        new_component._asset_name = asset_name
        new_component._asset_key = AssetKey(asset_name.split('.')) if '.' in asset_name else AssetKey([asset_name])
        
        # Set flat field names as attributes for backward compatibility
        for key, value in component_data.items():
            if hasattr(new_component, key):
                # If the field exists in the model, it's already set
                continue
            else:
                # Set as attribute for backward compatibility
                setattr(new_component, key, value)
        
        # Ensure environment resolution happens for the new component
        new_component._resolve_environment_config()
        
        return new_component

    def _apply_nested_check_config(self, component_data: dict, check_name: str, check_config: dict):
        """Apply nested check configuration directly to component fields."""
        # Handle special cases for custom_sql_check, dataframe_query_check, and custom_dataframe_check that support lists
        if check_name in ['custom_sql_check', 'dataframe_query_check', 'custom_dataframe_check']:
            # Support both single dict and list of dicts
            if check_name not in component_data:
                component_data[check_name] = []
            if isinstance(check_config, list):
                component_data[check_name].extend(check_config)
            else:
                component_data[check_name].append(check_config)
            return
            
        # Enable the check by default if not specified
        enable_key = f'enable_{check_name}'
        component_data[enable_key] = check_config.get('enable', True)
        
        # Map fields based on check type
        if check_name == 'row_count_check':
            if 'min_rows' in check_config:
                component_data['min_rows'] = check_config['min_rows']
            if 'max_rows' in check_config:
                component_data['max_rows'] = check_config['max_rows']
            if 'group_by' in check_config:
                component_data['row_count_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['row_count_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['row_count_blocking'] = check_config['blocking']
                
        elif check_name == 'null_check':
            if 'columns' in check_config:
                component_data['null_check_columns'] = check_config['columns']
            if 'group_by' in check_config:
                component_data['null_check_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['null_check_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['null_check_blocking'] = check_config['blocking']
                
        elif check_name == 'static_threshold':
            if 'metric' in check_config:
                component_data['static_threshold_metric'] = check_config['metric']
            if 'min_value' in check_config:
                component_data['static_threshold_min'] = check_config['min_value']
            if 'max_value' in check_config:
                component_data['static_threshold_max'] = check_config['max_value']
            if 'group_by' in check_config:
                component_data['static_threshold_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['static_threshold_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['static_threshold_blocking'] = check_config['blocking']
                
        elif check_name == 'pattern_matching':
            if 'column' in check_config:
                component_data['pattern_column'] = check_config['column']
            if 'regex_pattern' in check_config:
                component_data['pattern_regex'] = check_config['regex_pattern']
            elif 'regex' in check_config:
                component_data['pattern_regex'] = check_config['regex']
            if 'preset' in check_config:
                component_data['pattern_preset'] = check_config['preset']
            if 'group_by' in check_config:
                component_data['pattern_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['pattern_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['pattern_blocking'] = check_config['blocking']
                
        elif check_name == 'data_type_check':
            if 'columns' in check_config:
                component_data['data_type_columns'] = check_config['columns']
            if 'group_by' in check_config:
                component_data['data_type_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['data_type_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['data_type_blocking'] = check_config['blocking']
                
        elif check_name == 'range_check':
            if 'columns' in check_config:
                component_data['range_columns'] = check_config['columns']
            if 'group_by' in check_config:
                component_data['range_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['range_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['range_blocking'] = check_config['blocking']
                
        elif check_name == 'percent_delta':
            if 'metric' in check_config:
                component_data['percent_delta_metric'] = check_config['metric']
            if 'threshold' in check_config:
                component_data['percent_delta_threshold'] = check_config['threshold']
            if 'history' in check_config:
                component_data['percent_delta_history'] = check_config['history']
            if 'group_by' in check_config:
                component_data['percent_delta_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['percent_delta_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['percent_delta_blocking'] = check_config['blocking']
                
        elif check_name == 'anomaly_detection':
            if 'metric' in check_config:
                component_data['anomaly_detection_metric'] = check_config['metric']
            if 'threshold' in check_config:
                component_data['anomaly_detection_threshold'] = check_config['threshold']
            if 'history' in check_config:
                component_data['anomaly_detection_history'] = check_config['history']
            if 'group_by' in check_config:
                component_data['anomaly_detection_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['anomaly_detection_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['anomaly_detection_blocking'] = check_config['blocking']
                
        elif check_name == 'value_set_validation':
            if 'column' in check_config:
                component_data['value_set_column'] = check_config['column']
            if 'allowed_values' in check_config:
                component_data['value_set_allowed_values'] = check_config['allowed_values']
            if 'group_by' in check_config:
                component_data['value_set_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['value_set_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['value_set_blocking'] = check_config['blocking']
                
        elif check_name == 'uniqueness_check':
            if 'columns' in check_config:
                component_data['uniqueness_columns'] = check_config['columns']
            if 'group_by' in check_config:
                component_data['uniqueness_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['uniqueness_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['uniqueness_blocking'] = check_config['blocking']
                
        elif check_name == 'custom_sql_check':
            if 'query' in check_config:
                component_data['custom_sql_query'] = check_config['query']
            if 'expected_result' in check_config:
                component_data['custom_sql_expected_result'] = check_config['expected_result']
            if 'comparison' in check_config:
                component_data['custom_sql_comparison'] = check_config['comparison']
            if 'group_by' in check_config:
                component_data['custom_sql_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['custom_sql_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['custom_sql_blocking'] = check_config['blocking']
            if 'description' in check_config:
                component_data['custom_sql_description'] = check_config['description']
                
        elif check_name == 'dataframe_query_check':
            if 'query' in check_config:
                component_data['dataframe_query'] = check_config['query']
            if 'expected_result' in check_config:
                component_data['dataframe_query_expected_result'] = check_config['expected_result']
            if 'comparison' in check_config:
                component_data['dataframe_query_comparison'] = check_config['comparison']
            if 'group_by' in check_config:
                component_data['dataframe_query_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['dataframe_query_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['dataframe_query_blocking'] = check_config['blocking']
            if 'description' in check_config:
                component_data['dataframe_query_description'] = check_config['description']
                
        elif check_name == 'custom_dataframe_check':
            if 'query' in check_config:
                component_data['custom_dataframe_query'] = check_config['query']
            if 'expected_result' in check_config:
                component_data['custom_dataframe_expected_result'] = check_config['expected_result']
            if 'comparison' in check_config:
                component_data['custom_dataframe_comparison'] = check_config['comparison']
            if 'group_by' in check_config:
                component_data['custom_dataframe_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['custom_dataframe_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['custom_dataframe_blocking'] = check_config['blocking']
            if 'description' in check_config:
                component_data['custom_dataframe_description'] = check_config['description']
                
        elif check_name == 'cross_table_validation':
            if 'source_table' in check_config:
                component_data['cross_table_source_table'] = check_config['source_table']
            if 'source_database' in check_config:
                component_data['cross_table_source_database'] = check_config['source_database']
            if 'join_columns' in check_config:
                component_data['cross_table_join_columns'] = check_config['join_columns']
            if 'validation_type' in check_config:
                component_data['cross_table_validation_type'] = check_config['validation_type']
            if 'aggregate_column' in check_config:
                component_data['cross_table_aggregate_column'] = check_config['aggregate_column']
            if 'aggregate_function' in check_config:
                component_data['cross_table_aggregate_function'] = check_config['aggregate_function']
            if 'tolerance' in check_config:
                component_data['cross_table_tolerance'] = check_config['tolerance']
            if 'group_by' in check_config:
                component_data['cross_table_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['cross_table_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['cross_table_blocking'] = check_config['blocking']
            if 'description' in check_config:
                component_data['cross_table_description'] = check_config['description']
                
        elif check_name == 'benford_law':
            if 'column' in check_config:
                component_data['benford_column'] = check_config['column']
            if 'threshold' in check_config:
                component_data['benford_threshold'] = check_config['threshold']
            if 'digit_position' in check_config:
                component_data['benford_digit_position'] = check_config['digit_position']
            if 'min_samples' in check_config:
                component_data['benford_min_samples'] = check_config['min_samples']
            if 'group_by' in check_config:
                component_data['benford_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['benford_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['benford_law_blocking'] = check_config['blocking']
                
        elif check_name == 'entropy_analysis':
            if 'column' in check_config:
                component_data['entropy_column'] = check_config['column']
            if 'min_entropy' in check_config:
                component_data['entropy_min'] = check_config['min_entropy']
            if 'max_entropy' in check_config:
                component_data['entropy_max'] = check_config['max_entropy']
            if 'group_by' in check_config:
                component_data['entropy_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['entropy_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['entropy_analysis_blocking'] = check_config['blocking']
                
        elif check_name == 'correlation_check':
            if 'column_x' in check_config:
                component_data['correlation_column_x'] = check_config['column_x']
            if 'column_y' in check_config:
                component_data['correlation_column_y'] = check_config['column_y']
            if 'min_correlation' in check_config:
                component_data['correlation_min'] = check_config['min_correlation']
            if 'max_correlation' in check_config:
                component_data['correlation_max'] = check_config['max_correlation']
            if 'method' in check_config:
                component_data['correlation_method'] = check_config['method']
            if 'group_by' in check_config:
                component_data['correlation_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['correlation_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['correlation_blocking'] = check_config['blocking']
                
        elif check_name == 'predicted_range':
            if 'metric' in check_config:
                component_data['predicted_range_metric'] = check_config['metric']
            if 'confidence' in check_config:
                component_data['predicted_range_confidence'] = check_config['confidence']
            if 'history' in check_config:
                component_data['predicted_range_history'] = check_config['history']
            if 'method' in check_config:
                component_data['predicted_range_method'] = check_config['method']
            if 'group_by' in check_config:
                component_data['predicted_range_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['predicted_range_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['predicted_range_blocking'] = check_config['blocking']
                
        elif check_name == 'distribution_change':
            if 'column' in check_config:
                component_data['distribution_change_column'] = check_config['column']
            if 'threshold' in check_config:
                component_data['distribution_change_threshold'] = check_config['threshold']
            if 'history' in check_config:
                component_data['distribution_change_history'] = check_config['history']
            if 'method' in check_config:
                component_data['distribution_change_method'] = check_config['method']
            if 'group_by' in check_config:
                component_data['distribution_change_group_by'] = check_config['group_by']
            if 'allowed_failures' in check_config:
                component_data['distribution_change_allowed_failures'] = check_config['allowed_failures']
            if 'blocking' in check_config:
                component_data['distribution_change_blocking'] = check_config['blocking']

    def _build_single_asset_checks(self):
        """Build checks for a single asset (used by _create_asset_component)."""
        if "." in self._asset_name:
            parsed_asset_key = AssetKey(self._asset_name.split("."))
        else:
            parsed_asset_key = AssetKey([self._asset_name])
        
        # Set default data_source_type if not provided
        if self.data_source_type is None:
            self.data_source_type = "database"
        
        asset_checks = []
        
        # Process all nested check configurations
        check_types = [
            ('row_count_check', self._create_row_count_check),
            ('null_check', self._create_null_check),
            ('static_threshold', self._create_static_threshold_check),
            ('benford_law', self._create_benford_law_check),
            ('entropy_analysis', self._create_entropy_check),
            ('correlation_check', self._create_correlation_check),
            ('value_set_validation', self._create_value_set_validation_check),
            ('pattern_matching', self._create_pattern_matching_check),
            ('data_type_check', self._create_data_type_check),
            ('range_check', self._create_range_check),
            ('uniqueness_check', self._create_uniqueness_check),
            ('predicted_range', self._create_predicted_range_check),
            ('percent_delta', self._create_percent_delta_check),
            ('distribution_change', self._create_distribution_change_check),
            ('anomaly_detection', self._create_anomaly_detection_check),
            ('cross_table_validation', self._create_cross_table_validation_check),
        ]
        
        for check_type, create_method in check_types:
            checks = getattr(self, check_type, None)
            if checks:
                for idx, check_cfg in enumerate(checks):
                    # Create a temporary component with the check configuration
                    temp_component, check_config = self._create_check_component(check_cfg)
                    
                    # Apply the check configuration to the temporary component
                    if isinstance(check_config, dict):
                        # Create a component_data dictionary and apply the nested check config
                        component_data = {}
                        self._apply_nested_check_config(component_data, check_type, check_config)
                        # Store flat field names in a separate dictionary for backward compatibility
                        temp_component._flat_config = component_data
                    elif hasattr(check_config, '__dict__'):
                        # Handle Pydantic models by converting to dict
                        check_config_dict = check_config.dict() if hasattr(check_config, 'dict') else check_config.__dict__
                        component_data = {}
                        self._apply_nested_check_config(component_data, check_type, check_config_dict)
                        # Store flat field names in a separate dictionary for backward compatibility
                        temp_component._flat_config = component_data
                    
                    # Set the check configuration on the temp component for execution methods to access
                    temp_component._current_check_config = check_config
                    asset_checks.append(create_method(parsed_asset_key, temp_component))
        
        # Custom SQL Checks (Database-only) - support multiple checks
        custom_sql_checks = getattr(self, 'custom_sql_check', None)
        if custom_sql_checks:
            for idx, check_cfg in enumerate(custom_sql_checks):
                asset_checks.append(self._create_custom_sql_check(parsed_asset_key, check_cfg, idx))
                
        # Dataframe Query Checks (Dataframe-only) - support multiple checks
        dataframe_query_checks = getattr(self, 'dataframe_query_check', None)
        if dataframe_query_checks:
            for idx, check_cfg in enumerate(dataframe_query_checks):
                asset_checks.append(self._create_dataframe_query_check(parsed_asset_key, check_cfg, idx))
                
        # Custom Dataframe Checks (Dataframe-only) - support multiple checks
        custom_dataframe_checks = getattr(self, 'custom_dataframe_check', None)
        if custom_dataframe_checks:
            for idx, check_cfg in enumerate(custom_dataframe_checks):
                asset_checks.append(self._create_custom_dataframe_check(parsed_asset_key, check_cfg, idx))
        
        return asset_checks



    def _sanitize_asset_key_name(self, asset_key: AssetKey) -> str:
        """Sanitize asset key name for use in check names.
        
        Converts asset keys like 'RAW_DATA.users' to 'RAW_DATA_users' for valid Dagster names.
        """
        # Convert the asset key to a string and replace invalid characters
        asset_name = asset_key.to_user_string()
        # Replace forward slashes with underscores
        sanitized_name = asset_name.replace("/", "_")
        # Replace any other invalid characters with underscores
        import re
        sanitized_name = re.sub(r'[^A-Za-z0-9_]', '_', sanitized_name)
        # Remove consecutive underscores
        sanitized_name = re.sub(r'_+', '_', sanitized_name)
        # Remove leading/trailing underscores
        sanitized_name = sanitized_name.strip('_')
        return sanitized_name

    # ═══════════════════════════════════════════════════════════════
    # CHECK CREATION METHODS - Auto-detect processing mode
    # ═══════════════════════════════════════════════════════════════

    def _create_check_component(self, check_cfg: Union[dict, BaseModel]):
        """Create a temporary component with basic configuration and return the check config."""
        # Create a temporary component instance with basic configuration
        temp_component = type(self)()
        
        # Copy basic configuration from self to temp_component
        for attr in ['table_name', 'database_resource_key', 'data_source_type', 'where_clause', 
                    'time_filter_column', 'hours_back', 'days_back', 'sample_size', 'sample_method']:
            if hasattr(self, attr):
                setattr(temp_component, attr, getattr(self, attr))
        
        # Copy the asset name for historical data loading
        if hasattr(self, '_asset_name'):
            temp_component._asset_name = self._asset_name
        
        # Return both the temp component (for basic config) and the check config
        return temp_component, check_cfg
    
    def _get_check_config_value(self, field_name: str, default=None):
        """Helper method to get configuration values from component attributes."""
        # First try to get the value from the component's attributes
        if hasattr(self, field_name):
            return getattr(self, field_name, default)
        # If not found, try to get it from the flat config dictionary
        if hasattr(self, '_flat_config') and self._flat_config:
            return self._flat_config.get(field_name, default)
        return default

    def _create_row_count_check(self, asset_key: AssetKey, component=None):
        """Create row count check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_row_count")
            def dataframe_row_count_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_row_count(context, df)
            return dataframe_row_count_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_row_count", required_resource_keys={component.database_resource_key})
                def database_row_count_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_row_count(context)
                return database_row_count_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_row_count")
                def dataframe_row_count_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_row_count(context, df)
                return dataframe_row_count_check

    def _create_null_check(self, asset_key: AssetKey, component=None):
        """Create null check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_null_check")
            def dataframe_null_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_null_check(context, df)
            return dataframe_null_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_null_check", required_resource_keys={component.database_resource_key})
                def database_null_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_null_check(context)
                return database_null_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_null_check")
                def dataframe_null_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_null_check(context, df)
                return dataframe_null_check

    def _create_static_threshold_check(self, asset_key: AssetKey, component=None):
        """Create static threshold check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_static_threshold")
            def dataframe_static_threshold_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_static_threshold(context, df)
            return dataframe_static_threshold_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_static_threshold", required_resource_keys={component.database_resource_key})
                def database_static_threshold_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_static_threshold(context)
                return database_static_threshold_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_static_threshold")
                def dataframe_static_threshold_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_static_threshold(context, df)
                return dataframe_static_threshold_check

    def _create_benford_law_check(self, asset_key: AssetKey, component=None):
        """Create Benford's Law check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_benford_law")
            def dataframe_benford_law_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_benford_law(context, df)
            return dataframe_benford_law_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_benford_law", required_resource_keys={component.database_resource_key})
                def database_benford_law_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_benford_law(context)
                return database_benford_law_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_benford_law")
                def dataframe_benford_law_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_benford_law(context, df)
                return dataframe_benford_law_check

    def _create_entropy_check(self, asset_key: AssetKey, component=None):
        """Create entropy check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_entropy")
            def dataframe_entropy_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_entropy(context, df)
            return dataframe_entropy_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_entropy", required_resource_keys={component.database_resource_key})
                def database_entropy_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_entropy(context)
                return database_entropy_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_entropy")
                def dataframe_entropy_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_entropy(context, df)
                return dataframe_entropy_check

    def _create_correlation_check(self, asset_key: AssetKey, component=None):
        """Create correlation check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_correlation")
            def dataframe_correlation_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_correlation(context, df)
            return dataframe_correlation_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_correlation", required_resource_keys={component.database_resource_key})
                def database_correlation_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_correlation(context)
                return database_correlation_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_correlation")
                def dataframe_correlation_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_correlation(context, df)
                return dataframe_correlation_check

    def _create_value_set_validation_check(self, asset_key: AssetKey, component=None):
        """Create value set validation check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_value_set_validation")
            def dataframe_value_set_validation_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_value_set_validation(context, df)
            return dataframe_value_set_validation_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_value_set_validation", required_resource_keys={component.database_resource_key})
                def database_value_set_validation_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_value_set_validation(context)
                return database_value_set_validation_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_value_set_validation")
                def dataframe_value_set_validation_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_value_set_validation(context, df)
                return dataframe_value_set_validation_check

    def _create_pattern_matching_check(self, asset_key: AssetKey, component=None):
        """Create pattern matching check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_pattern_matching")
            def dataframe_pattern_matching_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_pattern_matching(context, df)
            return dataframe_pattern_matching_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_pattern_matching", required_resource_keys={component.database_resource_key})
                def database_pattern_matching_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_pattern_matching(context)
                return database_pattern_matching_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_pattern_matching")
                def dataframe_pattern_matching_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_pattern_matching(context, df)
                return dataframe_pattern_matching_check

    def _create_predicted_range_check(self, asset_key: AssetKey, component=None):
        """Create predicted range check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_predicted_range")
            def dataframe_predicted_range_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_predicted_range(context, df)
            return dataframe_predicted_range_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_predicted_range", required_resource_keys={component.database_resource_key})
                def database_predicted_range_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_predicted_range(context)
                return database_predicted_range_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_predicted_range")
                def dataframe_predicted_range_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_predicted_range(context, df)
                return dataframe_predicted_range_check

    def _create_percent_delta_check(self, asset_key: AssetKey, component=None):
        """Create percent delta check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_percent_delta")
            def dataframe_percent_delta_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_percent_delta(context, df)
            return dataframe_percent_delta_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_percent_delta", required_resource_keys={component.database_resource_key})
                def database_percent_delta_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_percent_delta(context)
                return database_percent_delta_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_percent_delta")
                def dataframe_percent_delta_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_percent_delta(context, df)
                return dataframe_percent_delta_check

    def _create_distribution_change_check(self, asset_key: AssetKey, component=None):
        """Create distribution change check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_distribution_change")
            def dataframe_distribution_change_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_distribution_change(context, df)
            return dataframe_distribution_change_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_distribution_change", required_resource_keys={component.database_resource_key})
                def database_distribution_change_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_distribution_change(context)
                return database_distribution_change_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_distribution_change")
                def dataframe_distribution_change_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_distribution_change(context, df)
                return dataframe_distribution_change_check

    def _create_anomaly_detection_check(self, asset_key: AssetKey, component=None):
        """Create anomaly detection check - can use SQL or dataframe."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_anomaly_detection")
            def dataframe_anomaly_detection_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_anomaly_detection(context, df)
            return dataframe_anomaly_detection_check
        else:
            # Database mode - only include required_resource_keys if database_resource_key is not None
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_anomaly_detection", required_resource_keys={component.database_resource_key})
                def database_anomaly_detection_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_anomaly_detection(context)
                return database_anomaly_detection_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_anomaly_detection")
                def dataframe_anomaly_detection_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_anomaly_detection(context, df)
                return dataframe_anomaly_detection_check

    def _create_data_type_check(self, asset_key: AssetKey, component=None):
        """Create data type check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_data_type")
            def dataframe_data_type_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_data_type(context, df)
            return dataframe_data_type_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_data_type", required_resource_keys={component.database_resource_key})
                def database_data_type_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_data_type(context)
                return database_data_type_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_data_type")
                def dataframe_data_type_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_data_type(context, df)
                return dataframe_data_type_check

    def _create_range_check(self, asset_key: AssetKey, component=None):
        """Create range check - can use SQL or dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_range_check")
            def dataframe_range_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_range_check(context, df)
            return dataframe_range_check
        else:
            # Database source - can use SQL for simple range checks
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_range_check", required_resource_keys={component.database_resource_key})
                def database_range_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_range_check(context)
                return database_range_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_range_check")
                def dataframe_range_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_range_check(context, df)
                return dataframe_range_check

    def _create_uniqueness_check(self, asset_key: AssetKey, component=None):
        """Create uniqueness check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_uniqueness_check")
            def dataframe_uniqueness_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_uniqueness_check(context, df)
            return dataframe_uniqueness_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_uniqueness_check", required_resource_keys={component.database_resource_key})
                def database_uniqueness_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_uniqueness_check(context)
                return database_uniqueness_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_uniqueness_check")
                def dataframe_uniqueness_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_uniqueness_check(context, df)
                return dataframe_uniqueness_check

    def _create_custom_dataframe_check(self, asset_key: AssetKey, component=None):
        """Create custom dataframe check - ALWAYS requires dataframe processing."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        if component.data_source_type == "dataframe" or (component.data_source_type != "database" and not component.database_resource_key):
            @asset_check(asset=asset_key, name=f"{sanitized_name}_custom_dataframe_check")
            def dataframe_custom_dataframe_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                return component._execute_dataframe_custom_dataframe_check(context, df)
            return dataframe_custom_dataframe_check
        else:
            # Database source but complex check → fetch data and process as dataframe
            if component.database_resource_key:
                @asset_check(asset=asset_key, name=f"{sanitized_name}_custom_dataframe_check", required_resource_keys={component.database_resource_key})
                def database_custom_dataframe_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                    return component._execute_database_to_dataframe_custom_dataframe_check(context)
                return database_custom_dataframe_check
            else:
                # Fallback to dataframe mode if no database resource is available
                @asset_check(asset=asset_key, name=f"{sanitized_name}_custom_dataframe_check")
                def dataframe_custom_dataframe_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
                    return component._execute_dataframe_custom_dataframe_check(context, df)
                return dataframe_custom_dataframe_check

    def _create_custom_sql_check(self, asset_key: AssetKey, check_cfg: Union[dict, CustomSqlCheckConfig], idx: int):
        """Create a custom SQL check (database-only)."""
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        
        if isinstance(check_cfg, CustomSqlCheckConfig):
            check_name = check_cfg.name or f"{sanitized_name}_custom_sql_check_{idx+1}"
            db_key = self.database_resource_key
        else:
            check_name = f"{sanitized_name}_custom_sql_check_{idx+1}"
            db_key = check_cfg.get('database_resource_key', self.database_resource_key)
            
        if not db_key:
            raise ValueError("custom_sql_check requires a database_resource_key.")
            
        @asset_check(asset=asset_key, name=check_name, required_resource_keys={db_key})
        def custom_sql_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
            return self._execute_custom_sql_check(context, check_cfg, db_key)
        return custom_sql_check

    def _create_dataframe_query_check(self, asset_key: AssetKey, check_cfg: Union[dict, DataframeQueryCheckConfig], idx: int):
        """Create a dataframe query check (dataframe-only)."""
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        
        if isinstance(check_cfg, DataframeQueryCheckConfig):
            check_name = check_cfg.name or f"{sanitized_name}_dataframe_query_check_{idx+1}"
        else:
            check_name = f"{sanitized_name}_dataframe_query_check_{idx+1}"
        
        # Dataframe query checks are always dataframe-only (no database fallback)
        @asset_check(asset=asset_key, name=check_name)
        def dataframe_query_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
            return self._execute_dataframe_query_check(context, df, check_cfg)
        return dataframe_query_check
        
    def _create_custom_dataframe_check(self, asset_key: AssetKey, check_cfg: Union[dict, CustomDataframeCheckConfig], idx: int):
        """Create a custom dataframe check (dataframe-only)."""
        sanitized_name = self._sanitize_asset_key_name(asset_key)
        
        if isinstance(check_cfg, CustomDataframeCheckConfig):
            check_name = check_cfg.name or f"{sanitized_name}_custom_dataframe_check_{idx+1}"
        else:
            check_name = f"{sanitized_name}_custom_dataframe_check_{idx+1}"
        
        # Custom dataframe checks are always dataframe-only (no database fallback)
        @asset_check(asset=asset_key, name=check_name)
        def custom_dataframe_check(context: AssetCheckExecutionContext, df) -> AssetCheckResult:
            return self._execute_custom_dataframe_check(context, df, check_cfg)
        return custom_dataframe_check
            
    def _create_cross_table_validation_check(self, asset_key: AssetKey, component=None):
        """Create cross-table validation check."""
        if component is None:
            component = self
            
        sanitized_name = component._sanitize_asset_key_name(asset_key)
        # Cross-table validation is database-only
        required_resource_keys = set()
        if component.database_resource_key:
            required_resource_keys.add(component.database_resource_key)
        
        # Get source database from current check config
        source_database = component._get_check_config_value('source_database')
        if source_database:
            required_resource_keys.add(source_database)
            
        if required_resource_keys:
            @asset_check(asset=asset_key, name=f"{sanitized_name}_cross_table_validation", required_resource_keys=required_resource_keys)
            def cross_table_validation_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                return component._execute_cross_table_validation(context)
            return cross_table_validation_check
        else:
            @asset_check(asset=asset_key, name=f"{sanitized_name}_cross_table_validation")
            def cross_table_validation_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
                return component._execute_cross_table_validation(context)
            return cross_table_validation_check

    # ═══════════════════════════════════════════════════════════════
    # EXECUTION METHODS - Simple checks
    # ═══════════════════════════════════════════════════════════════

    def _execute_dataframe_row_count(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute row count check on dataframe."""
        # Get configuration using helper method
        min_rows = self._get_check_config_value('min_rows', 1)
        max_rows = self._get_check_config_value('max_rows')
        group_by = self._get_check_config_value('group_by')
        
        # Apply WHERE clause filtering
        filtered_df = self._filter_dataframe(df)
        
        # Check if we need to group by
        if group_by:
            # Get current metric values grouped by the specified column
            current_values = self._get_current_metric_values(filtered_df, "num_rows", group_by)
            
            # Check each group against thresholds
            failed_groups = []
            total_groups = len(current_values)
            
            for group_name, row_count in current_values.items():
                if not (min_rows <= row_count <= (max_rows if max_rows else float('inf'))):
                    failed_groups.append({
                        "group": group_name,
                        "row_count": row_count,
                        "expected_min": min_rows,
                        "expected_max": max_rows or "∞"
                    })
            
            passed = len(failed_groups) == 0
            
            return AssetCheckResult(
                passed=passed,
                description=f"Row count check: {len(failed_groups)}/{total_groups} groups failed",
                metadata={
                    "total_groups": MetadataValue.int(total_groups),
                    "failed_groups": MetadataValue.json(failed_groups),
                    "group_by": MetadataValue.text(group_by),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
        else:
            # Original non-grouped logic
            # Auto-detect dataframe type
            if hasattr(filtered_df, 'height'):  # Polars
                row_count = filtered_df.height
            else:  # Pandas
                row_count = len(filtered_df)
            
            passed = min_rows <= row_count <= (max_rows if max_rows else float('inf'))
            
            return AssetCheckResult(
                passed=passed,
                description=f"Row count: {row_count} (expected: {min_rows}-{max_rows or '∞'})",
                metadata={
                    "row_count": MetadataValue.int(row_count),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )

    def _execute_database_row_count(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute row count check on database."""
        # Get configuration using helper method
        min_rows = self._get_check_config_value('min_rows', 1)
        max_rows = self._get_check_config_value('max_rows')
        group_by = self._get_check_config_value('group_by')
        allowed_failures = self._get_check_config_value('allowed_failures', 0)
        
        database_resource = getattr(context.resources, self.database_resource_key)
        
        # Build WHERE clause for filtering
        where_conditions = self._build_where_clause()
        where_sql = f" WHERE {where_conditions}" if where_conditions else ""
        
        # Check if we need to group by
        if group_by:
            # Get current metric values grouped by the specified column
            current_values = self._get_current_metric_values_database(database_resource, "num_rows", group_by)
            
            # Check each group against thresholds
            failed_groups = []
            total_groups = len(current_values)
            
            for group_name, row_count in current_values.items():
                if not (min_rows <= row_count <= (max_rows if max_rows else float('inf'))):
                    failed_groups.append({
                        "group": group_name,
                        "row_count": row_count,
                        "expected_min": min_rows,
                        "expected_max": max_rows or "∞"
                    })
            
            # Check if we're within allowed failures
            passed = len(failed_groups) <= allowed_failures
            
            return AssetCheckResult(
                passed=passed,
                description=f"Row count check: {len(failed_groups)}/{total_groups} groups failed (allowed: {allowed_failures})",
                metadata={
                    "total_groups": MetadataValue.int(total_groups),
                    "failed_groups": MetadataValue.json(failed_groups),
                    "group_by": MetadataValue.text(group_by),
                    "allowed_failures": MetadataValue.int(allowed_failures),
                    "processing_mode": MetadataValue.text("sql"),
                }
            )
        else:
            # Original non-grouped logic
            with database_resource.get_connection() as conn:
                result = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}{where_sql}").fetchone()
                row_count = result[0]
            
                passed = min_rows <= row_count <= (max_rows if max_rows else float('inf'))
            
            return AssetCheckResult(
                passed=passed,
                description=f"Row count: {row_count} (expected: {min_rows}-{max_rows or '∞'})",
                metadata={
                    "row_count": MetadataValue.int(row_count),
                    "processing_mode": MetadataValue.text("sql"),
                }
            )

    def _execute_database_range_check(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute range check on database using SQL."""
        # Get configuration using helper method
        range_columns = self._get_check_config_value('range_columns', [])
        
        database_resource = getattr(context.resources, self.database_resource_key)
        
        # Build WHERE clause for filtering
        where_conditions = self._build_where_clause()
        where_sql = f" WHERE {where_conditions}" if where_conditions else ""
        
        range_validation_results = {}
        failed_columns = []
        
        with database_resource.get_connection() as conn:
            for column_config in range_columns:
                column_name = column_config["column"]
                min_value = column_config.get("min_value")
                max_value = column_config.get("max_value")
                
                # Build range conditions for SQL
                range_conditions = []
                if min_value is not None:
                    range_conditions.append(f"{column_name} >= {min_value}")
                if max_value is not None:
                    range_conditions.append(f"{column_name} <= {max_value}")
                
                # Count total non-null values
                null_condition = f"{column_name} IS NOT NULL"
                if where_sql:
                    total_query = f"SELECT COUNT(*) FROM {self.table_name}{where_sql} AND {null_condition}"
                else:
                    total_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {null_condition}"
                total_result = conn.execute(total_query).fetchone()
                total_values = total_result[0]
                
                if total_values == 0:
                    # No data to analyze
                    range_validation_results[column_name] = {
                        "passed": True,
                        "min_value": min_value,
                        "max_value": max_value,
                        "outlier_count": 0,
                        "total_values": 0,
                        "description": f"Range validation: No data to analyze"
                    }
                    continue
                
                # Count outliers (values outside the range)
                outlier_conditions = []
                if min_value is not None:
                    outlier_conditions.append(f"{column_name} < {min_value}")
                if max_value is not None:
                    outlier_conditions.append(f"{column_name} > {max_value}")
                
                if outlier_conditions:
                    outlier_condition = f"({' OR '.join(outlier_conditions)})"
                    if where_sql:
                        outlier_query = f"SELECT COUNT(*) FROM {self.table_name}{where_sql} AND {outlier_condition}"
                    else:
                        outlier_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {outlier_condition}"
                    outlier_result = conn.execute(outlier_query).fetchone()
                    outlier_count = outlier_result[0]
                else:
                    outlier_count = 0
                
                # Check if validation passed (no outliers)
                passed = outlier_count == 0
                
                range_validation_results[column_name] = {
                    "passed": passed,
                    "min_value": min_value,
                    "max_value": max_value,
                    "outlier_count": outlier_count,
                    "total_values": total_values,
                    "description": f"Range validation: {outlier_count} outliers found"
                }
                
                if not passed:
                    failed_columns.append(column_name)
        
        # Overall result
        total_columns = len(range_columns)
        overall_passed = len(failed_columns) == 0
        
        return AssetCheckResult(
            passed=overall_passed,
            description=f"Range validation: {total_columns - len(failed_columns)}/{total_columns} columns passed",
            metadata={
                "failed_column_names": MetadataValue.json(failed_columns),
                "total_columns": MetadataValue.int(total_columns),
                "validation_results": MetadataValue.json(range_validation_results),
                "processing_mode": MetadataValue.text("sql"),
            }
        )

    def _execute_dataframe_null_check(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute null check on dataframe."""
        # Get configuration using helper method
        columns = self._get_check_config_value('columns', [])
        group_by = self._get_check_config_value('group_by')
        
        # Apply WHERE clause filtering
        filtered_df = self._filter_dataframe(df)
        
        # Check if we need to group by
        if group_by:
            # Check each group independently
            failed_groups = []
            total_groups = 0
            
            # Get unique groups
            if hasattr(filtered_df, 'select'):  # Polars
                groups = filtered_df.select(filtered_df[group_by].unique()).to_numpy().flatten()
            else:  # Pandas
                groups = filtered_df[group_by].unique()
            
            total_groups = len(groups)
            
            for group in groups:
                # Filter data for this group
                if hasattr(filtered_df, 'filter'):  # Polars
                    group_df = filtered_df.filter(filtered_df[group_by] == group)
                else:  # Pandas
                    group_df = filtered_df[filtered_df[group_by] == group]
                
                # Check nulls for this group
                group_null_counts = {}
                group_total_nulls = 0
                
                for column in columns:
                    if hasattr(group_df, 'select'):  # Polars
                        null_count = group_df.select(group_df[column].null_count()).to_numpy()[0][0]
                    else:  # Pandas
                        null_count = group_df[column].isnull().sum()
                    group_null_counts[column] = null_count
                    group_total_nulls += null_count
                
                # If this group has any nulls, it's a failure
                if group_total_nulls > 0:
                    failed_groups.append({
                        "group": str(group),
                        "null_counts": group_null_counts,
                        "total_nulls": group_total_nulls
                    })
            
            passed = len(failed_groups) == 0
            
            return AssetCheckResult(
                passed=passed,
                description=f"Null check: {len(failed_groups)}/{total_groups} groups failed",
                metadata={
                    "total_groups": MetadataValue.int(total_groups),
                    "failed_groups": MetadataValue.json(failed_groups),
                    "group_by": MetadataValue.text(group_by),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
        else:
            # Original non-grouped logic
            null_counts = {}
            
            for column in columns:
                if hasattr(filtered_df, 'select'):  # Polars
                    null_count = filtered_df.select(filtered_df[column].null_count()).to_numpy()[0][0]
                else:  # Pandas
                    null_count = filtered_df[column].isnull().sum()
                null_counts[column] = null_count
            
            total_nulls = sum(null_counts.values())
            passed = total_nulls == 0
            
            return AssetCheckResult(
                passed=passed,
                description=f"Null check: {total_nulls} null values found",
                metadata={
                    "total_nulls": MetadataValue.int(total_nulls),
                    "null_counts": MetadataValue.json(null_counts),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )

    def _execute_database_null_check(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute null check on database."""
        # Get configuration using helper method
        columns = self._get_check_config_value('columns', [])
        
        database_resource = getattr(context.resources, self.database_resource_key)
        null_counts = {}
        
        with database_resource.get_connection() as conn:
            for column in columns:
                result = conn.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE {column} IS NULL").fetchone()
                null_counts[column] = result[0]
        
        total_nulls = sum(null_counts.values())
        passed = total_nulls == 0
        
        return AssetCheckResult(
            passed=passed,
            description=f"Null check: {total_nulls} null values found",
            metadata={
                "total_nulls": MetadataValue.int(total_nulls),
                "null_counts": MetadataValue.json(null_counts),
                "processing_mode": MetadataValue.text("sql"),
            }
        )

    def _execute_dataframe_static_threshold(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute static threshold check on dataframe."""
        # Get configuration using helper method
        metric = self._get_check_config_value('metric', 'num_rows')
        group_by = self._get_check_config_value('group_by')
        min_value = self._get_check_config_value('min_value')
        max_value = self._get_check_config_value('max_value')
        
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Check if we need to group by
            if group_by:
                # Get current metric values grouped by the specified column
                current_values = self._get_current_metric_values(filtered_df, metric, group_by)
                
                # Check each group against thresholds
                failed_groups = []
                total_groups = len(current_values)
                
                for group_name, metric_value in current_values.items():
                    group_passed = True
                    failure_reasons = []
                    
                    if min_value is not None and metric_value < min_value:
                        group_passed = False
                        failure_reasons.append(f"value {metric_value} < min {min_value}")
                    
                    if max_value is not None and metric_value > max_value:
                        group_passed = False
                        failure_reasons.append(f"value {metric_value} > max {max_value}")
                    
                    if not group_passed:
                        failed_groups.append({
                            "group": str(group_name),
                            "metric_value": float(metric_value),
                            "failure_reasons": failure_reasons
                        })
                
                passed = len(failed_groups) == 0
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"Static threshold check: {len(failed_groups)}/{total_groups} groups failed",
                    metadata={
                        "metric": MetadataValue.text(metric),
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups": MetadataValue.json(failed_groups),
                        "group_by": MetadataValue.text(group_by),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            else:
                # Original non-grouped logic
                # Compute metric value
                metric_value = self._compute_dataframe_metric(filtered_df, metric)
                
                # Check against thresholds
                passed = True
                failure_reasons = []
                
                if min_value is not None and metric_value < min_value:
                    passed = False
                    failure_reasons.append(f"value {metric_value} < min {min_value}")
                
                if max_value is not None and metric_value > max_value:
                    passed = False
                    failure_reasons.append(f"value {metric_value} > max {max_value}")
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"Static threshold check ({'PASSED' if passed else 'FAILED'})",
                    metadata={
                        "metric": MetadataValue.text(metric),
                        "metric_value": MetadataValue.float(float(metric_value)),
                        "failure_reasons": MetadataValue.json(failure_reasons),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Static threshold check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_static_threshold(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute static threshold check on database."""
        # Get configuration using helper method
        metric = self._get_check_config_value('metric', 'num_rows')
        min_value = self._get_check_config_value('min_value')
        max_value = self._get_check_config_value('max_value')
        
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Debug: Log configuration
            context.log.info(f"Static threshold - Metric: {metric}")
            context.log.info(f"Static threshold - Table name: {self.table_name}")
            context.log.info(f"Static threshold - Database resource key: {self.database_resource_key}")
            context.log.info(f"Static threshold - Min value: {min_value}")
            context.log.info(f"Static threshold - Max value: {max_value}")
            
            # Compute metric value
            metric_value = self._compute_database_metric(metric, database_resource, context)
            
            # Debug: Log result
            context.log.info(f"Static threshold - Computed metric value: {metric_value}")
            
            # Check against thresholds
            passed = True
            failure_reasons = []
            
            if min_value is not None and metric_value < min_value:
                passed = False
                failure_reasons.append(f"value {metric_value} < min {min_value}")
            
            if max_value is not None and metric_value > max_value:
                passed = False
                failure_reasons.append(f"value {metric_value} > max {max_value}")
            
            return AssetCheckResult(
                passed=passed,
                description=f"Static threshold check ({'PASSED' if passed else 'FAILED'})",
                metadata={
                    "metric": MetadataValue.text(metric),
                    "metric_value": MetadataValue.float(float(metric_value)),
                    "failure_reasons": MetadataValue.json(failure_reasons),
                    "processing_mode": MetadataValue.text("sql"),
                }
            )
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Static threshold check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    # ═══════════════════════════════════════════════════════════════
    # EXECUTION METHODS - Complex checks (always dataframe)
    # ═══════════════════════════════════════════════════════════════

    def _execute_dataframe_benford_law(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute Benford's Law check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_benford_law(filtered_df, self._get_check_config_value('benford_column', 'column'))
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Benford's Law check: {result['description']}",
                metadata={
                    "max_deviation": MetadataValue.float(float(result["max_deviation"])),
                    "threshold": MetadataValue.float(self._get_check_config_value('benford_threshold')),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("dataframe"),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Benford's Law check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_benford_law(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute Benford's Law check: database → dataframe → analysis."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Run the same dataframe analysis
            result = self._analyze_benford_law(df, self._get_check_config_value('benford_column', 'column'))
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Benford's Law check: {result['description']}",
                metadata={
                    "max_deviation": MetadataValue.float(float(result["max_deviation"])),
                    "threshold": MetadataValue.float(self._get_check_config_value('benford_threshold', 0.05)),
                    "data_size": MetadataValue.int(len(df)),
                    "dataframe_type": MetadataValue.text(type(df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Benford's Law check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_entropy(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute entropy analysis on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Get configuration
            column = self._get_check_config_value('entropy_column', 'column')
            min_entropy = self._get_check_config_value('entropy_min', None)
            max_entropy = self._get_check_config_value('entropy_max', None)
            group_by = self._get_check_config_value('entropy_group_by', None)
            allowed_failures = self._get_check_config_value('entropy_allowed_failures', 0)
            
            # Add debugging
            context.log.info(f"Entropy analysis - column: {column}")
            context.log.info(f"Entropy analysis - group_by: {group_by}")
            context.log.info(f"Entropy analysis - min_entropy: {min_entropy}")
            context.log.info(f"Entropy analysis - max_entropy: {max_entropy}")
            context.log.info(f"Entropy analysis - allowed_failures: {allowed_failures}")
            
            if group_by:
                # Grouped entropy analysis
                group_results = {}
                failed_groups = []
                
                # Group by the specified column
                if hasattr(filtered_df, 'groupby'):  # Pandas
                    groups = filtered_df.groupby(group_by)
                else:  # Polars
                    groups = filtered_df.group_by(group_by)
                
                for group_name, group_df in groups:
                    group_entropy = self._calculate_shannon_entropy(group_df, column)
                    group_results[str(group_name)] = group_entropy
                    
                    # Check if this group's entropy is within bounds
                    group_passed = True
                    if min_entropy is not None and group_entropy < min_entropy:
                        group_passed = False
                    if max_entropy is not None and group_entropy > max_entropy:
                        group_passed = False
                    
                    if not group_passed:
                        failed_groups.append(str(group_name))
                
                # Overall result based on allowed failures
                total_groups = len(group_results)
                passed = len(failed_groups) <= allowed_failures
                
                description = f"Entropy analysis by {group_by}: {total_groups - len(failed_groups)}/{total_groups} groups passed"
                if not passed:
                    description += f". Failed groups: {failed_groups}"
                
                return AssetCheckResult(
                    passed=passed,
                    description=description,
                    metadata={
                        "group_results": MetadataValue.text(str(group_results)),
                        "failed_groups": MetadataValue.text(str(failed_groups)),
                        "total_groups": MetadataValue.int(total_groups),
                        "allowed_failures": MetadataValue.int(allowed_failures),
                        "min_entropy": MetadataValue.float(min_entropy) if min_entropy else MetadataValue.null(),
                        "max_entropy": MetadataValue.float(max_entropy) if max_entropy else MetadataValue.null(),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            else:
                # Simple entropy analysis (no grouping)
                entropy_value = self._calculate_shannon_entropy(filtered_df, column)
            
            # Check against thresholds
            passed = True
            failure_reasons = []
            
            if min_entropy is not None and entropy_value < min_entropy:
                passed = False
                failure_reasons.append(f"entropy {entropy_value:.3f} < min {min_entropy}")
            
            if max_entropy is not None and entropy_value > max_entropy:
                passed = False
                failure_reasons.append(f"entropy {entropy_value:.3f} > max {max_entropy}")
            
            return AssetCheckResult(
                passed=passed,
                description=f"Entropy analysis: {entropy_value:.3f} ({'PASSED' if passed else 'FAILED'})",
                metadata={
                    "entropy_value": MetadataValue.float(float(entropy_value)),
                    "failure_reasons": MetadataValue.json(failure_reasons),
                    "min_entropy": MetadataValue.float(min_entropy) if min_entropy else MetadataValue.null(),
                    "max_entropy": MetadataValue.float(max_entropy) if max_entropy else MetadataValue.null(),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Entropy analysis failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_entropy(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute entropy analysis: database → dataframe → analysis."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Get configuration
            column = self._get_check_config_value('entropy_column', 'column')
            min_entropy = self._get_check_config_value('entropy_min', None)
            max_entropy = self._get_check_config_value('entropy_max', None)
            group_by = self._get_check_config_value('entropy_group_by', None)
            allowed_failures = self._get_check_config_value('entropy_allowed_failures', 0)
            
            # Add debugging
            context.log.info(f"Database entropy analysis - column: {column}")
            context.log.info(f"Database entropy analysis - group_by: {group_by}")
            context.log.info(f"Database entropy analysis - min_entropy: {min_entropy}")
            context.log.info(f"Database entropy analysis - max_entropy: {max_entropy}")
            context.log.info(f"Database entropy analysis - allowed_failures: {allowed_failures}")
            
            if group_by:
                # Grouped entropy analysis
                group_results = {}
                failed_groups = []
                
                # Group by the specified column
                if hasattr(filtered_df, 'groupby'):  # Pandas
                    groups = filtered_df.groupby(group_by)
                else:  # Polars
                    groups = filtered_df.group_by(group_by)
                
                for group_name, group_df in groups:
                    group_entropy = self._calculate_shannon_entropy(group_df, column)
                    group_results[str(group_name)] = group_entropy
                    
                    # Check if this group's entropy is within bounds
                    group_passed = True
                    if min_entropy is not None and group_entropy < min_entropy:
                        group_passed = False
                    if max_entropy is not None and group_entropy > max_entropy:
                        group_passed = False
                    
                    if not group_passed:
                        failed_groups.append(str(group_name))
                
                # Overall result based on allowed failures
                total_groups = len(group_results)
                passed = len(failed_groups) <= allowed_failures
                
                description = f"Entropy analysis by {group_by}: {total_groups - len(failed_groups)}/{total_groups} groups passed"
                if not passed:
                    description += f". Failed groups: {failed_groups}"
                
                return AssetCheckResult(
                    passed=passed,
                    description=description,
                    metadata={
                        "group_results": MetadataValue.text(str(group_results)),
                        "failed_groups": MetadataValue.text(str(failed_groups)),
                        "total_groups": MetadataValue.int(total_groups),
                        "allowed_failures": MetadataValue.int(allowed_failures),
                        "min_entropy": MetadataValue.float(min_entropy) if min_entropy else MetadataValue.null(),
                        "max_entropy": MetadataValue.float(max_entropy) if max_entropy else MetadataValue.null(),
                        "data_size": MetadataValue.int(len(filtered_df)),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "processing_mode": MetadataValue.text("database_to_dataframe"),
                    }
                )
            else:
                # Simple entropy analysis (no grouping)
                entropy = self._calculate_shannon_entropy(filtered_df, column)
            
            # Check against bounds
            passed = True
            if min_entropy is not None and entropy < min_entropy:
                passed = False
            if max_entropy is not None and entropy > max_entropy:
                passed = False
            
            return AssetCheckResult(
                passed=passed,
                description=f"Entropy analysis: {entropy:.4f}",
                metadata={
                    "entropy": MetadataValue.float(float(entropy)),
                    "min_entropy": MetadataValue.float(min_entropy) if min_entropy else MetadataValue.null(),
                    "max_entropy": MetadataValue.float(max_entropy) if max_entropy else MetadataValue.null(),
                    "data_size": MetadataValue.int(len(filtered_df)),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Entropy check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_correlation(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute correlation analysis on dataframe."""
        # Get configuration from the current check config
        check_config = getattr(self, '_current_check_config', None)
        if check_config is None:
            # Fallback to direct attributes for backward compatibility
            column_x = self._get_check_config_value('correlation_column_x', 'column1')
            column_y = self._get_check_config_value('correlation_column_y', 'column2')
            method = self._get_check_config_value('correlation_method', 'pearson')
        else:
            # Access configuration from the Pydantic model
            column_x = check_config.column_x
            column_y = check_config.column_y
            method = check_config.method
        
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_correlation(filtered_df, column_x, column_y)
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Correlation analysis: {result['description']}",
                metadata={
                    "correlation_value": MetadataValue.float(float(result["correlation_value"])),
                    "correlation_method": MetadataValue.text(method),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Correlation analysis failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_correlation(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute correlation check: database → dataframe → analysis."""
        # Get configuration from the current check config
        check_config = getattr(self, '_current_check_config', None)
        if check_config is None:
            # Fallback to direct attributes for backward compatibility
            column_x = self._get_check_config_value('correlation_column_x', 'column1')
            column_y = self._get_check_config_value('correlation_column_y', 'column2')
        else:
            # Access configuration from the Pydantic model
            column_x = check_config.column_x
            column_y = check_config.column_y
        
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Run the same dataframe analysis
            result = self._analyze_correlation(df, column_x, column_y)
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Correlation check: {result['description']}",
                metadata={
                    "correlation": MetadataValue.float(float(result["correlation"])),
                    "p_value": MetadataValue.float(float(result["p_value"])),
                    "method": MetadataValue.text(result["method"]),
                    "data_size": MetadataValue.int(len(df)),
                    "dataframe_type": MetadataValue.text(type(df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Correlation check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_value_set_validation(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute value set validation on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Check if we need to group by
            if self._get_check_config_value('value_set_group_by', None):
                # Check each group independently
                failed_groups = []
                total_groups = 0
                
                # Get unique groups
                if hasattr(filtered_df, 'select'):  # Polars
                    groups = filtered_df.select(filtered_df[self._get_check_config_value('value_set_group_by', 'group_by')].unique()).to_numpy().flatten()
                else:  # Pandas
                    groups = filtered_df[self._get_check_config_value('value_set_group_by', 'group_by')].unique()
                
                total_groups = len(groups)
                
                for group in groups:
                    # Filter data for this group
                    if hasattr(filtered_df, 'filter'):  # Polars
                        group_df = filtered_df.filter(filtered_df[self._get_check_config_value('value_set_group_by', 'group_by')] == group)
                    else:  # Pandas
                        group_df = filtered_df[filtered_df[self._get_check_config_value('value_set_group_by', None)] == group]
                    
                    # Run value set validation analysis for this group
                    result = self._analyze_value_set_validation(group_df, self._get_check_config_value('value_set_column', 'column'), self._get_check_config_value('value_set_allowed_values', []))
                    
                    # If this group fails the validation, add it to failed groups
                    if not result["passed"]:
                        failed_groups.append({
                            "group": str(group),
                            "valid_percentage": float(result["valid_percentage"]),
                            "required_percentage": self._get_check_config_value('value_set_min_pct', 95.0),
                            "valid_values": int(result["valid_values"]),
                            "total_values": int(result["total_values"])
                        })
                
                passed = len(failed_groups) == 0
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"Value set validation: {len(failed_groups)}/{total_groups} groups failed",
                    metadata={
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups": MetadataValue.json(failed_groups),
                        "group_by": MetadataValue.text(self._get_check_config_value('value_set_group_by', None)),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            else:
                # Original non-grouped logic
                result = self._analyze_value_set_validation(filtered_df, self._get_check_config_value('value_set_column', 'column'), self._get_check_config_value('value_set_allowed_values', []))
                
                return AssetCheckResult(
                    passed=bool(result["passed"]),
                    description=f"Value set validation: {result['description']}",
                    metadata={
                        "valid_percentage": MetadataValue.float(result["valid_percentage"]),
                        "required_percentage": MetadataValue.float(self._get_check_config_value('value_set_min_pct', 95.0)),
                        "valid_values": MetadataValue.int(int(result["valid_values"])),
                        "total_values": MetadataValue.int(int(result["total_values"])),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Value set validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_value_set_validation(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute value set validation check: database → dataframe → analysis."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Run the same dataframe analysis
            result = self._analyze_value_set_validation(df, self._get_check_config_value('value_set_column', 'column'), self._get_check_config_value('value_set_allowed_values', []))
            
            return AssetCheckResult(
                passed=bool(result["passed"]),
                description=f"Value set validation: {result['description']}",
                metadata={
                    "valid_percentage": MetadataValue.float(float(result["valid_percentage"])),
                    "required_percentage": MetadataValue.float(self._get_check_config_value('value_set_min_pct', 95.0)),
                    "valid_values": MetadataValue.int(int(result["valid_values"])),
                    "total_values": MetadataValue.int(int(result["total_values"])),
                    "data_size": MetadataValue.int(len(df)),
                    "dataframe_type": MetadataValue.text(type(df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Value set validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_pattern_matching(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute pattern matching validation on dataframe."""
        # Get configuration from the current check config
        check_config = getattr(self, '_current_check_config', None)
        if check_config is None:
            # Fallback to direct attributes for backward compatibility
            column = self._get_check_config_value('pattern_column', 'column')
            group_by = self._get_check_config_value('pattern_group_by', None)
            min_pct = self._get_check_config_value('pattern_min_pct', 95.0)
        else:
            # Access configuration from the Pydantic model
            column = check_config.column
            group_by = check_config.group_by
            min_pct = check_config.match_percentage
        
        filtered_df = df  # Default to original df
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Debug: Log dataframe info
            context.log.info(f"Pattern matching - Original df shape: {len(df) if hasattr(df, '__len__') else 'unknown'}")
            context.log.info(f"Pattern matching - Filtered df shape: {len(filtered_df) if hasattr(filtered_df, '__len__') else 'unknown'}")
            context.log.info(f"Pattern matching - Column to check: {column}")
            context.log.info(f"Pattern matching - Available columns: {list(filtered_df.columns) if hasattr(filtered_df, 'columns') else 'unknown'}")
            
            # Check if column exists
            if hasattr(filtered_df, 'columns') and column not in filtered_df.columns:
                return AssetCheckResult(
                    passed=False,
                    description=f"Pattern matching failed: Column '{column}' not found in dataframe",
                    metadata={
                        "error": MetadataValue.text(f"Column '{column}' not found. Available columns: {list(filtered_df.columns)}"),
                        "total_count": MetadataValue.int(0),
                        "match_count": MetadataValue.int(0),
                        "match_percentage": MetadataValue.float(0.0),
                        "required_percentage": MetadataValue.float(min_pct),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                        **self._get_pattern_info()
                    }
                )
            
            # Check if we need to group by
            if group_by:
                # Check each group independently
                failed_groups = []
                total_groups = 0
                
                # Get unique groups
                if hasattr(filtered_df, 'select'):  # Polars
                    groups = filtered_df.select(filtered_df[group_by].unique()).to_numpy().flatten()
                else:  # Pandas
                    groups = filtered_df[group_by].unique()
                
                total_groups = len(groups)
                
                for group in groups:
                    # Filter data for this group
                    if hasattr(filtered_df, 'filter'):  # Polars
                        group_df = filtered_df.filter(filtered_df[group_by] == group)
                    else:  # Pandas
                        group_df = filtered_df[filtered_df[group_by] == group]
                    
                    # Run pattern matching analysis for this group
                    regex_pattern = self._get_pattern_regex()
                    result = self._analyze_pattern_matching(group_df, column, regex_pattern, min_pct)
                    
                    # If this group fails the pattern check, add it to failed groups
                    if not result["passed"]:
                        failed_groups.append({
                            "group": str(group),
                            "match_percentage": float(result["match_percentage"]),
                            "required_percentage": min_pct,
                            "match_count": int(result["matching_values"]),
                            "total_count": int(result["total_values"])
                        })
                
                passed = len(failed_groups) == 0
                
                # Get pattern information for metadata
                pattern_info = self._get_pattern_info()
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"Pattern matching: {len(failed_groups)}/{total_groups} groups failed",
                    metadata={
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups": MetadataValue.json(failed_groups),
                        "group_by": MetadataValue.text(group_by),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                        **pattern_info
                    }
                )
            else:
                # Original non-grouped logic
                regex_pattern = self._get_pattern_regex()
                result = self._analyze_pattern_matching(filtered_df, column, regex_pattern, min_pct)
                
                # Get pattern information for metadata
                pattern_info = self._get_pattern_info()
                
                return AssetCheckResult(
                    passed=bool(result["passed"]),
                    description=f"Pattern matching: {result['description']}",
                    metadata={
                        "match_percentage": MetadataValue.float(float(result["match_percentage"])),
                        "required_percentage": MetadataValue.float(min_pct),
                        "match_count": MetadataValue.int(int(result["matching_values"])),
                        "total_count": MetadataValue.int(int(result["total_values"])),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                        **pattern_info
                    }
                )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Pattern matching failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_pattern_matching(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute pattern matching check: database → dataframe → analysis."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Run the same dataframe analysis
            pattern_column = self._get_check_config_value('pattern_column', 'column')
            pattern_regex = self._get_pattern_regex()
            result = self._analyze_pattern_matching(df, pattern_column, pattern_regex)
            
            # Get pattern information for metadata
            pattern_info = self._get_pattern_info()
            
            return AssetCheckResult(
                passed=bool(result["passed"]),
                description=f"Pattern matching: {result['description']}",
                metadata={
                    "match_percentage": MetadataValue.float(float(result["match_percentage"])),
                    "required_percentage": MetadataValue.float(self._get_check_config_value('pattern_min_pct', 95.0)),
                    "match_count": MetadataValue.int(int(result["matching_values"])),
                    "total_count": MetadataValue.int(int(result["total_values"])),
                    "data_size": MetadataValue.int(len(df)),
                    "dataframe_type": MetadataValue.text(type(df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                    **pattern_info
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Pattern matching failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_predicted_range(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute predicted range check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_predicted_range(
                context, filtered_df, self.predicted_range_metric, self.predicted_range_group_by
            )
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Predicted range check: {result['description']}",
                metadata={
                    "failed_groups": MetadataValue.json(result["failed_groups"]),
                    "total_groups": MetadataValue.int(int(result["total_groups"])),
                    "allowed_failures": MetadataValue.int(self.predicted_range_allowed_failures),
                    "prediction_method": MetadataValue.text(self.predicted_range_method),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Predicted range check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_percent_delta(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute percent delta check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_percent_delta(
                context, filtered_df, self._get_check_config_value('percent_delta_metric', 'num_rows'), self._get_check_config_value('percent_delta_group_by', None)
            )
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Percent delta check: {result['description']}",
                metadata={
                    "failed_groups": MetadataValue.json(result["failed_groups"] if isinstance(result["failed_groups"], (list, dict)) else []),
                    "total_groups": MetadataValue.int(int(result["total_groups"])),
                    "allowed_failures": MetadataValue.int(self._get_check_config_value('percent_delta_allowed_failures', 0)),
                    "max_delta": MetadataValue.float(float(result["max_delta"])),
                    "historical_data": MetadataValue.json(result["current_values_for_storage"]),
                    "loaded_history": MetadataValue.json(result.get("loaded_history", {})),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Percent delta check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_distribution_change(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute distribution change check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_distribution_change(
                context, filtered_df, self.distribution_change_column, 
                self.distribution_change_group_by, self.distribution_change_method,
                self.distribution_change_history, self.distribution_change_threshold,
                self.distribution_change_allowed_failures
            )
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Distribution change check: {result['description']}",
                metadata={
                    "failed_groups": MetadataValue.json(result["failed_groups"]),
                    "total_groups": MetadataValue.int(result["total_groups"]),
                    "allowed_failures": MetadataValue.int(self.distribution_change_allowed_failures),
                    "max_distance": MetadataValue.float(float(result["max_distance"])),
                    "method": MetadataValue.text(self.distribution_change_method),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Distribution change check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_anomaly_detection(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute anomaly detection check on dataframe."""
        # Get configuration using helper method
        metric = self._get_check_config_value('metric', 'num_rows')
        group_by = self._get_check_config_value('group_by')
        allowed_failures = self._get_check_config_value('allowed_failures', 0)
        method = self._get_check_config_value('method', 'z_score')
        
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            result = self._analyze_anomaly_detection(
                context, filtered_df, metric, group_by,
                threshold=self._get_check_config_value('threshold', 2.0),
                method=method,
                history=self._get_check_config_value('history', 10),
                allowed_failures=allowed_failures
            )
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Anomaly detection: {result['description']}",
                metadata={
                    "anomalous_groups": MetadataValue.json(result["anomalous_groups"] if isinstance(result["anomalous_groups"], (list, dict)) else []),
                    "total_groups": MetadataValue.int(result["total_groups"]),
                    "allowed_failures": MetadataValue.int(allowed_failures),
                    "max_anomaly_score": MetadataValue.float(float(result["max_anomaly_score"])),
                    "historical_data": MetadataValue.json(result["current_values_for_storage"]),
                    "loaded_history": MetadataValue.json(result.get("loaded_history", {})),
                    "method": MetadataValue.text(method),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Anomaly detection failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_data_type(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute data type validation on dataframe."""
        # Get configuration using helper method
        columns = self._get_check_config_value('data_type_columns', [])
        group_by = self._get_check_config_value('data_type_group_by')
        
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Debug: Log the data_type_columns configuration (removed sensitive data logging)
            context.log.info(f"Data type validation - data_type_columns: {columns}")
            context.log.info(f"Data type validation - available columns: {list(filtered_df.columns) if hasattr(filtered_df, 'columns') else 'unknown'}")
            context.log.info(f"Data type validation - dataframe shape: {filtered_df.shape if hasattr(filtered_df, 'shape') else 'unknown'}")
            
            # Check if we need to group by
            if group_by:
                # Check each group independently
                failed_groups = []
                total_groups = 0
                
                # Get unique groups
                if hasattr(filtered_df, 'select'):  # Polars
                    groups = filtered_df.select(filtered_df[group_by].unique()).to_numpy().flatten()
                else:  # Pandas
                    groups = filtered_df[group_by].unique()
                
                total_groups = len(groups)
                
                for group in groups:
                    # Filter data for this group
                    if hasattr(filtered_df, 'filter'):  # Polars
                        group_df = filtered_df.filter(filtered_df[group_by] == group)
                    else:  # Pandas
                        group_df = filtered_df[filtered_df[group_by] == group]
                    
                    # Run data type validation analysis for this group
                    result = self._analyze_data_type_validation(group_df, columns)
                    
                    # If this group fails the validation, add it to failed groups
                    if not result["passed"]:
                        failed_groups.append({
                            "group": str(group),
                            "failed_column_names": result["failed_column_names"],
                            "total_columns": int(result["total_columns"]),
                            "validation_results": result["type_validation_results"]
                        })
                
                passed = len(failed_groups) == 0
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"Data type validation: {len(failed_groups)}/{total_groups} groups failed",
                    metadata={
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups": MetadataValue.json(failed_groups),
                        "group_by": MetadataValue.text(group_by),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            else:
                # Original non-grouped logic
                result = self._analyze_data_type_validation(filtered_df, columns)
                
                return AssetCheckResult(
                    passed=bool(result["passed"]),
                    description=f"Data type validation: {result['description']}",
                    metadata={
                        "failed_column_names": MetadataValue.json(result["failed_column_names"]),
                        "total_columns": MetadataValue.int(int(result["total_columns"])),
                        "validation_results": MetadataValue.json(result["type_validation_results"]),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Data type validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_range_check(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute range validation on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Get configuration using helper method
            range_columns = self._get_check_config_value('range_columns', [])
            
            # Debug: Log the range_columns configuration
            context.log.info(f"Range validation - range_columns: {range_columns}")
            context.log.info(f"Range validation - asset_key: {getattr(self, '_asset_name', 'N/A')}")
            context.log.info(f"Range validation - dataframe shape: {filtered_df.shape}")
            
            result = self._analyze_range_validation(filtered_df, range_columns)
            
            # Debug: Log the result
            context.log.info(f"Range validation result - total_columns: {result.get('total_columns', 'N/A')}")
            context.log.info(f"Range validation result - passed: {result.get('passed', 'N/A')}")
            
            return AssetCheckResult(
                passed=bool(result["passed"]),
                description=f"Range validation: {result['description']}",
                metadata={
                    "failed_column_names": MetadataValue.json(result["failed_column_names"]),
                    "total_columns": MetadataValue.int(int(result["total_columns"])),
                    "validation_results": MetadataValue.json(result["range_validation_results"]),
                    "outlier_counts": MetadataValue.json(result["outlier_counts"]),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Range validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_uniqueness_check(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute uniqueness validation on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Get configuration using helper method
            uniqueness_columns = self._get_check_config_value('uniqueness_columns', [])
            
            result = self._analyze_uniqueness_validation(filtered_df, uniqueness_columns)
            
            return AssetCheckResult(
                passed=bool(result["passed"]),
                description=f"Uniqueness validation: {result['description']}",
                metadata={
                    "failed_checks": MetadataValue.json(result["failed_check_names"]),
                    "total_checks": MetadataValue.int(int(result["total_checks"])),
                    "validation_results": MetadataValue.json(result["uniqueness_validation_results"]),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                    "filtered": MetadataValue.bool(filtered_df is not df),
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Uniqueness validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_dataframe_custom_sql_monitor(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute custom SQL monitor check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Execute custom SQL query
            result = self._execute_custom_sql_query(filtered_df)
            
            # Build metadata
            metadata = {
                "query_result": MetadataValue.text(result["query_result"]),
                "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                "filtered": MetadataValue.bool(filtered_df is not df),
            }
            
            # Add group-specific metadata if using group_by
            if self.custom_sql_group_by:
                metadata.update({
                    "group_by": MetadataValue.text(self.custom_sql_group_by),
                    "total_groups": MetadataValue.int(result.get("total_groups", 0)),
                    "failed_groups_count": MetadataValue.int(len(result.get("failed_groups", []))),
                    "allowed_failures": MetadataValue.int(self.custom_sql_allowed_failures),
                    "group_results": MetadataValue.json({str(k): float(v) for k, v in result.get("group_results", {}).items()}),
                })
                if result.get("failed_groups"):
                    metadata["failed_groups"] = MetadataValue.json(result["failed_groups"])
            else:
                # Non-grouped metadata
                if self.custom_sql_expected_result is not None:
                    metadata.update({
                        "expected_result": MetadataValue.text(str(self.custom_sql_expected_result)),
                        "comparison": MetadataValue.text(self._safe_enum_to_string(self.custom_sql_comparison)),
                    })
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Custom SQL monitor: {result['description']}",
                metadata=metadata
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Custom SQL monitor check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    # ═══════════════════════════════════════════════════════════════
    # EXECUTION METHODS - Complex checks (always dataframe)
    # ═══════════════════════════════════════════════════════════════

    def _execute_dataframe_correlation_check(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute correlation check on dataframe."""
        try:
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values(df, self.correlation_column_x)
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "correlation_check", self.correlation_column_x, self.correlation_column_y, self.correlation_history)
            
            # Step 3: Calculate correlation for each group
            group_correlations = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) < 3:  # Need minimum history for correlation
                    group_correlations[group_key] = {
                        "passed": False,
                        "reason": f"Insufficient history: {len(group_history)} values (need 3+)",
                        "current_value": current_value,
                        "correlation": None,
                        "history_count": len(group_history)
                    }
                    continue
                
                # Calculate correlation
                correlation, p_value = self._calculate_correlation(group_history, self.correlation_column_y)
                
                # Check against thresholds
                passed = True
                if self._get_check_config_value('correlation_min', None) is not None and correlation < self._get_check_config_value('correlation_min', None):
                    passed = False
                if self._get_check_config_value('correlation_max', None) is not None and correlation > self._get_check_config_value('correlation_max', None):
                    passed = False
                
                group_correlations[group_key] = {
                    "passed": passed,
                    "reason": f"Correlation within thresholds" if passed else f"Correlation outside thresholds",
                    "current_value": current_value,
                    "correlation": correlation,
                    "p_value": p_value,
                    "history_count": len(group_history)
                }
            
            # Step 4: Apply allowed failures logic
            failed_groups = [k for k, v in group_correlations.items() if not v["passed"]]
            total_groups = len(group_correlations)
            allowed_failures = self.correlation_allowed_failures
            
            overall_passed = len(failed_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if group_correlations:
                correlations = [v["correlation"] for v in group_correlations.values() if v["correlation"] is not None]
                max_correlation = max(correlations) if correlations else 0.0
            else:
                max_correlation = 0.0
            
            return {
                "passed": overall_passed,
                "description": self._create_correlation_description(overall_passed, failed_groups, total_groups, allowed_failures, max_correlation),
                "max_correlation": max_correlation,
                "total_groups": total_groups,
                "failed_groups": len(failed_groups),
                "allowed_failures": allowed_failures,
                "group_correlations": group_correlations,
                "current_values_for_storage": current_values,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Correlation check failed: {str(e)}",
                "max_correlation": 0.0,
                "total_groups": 0,
                "failed_groups": 0,
                "allowed_failures": 0,
                "group_correlations": {},
                "current_values_for_storage": {},
                "error": str(e)
            }

    def _execute_dataframe_custom_dataframe_check(self, context: AssetCheckExecutionContext, df) -> AssetCheckResult:
        """Execute custom dataframe check on dataframe."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Execute custom dataframe query
            result = self._execute_custom_dataframe_query(filtered_df)
            
            # Build metadata
            metadata = {
                "query_result": MetadataValue.text(result["query_result"]),
                "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                "filtered": MetadataValue.bool(filtered_df is not df),
            }
            
            # Add group-specific metadata if using group_by
            if self.custom_dataframe_group_by:
                metadata.update({
                    "group_by": MetadataValue.text(self.custom_dataframe_group_by),
                    "total_groups": MetadataValue.int(result.get("total_groups", 0)),
                    "failed_groups_count": MetadataValue.int(len(result.get("failed_groups", []))),
                    "allowed_failures": MetadataValue.int(self.custom_dataframe_allowed_failures),
                    "group_results": MetadataValue.json({str(k): float(v) for k, v in result.get("group_results", {}).items()}),
                })
                if result.get("failed_groups"):
                    metadata["failed_groups"] = MetadataValue.json(result["failed_groups"])
            else:
                # Non-grouped metadata
                if self.custom_dataframe_expected_result is not None:
                    metadata.update({
                        "expected_result": MetadataValue.text(str(self.custom_dataframe_expected_result)),
                        "comparison": MetadataValue.text(self._safe_enum_to_string(self.custom_dataframe_comparison)),
                    })
            
            return AssetCheckResult(
                passed=result["passed"],
                description=f"Custom dataframe check: {result['description']}",
                metadata=metadata
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Custom dataframe check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_custom_dataframe_check(self, context: AssetCheckExecutionContext, df, check_cfg: dict) -> AssetCheckResult:
        """Execute custom dataframe check from configuration."""
        try:
            # Apply WHERE clause filtering
            filtered_df = self._filter_dataframe(df)
            
            # Extract configuration from check_cfg
            # Handle both dict and Pydantic model
            if isinstance(check_cfg, CustomDataframeCheckConfig):
                query = check_cfg.python_code
                expected_result = check_cfg.expected_result
                comparison = check_cfg.comparison
                description = check_cfg.name or 'Custom dataframe check'
                group_by = check_cfg.group_by if hasattr(check_cfg, 'group_by') else None
                allowed_failures = check_cfg.allowed_failures if hasattr(check_cfg, 'allowed_failures') else 0
            else:
                query = check_cfg.get('python_code')
                expected_result = check_cfg.get('expected_result')
                comparison = check_cfg.get('comparison', 'equals')
                description = check_cfg.get('name', 'Custom dataframe check')
                group_by = check_cfg.get('group_by')
                allowed_failures = check_cfg.get('allowed_failures', 0)
            
            # Execute the query
            if group_by:
                # Grouped scenario
                group_results = {}
                failed_groups = []
                total_groups = 0
                
                if hasattr(filtered_df, 'select'):  # Polars
                    groups = filtered_df.select(group_by).unique().to_numpy().flatten()
                    total_groups = len(groups)
                    
                    for group_name in groups:
                        group_df = filtered_df.filter(filtered_df[group_by] == group_name)
                        try:
                            # Execute the query as Python code with df available
                            local_vars = {'df': group_df, 'pd': pd, 'np': np}
                            exec(f"result = {query}", {}, local_vars)
                            metric_value = float(local_vars['result'])
                            group_results[group_name] = metric_value
                            
                            # Check if this group passes
                            if expected_result is not None:
                                if not self._compare_values(str(metric_value), str(expected_result), comparison):
                                    failed_groups.append({
                                        "group": group_name,
                                        "actual": metric_value,
                                        "expected": expected_result
                                    })
                        except Exception as e:
                            failed_groups.append({
                                "group": group_name,
                                "error": str(e)
                            })
                else:  # Pandas
                    groups = filtered_df[group_by].unique()
                    total_groups = len(groups)
                    
                    for group_name in groups:
                        group_df = filtered_df[filtered_df[group_by] == group_name]
                        try:
                            # Execute the query as Python code with df available
                            local_vars = {'df': group_df, 'pd': pd, 'np': np}
                            exec(f"result = {query}", {}, local_vars)
                            metric_value = float(local_vars['result'])
                            group_results[group_name] = metric_value
                            
                            # Check if this group passes
                            if expected_result is not None:
                                if not self._compare_values(str(metric_value), str(expected_result), comparison):
                                    failed_groups.append({
                                        "group": group_name,
                                        "actual": metric_value,
                                        "expected": expected_result
                                    })
                        except Exception as e:
                            failed_groups.append({
                                "group": group_name,
                                "error": str(e)
                            })
                
                passed = len(failed_groups) <= allowed_failures
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"{description}: {len(failed_groups)}/{total_groups} groups failed",
                    metadata={
                        "query": MetadataValue.text(query),
                        "group_by": MetadataValue.text(group_by),
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups_count": MetadataValue.int(len(failed_groups)),
                        "allowed_failures": MetadataValue.int(allowed_failures),
                        "group_results": MetadataValue.json({str(k): float(v) for k, v in group_results.items()}),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
            else:
                # Non-grouped scenario
                try:
                    # Execute the query as Python code with df available
                    local_vars = {'df': filtered_df, 'pd': pd, 'np': np}
                    exec(f"result = {query}", {}, local_vars)
                    query_result = str(local_vars['result'])
                except Exception as e:
                    # Fallback to eval for simple expressions
                    try:
                        if hasattr(filtered_df, 'select'):  # Polars
                            result = filtered_df.select(query).to_numpy()
                        else:  # Pandas
                            result = filtered_df.eval(query)
                        query_result = str(result)
                    except Exception as eval_error:
                        return AssetCheckResult(
                            passed=False,
                            description=f"Custom dataframe check failed: {str(e)} (eval also failed: {str(eval_error)})",
                            metadata={"error": MetadataValue.text(str(e)), "eval_error": MetadataValue.text(str(eval_error))}
                        )
                
                # If no expected result specified, just return the query result
                if expected_result is None:
                    return AssetCheckResult(
                        passed=True,
                        description=f"{description}: {query_result}",
                        metadata={
                            "query": MetadataValue.text(query),
                            "query_result": MetadataValue.text(query_result),
                            "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                            "filtered": MetadataValue.bool(filtered_df is not df),
                        }
                    )
                
                # Perform comparison if expected result is specified
                passed = self._compare_values(query_result, str(expected_result), comparison)
                
                return AssetCheckResult(
                    passed=passed,
                    description=f"{description}: {query_result} (expected: {expected_result})",
                    metadata={
                        "query": MetadataValue.text(query),
                        "query_result": MetadataValue.text(query_result),
                        "expected_result": MetadataValue.text(str(expected_result)),
                        "comparison": MetadataValue.text(self._safe_enum_to_string(comparison)),
                        "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split('.')[0]),
                        "filtered": MetadataValue.bool(filtered_df is not df),
                    }
                )
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Custom dataframe check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _fetch_data_as_dataframe(self, database_resource):
        """Fetch data from database as dataframe with optional filtering using adapter pattern."""
        try:
            # Build WHERE clause for filtering
            where_conditions = self._build_where_clause()
            where_sql = f" WHERE {where_conditions}" if where_conditions else ""
            
            # Construct query with optional sampling
            if self.sample_size:
                if self.sample_method == "random":
                    query = f"SELECT * FROM {self.table_name}{where_sql} ORDER BY RANDOM() LIMIT {self.sample_size}"
                else:  # top
                    query = f"SELECT * FROM {self.table_name}{where_sql} LIMIT {self.sample_size}"
            else:
                query = f"SELECT * FROM {self.table_name}{where_sql}"
            
            # Execute query using database adapter
            result = self._execute_database_query(database_resource, query)
            
            # Debug: Log query and result info (removed sensitive data logging)
            print(f"DEBUG: Query executed: {query}")
            print(f"DEBUG: Result type: {type(result)}")
            print(f"DEBUG: Result length: {len(result) if isinstance(result, list) else 'N/A'}")
            
            # Convert result to dataframe
            import pandas as pd
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], (list, tuple)):
                    # Multiple columns - try to get column names from database
                    try:
                        # Get column names from database schema
                        schema_query = f"PRAGMA table_info({self.table_name})"
                        schema_result = self._execute_database_query(database_resource, schema_query)
                        
                        print(f"DEBUG: Schema query: {schema_query}")
                        print(f"DEBUG: Schema result: {schema_result}")
                        
                        if schema_result and len(schema_result) > 0:
                            # Extract column names from schema
                            columns = [row[1] for row in schema_result]  # Column name is at index 1
                            print(f"DEBUG: Extracted columns: {columns}")
                        else:
                            # Fallback to generic column names
                            columns = [f"col_{i}" for i in range(len(result[0]))]
                            print(f"DEBUG: Using fallback columns: {columns}")
                    except Exception as e:
                        # Fallback to generic column names if schema query fails
                        columns = [f"col_{i}" for i in range(len(result[0]))]
                        print(f"DEBUG: Schema query failed: {e}, using fallback columns: {columns}")
                    
                    df = pd.DataFrame(result, columns=columns)
                    print(f"DEBUG: Created DataFrame with shape: {df.shape}")
                    print(f"DEBUG: DataFrame columns: {list(df.columns)}")
                else:
                    # Single column
                    df = pd.DataFrame(result, columns=['value'])
                    print(f"DEBUG: Created single-column DataFrame with shape: {df.shape}")
            else:
                # Empty result - try to get column names from schema
                try:
                    schema_query = f"PRAGMA table_info({self.table_name})"
                    schema_result = self._execute_database_query(database_resource, schema_query)
                    
                    print(f"DEBUG: Empty result, schema query: {schema_query}")
                    print(f"DEBUG: Empty result, schema result: {schema_result}")
                    print(f"DEBUG: Schema result type: {type(schema_result)}")
                    print(f"DEBUG: Schema result length: {len(schema_result) if isinstance(schema_result, (list, tuple)) else 'N/A'}")
                    
                    if schema_result:
                        # Handle both single tuple and list of tuples
                        if isinstance(schema_result, tuple):
                            # Single column
                            columns = [schema_result[1]]  # Column name is at index 1
                            print(f"DEBUG: Single tuple schema result, columns: {columns}")
                        elif isinstance(schema_result, list) and len(schema_result) > 0:
                            # Multiple columns
                            columns = [row[1] for row in schema_result]  # Column name is at index 1
                            print(f"DEBUG: List of tuples schema result, columns: {columns}")
                        else:
                            # Empty schema result
                            columns = []
                            print(f"DEBUG: Empty schema result")
                        df = pd.DataFrame(columns=columns)
                        print(f"DEBUG: Created empty DataFrame with columns: {list(df.columns)}")
                    else:
                        df = pd.DataFrame()
                        print(f"DEBUG: Created empty DataFrame with no columns")
                except Exception as e:
                    df = pd.DataFrame()
                    print(f"DEBUG: Schema query failed for empty result: {e}, created empty DataFrame")
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to fetch data from {self.table_name}: {str(e)}")

    def _build_where_clause(self) -> str:
        """Build WHERE clause for time-based filtering and custom conditions."""
        conditions = []
        
        # Custom WHERE clause
        if self.where_clause:
            conditions.append(f"({self.where_clause})")
        
        # Time-based filtering
        if self.time_filter_column and (self.hours_back or self.days_back):
            if self.hours_back:
                conditions.append(f"{self.time_filter_column} >= datetime('now', '-{self.hours_back} hours')")
            elif self.days_back:
                conditions.append(f"{self.time_filter_column} >= datetime('now', '-{self.days_back} days')")
        
        # Combine conditions with AND
        return " AND ".join(conditions) if conditions else ""

    def _filter_dataframe(self, df) -> Any:
        """Apply WHERE clause filtering to dataframe."""
        # If no filtering is needed, return original dataframe
        if not self.where_clause and not (self.time_filter_column and (self.hours_back or self.days_back)):
            return df
        
        # For dataframe filtering, we need to convert WHERE clause to dataframe operations
        # This is a simplified implementation - in practice, you might want more sophisticated parsing
        filtered_df = df
        
        # Handle time-based filtering
        if self.time_filter_column and (self.hours_back or self.days_back):
            import pandas as pd
            from datetime import datetime, timedelta
            
            # Calculate cutoff time
            if self.hours_back:
                cutoff_time = datetime.now() - timedelta(hours=self.hours_back)
            else:  # days_back
                cutoff_time = datetime.now() - timedelta(days=self.days_back)
            
            # Filter dataframe
            if hasattr(df, 'filter'):  # Polars
                filtered_df = filtered_df.filter(df[self.time_filter_column] >= cutoff_time)
            else:  # Pandas
                filtered_df = filtered_df[filtered_df[self.time_filter_column] >= cutoff_time]
        
        # Handle custom WHERE clause (simplified - would need more sophisticated parsing)
        if self.where_clause:
            # For dataframe, we'd need to parse the WHERE clause and convert to dataframe operations
            # This is a placeholder - in practice, you'd want a proper SQL-to-dataframe parser
            # For now, we'll skip custom WHERE clauses for dataframe filtering
            pass
        
        return filtered_df

    def _compute_dataframe_metric(self, df, metric: str) -> float:
        """Compute metric value for dataframe (pandas or polars)."""
        if metric == "num_rows":
            if hasattr(df, 'height'):  # Polars
                return float(df.height)
            else:  # Pandas
                return float(len(df))
                
        elif ":" in metric:
            metric_type, column = metric.split(":", 1)
            
            # NULL-related metrics
            if metric_type == "null_count":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].null_count()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].isnull().sum())
                    
            elif metric_type == "null_pct":
                if hasattr(df, 'select'):  # Polars
                    null_count = df.select(df[column].null_count()).to_numpy()[0][0]
                    total = df.height
                else:  # Pandas
                    null_count = df[column].isnull().sum()
                    total = len(df)
                return float((null_count / total * 100) if total > 0 else 0)
                
            # DISTINCT metrics
            elif metric_type == "distinct_count":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].n_unique()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].nunique())
                    
            # AGGREGATION metrics
            elif metric_type == "mean":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].mean()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].mean())
                    
            elif metric_type == "sum":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].sum()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].sum())
                    
            elif metric_type == "max":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].max()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].max())
                    
            elif metric_type == "min":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].min()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].min())
                    
            # STATISTICAL metrics
            elif metric_type == "std":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].std()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].std())
                    
            elif metric_type == "var":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].var()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].var())
                    
            elif metric_type == "median":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].median()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].median())
                    
            elif metric_type == "mode":
                if hasattr(df, 'select'):  # Polars
                    # Polars doesn't have mode, use pandas logic
                    mode_values = df[column].mode()
                    return float(mode_values[0]) if len(mode_values) > 0 else 0.0
                else:  # Pandas
                    mode_values = df[column].mode()
                    return float(mode_values[0]) if len(mode_values) > 0 else 0.0
                    
            elif metric_type == "range":
                if hasattr(df, 'select'):  # Polars
                    max_val = df.select(df[column].max()).to_numpy()[0][0]
                    min_val = df.select(df[column].min()).to_numpy()[0][0]
                else:  # Pandas
                    max_val = df[column].max()
                    min_val = df[column].min()
                return float(max_val - min_val) if max_val is not None and min_val is not None else 0.0
                    
            elif metric_type == "iqr":
                if hasattr(df, 'select'):  # Polars
                    q75 = df.select(df[column].quantile(0.75)).to_numpy()[0][0]
                    q25 = df.select(df[column].quantile(0.25)).to_numpy()[0][0]
                else:  # Pandas
                    q75 = df[column].quantile(0.75)
                    q25 = df[column].quantile(0.25)
                return float(q75 - q25) if q75 is not None and q25 is not None else 0.0
                    
            elif metric_type == "skew":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].skew()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].skew())
                    
            elif metric_type == "kurt":
                if hasattr(df, 'select'):  # Polars
                    return float(df.select(df[column].kurtosis()).to_numpy()[0][0])
                else:  # Pandas
                    return float(df[column].kurtosis())
                    
            elif metric_type == "cv":
                # Coefficient of variation = std / mean
                if hasattr(df, 'select'):  # Polars
                    std_val = df.select(df[column].std()).to_numpy()[0][0]
                    mean_val = df.select(df[column].mean()).to_numpy()[0][0]
                else:  # Pandas
                    std_val = df[column].std()
                    mean_val = df[column].mean()
                return float(std_val / mean_val) if mean_val != 0 and mean_val is not None and std_val is not None else 0.0
                    
            elif metric_type == "zscore":
                # Z-score of the mean (how many std devs from 0)
                if hasattr(df, 'select'):  # Polars
                    mean_val = df.select(df[column].mean()).to_numpy()[0][0]
                    std_val = df.select(df[column].std()).to_numpy()[0][0]
                else:  # Pandas
                    mean_val = df[column].mean()
                    std_val = df[column].std()
                return float(mean_val / std_val) if std_val != 0 and std_val is not None and mean_val is not None else 0.0
                    
            elif metric_type == "outlier_count":
                # Count values beyond 3 standard deviations
                if hasattr(df, 'select'):  # Polars
                    mean_val = df.select(df[column].mean()).to_numpy()[0][0]
                    std_val = df.select(df[column].std()).to_numpy()[0][0]
                    if mean_val is not None and std_val is not None and std_val != 0:
                        lower_bound = mean_val - 3 * std_val
                        upper_bound = mean_val + 3 * std_val
                        outlier_count = df.select(
                            ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
                        ).to_numpy()[0][0]
                        return float(outlier_count)
                else:  # Pandas
                    mean_val = df[column].mean()
                    std_val = df[column].std()
                    if mean_val is not None and std_val is not None and std_val != 0:
                        lower_bound = mean_val - 3 * std_val
                        upper_bound = mean_val + 3 * std_val
                        outlier_count = ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
                        return float(outlier_count)
                return 0.0
                    
            # PERCENTILE metrics
            elif metric_type.startswith("p") and metric_type[1:].isdigit():
                percentile = int(metric_type[1:])
                if 0 <= percentile <= 100:
                    if hasattr(df, 'select'):  # Polars
                        return float(df.select(df[column].quantile(percentile / 100.0)).to_numpy()[0][0])
                    else:  # Pandas
                        return float(df[column].quantile(percentile / 100.0))
                    
        raise ValueError(f"Unsupported metric: {metric}")

    def _compute_database_metric(self, metric: str, database_resource, context=None) -> float:
        """Compute metric value for database using SQL with adapter pattern."""
        try:
            # Build WHERE clause for filtering
            where_conditions = self._build_where_clause()
            where_sql = f" WHERE {where_conditions}" if where_conditions else ""
            
            if metric == "num_rows":
                query = f"SELECT COUNT(*) FROM {self.table_name}{where_sql}"
                # Debug: Log the SQL query if context is available
                if context:
                    context.log.info(f"Database metric - SQL query: {query}")
                    context.log.info(f"Database metric - Table name: {self.table_name}")
                    context.log.info(f"Database metric - Where conditions: {where_conditions}")
            elif ":" in metric:
                metric_type, column = metric.split(":", 1)
                if metric_type == "null_count":
                    query = f"SELECT COUNT(*) - COUNT({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "null_pct":
                    query = f"SELECT ((COUNT(*) - COUNT({column})) * 100.0 / COUNT(*)) FROM {self.table_name}{where_sql}"
                elif metric_type == "distinct_count":
                    query = f"SELECT COUNT(DISTINCT {column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "mean":
                    query = f"SELECT AVG({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "sum":
                    query = f"SELECT SUM({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "max":
                    query = f"SELECT MAX({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "min":
                    query = f"SELECT MIN({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "std":
                    query = f"SELECT STDDEV({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "var":
                    query = f"SELECT VAR({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "median":
                    query = f"SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "mode":
                    # Most frequent value - complex SQL, use dataframe processing
                    raise ValueError(f"Mode metric not supported in database mode - use dataframe processing")
                elif metric_type == "range":
                    query = f"SELECT MAX({column}) - MIN({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "iqr":
                    query = f"SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) - PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "skew":
                    # Skewness - complex SQL, use dataframe processing
                    raise ValueError(f"Skewness metric not supported in database mode - use dataframe processing")
                elif metric_type == "kurt":
                    # Kurtosis - complex SQL, use dataframe processing
                    raise ValueError(f"Kurtosis metric not supported in database mode - use dataframe processing")
                elif metric_type == "cv":
                    # Coefficient of variation = std / mean
                    query = f"SELECT STDDEV({column}) / AVG({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "zscore":
                    # Z-score of the mean
                    query = f"SELECT AVG({column}) / STDDEV({column}) FROM {self.table_name}{where_sql}"
                elif metric_type == "outlier_count":
                    # Count values beyond 3 standard deviations
                    query = f"""
                    SELECT COUNT(*) FROM {self.table_name}{where_sql}
                    WHERE {column} < (AVG({column}) - 3 * STDDEV({column})) 
                       OR {column} > (AVG({column}) + 3 * STDDEV({column}))
                    """
                elif metric_type.startswith("p") and metric_type[1:].isdigit():
                    percentile = int(metric_type[1:])
                    if 0 <= percentile <= 100:
                        query = f"SELECT PERCENTILE_CONT({percentile / 100.0}) WITHIN GROUP (ORDER BY {column}) FROM {self.table_name}{where_sql}"
                    else:
                        raise ValueError(f"Invalid percentile: {percentile}")
                else:
                    raise ValueError(f"Unsupported metric type: {metric_type}")
            else:
                raise ValueError(f"Unsupported metric format: {metric}")
            
            # Execute query using database adapter
            result = self._execute_database_query(database_resource, query)
            if result and len(result) > 0 and len(result[0]) > 0:
                return float(result[0][0]) if result[0][0] is not None else 0.0
            else:
                return 0.0
            
        except Exception as e:
            raise Exception(f"Database metric computation failed: {str(e)}")

    def _execute_database_query(self, database_resource, query: str) -> list:
        """Execute database query using adapter pattern for different database resources."""
        try:
            # Try different database resource patterns
            if hasattr(database_resource, 'get_connection'):
                # Pattern: database_resource.get_connection() -> connection
                with database_resource.get_connection() as conn:
                    if hasattr(conn, 'execute'):
                        result = conn.execute(query)
                        if hasattr(result, 'fetchall'):
                            return result.fetchall()
                        elif hasattr(result, 'fetchone'):
                            # For single-row results (like COUNT queries)
                            row = result.fetchone()
                            return [row] if row else []
                        elif hasattr(result, 'df'):
                            # DuckDB with pandas
                            df = result.df()
                            if df.empty:
                                return []
                            elif len(df.columns) == 1:
                                return df.iloc[:, 0].tolist()
                            else:
                                return df.values.tolist()
                        else:
                            return list(result)
                    else:
                        raise ValueError("Connection object must have execute() method")
                        
            elif hasattr(database_resource, 'get_client'):
                # Pattern: database_resource.get_client() -> client
                with database_resource.get_client() as client:
                    if hasattr(client, 'query'):
                        # BigQuery pattern
                        result = client.query(query).result()
                        return [row[0] for row in result]
                    elif hasattr(client, 'execute_query'):
                        # Redshift/Athena pattern
                        result = client.execute_query(query, fetch_results=True)
                        return [row[0] for row in result]
                    else:
                        raise ValueError("Client object must have query() or execute_query() method")
                        
            elif hasattr(database_resource, 'execute'):
                # Pattern: database_resource.execute() directly
                result = database_resource.execute(query)
                if hasattr(result, 'fetchone'):
                    return result.fetchone()
                else:
                    return list(result)
                    
            else:
                # Try to detect the pattern automatically
                if hasattr(database_resource, 'cursor'):
                    # MySQL pattern
                    with database_resource.cursor() as cursor:
                        cursor.execute(query)
                        return cursor.fetchone()
                else:
                    raise ValueError(
                        f"Unsupported database resource type: {type(database_resource)}. "
                        "Resource must implement one of these patterns:\n"
                        "1. get_connection() -> connection with execute()\n"
                        "2. get_client() -> client with query() or execute_query()\n"
                        "3. execute() method directly\n"
                        "4. cursor() method (MySQL-style)"
                    )
                    
        except Exception as e:
            raise Exception(f"Database query execution failed: {str(e)}")

    def _analyze_benford_law(self, df, column: str) -> dict:
        """Enhanced Benford's Law analysis with statistical rigor."""
        
        # Benford's Law expected distributions
        BENFORD_DISTRIBUTIONS = {
            1: {  # First digit (1-9)
                1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079,
                6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
            },
            2: {  # Second digit (0-9)
                0: 0.1197, 1: 0.1139, 2: 0.1088, 3: 0.1043, 4: 0.1003,
                5: 0.0967, 6: 0.0934, 7: 0.0904, 8: 0.0876, 9: 0.0850
            },
            12: {  # First two digits (10-99)
                **{i: np.log10(1 + 1/i) for i in range(10, 100)}
            }
        }
        
        try:
            # Step 1: Data preprocessing and cleaning
            clean_data = self._preprocess_benford_data(df, column)
            
            if len(clean_data) < self._get_check_config_value('benford_min_samples', 100):
                return {
                    "passed": False,
                    "description": f"Insufficient data: {len(clean_data)} < {self._get_check_config_value('benford_min_samples', 100)} required",
                    "max_deviation": 1.0,
                    "sample_size": len(clean_data),
                    "chi_square_p_value": None,
                    "distribution_details": {}
                }
            
            # Step 2: Extract digits based on position
            digits_data = self._extract_benford_digits(clean_data, self._get_check_config_value('benford_digit_position', 1))
            
            if len(digits_data) == 0:
                return {
                    "passed": False,
                    "description": "No valid digits found after preprocessing",
                    "max_deviation": 1.0,
                    "sample_size": 0,
                    "chi_square_p_value": None,
                    "distribution_details": {}
                }
            
            # Step 3: Calculate actual distribution
            expected_dist = BENFORD_DISTRIBUTIONS[self._get_check_config_value('benford_digit_position', 1)]
            actual_dist = self._calculate_digit_distribution(digits_data, expected_dist.keys())
            
            # Step 4: Statistical analysis
            max_deviation = max(abs(actual_dist.get(digit, 0) - expected_dist[digit]) 
                              for digit in expected_dist.keys())
            
            # Step 5: Chi-square goodness of fit test
            chi_square_stat, chi_square_p = self._chi_square_test(digits_data, expected_dist)
            
            # Step 6: Determine if test passes
            # Use both max deviation and chi-square test
            deviation_passed = max_deviation <= self._get_check_config_value('benford_threshold')
            chi_square_passed = chi_square_p > 0.05 if chi_square_p is not None else True
            overall_passed = deviation_passed and chi_square_passed
            
            # Step 7: Detailed results
            distribution_details = {}
            for digit in expected_dist.keys():
                expected = expected_dist[digit]
                actual = actual_dist.get(digit, 0)
                deviation = abs(actual - expected)
                distribution_details[str(digit)] = {
                    "expected": expected,
                    "actual": actual,
                    "deviation": deviation,
                    "count": digits_data.count(digit) if hasattr(digits_data, 'count') else sum(1 for x in digits_data if x == digit)
                }
            
            return {
                "passed": overall_passed,
                "description": self._create_benford_description(overall_passed, max_deviation, chi_square_p),
                "max_deviation": max_deviation,
                "sample_size": len(digits_data),
                "chi_square_statistic": chi_square_stat,
                "chi_square_p_value": chi_square_p,
                                    "digit_position": self._get_check_config_value('benford_digit_position', 1),
                "distribution_details": distribution_details,
                "deviation_test_passed": deviation_passed,
                "chi_square_test_passed": chi_square_passed,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Benford's Law analysis failed: {str(e)}",
                "max_deviation": 1.0,
                "sample_size": 0,
                "chi_square_p_value": None,
                "distribution_details": {},
                "error": str(e)
            }

    def _preprocess_benford_data(self, df, column: str) -> list:
        """Clean and preprocess data for Benford's Law analysis."""
        
        # Handle both pandas and polars
        if hasattr(df, 'select'):  # Polars
            import polars as pl
            # Get non-null values as strings
            series = df.select(pl.col(column).cast(pl.Utf8)).to_pandas().iloc[:, 0]
        else:  # Pandas
            series = df[column].astype(str)
        
        clean_values = []
        
        for value in series:
            if pd.isna(value) or value in ['', 'nan', 'None', 'null']:
                continue
                
            # Convert to string and clean
            str_value = str(value).strip()
            
            # Remove common prefixes/suffixes (currency symbols, etc.)
            str_value = str_value.replace('$', '').replace(',', '').replace(' ', '')
            str_value = str_value.replace('€', '').replace('£', '').replace('¥', '')
            
            # Handle negative numbers (use absolute value)
            if str_value.startswith('-'):
                str_value = str_value[1:]
            
            # Handle decimal numbers (use integer part)
            if '.' in str_value:
                str_value = str_value.split('.')[0]
            
            # Must be numeric and positive
            try:
                numeric_value = float(str_value)
                if numeric_value > 0:  # Benford's Law applies to positive numbers
                    clean_values.append(str_value)
            except (ValueError, TypeError):
                continue
        
        return clean_values

    def _extract_benford_digits(self, clean_data: list, digit_position: int) -> list:
        """Extract specific digits for Benford's Law analysis."""
        
        digits = []
        
        for value_str in clean_data:
            # Remove leading zeros
            value_str = value_str.lstrip('0')
            
            if len(value_str) == 0:
                continue
                
            try:
                if digit_position == 1:  # First digit
                    digit = int(value_str[0])
                    if 1 <= digit <= 9:  # First digit must be 1-9
                        digits.append(digit)
                        
                elif digit_position == 2:  # Second digit
                    if len(value_str) >= 2:
                        digit = int(value_str[1])
                        if 0 <= digit <= 9:  # Second digit can be 0-9
                            digits.append(digit)
                            
                elif digit_position == 12:  # First two digits
                    if len(value_str) >= 2:
                        first_two = int(value_str[:2])
                        if 10 <= first_two <= 99:  # First two digits: 10-99
                            digits.append(first_two)
                            
            except (ValueError, IndexError):
                continue
        
        return digits

    def _calculate_digit_distribution(self, digits: list, expected_keys) -> dict:
        """Calculate the actual distribution of digits."""
        
        if len(digits) == 0:
            return {}
        
        # Count occurrences
        digit_counts = {}
        for digit in digits:
            digit_counts[digit] = digit_counts.get(digit, 0) + 1
        
        # Convert to proportions
        total_count = len(digits)
        distribution = {}
        for key in expected_keys:
            distribution[key] = digit_counts.get(key, 0) / total_count
            
        return distribution

    def _chi_square_test(self, digits: list, expected_dist: dict):
        """Perform chi-square goodness of fit test."""
        
        try:
            from scipy import stats
            
            # Observed frequencies
            observed = []
            expected = []
            
            total_count = len(digits)
            
            for digit in sorted(expected_dist.keys()):
                observed_count = digits.count(digit) if hasattr(digits, 'count') else sum(1 for x in digits if x == digit)
                expected_count = expected_dist[digit] * total_count
                
                observed.append(observed_count)
                expected.append(expected_count)
            
            # Perform chi-square test
            chi2_stat, p_value = stats.chisquare(observed, expected)
            
            return float(chi2_stat), float(p_value)
            
        except ImportError:
            # Fallback if scipy not available
            return None, None
        except Exception:
            return None, None

    def _create_benford_description(self, passed: bool, max_deviation: float, chi_square_p: float) -> str:
        """Create a descriptive result message."""
        
        status = "PASSED" if passed else "FAILED"
        description = f"Benford's Law check {status}"
        
        if self._get_check_config_value('benford_digit_position', 1) == 1:
            position_desc = "first digit"
        elif self._get_check_config_value('benford_digit_position', 1) == 2:
            position_desc = "second digit"
        elif self._get_check_config_value('benford_digit_position', 1) == 12:
            position_desc = "first two digits"
        else:
            position_desc = f"digit position {self._get_check_config_value('benford_digit_position', 1)}"
        
        description += f" ({position_desc})"
        description += f" - Max deviation: {max_deviation:.4f}"
        
        if chi_square_p is not None:
            description += f", χ² p-value: {chi_square_p:.4f}"
        else:
            description += f", χ² p-value: N/A"
        
        return description

    def _calculate_shannon_entropy(self, df, column: str) -> float:
        """Calculate Shannon entropy (same for pandas/polars)."""
        # Get value counts
        if hasattr(df, 'select'):  # Polars
            value_counts = df[column].value_counts().to_pandas()['count'].values
        else:  # Pandas
            value_counts = df[column].value_counts().values
        
        # Calculate probabilities
        probabilities = value_counts / value_counts.sum()
        
        # Shannon entropy: H = -Σ(p * log2(p))
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        
        return entropy

    def _analyze_predicted_range(self, context: AssetCheckExecutionContext, df, metric: str, group_by: Optional[str] = None) -> dict:
        """Analyze predicted range using time series forecasting."""
        
        try:
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values(df, metric, group_by)
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "predicted_range", metric, group_by, self.predicted_range_history)
            
            # Step 3: Generate predictions for each group
            predictions = {}
            group_results = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) < 3:  # Need minimum history for prediction
                    predictions[group_key] = {
                        "passed": False,
                        "reason": f"Insufficient history: {len(group_history)} values (need 3+)",
                        "current_value": current_value,
                        "predicted_range": None,
                        "confidence": None
                    }
                    continue
                
                # Generate prediction
                prediction_result = self._generate_prediction(
                    group_history, 
                    method=self.predicted_range_method,
                    confidence=self.predicted_range_confidence
                )
                
                # Check if current value is within predicted range
                in_range = (prediction_result["lower_bound"] <= current_value <= prediction_result["upper_bound"])
                
                predictions[group_key] = {
                    "passed": in_range,
                    "reason": "Within predicted range" if in_range else "Outside predicted range",
                    "current_value": current_value,
                    "predicted_value": prediction_result["predicted_value"],
                    "predicted_range": (prediction_result["lower_bound"], prediction_result["upper_bound"]),
                    "confidence": self.predicted_range_confidence,
                    "deviation": abs(current_value - prediction_result["predicted_value"]),
                    "history_count": len(group_history)
                }
                
                group_results[group_key] = prediction_result
            
            # Step 4: Apply allowed failures logic
            failed_groups = [k for k, v in predictions.items() if not v["passed"]]
            total_groups = len(predictions)
            allowed_failures = self.predicted_range_allowed_failures
            
            overall_passed = len(failed_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if predictions:
                deviations = [v["deviation"] for v in predictions.values() if v["deviation"] is not None]
                max_deviation = max(deviations) if deviations else 0.0
            else:
                max_deviation = 0.0
            
            # Step 6: Store current values for future predictions
            # Note: Current values are now stored in metadata, not files
            
            return {
                "passed": overall_passed,
                "description": self._create_predicted_range_description(overall_passed, failed_groups, total_groups, allowed_failures),
                "max_deviation": max_deviation,
                "total_groups": total_groups,
                "failed_groups": len(failed_groups),
                "allowed_failures": allowed_failures,
                "group_predictions": predictions,
                "method": self.predicted_range_method,
                "confidence": self.predicted_range_confidence,
                "current_values_for_storage": current_values,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Predicted range analysis failed: {str(e)}",
                "max_deviation": 0.0,
                "total_groups": 0,
                "failed_groups": 0,
                "allowed_failures": 0,
                "group_predictions": {},
                "error": str(e)
            }

    def _get_current_metric_values(self, df, metric: str, group_by: Optional[str] = None) -> dict:
        """Get current metric values, optionally grouped."""
        
        if group_by is None:
            # No grouping - single value
            value = self._compute_dataframe_metric(df, metric)
            return {"__total__": float(value)}
        else:
            # Group by specified column
            values = {}
            
            if hasattr(df, 'select'):  # Polars
                import polars as pl
                
                if metric == "num_rows":
                    # Count rows per group
                    grouped = df.group_by(group_by).agg(pl.count().alias("count"))
                    for row in grouped.iter_rows(named=True):
                        values[str(row[group_by])] = float(row["count"])
                elif ":" in metric:
                    metric_type, column = metric.split(":", 1)
                    if metric_type == "mean":
                        grouped = df.group_by(group_by).agg(pl.col(column).mean().alias("mean_val"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["mean_val"])
                    elif metric_type == "sum":
                        grouped = df.group_by(group_by).agg(pl.col(column).sum().alias("sum_val"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["sum_val"])
                    elif metric_type == "max":
                        grouped = df.group_by(group_by).agg(pl.col(column).max().alias("max_val"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["max_val"])
                    elif metric_type == "min":
                        grouped = df.group_by(group_by).agg(pl.col(column).min().alias("min_val"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["min_val"])
                    elif metric_type == "distinct_count":
                        grouped = df.group_by(group_by).agg(pl.col(column).n_unique().alias("distinct_count"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["distinct_count"])
                    elif metric_type == "null_count":
                        grouped = df.group_by(group_by).agg(pl.col(column).null_count().alias("null_count"))
                        for row in grouped.iter_rows(named=True):
                            values[str(row[group_by])] = float(row["null_count"])
                    elif metric_type == "null_pct":
                        grouped = df.group_by(group_by).agg([
                            pl.col(column).null_count().alias("nulls"),
                            pl.count().alias("total")
                        ])
                        for row in grouped.iter_rows(named=True):
                            pct = (row["nulls"] / row["total"] * 100) if row["total"] > 0 else 0
                            values[str(row[group_by])] = float(pct)
                    
            else:  # Pandas
                if metric == "num_rows":
                    # Count rows per group
                    grouped = df.groupby(group_by).size()
                    values = {str(k): float(v) for k, v in grouped.items()}
                elif ":" in metric:
                    metric_type, column = metric.split(":", 1)
                    if metric_type == "mean":
                        grouped = df.groupby(group_by)[column].mean()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "sum":
                        grouped = df.groupby(group_by)[column].sum()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "max":
                        grouped = df.groupby(group_by)[column].max()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "min":
                        grouped = df.groupby(group_by)[column].min()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "distinct_count":
                        grouped = df.groupby(group_by)[column].nunique()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "null_count":
                        grouped = df.groupby(group_by)[column].isnull().sum()
                        values = {str(k): float(v) for k, v in grouped.items()}
                    elif metric_type == "null_pct":
                        grouped = df.groupby(group_by)[column].apply(lambda x: x.isnull().sum() / len(x) * 100)
                        values = {str(k): float(v) for k, v in grouped.items()}
            
            return values

    def _load_historical_data(self, context: AssetCheckExecutionContext, check_name: str, metric: str, group_by: Optional[str] = None, history: int = 10) -> dict:
        """Load historical data for all checks from Dagster asset check metadata."""
        
        try:
            # Get historical asset check evaluation events (where check metadata is stored)
            # Get asset key from the component's stored asset key or construct from asset name
            if hasattr(self, '_asset_key'):
                asset_key_for_filter = self._asset_key
            elif hasattr(self, '_asset_name'):
                asset_key_for_filter = AssetKey(self._asset_name.split('.')) if '.' in self._asset_name else AssetKey([self._asset_name])
            else:
                # Fallback: try to get from context if available
                try:
                    asset_key_for_filter = context.asset_check_spec.asset_key
                except:
                    # Last resort: construct from the check name itself
                    check_name = str(context.asset_check_spec.name)
                    if '_' in check_name:
                        asset_part = check_name.split('_')[0]
                        asset_key_for_filter = AssetKey([asset_part])
                    else:
                        asset_key_for_filter = AssetKey(['unknown'])
            
            context.log.info(f"Historical data - Using asset key for filter: {asset_key_for_filter}")
            
            # Strategy 1: Try asset key filter first (most efficient) - may fail due to Dagster bug
            context.log.info(f"Historical data - Strategy 1: Filtering by asset_key={asset_key_for_filter}")
            records = context.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_CHECK_EVALUATION, 
                    asset_key=asset_key_for_filter
                ),
                limit=history * 3,  # Get extra records to find relevant ones
            )
            
            context.log.info(f"Historical data - Strategy 1 (asset_key filter): Found {len(records)} records")
            
            # Strategy 2: If no records found, try with larger limit but still filtered by asset
            if len(records) == 0:
                context.log.info(f"Historical data - Strategy 1 failed, trying Strategy 2 (larger asset_key filter)")
                records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_CHECK_EVALUATION, 
                        asset_key=asset_key_for_filter
                    ),
                    limit=history * 20,  # Much larger limit for infrequently run checks
                )
                context.log.info(f"Historical data - Strategy 2: Found {len(records)} records")
            
            # Strategy 3: If still no records, try broader search but with precise filtering
            # This is the most reliable approach due to Dagster's asset_key filtering bug for check events
            if len(records) == 0:
                context.log.info(f"Historical data - Strategy 2 failed, trying Strategy 3 (broader search with precise filtering)")
                
                # Get all check events with much larger limit
                all_check_events = context.instance.get_event_records(
                    EventRecordsFilter(event_type=DagsterEventType.ASSET_CHECK_EVALUATION),
                    limit=history * 100,  # Much larger limit to handle many assets
                )
                
                # Filter for events that match our exact asset and check name
                matching_events = []
                
                # Get the correct check name - it should be the full check name, not just the type
                sanitized_name = self._sanitize_asset_key_name(asset_key_for_filter)
                expected_check_name = f"{sanitized_name}_{check_name}"
                
                context.log.info(f"Historical data - Looking for asset: {asset_key_for_filter}, check_name: {expected_check_name}")
                
                for event in all_check_events:
                    if (hasattr(event, 'event_log_entry') and 
                        event.event_log_entry and 
                        event.event_log_entry.dagster_event and
                        event.event_log_entry.dagster_event.event_specific_data):
                        
                        check_eval = event.event_log_entry.dagster_event.event_specific_data
                        
                        # Check if this event matches our asset and check name exactly
                        if (hasattr(check_eval, 'asset_key') and 
                            hasattr(check_eval, 'check_name')):
                            
                            actual_asset_key = check_eval.asset_key
                            actual_check_name = check_eval.check_name
                            
                            # Check if this is our exact target (only log matches, not every record)
                            if (actual_asset_key == asset_key_for_filter and 
                                actual_check_name == expected_check_name):
                                context.log.info(f"Historical data - ✅ EXACT MATCH: {actual_asset_key} / {actual_check_name}")
                                matching_events.append(event)
                
                context.log.info(f"Historical data - Strategy 3: Found {len(matching_events)} matching records")
                records = matching_events


            
            historical_data = {}
            
            for record in records:
                # Access metadata through the correct path as per Dagster docs
                if record.event_log_entry and record.event_log_entry.dagster_event and record.event_log_entry.dagster_event.event_specific_data:
                    metadata = record.event_log_entry.dagster_event.event_specific_data.metadata
                    
                    # Look for historical data in the metadata
                    if metadata and 'historical_data' in metadata:
                        historical_values = metadata['historical_data'].value
                    
                    if group_by:
                        # Group-by case: historical_values is a dict {group_key: value}
                        for group_key, value in historical_values.items():
                            if group_key not in historical_data:
                                historical_data[group_key] = []
                            historical_data[group_key].append(float(value))
                    else:
                        # Non-grouped case: single value
                        if '__total__' not in historical_data:
                            historical_data['__total__'] = []
                        if isinstance(historical_values, dict) and '__total__' in historical_values:
                            historical_data['__total__'].append(float(historical_values['__total__']))
                        elif isinstance(historical_values, (int, float)):
                            historical_data['__total__'].append(float(historical_values))

                
                # Stop when we have enough history for all groups
                if historical_data:
                    min_history_length = min(len(values) for values in historical_data.values())
                    if min_history_length >= history:
                        break
            
            # Keep only the most recent N values for each group
            for group_key in historical_data:
                historical_data[group_key] = historical_data[group_key][-history:]
            
            return historical_data
            
        except Exception as e:
            # Log error and return empty data - no file fallback
            context.log.error(f"Failed to load historical data for {check_name}: {e}")
            return {}

    def _generate_prediction(self, historical_values: list, method: str, confidence: float) -> dict:
        """Generate prediction using specified method."""
        
        if method == "moving_average":
            return self._predict_moving_average(historical_values, confidence)
        elif method == "linear_regression":
            return self._predict_linear_regression(historical_values, confidence)
        elif method == "exponential_smoothing":
            return self._predict_exponential_smoothing(historical_values, confidence)
        elif method == "arima":
            return self._predict_arima(historical_values, confidence)
        else:
            raise ValueError(f"Unknown prediction method: {method}")

    def _predict_moving_average(self, values: list, confidence: float) -> dict:
        """Simple moving average prediction."""
        
        # Use last N values for prediction (default: half of available data, min 3)
        window_size = max(3, len(values) // 2)
        recent_values = values[-window_size:]
        
        # Predicted value is the mean of recent values
        predicted_value = np.mean(recent_values)
        
        # Standard deviation for confidence interval
        std_dev = np.std(recent_values, ddof=1) if len(recent_values) > 1 else 0
        
        # Calculate confidence interval
        z_score = 1.96 if confidence >= 0.95 else 1.64  # 95% or 90% confidence
        margin_of_error = z_score * std_dev
        
        return {
            "predicted_value": predicted_value,
            "lower_bound": predicted_value - margin_of_error,
            "upper_bound": predicted_value + margin_of_error,
            "method": "moving_average",
            "window_size": window_size,
            "std_dev": std_dev
        }

    def _predict_linear_regression(self, values: list, confidence: float) -> dict:
        """Linear regression prediction."""
        
        try:
            # Create time series (x = time, y = values)
            x = np.arange(len(values))
            y = np.array(values)
            
            # Fit linear regression
            coeffs = np.polyfit(x, y, 1)  # degree 1 = linear
            slope, intercept = coeffs
            
            # Predict next value
            next_x = len(values)
            predicted_value = slope * next_x + intercept
            
            # Calculate residuals for confidence interval
            y_pred = np.polyval(coeffs, x)
            residuals = y - y_pred
            mse = np.mean(residuals ** 2)
            std_error = np.sqrt(mse)
            
            # Calculate confidence interval
            z_score = 1.96 if confidence >= 0.95 else 1.64
            margin_of_error = z_score * std_error
            
            return {
                "predicted_value": predicted_value,
                "lower_bound": predicted_value - margin_of_error,
                "upper_bound": predicted_value + margin_of_error,
                "method": "linear_regression",
                "slope": slope,
                "intercept": intercept,
                "std_error": std_error,
                "r_squared": 1 - (np.sum(residuals ** 2) / np.sum((y - np.mean(y)) ** 2))
            }
            
        except Exception as e:
            # Fallback to moving average if linear regression fails
            return self._predict_moving_average(values, confidence)

    def _predict_exponential_smoothing(self, values: list, confidence: float) -> dict:
        """Exponential smoothing prediction."""
        
        try:
            # Simple exponential smoothing
            alpha = 0.3  # Smoothing parameter
            
            # Initialize with first value
            smoothed = [values[0]]
            
            # Apply exponential smoothing
            for i in range(1, len(values)):
                smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[-1]
                smoothed.append(smoothed_value)
            
            # Predicted value is the next smoothed value
            predicted_value = smoothed[-1]
            
            # Calculate residuals for confidence interval
            residuals = np.array(values[1:]) - np.array(smoothed[1:])
            std_error = np.std(residuals, ddof=1) if len(residuals) > 1 else 0
            
            # Calculate confidence interval
            z_score = 1.96 if confidence >= 0.95 else 1.64
            margin_of_error = z_score * std_error
            
            return {
                "predicted_value": predicted_value,
                "lower_bound": predicted_value - margin_of_error,
                "upper_bound": predicted_value + margin_of_error,
                "method": "exponential_smoothing",
                "alpha": alpha,
                "std_error": std_error
            }
            
        except Exception as e:
            # Fallback to moving average if exponential smoothing fails
            return self._predict_moving_average(values, confidence)

    def _predict_arima(self, values: list, confidence: float) -> dict:
        """ARIMA prediction (simplified implementation)."""
        
        try:
            # For simplicity, use a basic ARIMA(1,1,1) model
            # In practice, you'd use statsmodels or similar library
            
            # First difference to make series stationary
            if len(values) > 1:
                diff_values = np.diff(values)
                
                # Simple autoregressive prediction on differenced series
                if len(diff_values) > 1:
                    # Predict next difference as mean of recent differences
                    predicted_diff = np.mean(diff_values[-3:])  # Use last 3 differences
                    predicted_value = values[-1] + predicted_diff
                    
                    # Standard deviation of differences for confidence interval
                    std_diff = np.std(diff_values, ddof=1) if len(diff_values) > 1 else 0
                    
                    # Calculate confidence interval
                    z_score = 1.96 if confidence >= 0.95 else 1.64
                    margin_of_error = z_score * std_diff
                    
                    return {
                        "predicted_value": predicted_value,
                        "lower_bound": predicted_value - margin_of_error,
                        "upper_bound": predicted_value + margin_of_error,
                        "method": "arima_simple",
                        "predicted_diff": predicted_diff,
                        "std_diff": std_diff
                    }
            
            # Fallback to moving average if ARIMA fails
            return self._predict_moving_average(values, confidence)
            
        except Exception as e:
            # Fallback to moving average if ARIMA fails
            return self._predict_moving_average(values, confidence)

    def _create_predicted_range_description(self, passed: bool, failed_groups: list, total_groups: int, allowed_failures: int) -> str:
        """Create a descriptive result message for predicted range check."""
        
        if passed:
            if total_groups == 1:
                return "Current value is within predicted range"
            else:
                return f"Predicted range check PASSED: {total_groups - len(failed_groups)}/{total_groups} groups within range (allowed failures: {allowed_failures})"
        else:
            if total_groups == 1:
                return "Current value is outside predicted range"
            else:
                return f"Predicted range check FAILED: {len(failed_groups)}/{total_groups} groups outside range (allowed failures: {allowed_failures})"

    def _analyze_percent_delta(self, context: AssetCheckExecutionContext, df, metric: str, group_by: Optional[str] = None) -> dict:
        """Analyze percent delta using dataframe processing."""
        
        try:
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values(df, metric, group_by)
            context.log.info(f"Percent delta - Current values: {current_values}")
            context.log.info(f"Percent delta - Current values type: {type(current_values)}")
            context.log.info(f"Percent delta - Current values empty: {not current_values}")
            context.log.info(f"Percent delta - Metric: {metric}")
            context.log.info(f"Percent delta - Group by: {group_by}")
            context.log.info(f"Percent delta - DataFrame shape: {df.shape}")
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "percent_delta", metric, group_by, self._get_check_config_value('percent_delta_history', 10))
            context.log.info(f"Percent delta - Historical data: {historical_data}")
            
            # Step 3: Calculate percent deltas for each group
            group_deltas = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) == 0:
                    group_deltas[group_key] = {
                        "passed": True,  # No history to compare against
                        "reason": "No historical data available",
                        "current_value": current_value,
                        "historical_average": None,
                        "percent_delta": None,
                        "threshold": self._get_check_config_value('percent_delta_threshold', 10.0)
                    }
                    continue
                
                # Calculate historical average
                historical_avg = sum(group_history) / len(group_history)
                
                # Calculate percent delta
                if historical_avg == 0:
                    if current_value == 0:
                        percent_delta = 0.0
                    else:
                        percent_delta = 100.0  # Changed from 0 to non-zero
                else:
                    percent_delta = abs((current_value - historical_avg) / historical_avg * 100)
                
                # Check against threshold
                passed = percent_delta <= self._get_check_config_value('percent_delta_threshold', 20.0)
                
                
                group_deltas[group_key] = {
                    "passed": passed,
                    "reason": f"Delta within threshold" if passed else f"Delta exceeds threshold",
                    "current_value": current_value,
                    "historical_average": historical_avg,
                    "percent_delta": percent_delta,
                    "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                    "history_count": len(group_history)
                }
            
            # Step 4: Apply allowed failures logic
            failed_groups = [k for k, v in group_deltas.items() if not v["passed"]]
            total_groups = len(group_deltas)
            allowed_failures = self._get_check_config_value("percent_delta_allowed_failures", 0)
            
            overall_passed = len(failed_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if group_deltas:
                deltas = [v["percent_delta"] for v in group_deltas.values() if v["percent_delta"] is not None]
                max_delta = max(deltas) if deltas else 0.0
            else:
                max_delta = 0.0
            
            return {
                "passed": overall_passed,
                "description": self._create_percent_delta_description(overall_passed, failed_groups, total_groups, allowed_failures, max_delta),
                "max_delta": max_delta,
                "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                "total_groups": total_groups,
                "failed_groups": failed_groups,
                "allowed_failures": allowed_failures,
                "group_deltas": group_deltas,
                "current_values_for_storage": current_values if isinstance(current_values, dict) else {"__total__": float(current_values) if isinstance(current_values, (int, float)) else 0.0},
                "loaded_history": historical_data,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Percent delta analysis failed: {str(e)}",
                "max_delta": 0.0,
                "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                "total_groups": 0,
                "failed_groups": 0,
                "allowed_failures": 0,
                "group_deltas": {},
                "current_values_for_storage": {},
                "error": str(e)
            }

    def _analyze_percent_delta_database(self, context: AssetCheckExecutionContext, metric: str, group_by: Optional[str] = None) -> dict:
        """Analyze percent delta using database processing."""
        
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values_database(database_resource, metric, group_by)
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "percent_delta", metric, group_by, self._get_check_config_value('percent_delta_history', 10))
            
            # Step 3: Calculate percent deltas for each group
            group_deltas = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) == 0:
                    group_deltas[group_key] = {
                        "passed": True,  # No history to compare against
                        "reason": "No historical data available",
                        "current_value": current_value,
                        "historical_average": None,
                        "percent_delta": None,
                        "threshold": self._get_check_config_value('percent_delta_threshold', 20.0)
                    }
                    continue
                
                # Calculate historical average
                historical_avg = sum(group_history) / len(group_history)
                
                # Calculate percent delta
                if historical_avg == 0:
                    if current_value == 0:
                        percent_delta = 0.0
                    else:
                        percent_delta = 100.0  # Changed from 0 to non-zero
                else:
                    percent_delta = abs((current_value - historical_avg) / historical_avg * 100)
                
                # Check against threshold
                passed = percent_delta <= self._get_check_config_value('percent_delta_threshold', 20.0)
                
                group_deltas[group_key] = {
                    "passed": passed,
                    "reason": f"Delta within threshold" if passed else f"Delta exceeds threshold",
                    "current_value": current_value,
                    "historical_average": historical_avg,
                    "percent_delta": percent_delta,
                    "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                    "history_count": len(group_history)
                }
            
            # Step 4: Apply allowed failures logic
            failed_groups = [k for k, v in group_deltas.items() if not v["passed"]]
            total_groups = len(group_deltas)
            allowed_failures = self._get_check_config_value("percent_delta_allowed_failures", 0)
            
            overall_passed = len(failed_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if group_deltas:
                deltas = [v["percent_delta"] for v in group_deltas.values() if v["percent_delta"] is not None]
                max_delta = max(deltas) if deltas else 0.0
            else:
                max_delta = 0.0
            
            return {
                "passed": overall_passed,
                "description": self._create_percent_delta_description(overall_passed, failed_groups, total_groups, allowed_failures, max_delta),
                "max_delta": max_delta,
                "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                "total_groups": total_groups,
                "failed_groups": failed_groups,
                "allowed_failures": allowed_failures,
                "group_deltas": group_deltas,
                "current_values_for_storage": current_values if isinstance(current_values, dict) else {"__total__": float(current_values) if isinstance(current_values, (int, float)) else 0.0},
                "loaded_history": historical_data,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Percent delta analysis failed: {str(e)}",
                "max_delta": 0.0,
                "threshold": self._get_check_config_value('percent_delta_threshold', 20.0),
                "total_groups": 0,
                "failed_groups": 0,
                "allowed_failures": 0,
                "group_deltas": {},
                "current_values_for_storage": {},
                "error": str(e)
            }

    def _get_current_metric_values_database(self, database_resource, metric: str, group_by: Optional[str] = None) -> dict:
        """Get current metric values from database, optionally grouped."""
        
        if group_by is None:
            # No grouping - single value
            value = self._compute_database_metric(metric, database_resource)
            return {"__total__": float(value)}
        else:
            # Group by specified column
            values = {}
            
            with database_resource.get_connection() as conn:
                if metric == "num_rows":
                    # Count rows per group
                    query = f"SELECT {group_by}, COUNT(*) as count FROM {self.table_name} GROUP BY {group_by}"
                    result = conn.execute(query).fetchall()
                    for row in result:
                        values[str(row[0])] = float(row[1])
                        
                elif ":" in metric:
                    metric_type, column = metric.split(":", 1)
                    
                    if metric_type == "mean":
                        query = f"SELECT {group_by}, AVG({column}) as mean_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "sum":
                        query = f"SELECT {group_by}, SUM({column}) as sum_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "max":
                        query = f"SELECT {group_by}, MAX({column}) as max_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "min":
                        query = f"SELECT {group_by}, MIN({column}) as min_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "distinct_count":
                        query = f"SELECT {group_by}, COUNT(DISTINCT {column}) as distinct_count FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "null_count":
                        query = f"SELECT {group_by}, COUNT(*) - COUNT({column}) as null_count FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "null_pct":
                        query = f"SELECT {group_by}, ((COUNT(*) - COUNT({column})) * 100.0 / COUNT(*)) as null_pct FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "std":
                        query = f"SELECT {group_by}, STDDEV({column}) as std_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "var":
                        query = f"SELECT {group_by}, VAR({column}) as var_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "median":
                        query = f"SELECT {group_by}, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column}) as median_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "mode":
                        # Mode not supported in database mode
                        raise ValueError(f"Mode metric not supported in database mode - use dataframe processing")
                    elif metric_type == "range":
                        query = f"SELECT {group_by}, MAX({column}) - MIN({column}) as range_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "iqr":
                        query = f"SELECT {group_by}, PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) - PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) as iqr_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "skew":
                        # Skewness not supported in database mode
                        raise ValueError(f"Skewness metric not supported in database mode - use dataframe processing")
                    elif metric_type == "kurt":
                        # Kurtosis not supported in database mode
                        raise ValueError(f"Kurtosis metric not supported in database mode - use dataframe processing")
                    elif metric_type == "cv":
                        query = f"SELECT {group_by}, STDDEV({column}) / AVG({column}) as cv_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "zscore":
                        query = f"SELECT {group_by}, AVG({column}) / STDDEV({column}) as zscore_val FROM {self.table_name} GROUP BY {group_by}"
                    elif metric_type == "outlier_count":
                        query = f"""
                        SELECT {group_by}, COUNT(*) as outlier_count FROM {self.table_name} 
                        WHERE {column} < (AVG({column}) OVER (PARTITION BY {group_by}) - 3 * STDDEV({column}) OVER (PARTITION BY {group_by}))
                           OR {column} > (AVG({column}) OVER (PARTITION BY {group_by}) + 3 * STDDEV({column}) OVER (PARTITION BY {group_by}))
                        GROUP BY {group_by}
                        """
                    elif metric_type.startswith("p") and metric_type[1:].isdigit():
                        percentile = int(metric_type[1:])
                        if 0 <= percentile <= 100:
                            query = f"SELECT {group_by}, PERCENTILE_CONT({percentile / 100.0}) WITHIN GROUP (ORDER BY {column}) as p{percentile}_val FROM {self.table_name} GROUP BY {group_by}"
                        else:
                            raise ValueError(f"Invalid percentile: {percentile}")
                    else:
                        raise ValueError(f"Unsupported metric type: {metric_type}")
                    
                    result = conn.execute(query).fetchall()
                    for row in result:
                        values[str(row[0])] = float(row[1]) if row[1] is not None else 0.0
                        
            return values

    def _create_percent_delta_description(self, passed: bool, failed_groups: list, total_groups: int, allowed_failures: int, max_delta: float) -> str:
        """Create a descriptive result message for percent delta check."""
        
        if passed:
            if total_groups == 1:
                return f"Percent delta within threshold: {max_delta:.2f}%"
            else:
                return f"Percent delta check PASSED: {total_groups - len(failed_groups)}/{total_groups} groups within threshold (max: {max_delta:.2f}%, allowed failures: {allowed_failures})"
        else:
            if total_groups == 1:
                return f"Percent delta exceeds threshold: {max_delta:.2f}%"
            else:
                return f"Percent delta check FAILED: {len(failed_groups)}/{total_groups} groups exceed threshold (max: {max_delta:.2f}%, allowed failures: {allowed_failures})"

    # ═══════════════════════════════════════════════════════════════
    # CORRELATION ANALYSIS METHODS
    # ═══════════════════════════════════════════════════════════════

    def _analyze_correlation(self, df, column_x: str, column_y: str) -> dict:
        """Analyze correlation between two columns."""
        try:
            # Calculate correlation
            correlation, p_value = self._calculate_correlation(df, column_x, column_y)
            
            # Check against thresholds
            passed = True
            if self._get_check_config_value('correlation_min', None) is not None and correlation < self._get_check_config_value('correlation_min', None):
                passed = False
            if self._get_check_config_value('correlation_max', None) is not None and correlation > self._get_check_config_value('correlation_max', None):
                passed = False
            
            return {
                "passed": passed,
                "description": f"Correlation: {correlation:.4f} (p-value: {p_value:.4f})",
                "correlation": correlation,
                "p_value": p_value,
                "method": self._get_check_config_value('correlation_method', 'pearson'),
                "column_x": column_x,
                "column_y": column_y
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Correlation analysis failed: {str(e)}",
                "correlation": 0.0,
                "p_value": 1.0,
                "method": self._get_check_config_value('correlation_method', 'pearson'),
                "error": str(e)
            }

    def _calculate_correlation(self, df, column_x: str, column_y: str) -> tuple:
        """Calculate correlation between two columns using specified method."""
        try:
            # Handle different dataframe types
            if hasattr(df, 'select'):  # Polars
                # Convert to pandas for correlation calculation
                df_pandas = df.select([column_x, column_y]).to_pandas()
                x_values = df_pandas[column_x].dropna()
                y_values = df_pandas[column_y].dropna()
            else:  # Pandas
                x_values = df[column_x].dropna()
                y_values = df[column_y].dropna()
            
            # Align the series (same length)
            common_index = x_values.index.intersection(y_values.index)
            if len(common_index) < 3:  # Need at least 3 points for correlation
                return 0.0, 1.0
            
            x_aligned = x_values.loc[common_index]
            y_aligned = y_values.loc[common_index]
            
            # Calculate correlation based on method
            method = self._get_check_config_value('correlation_method', 'pearson')
            if method == "pearson":
                correlation = x_aligned.corr(y_aligned, method='pearson')
            elif method == "spearman":
                correlation = x_aligned.corr(y_aligned, method='spearman')
            elif method == "kendall":
                correlation = x_aligned.corr(y_aligned, method='kendall')
            else:
                correlation = x_aligned.corr(y_aligned, method='pearson')
            
            # Calculate p-value (simplified)
            if len(common_index) > 3:
                # Simple t-test for correlation significance
                t_stat = correlation * np.sqrt((len(common_index) - 2) / (1 - correlation**2))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(common_index) - 2))
            else:
                p_value = 1.0
            
            return float(correlation) if not np.isnan(correlation) else 0.0, float(p_value)
            
        except Exception as e:
            return 0.0, 1.0

    def _create_correlation_description(self, passed: bool, failed_groups: list, total_groups: int, allowed_failures: int, max_correlation: float) -> str:
        """Create a descriptive result message for correlation check."""
        
        if passed:
            if total_groups == 1:
                return f"Correlation within expected range: {max_correlation:.4f}"
            else:
                return f"Correlation check PASSED: {total_groups - len(failed_groups)}/{total_groups} groups within range (max: {max_correlation:.4f}, allowed failures: {allowed_failures})"
        else:
            if total_groups == 1:
                return f"Correlation outside expected range: {max_correlation:.4f}"
            else:
                return f"Correlation check FAILED: {len(failed_groups)}/{total_groups} groups outside range (max: {max_correlation:.4f}, allowed failures: {allowed_failures})"

    # ═══════════════════════════════════════════════════════════════
    # VALUE SET VALIDATION METHODS
    # ═══════════════════════════════════════════════════════════════

    def _analyze_value_set_validation(self, df, column: str, allowed_values: List[str]) -> dict:
        """Analyze value set validation for a column."""
        try:
            # Get unique values in the column
            if hasattr(df, 'select'):  # Polars
                unique_values = df[column].unique().to_list()
                total_values = df.height
            else:  # Pandas
                unique_values = df[column].unique().tolist()
                total_values = len(df)
            
            # Count valid and invalid values
            valid_values = 0
            invalid_values = []
            
            for value in unique_values:
                if str(value) in allowed_values:
                    # Count occurrences of this valid value
                    if hasattr(df, 'select'):  # Polars
                        count = df.filter(df[column] == value).height
                    else:  # Pandas
                        count = (df[column] == value).sum()
                    valid_values += count
                else:
                    # Count occurrences of this invalid value
                    if hasattr(df, 'select'):  # Polars
                        count = df.filter(df[column] == value).height
                    else:  # Pandas
                        count = (df[column] == value).sum()
                    invalid_values.append({"value": str(value), "count": int(count)})
            
            # Calculate percentage of valid values
            valid_percentage = (valid_values / total_values * 100) if total_values > 0 else 0.0
            
            # Check against minimum required percentage
            passed = valid_percentage >= self._get_check_config_value('value_set_min_pct', 95.0)
            
            return {
                "passed": passed,
                "description": f"Value set validation: {valid_percentage:.2f}% valid (required: {self._get_check_config_value('value_set_min_pct', 95.0):.2f}%)",
                "valid_percentage": valid_percentage,
                "min_required_pct": self._get_check_config_value('value_set_min_pct', 95.0),
                "invalid_values": invalid_values,
                "total_values": total_values,
                "valid_values": valid_values,
                "allowed_values": allowed_values
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Value set validation failed: {str(e)}",
                "valid_percentage": 0.0,
                "min_required_pct": self._get_check_config_value('value_set_min_pct', 95.0),
                "invalid_values": [],
                "total_values": 0,
                "valid_values": 0,
                "error": str(e)
            }

    # ═══════════════════════════════════════════════════════════════
    # ANOMALY DETECTION METHODS
    # ═══════════════════════════════════════════════════════════════

    def _analyze_anomaly_detection(self, context: AssetCheckExecutionContext, df, metric: str, group_by: Optional[str] = None, threshold: float = 2.0, method: str = "z_score", history: int = 10, allowed_failures: int = 0) -> dict:
        """Analyze anomaly detection using dataframe processing."""
        
        try:
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values(df, metric, group_by)
            context.log.info(f"Anomaly detection - Current values: {current_values}")
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "anomaly_detection", metric, group_by, history)
            context.log.info(f"Anomaly detection - Historical data: {historical_data}")
            
            # Step 3: Calculate anomaly scores for each group
            group_anomalies = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) < 3:  # Need minimum history for anomaly detection
                    group_anomalies[group_key] = {
                        "passed": True,  # No history to compare against
                        "reason": f"Insufficient history: {len(group_history)} values (need 3+)",
                        "current_value": current_value,
                        "anomaly_score": None,
                        "history_count": len(group_history)
                    }
                    continue
                
                # Calculate anomaly score using specified method
                anomaly_score = self._calculate_anomaly_score(group_history, current_value, method)
                
                # Check against threshold
                passed = anomaly_score <= threshold
                
                group_anomalies[group_key] = {
                    "passed": passed,
                    "reason": f"Anomaly score within threshold" if passed else f"Anomaly score exceeds threshold",
                    "current_value": current_value,
                    "anomaly_score": anomaly_score,
                    "threshold": threshold,
                    "history_count": len(group_history),
                    "method": method
                }
            
            # Step 4: Apply allowed failures logic
            anomalous_groups = [k for k, v in group_anomalies.items() if not v["passed"]]
            total_groups = len(group_anomalies)
            
            overall_passed = len(anomalous_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if group_anomalies:
                scores = [v["anomaly_score"] for v in group_anomalies.values() if v["anomaly_score"] is not None]
                max_anomaly_score = max(scores) if scores else 0.0
            else:
                max_anomaly_score = 0.0
            
            return {
                "passed": overall_passed,
                "description": self._create_anomaly_detection_description(overall_passed, anomalous_groups, total_groups, allowed_failures, max_anomaly_score),
                "max_anomaly_score": max_anomaly_score,
                "threshold": self._get_check_config_value('anomaly_detection_threshold', 2.0),
                "total_groups": total_groups,
                "anomalous_groups": anomalous_groups,
                "allowed_failures": allowed_failures,
                "group_anomalies": group_anomalies,
                "current_values_for_storage": current_values if isinstance(current_values, dict) else {"__total__": float(current_values) if isinstance(current_values, (int, float)) else 0.0},
                "method": self._get_check_config_value('anomaly_detection_method', 'z_score'),
                "loaded_history": historical_data,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Anomaly detection analysis failed: {str(e)}",
                "max_anomaly_score": 0.0,
                "threshold": self._get_check_config_value('anomaly_detection_threshold', 2.0),
                "total_groups": 0,
                "anomalous_groups": 0,
                "allowed_failures": 0,
                "group_anomalies": {},
                "current_values_for_storage": {},
                "method": self._get_check_config_value('anomaly_detection_method', 'z_score'),
                "error": str(e)
            }

    def _analyze_anomaly_detection_database(self, context: AssetCheckExecutionContext, metric: str, group_by: Optional[str] = None, threshold: float = 2.0, method: str = "z_score", history: int = 10, allowed_failures: int = 0) -> dict:
        """Analyze anomaly detection using database processing."""
        
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Step 1: Get current metric values
            current_values = self._get_current_metric_values_database(database_resource, metric, group_by)
            
            # Step 2: Load historical data
            historical_data = self._load_historical_data(context, "anomaly_detection", metric, group_by, history)
            
            # Step 3: Calculate anomaly scores for each group
            group_anomalies = {}
            
            for group_key, current_value in current_values.items():
                # Get historical values for this group
                group_history = historical_data.get(group_key, [])
                
                if len(group_history) < 3:  # Need minimum history for anomaly detection
                    group_anomalies[group_key] = {
                        "passed": True,  # No history to compare against
                        "reason": f"Insufficient history: {len(group_history)} values (need 3+)",
                        "current_value": current_value,
                        "anomaly_score": None,
                        "history_count": len(group_history)
                    }
                    continue
                
                # Calculate anomaly score using specified method
                anomaly_score = self._calculate_anomaly_score(group_history, current_value, method)
                
                # Check against threshold
                passed = anomaly_score <= threshold
                
                group_anomalies[group_key] = {
                    "passed": passed,
                    "reason": f"Anomaly score within threshold" if passed else f"Anomaly score exceeds threshold",
                    "current_value": current_value,
                    "anomaly_score": anomaly_score,
                    "threshold": threshold,
                    "history_count": len(group_history),
                    "method": method
                }
            
            # Step 4: Apply allowed failures logic
            anomalous_groups = [k for k, v in group_anomalies.items() if not v["passed"]]
            total_groups = len(group_anomalies)
            
            overall_passed = len(anomalous_groups) <= allowed_failures
            
            # Step 5: Calculate summary statistics
            if group_anomalies:
                scores = [v["anomaly_score"] for v in group_anomalies.values() if v["anomaly_score"] is not None]
                max_anomaly_score = max(scores) if scores else 0.0
            else:
                max_anomaly_score = 0.0
            
            return {
                "passed": overall_passed,
                "description": self._create_anomaly_detection_description(overall_passed, anomalous_groups, total_groups, allowed_failures, max_anomaly_score),
                "max_anomaly_score": max_anomaly_score,
                "threshold": threshold,
                "total_groups": total_groups,
                "anomalous_groups": anomalous_groups,
                "allowed_failures": allowed_failures,
                "group_anomalies": group_anomalies,
                "current_values_for_storage": current_values if isinstance(current_values, dict) else {"__total__": float(current_values) if isinstance(current_values, (int, float)) else 0.0},
                "method": method,
                "loaded_history": historical_data,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Anomaly detection analysis failed: {str(e)}",
                "max_anomaly_score": 0.0,
                "threshold": threshold,
                "total_groups": 0,
                "anomalous_groups": 0,
                "allowed_failures": allowed_failures,
                "group_anomalies": {},
                "current_values_for_storage": {},
                "method": method,
                "error": str(e)
            }

    def _calculate_anomaly_score(self, historical_values: list, current_value: float, method: str) -> float:
        """Calculate anomaly score using specified method."""
        
        if method == "z_score":
            return self._calculate_z_score_anomaly(historical_values, current_value)
        elif method == "iqr":
            return self._calculate_iqr_anomaly(historical_values, current_value)
        elif method == "isolation_forest":
            return self._calculate_isolation_forest_anomaly(historical_values, current_value)
        else:
            # Default to z-score
            return self._calculate_z_score_anomaly(historical_values, current_value)

    def _calculate_z_score_anomaly(self, historical_values: list, current_value: float) -> float:
        """Calculate anomaly score using z-score method."""
        
        if len(historical_values) < 2:
            return 0.0  # Not enough data for z-score
        
        # Calculate mean and standard deviation
        mean_val = np.mean(historical_values)
        std_val = np.std(historical_values, ddof=1)  # Sample standard deviation
        
        if std_val == 0:
            return 0.0  # No variation in historical data
        
        # Calculate z-score
        z_score = abs((current_value - mean_val) / std_val)
        
        return z_score

    def _calculate_iqr_anomaly(self, historical_values: list, current_value: float) -> float:
        """Calculate anomaly score using IQR method."""
        
        if len(historical_values) < 4:
            return 0.0  # Need at least 4 values for IQR
        
        # Calculate quartiles
        sorted_values = sorted(historical_values)
        q1 = np.percentile(sorted_values, 25)
        q3 = np.percentile(sorted_values, 75)
        iqr = q3 - q1
        
        if iqr == 0:
            return 0.0  # No variation in historical data
        
        # Calculate how many IQRs away the current value is
        if current_value < q1:
            # Below Q1
            distance = (q1 - current_value) / iqr
        elif current_value > q3:
            # Above Q3
            distance = (current_value - q3) / iqr
        else:
            # Within IQR range
            distance = 0.0
        
        return distance

    def _calculate_isolation_forest_anomaly(self, historical_values: list, current_value: float) -> float:
        """Calculate anomaly score using simplified isolation forest method."""
        
        if len(historical_values) < 3:
            return 0.0  # Need at least 3 values
        
        # Simplified isolation forest: calculate how "isolated" the current value is
        # This is a simplified version - in practice you'd use sklearn's IsolationForest
        
        # Calculate the range of historical values
        min_val = min(historical_values)
        max_val = max(historical_values)
        range_val = max_val - min_val
        
        if range_val == 0:
            return 0.0  # No variation in historical data
        
        # Calculate how far the current value is from the center of the range
        center = (min_val + max_val) / 2
        distance_from_center = abs(current_value - center)
        
        # Normalize by the range
        normalized_distance = distance_from_center / range_val
        
        # Convert to anomaly score (higher = more anomalous)
        anomaly_score = normalized_distance * 2.0  # Scale to reasonable range
        
        return anomaly_score

    def _create_anomaly_detection_description(self, passed: bool, anomalous_groups: list, total_groups: int, allowed_failures: int, max_anomaly_score: float) -> str:
        """Create a descriptive result message for anomaly detection check."""
        
        if passed:
            if total_groups == 1:
                return f"Anomaly detection: score {max_anomaly_score:.2f} within threshold"
            else:
                return f"Anomaly detection PASSED: {total_groups - len(anomalous_groups)}/{total_groups} groups normal (max score: {max_anomaly_score:.2f}, allowed failures: {allowed_failures})"
        else:
            if total_groups == 1:
                return f"Anomaly detection: score {max_anomaly_score:.2f} exceeds threshold"
            else:
                return f"Anomaly detection FAILED: {len(anomalous_groups)}/{total_groups} groups anomalous (max score: {max_anomaly_score:.2f}, allowed failures: {allowed_failures})"

    # ═══════════════════════════════════════════════════════════════
    # PATTERN MATCHING METHODS
    # ═══════════════════════════════════════════════════════════════

    def _analyze_pattern_matching(self, df, column: str, regex_pattern: str, min_pct: float = 95.0) -> dict:
        """Analyze pattern matching for a column using regex."""
        try:
            import re
            
            # Get total number of values
            if hasattr(df, 'height'):  # Polars
                total_values = df.height
            else:  # Pandas
                total_values = len(df)
            
            # Count matching and non-matching values
            matching_values = 0
            non_matching_values = []
            
            # Compile regex pattern
            pattern = re.compile(regex_pattern)
            
            # Check each value in the column
            if hasattr(df, 'select'):  # Polars
                # Get unique values to avoid counting duplicates multiple times
                unique_values = df[column].unique().to_list()
                for value in unique_values:
                    str_value = str(value)
                    if pattern.match(str_value):
                        # Count occurrences of this matching value
                        count = df.filter(df[column] == value).height
                        matching_values += count
                    else:
                        # Count occurrences of this non-matching value
                        count = df.filter(df[column] == value).height
                        non_matching_values.append({"value": str_value, "count": int(count)})
            else:  # Pandas
                # Get unique values to avoid counting duplicates multiple times
                unique_values = df[column].unique().tolist()
                for value in unique_values:
                    str_value = str(value)
                    if pattern.match(str_value):
                        # Count occurrences of this matching value
                        count = (df[column] == value).sum()
                        matching_values += count
                    else:
                        # Count occurrences of this non-matching value
                        count = (df[column] == value).sum()
                        non_matching_values.append({"value": str_value, "count": int(count)})
            
            # Calculate percentage of matching values
            match_percentage = (matching_values / total_values * 100) if total_values > 0 else 0.0
            
            # Check against minimum required percentage
            passed = match_percentage >= min_pct
            
            return {
                "passed": passed,
                "description": f"Pattern matching: {match_percentage:.2f}% match (required: {min_pct:.2f}%)",
                "match_percentage": match_percentage,
                "min_required_pct": min_pct,
                "non_matching_values": non_matching_values,
                "total_values": total_values,
                "matching_values": matching_values,
                "pattern_regex": regex_pattern
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Pattern matching failed: {str(e)}",
                "match_percentage": 0.0,
                "min_required_pct": min_pct,
                "non_matching_values": [],
                "total_values": 0,
                "matching_values": 0,
                "pattern_regex": regex_pattern,
                "error": str(e)
            }

    def _analyze_data_type_validation(self, df, data_type_columns: List[Dict[str, str]]) -> dict:
        """Analyze data type validation for multiple columns."""
        try:
            type_validation_results = {}
            failed_columns = []
            
            # Debug: Log available columns
            available_columns = list(df.columns) if hasattr(df, 'columns') else []
            
            # Check if DataFrame is empty
            is_empty = len(df) == 0 if hasattr(df, '__len__') else True
            
            for column_config in data_type_columns:
                column_name = column_config["column"]
                expected_type = column_config["expected_type"]
                
                # Debug: Check if column exists
                if column_name not in available_columns:
                    type_validation_results[column_name] = {
                        "passed": False,
                        "expected_type": expected_type,
                        "actual_type": "missing",
                        "description": f"Column '{column_name}' not found in dataframe. Available columns: {available_columns}"
                    }
                    failed_columns.append(column_name)
                    continue
                
                # Get actual data type of the column
                if hasattr(df, 'select'):  # Polars
                    actual_type = str(df[column_name].dtype)
                else:  # Pandas
                    actual_type = str(df[column_name].dtype)
                
                # Special handling for empty DataFrames
                if is_empty:
                    # For empty DataFrames, we can't reliably determine the actual type
                    # since pandas infers 'object' for all columns. Instead, we'll
                    # assume the type is correct if the column exists and skip validation.
                    type_validation_results[column_name] = {
                        "passed": True,
                        "expected_type": expected_type,
                        "actual_type": "unknown (empty dataframe)",
                        "description": f"Column exists in empty dataframe, assuming correct type: {expected_type}"
                    }
                else:
                    # Validate data type for non-empty DataFrames
                    passed = self._validate_data_type(actual_type, expected_type)
                    
                    type_validation_results[column_name] = {
                        "passed": passed,
                        "expected_type": expected_type,
                        "actual_type": actual_type,
                        "description": f"Type validation: {actual_type} vs {expected_type}"
                    }
                    
                    if not passed:
                        failed_columns.append(column_name)
            
            # Overall result
            total_columns = len(data_type_columns)
            overall_passed = len(failed_columns) == 0
            
            return {
                "passed": overall_passed,
                "description": f"Data type validation: {total_columns - len(failed_columns)}/{total_columns} columns passed",
                "type_validation_results": type_validation_results,
                "total_columns": total_columns,
                "failed_columns": len(failed_columns),
                "failed_column_names": failed_columns
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Data type validation failed: {str(e)}",
                "type_validation_results": {},
                "total_columns": 0,
                "failed_columns": 0,
                "failed_column_names": [],
                "error": str(e)
            }

    def _validate_data_type(self, actual_type: str, expected_type: str) -> bool:
        """Validate if actual data type matches expected type."""
        
        # Normalize type names for comparison
        actual_normalized = actual_type.lower().replace('64', '').replace('32', '').replace('16', '').replace('8', '')
        expected_normalized = expected_type.lower()
        
        # Handle common type mappings
        type_mappings = {
            "integer": ["int", "int64", "int32", "int16", "int8"],
            "float": ["float", "float64", "float32", "double"],
            "string": ["object", "string", "str", "text"],
            "text": ["object", "string", "str", "text"],
            "boolean": ["bool", "boolean"],
            "datetime": ["datetime", "datetime64", "timestamp", "datetime64[ns]"],
            "date": ["date", "datetime64[ns]"],
            "numeric": ["int", "int64", "int32", "int16", "int8", "float", "float64", "float32", "double"]
        }
        
        # Check if expected type is in mappings
        if expected_normalized in type_mappings:
            return actual_normalized in type_mappings[expected_normalized] or actual_type.lower() in type_mappings[expected_normalized]
        
        # Direct comparison
        return actual_normalized == expected_normalized or actual_type.lower() == expected_normalized

    def _analyze_range_validation(self, df, range_columns: List[Dict[str, Any]]) -> dict:
        """Analyze range validation for multiple columns."""
        try:
            # Debug: Check if range_columns is None or empty
            if range_columns is None:
                return {
                    "passed": True,
                    "description": "Range validation: No columns configured",
                    "range_validation_results": {},
                    "total_columns": 0,
                    "failed_columns": 0,
                    "failed_column_names": []
                }
            
            if len(range_columns) == 0:
                return {
                    "passed": True,
                    "description": "Range validation: No columns configured",
                    "range_validation_results": {},
                    "total_columns": 0,
                    "failed_columns": 0,
                    "failed_column_names": []
                }
            
            range_validation_results = {}
            outlier_counts = {}
            failed_columns = []
            
            for column_config in range_columns:
                column_name = column_config["column"]
                min_value = column_config.get("min_value")
                max_value = column_config.get("max_value")
                
                # Get column data
                if hasattr(df, 'select'):  # Polars
                    column_data = df[column_name].to_numpy()
                else:  # Pandas
                    column_data = df[column_name].values
                
                # Remove null values for analysis
                column_data = column_data[~pd.isna(column_data)]
                
                if len(column_data) == 0:
                    # No data to analyze
                    range_validation_results[column_name] = {
                        "passed": True,
                        "min_value": min_value,
                        "max_value": max_value,
                        "outlier_count": 0,
                        "total_values": 0,
                        "description": f"Range validation: No data to analyze"
                    }
                    outlier_counts[column_name] = 0
                    continue
                
                # Count outliers
                outlier_count = 0
                outliers = []
                
                for value in column_data:
                    is_outlier = False
                    
                    if min_value is not None and value < min_value:
                        is_outlier = True
                    if max_value is not None and value > max_value:
                        is_outlier = True
                    
                    if is_outlier:
                        outlier_count += 1
                        outliers.append(float(value))
                
                # Check if validation passed (no outliers)
                passed = outlier_count == 0
                
                range_validation_results[column_name] = {
                    "passed": passed,
                    "min_value": min_value,
                    "max_value": max_value,
                    "outlier_count": outlier_count,
                    "total_values": len(column_data),
                    "outliers": outliers[:10],  # Limit to first 10 outliers for metadata
                    "description": f"Range validation: {outlier_count} outliers found"
                }
                
                # Debug: Log outlier information
                if outlier_count > 0:
                    print(f"Range validation - Column '{column_name}': {outlier_count} outliers found")
                    print(f"Range validation - Min value: {min_value}, Max value: {max_value}")
                    print(f"Range validation - First 5 outliers: {outliers[:5]}")
                    print(f"Range validation - Total values: {len(column_data)}")
                
                outlier_counts[column_name] = outlier_count
                
                if not passed:
                    failed_columns.append(column_name)
            
            # Overall result
            total_columns = len(range_columns)
            overall_passed = len(failed_columns) == 0
            
            return {
                "passed": overall_passed,
                "description": f"Range validation: {total_columns - len(failed_columns)}/{total_columns} columns passed",
                "range_validation_results": range_validation_results,
                "total_columns": total_columns,
                "failed_columns": len(failed_columns),
                "failed_column_names": failed_columns,
                "outlier_counts": outlier_counts
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Range validation failed: {str(e)}",
                "range_validation_results": {},
                "total_columns": 0,
                "failed_columns": 0,
                "failed_column_names": [],
                "outlier_counts": {},
                "error": str(e)
            }

    def _analyze_uniqueness_validation(self, df, uniqueness_columns: List[Dict[str, Any]]) -> dict:
        """Analyze uniqueness validation for multiple columns or column combinations."""
        try:
            uniqueness_validation_results = {}
            duplicate_counts = {}
            failed_checks = []
            
            for column_config in uniqueness_columns:
                # Handle both single column and multi-column uniqueness
                if "column" in column_config:
                    # Single column uniqueness
                    column_name = column_config["column"]
                    columns_to_check = [column_name]
                    check_name = f"column_{column_name}"
                elif "columns" in column_config:
                    # Multi-column uniqueness
                    columns_to_check = column_config["columns"]
                    check_name = f"columns_{'_'.join(columns_to_check)}"
                else:
                    continue
                
                # Check if all columns exist in dataframe
                missing_columns = [col for col in columns_to_check if col not in df.columns]
                if missing_columns:
                    uniqueness_validation_results[check_name] = {
                        "passed": False,
                        "columns": columns_to_check,
                        "duplicate_count": 0,
                        "total_rows": int(len(df)),
                        "description": f"Uniqueness validation failed: Missing columns {missing_columns}"
                    }
                    duplicate_counts[check_name] = 0
                    failed_checks.append(check_name)
                    continue
                
                # Check for duplicates
                if hasattr(df, 'select'):  # Polars
                    # For Polars, we need to handle differently
                    subset_df = df.select(columns_to_check)
                    duplicate_mask = subset_df.is_duplicated()
                    duplicate_count = duplicate_mask.sum()
                else:  # Pandas
                    duplicate_mask = df.duplicated(subset=columns_to_check, keep=False)
                    duplicate_count = duplicate_mask.sum()
                
                # Check if validation passed (no duplicates)
                passed = duplicate_count == 0
                
                uniqueness_validation_results[check_name] = {
                    "passed": bool(passed),
                    "columns": columns_to_check,
                    "duplicate_count": int(duplicate_count),
                    "total_rows": int(len(df)),
                    "description": f"Uniqueness validation: {duplicate_count} duplicate rows found"
                }
                
                duplicate_counts[check_name] = int(duplicate_count)
                
                if not passed:
                    failed_checks.append(check_name)
            
            # Overall result
            total_checks = len(uniqueness_columns)
            overall_passed = len(failed_checks) == 0
            
            return {
                "passed": bool(overall_passed),
                "description": f"Uniqueness validation: {total_checks - len(failed_checks)}/{total_checks} checks passed",
                "uniqueness_validation_results": uniqueness_validation_results,
                "total_checks": int(total_checks),
                "failed_checks": int(len(failed_checks)),
                "failed_check_names": failed_checks,
                "duplicate_counts": {k: int(v) for k, v in duplicate_counts.items()}
            }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Uniqueness validation failed: {str(e)}",
                "uniqueness_validation_results": {},
                "total_checks": 0,
                "failed_checks": 0,
                "failed_check_names": [],
                "duplicate_counts": {},
                "error": str(e)
            }

    def _execute_database_to_dataframe_pattern_matching(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute pattern matching check: database → dataframe → analysis."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            # Fetch data as dataframe (auto-select pandas/polars)
            df = self._fetch_data_as_dataframe(database_resource)
            
            # Run the same dataframe analysis
            pattern_column = self._get_check_config_value('pattern_column', 'column')
            pattern_regex = self._get_pattern_regex()
            result = self._analyze_pattern_matching(df, pattern_column, pattern_regex)
            
            # Get pattern information for metadata
            pattern_info = self._get_pattern_info()
            
            return AssetCheckResult(
                passed=bool(result["passed"]),
                description=f"Pattern matching: {result['description']}",
                metadata={
                    "match_percentage": MetadataValue.float(float(result["match_percentage"])),
                    "required_percentage": MetadataValue.float(self._get_check_config_value('pattern_min_pct', 95.0)),
                    "match_count": MetadataValue.int(int(result["matching_values"])),
                    "total_count": MetadataValue.int(int(result["total_values"])),
                    "data_size": MetadataValue.int(len(df)),
                    "dataframe_type": MetadataValue.text(type(df).__module__.split('.')[0]),
                    "processing_mode": MetadataValue.text("database_to_dataframe"),
                    **pattern_info
                }
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Pattern matching failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_predicted_range(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute predicted range check by loading data from database into dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_predicted_range(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Predicted range check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_percent_delta(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute percent delta check by loading data from database into dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_percent_delta(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Percent delta check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_distribution_change(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute distribution change check by loading data from database into dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_distribution_change(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Distribution change check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_anomaly_detection(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute anomaly detection check by loading data from database into dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_anomaly_detection(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Anomaly detection failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_to_dataframe_data_type(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute data type validation by loading data from database into dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_data_type(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Data type validation failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )



    def _execute_database_to_dataframe_uniqueness_check(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute uniqueness check by fetching data from database and processing as dataframe."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            df = self._fetch_data_as_dataframe(database_resource)
            return self._execute_dataframe_uniqueness_check(context, df)
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Database uniqueness check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_database_custom_sql_monitor(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute custom SQL monitor by running SQL directly against the database."""
        try:
            database_resource = getattr(context.resources, self.database_resource_key)
            
            if not self.custom_sql_query:
                raise ValueError("custom_sql_query is required for custom SQL monitor")
            
            with database_resource.get_connection() as conn:
                # Execute the SQL query directly against the database
                result = conn.execute(self.custom_sql_query).fetchone()
                query_result = result[0] if result else None
                
            # Build metadata
            metadata = {
                "query": MetadataValue.text(self.custom_sql_query),
                "query_result": MetadataValue.text(str(query_result)),
            }
            
            # If no expected result specified, just return the query result
            if self.custom_sql_expected_result is None:
                return AssetCheckResult(
                    passed=True,
                    description=f"Custom SQL query executed successfully: {query_result}",
                    metadata=metadata
                )
            
            # Perform comparison if expected result is specified
            expected_result = str(self.custom_sql_expected_result)
            passed = self._compare_values(str(query_result), expected_result, self.custom_sql_comparison)
            
            description = f"Custom SQL query result: {query_result}, Expected: {expected_result}, Comparison: {self.custom_sql_comparison}"
            if passed:
                description += " - PASSED"
            else:
                description += " - FAILED"
            
            metadata.update({
                "expected_result": MetadataValue.text(expected_result),
                "comparison": MetadataValue.text(self._safe_enum_to_string(self.custom_sql_comparison)),
            })
            
            return AssetCheckResult(
                passed=passed,
                description=description,
                metadata=metadata
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Database custom SQL monitor failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_custom_sql_check(self, context: AssetCheckExecutionContext, check_cfg: Union[dict, CustomSqlCheckConfig], db_key: str) -> AssetCheckResult:
        """Execute custom SQL check against the database."""
        try:
            database_resource = getattr(context.resources, db_key)
            
            # Extract configuration from check_cfg
            if isinstance(check_cfg, CustomSqlCheckConfig):
                sql_query = check_cfg.sql_query
                expected_result = check_cfg.expected_result
                comparison = check_cfg.comparison
            else:
                sql_query = check_cfg.get('sql_query')
                expected_result = check_cfg.get('expected_result')
                comparison = check_cfg.get('comparison', 'equals')
            
            if not sql_query:
                raise ValueError("sql_query is required for custom SQL check")
            
            with database_resource.get_connection() as conn:
                # Execute the SQL query directly against the database
                result = conn.execute(sql_query).fetchone()
                query_result = result[0] if result else None
                
            # Build metadata
            metadata = {
                "query": MetadataValue.text(sql_query),
                "query_result": MetadataValue.text(str(query_result)),
            }
            
            # If no expected result specified, just return the query result
            if expected_result is None:
                return AssetCheckResult(
                    passed=True,
                    description=f"Custom SQL query executed successfully: {query_result}",
                    metadata=metadata
                )
            
            # Perform comparison if expected result is specified
            expected_result_str = str(expected_result)
            passed = self._compare_values(str(query_result), expected_result_str, comparison)
            
            description = f"Custom SQL query result: {query_result}, Expected: {expected_result_str}, Comparison: {comparison}"
            if passed:
                description += " - PASSED"
            else:
                description += " - FAILED"
            
            metadata.update({
                "expected_result": MetadataValue.text(expected_result_str),
                "comparison": MetadataValue.text(self._safe_enum_to_string(comparison)),
            })
            
            return AssetCheckResult(
                passed=passed,
                description=description,
                metadata=metadata
            )
            
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Custom SQL check failed: {str(e)}",
                metadata={"error": MetadataValue.text(str(e))}
            )

    def _execute_custom_dataframe_query(self, df) -> dict:
        """Execute custom dataframe query and validate results."""
        if not self._get_check_config_value('custom_dataframe_query', None):
            raise ValueError("custom_dataframe_query is required for custom dataframe check")
        
        try:
            # Handle group_by scenario
            if self._get_check_config_value('custom_dataframe_group_by', None):
                # For group_by, we apply the query to each group separately
                group_results = {}
                failed_groups = []
                total_groups = 0
                
                if hasattr(df, 'select'):  # Polars
                    # Get unique groups
                    groups = df.select(df[self._get_check_config_value('custom_dataframe_group_by', None)].unique()).to_numpy().flatten()
                    total_groups = len(groups)
                    
                    for group_name in groups:
                        # Filter data for this group
                        group_df = df.filter(df[self._get_check_config_value('custom_dataframe_group_by', None)] == group_name)
                        
                        # Apply the query to this group's data
                        try:
                            if self._get_check_config_value('custom_dataframe_query', None).startswith("SELECT"):
                                # Handle SELECT queries
                                result = group_df.select(self._get_check_config_value('custom_dataframe_query', None)).to_numpy()
                                metric_value = float(result[0][0]) if len(result) > 0 else 0.0
                            else:
                                # Handle aggregation queries (like COUNT, SUM, etc.)
                                result = group_df.select(self._get_check_config_value('custom_dataframe_query', None)).to_numpy()
                                metric_value = float(result[0][0]) if len(result) > 0 else 0.0
                        except Exception as e:
                            # If query fails for this group, mark as failed
                            metric_value = None
                        
                        group_results[str(group_name)] = metric_value
                        
                        # Check if this group passes the validation
                        if self._get_check_config_value('custom_dataframe_expected_result', None) is not None:
                            if metric_value is not None:
                                passed = self._compare_values(str(metric_value), str(self._get_check_config_value('custom_dataframe_expected_result', None)), self._get_check_config_value('custom_dataframe_comparison', None))
                                if not passed:
                                    failed_groups.append(str(group_name))
                            else:
                                failed_groups.append(str(group_name))
                        else:
                            # No expected result specified, just check if metric_value is valid
                            if metric_value is None or pd.isna(metric_value):
                                failed_groups.append(str(group_name))
                
                else:  # Pandas
                    # Get unique groups
                    groups = df[self._get_check_config_value('custom_dataframe_group_by', None)].unique()
                    total_groups = len(groups)
                    
                    for group_name in groups:
                        # Filter data for this group
                        group_df = df[df[self._get_check_config_value('custom_dataframe_group_by', None)] == group_name]
                        
                        # Apply the query to this group's data
                        try:
                            if self._get_check_config_value('custom_dataframe_query', None).startswith("SELECT"):
                                # Handle SELECT queries
                                result = group_df.eval(self._get_check_config_value('custom_dataframe_query', None))
                                metric_value = float(result.iloc[0]) if len(result) > 0 else 0.0
                            else:
                                # Handle aggregation queries
                                result = group_df.eval(self._get_check_config_value('custom_dataframe_query', None))
                                metric_value = float(result) if result is not None else 0.0
                        except Exception as e:
                            # If query fails for this group, mark as failed
                            metric_value = None
                        
                        group_results[str(group_name)] = metric_value
                        
                        # Check if this group passes the validation
                        if self._get_check_config_value('custom_dataframe_expected_result', None) is not None:
                            if metric_value is not None:
                                passed = self._compare_values(str(metric_value), str(self._get_check_config_value('custom_dataframe_expected_result', None)), self._get_check_config_value('custom_dataframe_comparison', None))
                                if not passed:
                                    failed_groups.append(str(group_name))
                            else:
                                failed_groups.append(str(group_name))
                        else:
                            # No expected result specified, just check if metric_value is valid
                            if metric_value is None or pd.isna(metric_value):
                                failed_groups.append(str(group_name))
                
                # Determine overall pass/fail based on allowed_failures
                passed = len(failed_groups) <= self._get_check_config_value('custom_dataframe_allowed_failures', 0)
                
                description = f"Custom dataframe check grouped by {self._get_check_config_value('custom_dataframe_group_by', None)}: {total_groups - len(failed_groups)}/{total_groups} groups passed"
                if failed_groups:
                    description += f". Failed groups: {failed_groups}"
                
                return {
                    "passed": passed,
                    "description": description,
                    "query_result": str(group_results),
                    "group_results": group_results,
                    "failed_groups": failed_groups,
                    "total_groups": total_groups
                }
            else:
                # Non-grouped scenario - original logic
                if hasattr(df, 'select'):  # Polars
                    result = df.select(self._get_check_config_value('custom_dataframe_query', None)).to_numpy()
                else:  # Pandas
                    result = df.eval(self._get_check_config_value('custom_dataframe_query', None))
                
                query_result = str(result)
                
                # If no expected result specified, just return the query result
                if self._get_check_config_value('custom_dataframe_expected_result', None) is None:
                    return {
                        "passed": True,
                        "description": f"Custom dataframe query executed successfully: {query_result}",
                        "query_result": query_result
                    }
                
                # Perform comparison if expected result is specified
                expected_result = str(self._get_check_config_value('custom_dataframe_expected_result', None))
                passed = self._compare_values(query_result, expected_result, self._get_check_config_value('custom_dataframe_comparison', None))
                
                description = f"Custom dataframe query result: {query_result}, Expected: {expected_result}, Comparison: {self._get_check_config_value('custom_dataframe_comparison', None)}"
                if passed:
                    description += " - PASSED"
                else:
                    description += " - FAILED"
                
                return {
                    "passed": passed,
                    "description": description,
                    "query_result": query_result
                }
            
        except Exception as e:
            return {
                "passed": False,
                "description": f"Custom dataframe query execution failed: {str(e)}",
                "query_result": str(e)
            }

    def _safe_enum_to_string(self, value) -> str:
        """Safely convert enum values to strings for metadata storage.
        
        Args:
            value: Any value that might be an enum
            
        Returns:
            String representation of the value
        """
        if hasattr(value, 'value') and hasattr(value, '__class__') and hasattr(value.__class__, '__bases__'):
            # Check if it's an enum by looking for the value attribute and enum base classes
            for base in value.__class__.__bases__:
                if 'Enum' in str(base):
                    return str(value.value)
        return str(value)

    def _compare_values(self, actual: str, expected: str, comparison: Union[str, ComparisonOperator]) -> bool:
        """Compare actual and expected values based on the specified comparison operator.
        
        Args:
            actual: The actual value to compare
            expected: The expected value to compare against
            comparison: Comparison operator (string or ComparisonOperator enum)
        """
        # Convert enum to string if needed
        comparison_str = comparison.value if isinstance(comparison, ComparisonOperator) else comparison
        
        if comparison_str == "equals":
            return actual == expected
        elif comparison_str == "not_equals":
            return actual != expected
        elif comparison_str == "contains":
            return expected in actual
        elif comparison_str == "not_contains":
            return expected not in actual
        elif comparison_str == "is_null":
            return actual.lower() in ["null", "none", "nan"]
        elif comparison_str == "is_not_null":
            return actual.lower() not in ["null", "none", "nan"]
        else:
            # For numeric comparisons, try to convert to float
            try:
                actual_num = float(actual)
                expected_num = float(expected)
                
                if comparison_str == "greater_than":
                    return actual_num > expected_num
                elif comparison_str == "less_than":
                    return actual_num < expected_num
                elif comparison_str == "greater_than_or_equal":
                    return actual_num >= expected_num
                elif comparison_str == "less_than_or_equal":
                    return actual_num <= expected_num
                else:
                    return False
            except ValueError:
                return False

    def _get_pattern_regex(self) -> str:
        """Get regex pattern from preset or custom regex."""
        if self._get_check_config_value('pattern_preset', None):
            return self._get_preset_regex(self._get_check_config_value('pattern_preset', None))
        elif self._get_check_config_value('pattern_regex', None):
            return self._get_check_config_value('pattern_regex', None)
        else:
            raise ValueError("Either pattern_preset or pattern_regex must be specified for pattern matching")
    
    def _get_preset_regex(self, preset: str) -> str:
        """Get regex pattern for common data types."""
        patterns = {
            # Email validation (RFC 5322 compliant)
            "email": r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            
            # URL validation (supports http, https, ftp)
            "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
            
            # UUID validation (version 4)
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            
            # Phone number validation (international format)
            "phone": r"^\+?[1-9]\d{1,14}$",
            
            # Date validation (YYYY-MM-DD)
            "date": r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$",
            
            # Time validation (HH:MM:SS)
            "time": r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$",
            
            # DateTime validation (YYYY-MM-DD HH:MM:SS)
            "datetime": r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\s(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$",
            
            # IPv4 validation
            "ipv4": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            
            # IPv6 validation
            "ipv6": r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$",
            
            # Credit card validation (basic format)
            "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$",
            
            # Social Security Number validation
            "ssn": r"^\d{3}-?\d{2}-?\d{4}$",
            
            # US ZIP code validation
            "zipcode": r"^\d{5}(?:-\d{4})?$",
            
            # Currency validation ($1,234.56 or $1234.56)
            "currency": r"^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$",
            
            # Percentage validation (0-100%)
            "percentage": r"^(?:100(?:\.0+)?%?|\d{1,2}(?:\.\d+)?%?)$"
        }
        
        if preset not in patterns:
            raise ValueError(f"Unsupported pattern preset: {preset}. Supported presets: {list(patterns.keys())}")
        
        return patterns[preset]
    
    def _get_pattern_info(self) -> dict:
        """Get pattern information for metadata."""
        pattern_info = {}
        
        if self._get_check_config_value('pattern_preset', None):
            pattern_info["pattern_preset"] = MetadataValue.text(self._get_check_config_value('pattern_preset', None))
            pattern_info["pattern_regex"] = MetadataValue.text(self._get_preset_regex(self._get_check_config_value('pattern_preset', None)))
        elif self._get_check_config_value('pattern_regex', None):
            pattern_info["pattern_regex"] = MetadataValue.text(self._get_check_config_value('pattern_regex', None))
        
        pattern_column = self._get_check_config_value('pattern_column', None)
        if pattern_column:
            pattern_info["pattern_column"] = MetadataValue.text(pattern_column)
        
        return pattern_info
        
    def _execute_cross_table_validation(self, context: AssetCheckExecutionContext) -> AssetCheckResult:
        """Execute cross-table validation check."""
        # Get configuration using helper method with correct prefixed field names
        source_table = self._get_check_config_value('cross_table_source_table', '')
        source_database = self._get_check_config_value('cross_table_source_database')
        validation_type = self._get_check_config_value('cross_table_validation_type', 'row_count')
        join_columns = self._get_check_config_value('cross_table_join_columns', [])
        group_by = self._get_check_config_value('cross_table_group_by')
        
        # Add debugging
        context.log.info(f"Cross-table validation - source_table: {source_table}")
        context.log.info(f"Cross-table validation - join_columns: {join_columns}")
        context.log.info(f"Cross-table validation - validation_type: {validation_type}")
        context.log.info(f"Cross-table validation - _flat_config: {getattr(self, '_flat_config', {})}")
        
        # Validate required configuration
        if not source_table:
            return AssetCheckResult(
                passed=False,
                description="Cross-table validation failed: source_table is required",
                metadata={
                    "error": MetadataValue.text("source_table is required"),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name),
                    "validation_type": MetadataValue.text(validation_type)
                }
            )
        
        if not join_columns:
            return AssetCheckResult(
                passed=False,
                description="Cross-table validation failed: join_columns is required",
                metadata={
                    "error": MetadataValue.text("join_columns is required"),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name),
                    "validation_type": MetadataValue.text(validation_type)
                }
            )
        
        try:
            # Get database resources
            dest_db = getattr(context.resources, self.database_resource_key)
            source_db = getattr(context.resources, source_database or self.database_resource_key)
            
            # Build WHERE clause for filtering
            where_clause = self._build_where_clause()
            
            # Determine validation type and execute appropriate logic
            if validation_type == "row_count":
                return self._execute_cross_table_row_count_validation(context, dest_db, source_db, where_clause)
            elif validation_type == "column_values":
                return self._execute_cross_table_column_values_validation(context, dest_db, source_db, where_clause)
            elif validation_type == "aggregate":
                return self._execute_cross_table_aggregate_validation(context, dest_db, source_db, where_clause)
            else:
                raise ValueError(f"Unsupported validation type: {validation_type}")
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Cross-table validation failed: {str(e)}",
                metadata={
                    "error": MetadataValue.text(str(e)),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name),
                    "validation_type": MetadataValue.text(validation_type)
                }
            )
    
    def _execute_cross_table_row_count_validation(self, context: AssetCheckExecutionContext, dest_db, source_db, where_clause: str) -> AssetCheckResult:
        """Execute row count validation between source and destination tables."""
        # Get configuration using helper method with correct prefixed field names
        source_table = self._get_check_config_value('cross_table_source_table', '')
        join_columns = self._get_check_config_value('cross_table_join_columns', [])
        group_by = self._get_check_config_value('cross_table_group_by')
        tolerance = self._get_check_config_value('cross_table_tolerance', 5.0)
        allowed_failures = self._get_check_config_value('cross_table_allowed_failures', 0)
        
        # Add debugging
        context.log.info(f"Cross-table row count validation - source_table: {source_table}")
        context.log.info(f"Cross-table row count validation - join_columns: {join_columns}")
        context.log.info(f"Cross-table row count validation - group_by: {group_by}")
        
        # Validate required configuration
        if not source_table:
            return AssetCheckResult(
                passed=False,
                description="Cross-table row count validation failed: source_table is required",
                metadata={
                    "error": MetadataValue.text("source_table is required"),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name)
                }
            )
        
        if not join_columns:
            return AssetCheckResult(
                passed=False,
                description="Cross-table row count validation failed: join_columns is required",
                metadata={
                    "error": MetadataValue.text("join_columns is required"),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name)
                }
            )
        
        try:
            # Build join conditions
            join_conditions = " AND ".join([f"dest.{col} = src.{col}" for col in join_columns])
            
            # Query to get row counts
            if group_by:
                # Grouped validation
                query = f"""
                SELECT 
                    dest.{group_by} as group_name,
                    COUNT(DISTINCT dest.*) as dest_count,
                    COUNT(DISTINCT src.*) as src_count
                FROM {self.table_name} dest
                LEFT JOIN {source_table} src ON {join_conditions}
                {f"WHERE {where_clause}" if where_clause else ""}
                GROUP BY dest.{group_by}
                """
            else:
                # Simple validation
                query = f"""
                SELECT 
                    COUNT(DISTINCT dest.*) as dest_count,
                    COUNT(DISTINCT src.*) as src_count
                FROM {self.table_name} dest
                LEFT JOIN {source_table} src ON {join_conditions}
                {f"WHERE {where_clause}" if where_clause else ""}
                """
            
            # Execute query
            results = self._execute_database_query(dest_db, query)
            
            if group_by:
                # Process grouped results
                failed_groups = []
                total_groups = len(results)
                group_results = {}
                
                for row in results:
                    group_name = row[0]
                    dest_count = float(row[1])
                    src_count = float(row[2])
                    
                    # Calculate difference percentage
                    if src_count > 0:
                        diff_pct = abs(dest_count - src_count) / src_count * 100
                    else:
                        diff_pct = 0 if dest_count == 0 else 100
                    
                    group_results[group_name] = {
                        "dest_count": dest_count,
                        "src_count": src_count,
                        "difference_pct": diff_pct
                    }
                    
                    # Check if difference exceeds tolerance
                    if diff_pct > tolerance:
                        failed_groups.append(group_name)
                
                passed = len(failed_groups) <= allowed_failures
                description = f"Cross-table row count validation: {total_groups - len(failed_groups)}/{total_groups} groups passed"
                if not passed:
                    description += f". Failed groups: {failed_groups}"
                
                return AssetCheckResult(
                    passed=bool(passed),
                    description=description,
                    metadata={
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups_count": MetadataValue.int(len(failed_groups)),
                        "allowed_failures": MetadataValue.int(allowed_failures),
                        "tolerance_pct": MetadataValue.float(tolerance),
                        "group_results": MetadataValue.json(group_results),
                        "source_table": MetadataValue.text(self.cross_table_source_table),
                        "destination_table": MetadataValue.text(self.table_name)
                    }
                )
            else:
                # Process simple results
                dest_count = float(results[0][0])
                src_count = float(results[0][1])
                
                # Calculate difference percentage
                if src_count > 0:
                    diff_pct = abs(dest_count - src_count) / src_count * 100
                else:
                    diff_pct = 0 if dest_count == 0 else 100
                
                passed = diff_pct <= tolerance
                description = f"Cross-table row count validation: destination={dest_count}, source={src_count}, difference={diff_pct:.2f}%"
                
                return AssetCheckResult(
                    passed=bool(passed),
                    description=description,
                    metadata={
                        "dest_count": MetadataValue.int(int(dest_count)),
                        "src_count": MetadataValue.int(int(src_count)),
                        "difference_pct": MetadataValue.float(diff_pct),
                        "tolerance_pct": MetadataValue.float(tolerance),
                        "source_table": MetadataValue.text(source_table),
                        "destination_table": MetadataValue.text(self.table_name)
                    }
                )
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Cross-table row count validation failed: {str(e)}",
                metadata={
                    "error": MetadataValue.text(str(e)),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name)
                }
            )
    
    def _execute_cross_table_column_values_validation(self, context: AssetCheckExecutionContext, dest_db, source_db, where_clause: str) -> AssetCheckResult:
        """Execute column values validation between source and destination tables."""
        # This would compare specific column values between tables
        # Implementation would depend on specific requirements
        return AssetCheckResult(
            passed=False,
            description="Column values validation not yet implemented",
            metadata={
                "note": MetadataValue.text("Column values validation requires specific implementation based on requirements")
            }
        )
    
    def _execute_cross_table_aggregate_validation(self, context: AssetCheckExecutionContext, dest_db, source_db, where_clause: str) -> AssetCheckResult:
        """Execute aggregate validation between source and destination tables."""
        try:
            # Get source table from configuration
            source_table = self._get_check_config_value('cross_table_source_table', '')
            
            # Build join conditions
            join_conditions = " AND ".join([f"dest.{col} = src.{col}" for col in self._get_check_config_value('cross_table_join_columns', [])])
            
            # Build aggregate query
            agg_function = self._get_check_config_value('cross_table_aggregate_function', 'sum').upper()
            agg_column = self._get_check_config_value('cross_table_aggregate_column', 'column')
            
            if self._get_check_config_value('cross_table_group_by', None):
                # Grouped aggregate validation
                query = f"""
                SELECT 
                    dest.{self._get_check_config_value('cross_table_group_by', None)} as group_name,
                    {agg_function}(dest.{agg_column}) as dest_agg,
                    {agg_function}(src.{agg_column}) as src_agg
                FROM {self.table_name} dest
                LEFT JOIN {source_table} src ON {join_conditions}
                {f"WHERE {where_clause}" if where_clause else ""}
                GROUP BY dest.{self._get_check_config_value('cross_table_group_by', None)}
                """
            else:
                # Simple aggregate validation
                query = f"""
                SELECT 
                    {agg_function}(dest.{agg_column}) as dest_agg,
                    {agg_function}(src.{agg_column}) as src_agg
                FROM {self.table_name} dest
                LEFT JOIN {source_table} src ON {join_conditions}
                {f"WHERE {where_clause}" if where_clause else ""}
                """
            
            # Execute query
            results = self._execute_database_query(dest_db, query)
            
            if self._get_check_config_value('cross_table_group_by', None):
                # Process grouped results
                failed_groups = []
                total_groups = len(results)
                group_results = {}
                
                for row in results:
                    group_name = row[0]
                    dest_agg = float(row[1]) if row[1] is not None else 0
                    src_agg = float(row[2]) if row[2] is not None else 0
                    
                    # Calculate difference percentage
                    if src_agg != 0:
                        diff_pct = abs(dest_agg - src_agg) / abs(src_agg) * 100
                    else:
                        diff_pct = 0 if dest_agg == 0 else 100
                    
                    group_results[group_name] = {
                        "dest_agg": dest_agg,
                        "src_agg": src_agg,
                        "difference_pct": diff_pct
                    }
                    
                    # Check if difference exceeds tolerance
                    if diff_pct > self._get_check_config_value('cross_table_tolerance', 5.0):
                        failed_groups.append(group_name)
                
                passed = len(failed_groups) <= self._get_check_config_value('cross_table_allowed_failures', 0)
                description = f"Cross-table {agg_function.lower()} validation: {total_groups - len(failed_groups)}/{total_groups} groups passed"
                if not passed:
                    description += f". Failed groups: {failed_groups}"
                
                return AssetCheckResult(
                    passed=bool(passed),
                    description=description,
                    metadata={
                        "total_groups": MetadataValue.int(total_groups),
                        "failed_groups_count": MetadataValue.int(len(failed_groups)),
                        "allowed_failures": MetadataValue.int(self._get_check_config_value('cross_table_allowed_failures', 0)),
                        "tolerance_pct": MetadataValue.float(self._get_check_config_value('cross_table_tolerance', 5.0)),
                        "aggregate_function": MetadataValue.text(agg_function),
                        "aggregate_column": MetadataValue.text(agg_column),
                        "group_results": MetadataValue.json(group_results),
                        "source_table": MetadataValue.text(source_table),
                        "destination_table": MetadataValue.text(self.table_name)
                    }
                )
            else:
                # Process simple results
                dest_agg = float(results[0][0]) if results[0][0] is not None else 0
                src_agg = float(results[0][1]) if results[0][1] is not None else 0
                
                # Calculate difference percentage
                if src_agg != 0:
                    diff_pct = abs(dest_agg - src_agg) / abs(src_agg) * 100
                else:
                    diff_pct = 0 if dest_agg == 0 else 100
                
                passed = diff_pct <= self._get_check_config_value('cross_table_tolerance', 5.0)
                description = f"Cross-table {agg_function.lower()} validation: destination={dest_agg}, source={src_agg}, difference={diff_pct:.2f}%"
                
                return AssetCheckResult(
                    passed=bool(passed),
                    description=description,
                    metadata={
                        "dest_agg": MetadataValue.float(dest_agg),
                        "src_agg": MetadataValue.float(src_agg),
                        "difference_pct": MetadataValue.float(diff_pct),
                        "tolerance_pct": MetadataValue.float(self._get_check_config_value('cross_table_tolerance', 5.0)),
                        "aggregate_function": MetadataValue.text(agg_function),
                        "aggregate_column": MetadataValue.text(agg_column),
                        "source_table": MetadataValue.text(source_table),
                        "destination_table": MetadataValue.text(self.table_name)
                    }
                )
                
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                description=f"Cross-table aggregate validation failed: {str(e)}",
                metadata={
                    "error": MetadataValue.text(str(e)),
                    "source_table": MetadataValue.text(source_table),
                    "destination_table": MetadataValue.text(self.table_name),
                    "aggregate_function": MetadataValue.text(self._get_check_config_value('cross_table_aggregate_function', 'sum')),
                    "aggregate_column": MetadataValue.text(self._get_check_config_value('cross_table_aggregate_column', 'column'))
                }
            )

    def _execute_dataframe_query_check(self, context: AssetCheckExecutionContext, df, check_cfg: Union[dict, DataframeQueryCheckConfig]) -> AssetCheckResult:
        """Execute a dataframe query check against the dataframe."""
        try:
            # Get configuration using helper method
            query = self._get_check_config_value('query', '')
            expected = self._get_check_config_value('expected_result', None)
            comparison = self._get_check_config_value('comparison', 'equals')
            description = self._get_check_config_value('name', '')
            blocking = self._get_check_config_value('blocking', False)
            
            filtered_df = self._filter_dataframe(df)
            
            # Handle different dataframe types
            import pandas as pd
            if isinstance(filtered_df, pd.DataFrame):
                # Pandas dataframe
                result_df = filtered_df.query(query)
                actual_result = len(result_df)
            else:
                # Polars or other dataframe - convert to pandas for query
                try:
                    pdf = filtered_df.to_pandas()
                    result_df = pdf.query(query)
                    actual_result = len(result_df)
                except Exception:
                    # Fallback: try to evaluate the query as a boolean expression
                    # This handles simple queries like "year_of_birth >= 2020"
                    try:
                        # For simple boolean expressions, we can evaluate them
                        import pandas as pd
                        pdf = filtered_df.to_pandas() if hasattr(filtered_df, 'to_pandas') else pd.DataFrame(filtered_df)
                        # Create a boolean mask from the query
                        mask = pdf.eval(query)
                        result_df = pdf[mask]
                        actual_result = len(result_df)
                    except Exception as eval_error:
                        # Last resort: try to parse the query manually
                        actual_result = 0
                        context.log.warning(f"Could not execute dataframe query '{query}': {eval_error}")
                
            passed = self._compare_values(actual_result, expected, comparison)
            desc = f"Dataframe Query Check: {description}"
            if not passed:
                desc += f" - FAILED (Expected: {expected}, Got: {actual_result})"
                
            return AssetCheckResult(
                passed=passed,
                metadata={
                    "query": MetadataValue.text(query),
                    "expected_result": MetadataValue.text(str(expected)),
                    "actual_result": MetadataValue.int(actual_result),
                    "comparison": MetadataValue.text(self._safe_enum_to_string(comparison)),
                    "dataframe_type": MetadataValue.text(type(filtered_df).__module__.split(".")[0]),
                    "blocking": MetadataValue.bool(blocking)
                },
                description=desc
            )
        except Exception as e:
            return AssetCheckResult(
                passed=False,
                metadata={"error": MetadataValue.text(str(e))},
                description=f"Dataframe query check failed with error: {e}"
            )
