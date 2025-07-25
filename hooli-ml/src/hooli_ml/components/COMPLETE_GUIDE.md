# DatabricksMultiNotebookJobComponent - Complete Guide

## Goals

* Demonstrate how to create a re-usable Dagster component that can translate Databricks concepts into Dagster concepts, and have Dagster orchestrate those Databricks concepts. I used the [mlops stack databricks asset bundle](https://docs.databricks.com/aws/en/dev-tools/bundles/mlops-stacks) as a great jumping off point.
* Demonstrate how to scaffold this re-usable component from exsiting databricks config (in this case, from a databricks asset bundle).
* Demonstrate how Dagster can create and submit ad hoc Databricks jobs (whether to an existing cluster, a new cluster, or serverless) that are comprised of individual databricks tasks that can be selected either for ad hoc materializations or via schedule Dagster jobs.

## Current functionality

This re-usable component works with the following databricks entities:

* Notebook tasks
* wheel tasks (Java or Python)
* Conditional tasks on previous outputs

## Future ideas

* Translate monitors into Dagster asset checks
* Show how to return results from the databricks task into a Dagster asset metadata or use in a Dagster asset check
* Implement a Databricks API scaffolder which goes to a specific databricks instance and pulls in tasks from there
* Pull in Databricks job information and translate to Dagter jobs


## Overview

The `DatabricksMultiNotebookJobComponent` is a Dagster component that allows you to run multiple Databricks notebooks as tasks within a single Databricks job. Each task can produce multiple assets, with full support for Dagster's asset subsetting, config overrides, and default behaviors.

## Key Features

### 1. Multiple Asset Specs Per Task
Each task can define multiple `asset_specs`, allowing a single notebook to produce multiple logical assets:

```yaml
tasks:
  - task_key: "feature_engineering"
    notebook_path: "/path/to/notebook"
    asset_specs:
      - key: raw_features
        description: "Raw features extracted from source data"
      - key: engineered_features  
        description: "Transformed and engineered features"
      - key: feature_quality_report
        description: "Feature validation and quality metrics"
```

### 2. Smart Defaults
All asset specs have sensible defaults:
- `skippable: true` - Assets can be skipped during subsetting
- `kinds: ["databricks"]` - Tagged as Databricks assets
- `description: "Asset for task {task_key}"` - Auto-generated description

### 3. Flexible Override Patterns
You can override defaults at multiple levels:

```yaml
asset_specs:
  # Uses all defaults
  - key: basic_asset
  
  # Override only kinds
  - key: custom_kinds_asset
    kinds: ["databricks", "ml", "feature_engineering"]
  
  # Override only skippable
  - key: critical_asset
    skippable: false
    
  # Add dependencies
  - key: dependent_asset
    description: "Asset that depends on other assets"
    deps: ["basic_asset", "custom_kinds_asset"]
    
  # Override everything
  - key: fully_custom_asset
    description: "Custom description"
    kinds: ["databricks", "custom"]
    skippable: false
    deps: ["critical_asset"]
    skippable: false
```

### 4. Default Asset Creation
Tasks without `asset_specs` automatically get a default asset:

```yaml
tasks:
  - task_key: "simple_task"
    notebook_path: "/path/to/notebook"
    # No asset_specs - creates:
    # key: "simple_task"
    # kinds: ["databricks"] 
    # skippable: true
    # description: "Asset for task simple_task"
```

### 5. Per-Asset Config Overrides
Use Dagster's config system to override parameters for specific assets:

```python
config = MultiNotebookJobConfig(
    asset_configs={
        "advanced_model": NotebookTaskConfig(
            parameters={
                "model_type": "XGBoost",
                "n_estimators": 200,
                "learning_rate": 0.1
            }
        ),
        "baseline_model": NotebookTaskConfig(
            parameters={
                "model_type": "RandomForest", 
                "n_estimators": 100
            }
        )
    }
)
```

### 6. Asset Subsetting Support
Select specific assets for materialization:
- Only tasks producing selected assets will run
- Config overrides apply to selected assets
- Efficient resource usage

### 7. Databricks Job Run URLs and Metadata

The component automatically provides rich metadata and direct links to Databricks job runs:

#### Structured Logging

- Job run URLs in execution logs: `context.log.info(f"Databricks job run URL: {job_run_url}")`
- Individual task URLs: `context.log.info(f"Task {task_key} details: {task_url}")`
- Job completion status and summaries

#### Metadata in MaterializeResult

Each successful asset includes comprehensive metadata:

```python
# Metadata automatically attached to each asset
{
    "databricks_job_url": MetadataValue.url("https://workspace.cloud.databricks.com/jobs/12345"),
    "databricks_task_url": MetadataValue.url("https://workspace.cloud.databricks.com/jobs/12345#task/my_task"),
    "job_run_id": "67890",
    "task_key": "my_task",
    "task_state": "SUCCESS",
    "notebook_path": "/path/to/notebook",
    "serverless": True,
    "final_parameters": {"param1": "value1"},
    "config_overrides": {"param1": "override_value"}
}
```

#### URL Format

- **Job Run URL**: `{workspace_url}/jobs/{run_id}` - View overall job status and logs
- **Task URL**: `{workspace_url}/jobs/{run_id}#task/{task_key}` - Direct link to specific task execution

This enables easy debugging and monitoring by providing direct access to:

- Individual task execution logs
- Cluster metrics and resource usage
- Spark UI for performance analysis
- Error details and stack traces

## Configuration Patterns

### Basic Configuration
```yaml
type: hooli_ml.components.DatabricksMultiNotebookJobComponent
attributes:
  job_name_prefix: "my_pipeline"
  serverless: true
  tasks:
    - task_key: "process_data"
      notebook_path: "/path/to/notebook"
      parameters:
        input_table: "raw.data"
```

### Multiple Assets Per Task
```yaml
tasks:
  - task_key: "ml_training"
    notebook_path: "/notebooks/train.py"
    asset_specs:
      - key: model_v1
        description: "RandomForest model"
        skippable: false
      - key: model_v2  
        description: "XGBoost model"
        skippable: false
      - key: training_metrics
        description: "Training performance metrics"
        # Uses default skippable: true
    parameters:
      target_column: "price"
```

### Mixed Default and Custom Specs
```yaml
tasks:
  # Task with explicit asset specs
  - task_key: "feature_eng"
    asset_specs:
      - key: features
        kinds: ["databricks", "ml"]
      - key: feature_stats
        kinds: ["databricks", "analytics"]
        
  # Task with default asset spec  
  - task_key: "validation"
    # Creates default: key="validation", kinds=["databricks"], skippable=true
```

### Cluster vs Serverless
```yaml
# Serverless (recommended)
attributes:
  serverless: true
  
# Or traditional cluster
attributes:
  serverless: false
  spark_version: "13.3.x-scala2.12"
  node_type_id: "i3.xlarge" 
  num_workers: 2
```

## Python Usage Examples

### Basic Component Creation
```python
from hooli_ml.components.databricks_notebook_component import DatabricksMultiNotebookJobComponent

component = DatabricksMultiNotebookJobComponent(
    job_name_prefix="my_pipeline",
    serverless=True,
    tasks=[
        {
            "task_key": "process_data",
            "notebook_path": "/notebooks/process.py",
            "asset_specs": [
                {"key": "processed_data", "skippable": False},
                {"key": "data_quality", "kinds": ["databricks", "quality"]}
            ],
            "parameters": {"input_table": "raw.data"}
        }
    ]
)

defs = component.build_defs(context=None)
```

### With Config Overrides
```python
from hooli_ml.components.databricks_notebook_component import (
    MultiNotebookJobConfig, 
    NotebookTaskConfig
)

# Configure different parameters per asset
config = MultiNotebookJobConfig(
    asset_configs={
        "model_v1": NotebookTaskConfig(
            parameters={"model_type": "RandomForest", "n_estimators": 100}
        ),
        "model_v2": NotebookTaskConfig(
            parameters={"model_type": "XGBoost", "learning_rate": 0.1}
        )
    }
)

# Use config during materialization
# (passed to the multi-asset function via Dagster's config system)
```

### Asset Subsetting
```python
import dagster as dg

# Select specific assets for materialization
selected_assets = [
    dg.AssetKey("processed_data"),
    dg.AssetKey("model_v1")
]

# Only tasks producing these assets will run
# Config overrides still apply to selected assets
```

## Best Practices

### 1. Naming Conventions
- Use descriptive, consistent asset keys
- Include the data type or purpose in the key
- Example: `feature_engineering_pickup`, `model_training_v2`, `validation_report`

### 2. Default Usage
- Rely on defaults (`skippable: true`, `kinds: ["databricks"]`) when appropriate
- Only override when you need different behavior
- Use `skippable: false` for critical assets that should never be skipped

### 3. Asset Organization
- Group related assets in the same task
- Use kinds to categorize assets (`ml`, `feature_engineering`, `validation`, etc.)
- Consider asset dependencies when organizing tasks

### 4. Config Overrides
- Use config overrides for environment-specific parameters
- Keep base parameters in the task definition
- Use meaningful parameter names that are self-documenting

### 5. Error Handling
- Set `skippable: false` for critical assets
- Use validation in notebooks to catch errors early
- Include sufficient logging for debugging

## Migration from Previous Versions

### Old Pattern (Single Asset Per Task)
```yaml
# OLD: One task per asset
tasks:
  - task_key: "pickup_features"
    asset_key: "feature_engineering_pickup_job"
  - task_key: "dropoff_features" 
    asset_key: "feature_engineering_dropoff_job"
```

### New Pattern (Multiple Assets Per Task)
```yaml
# NEW: Multiple assets per task
tasks:
  - task_key: "location_features"
    asset_specs:
      - key: "feature_engineering_pickup_job"
      - key: "feature_engineering_dropoff_job"
```

### Benefits of Migration
- Reduced job overhead (fewer Databricks tasks)
- Better resource utilization
- More flexible asset organization
- Support for config overrides per asset

## Troubleshooting

### Common Issues

1. **Asset key collisions**: Ensure all asset keys are unique across all tasks
2. **Missing cluster config**: When `serverless: false`, provide `spark_version`, `node_type_id`, `num_workers`
3. **Config override not working**: Check that the asset key in config matches the asset spec key exactly
4. **Task not running**: Verify that at least one asset from the task is selected for materialization

### Debugging Tips

1. Check logs for asset selection information
2. Verify config merging in metadata
3. Use `can_subset=True` for testing subsetting behavior
4. Review Databricks job logs for notebook execution details

## Examples

See the following files for complete examples:
- `defs.yaml` - Basic configuration with defaults
- `defs_with_config_overrides.yaml` - Config override examples  
- `comprehensive_multi_notebook_example.py` - Complete Python examples
- `README_ASSET_SPECS_UPDATE.md` - Migration guide and detailed explanations
