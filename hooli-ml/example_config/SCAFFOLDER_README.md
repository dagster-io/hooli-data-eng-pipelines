# DatabricksMultiNotebookJobComponent Scaffolder

This directory contains examples and documentation for the updated `DatabricksMultiNotebookJobComponent` scaffolder that now supports all the new features we've added.

## Features Extracted from Databricks Bundle

The scaffolder automatically extracts the following features from Databricks bundle configurations:

### 1. Libraries (Databricks Supported)
- **Automatic Extraction**: Libraries from Databricks tasks are automatically included
- **Supported Types**: 
  - Python wheels (whl)
  - JAR files (jar) 
  - PyPI packages (pypi)
  - Maven packages (maven)
  - CRAN packages (cran)
- **Configuration**: Libraries are preserved as-is from the original Databricks configuration

### 2. Job Parameters (Databricks Supported)
- **Task Configuration**: Job parameters for task configuration (not job invocation) are automatically extracted
- **Format Support**: Both list format `[{name: "param", default: "value"}]` and dict format `{param: "value"}`
- **Template Variables**: Job parameters support template variables like `{{ env }}` and `{{ run_id }}`

### 3. Table Location Metadata (Dagster Enhancement)
- **Automatic Extraction**: Table and data location information is automatically extracted from task parameters
- **Comprehensive Coverage**: Supports input/output tables, paths, and locations
- **Metadata Integration**: Table locations are included in asset metadata for lineage tracking

## Features to Add Manually

### 4. Common Configuration (Dagster-Specific Feature)
- **Manual Addition**: Common configuration should be added manually to the generated component YAML
- **Bundle Variables**: Bundle variables can be used as a reference for creating common configuration
- **Format**: Use `--key=value` format for all tasks
- **Override**: Task-specific parameters take precedence over common configuration

## Example Files

### `sample_databricks_bundle.yml`
A complete Databricks bundle configuration that demonstrates all the new features:

- **Bundle Variables**: Converted to common configuration
- **Multiple Task Types**: Notebook, Python wheel, Spark JAR, run job, and condition tasks
- **Libraries**: Various library types (whl, pypi, maven, cran, jar)
- **Job Parameters**: Both list and dict formats
- **Table Locations**: Comprehensive table and data location parameters

### `resources/jobs.yml`
Detailed job configuration showing:

- **Notebook Tasks**: With libraries, job parameters, and table locations
- **Python Wheel Tasks**: With comprehensive library and parameter configuration
- **Spark JAR Tasks**: With JAR libraries and Spark-specific parameters
- **Run Job Tasks**: With job parameters for existing job invocation
- **Condition Tasks**: With dependency management

## Usage

### Basic Scaffolding
```bash
# Auto-discover databricks.yml in current directory or parents
dg scaffold defs hooli_ml.components.DatabricksMultiNotebookJobComponent my_component
```

### Specify Databricks Config Path
```bash
# Use a specific databricks.yml file
dg scaffold defs hooli_ml.components.DatabricksMultiNotebookJobComponent my_component --databricks_config example_config/sample_databricks_bundle.yml
```

## Generated Output

The scaffolder will generate a component configuration that includes:

### Common Configuration (Add Manually)
```yaml
# Add this section manually to the generated component YAML
common_config:
  - "--experiment_settings={{ experiment_settings }}"
  - "--catalog_map={{ catalog_map }}"
  - "--log_level={{ log_level }}"
  - "--llm_calls={{ llm_calls }}"
  - "--git_sha={{ git_sha }}"
  - "--output_bucket_name={{ output_bucket_name }}"
  - "--orchestrator_job_run_id={{ orchestrator_job_run_id }}"
  - "--environment={{ environment }}"
  - "--profiler_enabled={{ profiler_enabled }}"
```

### Task Configuration with Libraries
```yaml
tasks:
  - task_key: data_processing_notebook
    notebook_path: "/Users/{{ workspace_user }}/ml_pipelines/data_processing"
    parameters:
      input_table: "{{ env }}.raw.customer_data"
      output_table: "{{ env }}.processed.customer_data"
      # ... more parameters
    libraries:
      - whl: "dbfs:/FileStore/wheels/data_processing-1.0.0-py3-none-any.whl"
      - pypi:
          package: "pandas"
          version: "2.0.0"
      - maven:
          coordinates: "org.apache.spark:spark-sql_2.12:3.4.0"
          repo: "https://repo1.maven.org/maven2/"
    job_parameters:
      - name: orchestrator_job_run_id
        default: "{{ run_id }}"
      - name: environment
        default: "{{ env }}"
      # ... more job parameters
```

### Asset Specs with Table Location Metadata
```yaml
asset_specs:
  - key: data_processing_notebook
    description: "data_processing_notebook from ml_pipeline_job job (notebook task)"
    kinds: ["databricks", "notebook"]
    table_location: "{{ env }}.processed.customer_data"
    data_location: "/dbfs/data/processed/customers/"
```

## Key Benefits

1. **Automatic Feature Extraction**: All new features are automatically extracted from Databricks bundle configurations
2. **Comprehensive Metadata**: Table location information is automatically included in asset metadata
3. **Template Variable Support**: All features support Databricks template variables
4. **Dependency Preservation**: Task dependencies are correctly mapped to asset dependencies
5. **Library Management**: All library types are preserved and configured correctly
6. **Parameter Flexibility**: Supports both list and dict formats for job parameters

## Migration Guide

If you have existing Databricks bundle configurations:

1. **No Changes Required**: The scaffolder will automatically extract Databricks-supported features if they exist
2. **Backward Compatible**: Existing configurations without new features will work as before
3. **Gradual Adoption**: You can add libraries, job parameters, and table locations to your existing Databricks configurations
4. **Enhanced Metadata**: Table location metadata will be automatically available for data lineage tracking
5. **Manual Common Config**: Add common configuration manually to the generated component YAML using bundle variables as reference

## Best Practices

1. **Use Bundle Variables**: Define common configuration in bundle variables for automatic conversion
2. **Include Table Locations**: Add table and data location parameters for comprehensive metadata
3. **Library Organization**: Use appropriate library types for your dependencies
4. **Parameter Naming**: Use descriptive parameter names that include location information
5. **Template Variables**: Leverage Databricks template variables for environment-specific configuration 