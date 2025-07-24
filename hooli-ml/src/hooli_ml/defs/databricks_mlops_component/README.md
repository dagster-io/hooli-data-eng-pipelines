# DatabricksMultiNotebookJobComponent

This component was automatically generated from Databricks bundle configuration.

## Source Configuration
- **Databricks Config**: `databricks_mlops/databricks_mlops/databricks.yml` (absolute path)
- **Generated Tasks**: 6

## Generated Tasks

### batch_inference_job
- **Job**: batch_inference_job
- **Type**: NOTEBOOK
- **Config**: `../deployment/batch_inference/notebooks/BatchInference.py`
- **Asset Key**: `batch_inference_job`
- **Dependencies**: None

### Train
- **Job**: model_training_job
- **Type**: NOTEBOOK
- **Config**: `../training/notebooks/TrainWithFeatureStore.py`
- **Asset Key**: `train`
- **Dependencies**: None

### ModelValidation
- **Job**: model_training_job
- **Type**: NOTEBOOK
- **Config**: `../validation/notebooks/ModelValidation.py`
- **Asset Key**: `model_validation`
- **Dependencies**: Train

### ModelDeployment
- **Job**: model_training_job
- **Type**: NOTEBOOK
- **Config**: `../deployment/model_deployment/notebooks/ModelDeployment.py`
- **Asset Key**: `model_deployment`
- **Dependencies**: ModelValidation

### PickupFeatures
- **Job**: write_feature_table_job
- **Type**: NOTEBOOK
- **Config**: `../feature_engineering/notebooks/GenerateAndWriteFeatures.py`
- **Asset Key**: `pickup_features`
- **Dependencies**: None

### DropoffFeatures
- **Job**: write_feature_table_job
- **Type**: NOTEBOOK
- **Config**: `../feature_engineering/notebooks/GenerateAndWriteFeatures.py`
- **Asset Key**: `dropoff_features`
- **Dependencies**: None


## Usage

### Basic Scaffolding (Auto-discovery)
```bash
dg scaffold defs hooli_ml.components.DatabricksMultiNotebookJobComponent my_component
```

### Specify Databricks Config Path
```bash
dg scaffold defs hooli_ml.components.DatabricksMultiNotebookJobComponent my_component --databricks_config /path/to/databricks.yml
```

### Customization Steps
1. Update the notebook paths to match your Databricks workspace structure
2. Modify parameters as needed for your environment
3. Ensure dependencies are correctly mapped
4. Test the component with `dg dev`

## Configuration Options

- **Serverless**: Currently set to `true`. Change to `false` and configure cluster settings if needed.
- **Asset Dependencies**: Review the `deps` field in each asset spec to ensure correct lineage.
- **Parameters**: Update template variables (e.g., `{{ env }}`) to match your setup.

## Command Line Options

- `--databricks_config`: Specify the path to your databricks.yml file
  - If not provided, the scaffolder will search for databricks.yml in the current directory and parent directories
  - Useful when your databricks.yml is in a non-standard location
