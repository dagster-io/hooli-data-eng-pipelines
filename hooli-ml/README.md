# Hooli ML

This directory contains ML-related components and utilities for the Hooli data engineering platform.

## DatabricksMultiNotebookJobComponent

The `DatabricksMultiNotebookJobComponent` is a powerful Dagster component that allows you to run multiple Databricks tasks as a single job, providing better resource utilization and coordination between related tasks.

### Features

- **Multiple Task Types**: Support for notebook tasks, existing job tasks, Python wheel tasks, Spark JAR tasks, and condition tasks
- **Library Management**: Configure libraries per task for Python wheels, JAR files, PyPI packages, Maven packages, and CRAN packages
- **Job Parameters**: Configure job parameters for individual tasks with support for both list and dict formats
- **Common Configuration**: Apply shared parameters to all tasks in the job
- **Comprehensive Metadata**: Rich metadata for Databricks-like experience
- **Table Location Metadata**: Automatic extraction of table and data location information
- **Asset Dependencies**: Map asset dependencies to task dependencies automatically
- **Config Overrides**: Override parameters per asset
- **Asset Subsetting**: Run only selected assets
- **Scaffolding**: Generate components from Databricks bundle configurations

### Supported Libraries

The component supports the following library types:

#### Python Libraries
- **Wheels (whl)**: Custom Python wheel packages
- **PyPI Packages**: Python packages from PyPI with optional version specification
- **Eggs (egg)**: Python egg packages

#### Java/Scala Libraries
- **JAR Files**: Custom JAR files
- **Maven Packages**: Maven dependencies with coordinates, repository, and exclusions

#### R Libraries
- **CRAN Packages**: R packages from CRAN with optional repository specification

### Usage Examples

#### Basic Configuration

```yaml
type: hooli_ml.components.DatabricksMultiNotebookJobComponent

attributes:
  job_name_prefix: "my_ml_pipeline"
  serverless: false
  spark_version: "13.3.x-scala2.12"
  node_type_id: "i3.xlarge"
  num_workers: 2
  
  tasks:
    - task_key: "feature_engineering"
      notebook_path: "/Users/workspace_user/ml_pipelines/feature_engineering"
      parameters:
        input_table: "raw.customer_data"
        output_table: "features.customer_features"
      libraries:
        - whl: "dbfs:/FileStore/wheels/my_custom_package-1.0.0-py3-none-any.whl"
        - pypi:
            package: "pandas"
            version: "2.0.0"
        - pypi:
            package: "scikit-learn"
            version: "1.3.0"
      asset_specs:
        - key: customer_features
          description: "Engineered customer features"
```

#### Library Configuration Examples

**Python Wheel with PyPI Libraries:**
```yaml
libraries:
  - whl: "dbfs:/FileStore/wheels/ml_processing-2.1.0-py3-none-any.whl"
  - pypi:
      package: "numpy"
      version: "1.24.0"
  - pypi:
      package: "matplotlib"
      version: "3.7.0"
```

**Maven Dependencies:**
```yaml
libraries:
  - maven:
      coordinates: "org.apache.spark:spark-sql_2.12:3.4.0"
      repo: "https://repo1.maven.org/maven2/"
  - maven:
      coordinates: "com.amazonaws:aws-java-sdk-s3:1.12.261"
      exclusions: ["com.fasterxml.jackson.core:jackson-core"]
```

**R Libraries:**
```yaml
libraries:
  - cran:
      package: "dplyr"
      repo: "https://cran.r-project.org"
  - cran:
      package: "ggplot2"
  - pypi:
      package: "rpy2"
      version: "3.5.0"
```

#### Template Variables

You can use template variables for dynamic library paths:

```yaml
libraries:
  - whl: "${var.lib_file_path}"
  - pypi:
      package: "pandas"
```

#### Job Parameters

Configure job parameters for individual tasks. Supports both list and dictionary formats:

**List Format (with name/default pairs):**
```yaml
job_parameters:
  - name: orchestrator_job_run_id
    default: "{{ run_id }}"
  - name: environment
    default: "{{ env }}"
  - name: output_bucket_name
    default: "{{ var.output_bucket_name }}"
  - name: profiler_enabled
    default: false
```

**Dictionary Format (direct key-value pairs):**
```yaml
job_parameters:
  orchestrator_job_run_id: "{{ run_id }}"
  environment: "{{ env }}"
  output_bucket_name: "{{ var.output_bucket_name }}"
  profiler_enabled: false
  batch_size: 1000
  timeout_minutes: 30
```

#### Common Configuration

Apply shared parameters to all tasks in the job. Supports both key-value pairs and boolean flags:

```yaml
common_config:
  - "--experiment_settings={{ experiment_settings }}"
  - "--catalog_map={{ catalog_map }}"
  - "--log_level={{ log_level }}"
  - "--llm_calls={{ llm_calls }}"
  - "--git_sha={{ git_sha }}"
  - "--output_bucket_name={{ output_bucket_name }}"
  - "--run_id={{ orchestrator_job_run_id }}"
  - "--module=ml_etl.projects.tune.tasks.test_task"
  - "--class=TestTask"
  - "--environment={{ environment }}"
  - "--profiler_enabled={{ profiler_enabled }}"
  - "--debug"  # Boolean flag (no value)
  - "--verbose"  # Boolean flag (no value)
```

**Note**: Task-specific parameters take precedence over common configuration parameters.

### Configuration Files

See the `example_config/` directory for complete examples:

- `job_task_examples.yaml`: Mixed task types with dependencies
- `condition_task_example.yaml`: Condition task examples
- `libraries_example.yaml`: Comprehensive library usage examples
- `job_parameters_example.yaml`: Job parameters configuration examples
- `common_config_example.yaml`: Common configuration examples
- `metadata_example.yaml`: Metadata access examples
- `table_locations_example.yaml`: Table location metadata examples
- `generated_component_config.yaml`: Auto-generated component configuration

### Advanced Features

#### Asset Dependencies

Tasks can depend on other tasks through asset dependencies:

```yaml
asset_specs:
  - key: processed_data
    description: "Processed data"
    deps: ["raw_data"]  # This task waits for raw_data asset
```

#### Config Overrides

Override parameters per asset:

```python
from dagster import Config

class MultiNotebookJobConfig(Config):
    asset_configs: Dict[str, NotebookTaskConfig] = {
        "customer_features": NotebookTaskConfig(
            parameters={"feature_version": "v2.0"}
        )
    }
```

#### Job Parameters

Job parameters can be configured for any task type (except run_job_task which uses job_parameters differently):

```yaml
# For notebook tasks, wheel tasks, jar tasks, etc.
- task_key: "my_task"
  notebook_path: "/path/to/notebook"
  job_parameters:
    - name: orchestrator_job_run_id
      default: "{{ run_id }}"
    - name: environment
      default: "{{ env }}"
    - name: profiler_enabled
      default: false
```

**Note**: For `run_job_task` (tasks that invoke existing jobs), the `job_parameters` field is used to pass parameters to the existing job, not to configure the task itself.

#### Common Configuration

Common configuration applies to all tasks in the job and supports command-line style parameters:

```yaml
# Component level configuration
common_config:
  - "--experiment_settings={{ experiment_settings }}"
  - "--catalog_map={{ catalog_map }}"
  - "--log_level={{ log_level }}"
  - "--llm_calls={{ llm_calls }}"
  - "--git_sha={{ git_sha }}"
  - "--output_bucket_name={{ output_bucket_name }}"
  - "--run_id={{ orchestrator_job_run_id }}"
  - "--module=ml_etl.projects.tune.tasks.test_task"
  - "--class=TestTask"
  - "--environment={{ environment }}"
  - "--profiler_enabled={{ profiler_enabled }}"
  - "--debug"  # Boolean flag
  - "--verbose"  # Boolean flag
```

**Features**:
- Supports both `--key=value` and `--key` (boolean flag) formats
- Task-specific parameters override common configuration
- Template variables are supported
- Applies to all task types (notebook, wheel, jar, etc.)

#### Table Location Metadata

The component automatically extracts table and data location information from task parameters:

**Supported Location Patterns**:
- Task parameters: `input_table`, `output_table`, `input_path`, `output_path`, `data_location`, etc.
- Job parameters: Any parameter containing "table", "path", or "location" keywords
- Asset spec: `table_location`, `data_location` fields

**Example table location metadata**:
```python
{
    "input_table": "{{ env }}.raw.customer_data",
    "output_table": "{{ env }}.processed.customer_data",
    "input_path": "/dbfs/data/raw/customers/",
    "output_path": "/dbfs/data/processed/customers/",
    "data_location": "s3://my-bucket/data/",
    "source_table": "{{ env }}.raw.transactions",
    "target_table": "{{ env }}.processed.transactions",
    "job_param_input_table_location": "{{ env }}.raw.customer_data",
    "job_param_output_table_location": "{{ env }}.processed.customer_data",
    "asset_spec_table_location": "{{ env }}.processed.customer_data",
    "asset_spec_data_location": "/dbfs/data/processed/customers/"
}
```

**Use cases**:
- Data lineage tracking
- Data validation and quality checks
- Data catalog management
- Storage cost analysis
- Data governance compliance

#### Comprehensive Metadata

The component provides rich metadata for a Databricks-like experience:

**Asset Spec Metadata** (available at definition time):
- Task configuration (type, path, parameters)
- Compute configuration (serverless, spark version, node type, workers)
- Libraries configuration
- Job parameters
- Common configuration
- Asset configuration (key, description, kinds, dependencies)

**Execution Metadata** (available at runtime):
- Databricks job run ID and URL
- Task-specific URLs and status
- Selected tasks and assets
- Compute configuration
- Common configuration
- Task parameters and overrides
- Asset configuration details

**Example metadata structure**:
```python
{
    "task_key": "feature_engineering",
    "task_type": "notebook",
    "notebook_path": "/Users/workspace_user/ml_pipelines/feature_engineering",
    "compute_config": {
        "serverless": False,
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 2
    },
    "libraries": [
        {"whl": "dbfs:/FileStore/wheels/my_package-1.0.0-py3-none-any.whl"},
        {"pypi": {"package": "pandas", "version": "2.0.0"}}
    ],
    "job_parameters": [
        {"name": "environment", "default": "{{ env }}"},
        {"name": "profiler_enabled", "default": False}
    ],
    "common_config": [
        "--experiment_settings={{ experiment_settings }}",
        "--catalog_map={{ catalog_map }}"
    ],
    "asset_config": {
        "key": "customer_features",
        "description": "Engineered customer features",
        "kinds": ["databricks", "notebook", "features"],
        "skippable": True,
        "deps": ["processed_customer_data"]
    },
    "table_locations": {
        "input_table": "{{ env }}.processed.customer_data",
        "output_table": "{{ env }}.features.customer_features",
        "input_path": "/dbfs/data/processed/",
        "output_path": "/dbfs/data/features/",
        "source_location": "s3://my-bucket/processed/",
        "target_location": "s3://my-bucket/features/",
        "job_param_source_table_location": "{{ env }}.processed.customer_data",
        "job_param_target_table_location": "{{ env }}.features.customer_features",
        "asset_spec_table_location": "{{ env }}.features.customer_features",
        "asset_spec_data_location": "/dbfs/data/features/"
    }
}
```

#### Serverless Mode

For lightweight tasks, use serverless mode:

```yaml
attributes:
  serverless: true
  # No need to specify spark_version, node_type_id, or num_workers
```

### Error Handling

The component includes comprehensive error handling and logging:

- Validates library configurations
- Logs library installation status
- Provides detailed error messages for unsupported library types
- Tracks task dependencies and execution order

### Best Practices

1. **Library Versioning**: Always specify versions for PyPI packages to ensure reproducibility
2. **Custom Wheels**: Store custom wheels in DBFS for reliable access
3. **Maven Dependencies**: Use specific versions and consider exclusions for large dependencies
4. **R Libraries**: Combine R and Python libraries when using rpy2 for interoperability
5. **Asset Organization**: Use descriptive asset keys and organize by domain
6. **Job Parameters**: Use consistent parameter naming and provide meaningful defaults
7. **Parameter Validation**: Validate job parameters in your notebooks/tasks to handle missing values gracefully
8. **Common Configuration**: Use common configuration for shared parameters across all tasks
9. **Configuration Hierarchy**: Understand that task-specific parameters override common configuration
10. **Metadata Access**: Use asset metadata to access task configuration, compute details, and execution information
11. **Table Location Tracking**: Use table location metadata for data lineage, validation, and catalog management

### Troubleshooting

**Common Issues:**

1. **Library not found**: Ensure the library path is correct and accessible
2. **Version conflicts**: Check for conflicting library versions across tasks
3. **Memory issues**: Consider using larger node types for memory-intensive libraries
4. **Network issues**: Verify repository URLs for Maven and CRAN packages

**Debugging:**

Enable detailed logging by setting the log level in your Dagster configuration:

```python
import logging
logging.getLogger("hooli_ml.components.databricks_notebook_component").setLevel(logging.DEBUG)
```

### Contributing

When adding new library types or features:

1. Update the component documentation
2. Add comprehensive examples
3. Include error handling for unsupported configurations
4. Add tests for new functionality 