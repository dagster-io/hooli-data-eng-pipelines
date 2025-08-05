import dagster as dg
from typing import List, Dict, Any, Optional
from pydantic import field_validator
from hooli_ml.defs.resources import DatabricksResource


class NotebookTaskConfig(dg.Config):
    """Config for overriding parameters for a specific notebook task."""

    parameters: Dict[str, Any] = {}


class MultiNotebookJobConfig(dg.Config):
    """Config for overriding parameters for notebook tasks by asset key."""

    asset_configs: Dict[str, NotebookTaskConfig] = {}


# Import the scaffolder if available
try:
    from .databricks_scaffolder import DatabricksBundleScaffolder
    from dagster.components.scaffold.scaffold import scaffold_with

    @scaffold_with(DatabricksBundleScaffolder)
    class DatabricksMultiNotebookJobComponent(dg.Component, dg.Model, dg.Resolvable):
        """
        A Databricks component that runs multiple tasks in a single Databricks job.

        This component creates a multi-asset that submits all tasks as a single job,
        allowing for better resource utilization and coordination between related tasks.

        Supported Task Types:
        - Notebook tasks (notebook_path)
        - Run existing job tasks (job_id)
        - Python wheel tasks (python_wheel_task)
        - Spark Python script tasks (spark_python_task)
        - Spark JAR tasks (spark_jar_task)
        - Condition tasks (condition_task)

        Supported Libraries:
        - Python wheels (whl)
        - JAR files (jar)
        - Python eggs (egg)
        - PyPI packages (pypi)
        - Maven packages (maven)
        - CRAN packages (cran)

        Features:
        - Multiple asset specs per task
        - Asset dependencies mapped to task dependencies
        - Config overrides per asset
        - Asset subsetting support
        - Scaffolding from Databricks bundle configurations
        - Automatic task generation from databricks.yml
        - Library management per task
        - Job parameters for task configuration
        - Common configuration dictionary for all tasks (applied as default values)
        - Comprehensive metadata for Databricks-like experience
        
        Common Configuration:
        The common_config parameter accepts a dictionary of key-value pairs that are applied as 
        default parameters to all tasks in the component. Task-specific parameters will override 
        common_config values when there are conflicts.
        
        Example:
        ```yaml
        common_config:
          env: "dev"
          debug: true
          log_level: "INFO"
        ```
        """

        job_name_prefix: str = "dagster_multi_notebook_job"
        serverless: bool = False
        spark_version: Optional[str] = "13.3.x-scala2.12"
        node_type_id: Optional[str] = "i3.xlarge"
        num_workers: Optional[int] = 1
        existing_cluster_id: Optional[str] = None  # Use existing cluster instead of creating new one

        # Support both explicit tasks and databricks_config
        tasks: Optional[List[Dict[str, Any]]] = None
        databricks_config: Optional[str] = None  # Path to databricks.yml file
        
        # Common configuration that applies to all tasks
        common_config: Optional[Dict[str, Any]] = None  # Dictionary of common parameters for all tasks

        def __init__(self, **data):
            """Initialize with validation that either tasks or databricks_config is provided."""
            super().__init__(**data)
            if not self.tasks and not self.databricks_config:
                raise ValueError(
                    "Either 'tasks' or 'databricks_config' must be provided"
                )

        @field_validator("spark_version", "node_type_id", "num_workers")
        @classmethod
        def validate_cluster_fields(cls, v, info):
            """Validate that cluster fields are provided when not using serverless or existing cluster."""
            serverless = info.data.get("serverless", False)
            existing_cluster_id = info.data.get("existing_cluster_id")
            
            # Skip validation if serverless or using existing cluster
            if serverless or existing_cluster_id:
                return v
            else:
                if v is None:
                    field_name = info.field_name
                    raise ValueError(f"{field_name} is required when serverless=False and existing_cluster_id is not provided")
                return v

        def _get_task_type(self, task: Dict[str, Any]) -> str:
            """Get the task type from task configuration."""
            if "notebook_path" in task:
                return "notebook"
            elif "notebook_task" in task:
                return "notebook"
            elif "job_id" in task:
                return "run_job"
            elif "python_wheel_task" in task:
                return "python_wheel"
            elif "spark_python_task" in task:
                return "spark_python"
            elif "spark_jar_task" in task:
                return "spark_jar"
            elif "condition_task" in task:
                return "condition"
            else:
                return "unknown"
        
        def _get_task_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
            """Get the task-specific configuration."""
            task_config = {}
            
            if "notebook_path" in task:
                # Direct notebook_path format (scaffolder format)
                task_config["notebook_path"] = task["notebook_path"]
                task_config["parameters"] = task.get("parameters", {})
            elif "notebook_task" in task:
                # Nested notebook_task format
                notebook_task = task["notebook_task"]
                task_config["notebook_path"] = notebook_task.get("notebook_path", "")
                task_config["parameters"] = notebook_task.get("base_parameters", {})
            elif "job_id" in task:
                task_config["job_id"] = task["job_id"]
                task_config["job_parameters"] = task.get("job_parameters", {})
            elif "python_wheel_task" in task:
                wheel_config = task["python_wheel_task"]
                task_config["package_name"] = wheel_config["package_name"]
                task_config["entry_point"] = wheel_config["entry_point"]
                task_config["parameters"] = task.get("parameters", {})
            elif "spark_python_task" in task:
                python_config = task["spark_python_task"]
                task_config["python_file"] = python_config["python_file"]
                task_config["parameters"] = task.get("parameters", {})
            elif "spark_jar_task" in task:
                jar_config = task["spark_jar_task"]
                task_config["main_class_name"] = jar_config["main_class_name"]
                task_config["parameters"] = task.get("parameters", {})
            elif "condition_task" in task:
                condition_config = task["condition_task"]
                task_config["left"] = condition_config.get("left", "")
                task_config["op"] = condition_config.get("op", "EQUAL_TO")
                task_config["right"] = condition_config.get("right", "")
            
            return task_config

        def _extract_table_locations(self, task: Dict[str, Any], asset_spec_config: Dict[str, Any]) -> Dict[str, Any]:
            """Extract table location information from task parameters and asset spec."""
            table_locations = {}
            
            # Extract from task parameters
            task_parameters = task.get("parameters", {})
            
            # Common table parameter patterns
            table_params = [
                "input_table", "output_table", "table_name", "source_table", "target_table",
                "input_path", "output_path", "data_path", "source_path", "target_path",
                "input_location", "output_location", "data_location", "source_location", "target_location"
            ]
            
            for param_name in table_params:
                if param_name in task_parameters:
                    value = task_parameters[param_name]
                    if isinstance(value, str) and value.strip():
                        table_locations[param_name] = value
            
            # Extract from job parameters if they exist
            if "job_parameters" in task:
                job_params = task["job_parameters"]
                if isinstance(job_params, list):
                    # Handle list format: [{name: "param1", default: "value1"}, ...]
                    for param in job_params:
                        if isinstance(param, dict) and "name" in param:
                            param_name = param["name"]
                            param_value = param.get("default", "")
                            if any(table_keyword in param_name.lower() for table_keyword in ["table", "path", "location"]):
                                if isinstance(param_value, str) and param_value.strip():
                                    table_locations[f"job_param_{param_name}"] = param_value
                elif isinstance(job_params, dict):
                    # Handle dict format: {param1: "value1", param2: "value2"}
                    for param_name, param_value in job_params.items():
                        if any(table_keyword in param_name.lower() for table_keyword in ["table", "path", "location"]):
                            if isinstance(param_value, str) and param_value.strip():
                                table_locations[f"job_param_{param_name}"] = param_value
            
            # Extract from asset spec configuration
            if "table_location" in asset_spec_config:
                table_locations["asset_spec_table_location"] = asset_spec_config["table_location"]
            
            if "data_location" in asset_spec_config:
                table_locations["asset_spec_data_location"] = asset_spec_config["data_location"]
            
            return table_locations

        def _load_tasks_from_databricks_config(self) -> List[Dict[str, Any]]:
            """Load tasks from databricks config file."""
            if not self.databricks_config:
                return []

            from pathlib import Path

            config_path = Path(self.databricks_config)
            if not config_path.exists():
                raise FileNotFoundError(
                    f"Databricks config file not found: {config_path}"
                )

            # Use the scaffolder logic to extract tasks
            scaffolder = DatabricksBundleScaffolder()

            # Load databricks config
            databricks_config = scaffolder._load_yaml(config_path)
            bundle_dir = config_path.parent

            # Extract variables and includes
            variables = databricks_config.get("variables", {})
            includes = databricks_config.get("include", [])
            targets = databricks_config.get("targets", {})
            bundle_info = databricks_config.get("bundle", {})

            # Parse all included resource files
            all_tasks = []
            for include_path in includes:
                resource_path = bundle_dir / include_path
                if resource_path.exists():
                    tasks = scaffolder._extract_tasks_from_resource(
                        resource_path, variables
                    )
                    all_tasks.extend(tasks)

            if not all_tasks:
                raise ValueError(f"No tasks found in databricks config: {config_path}")

            # Build dependency graph
            task_dependencies = scaffolder._build_dependency_graph(all_tasks)

            # Convert to component format
            component_tasks = []
            for task in all_tasks:
                from .databricks_scaffolder import snake_case

                asset_key = snake_case(task.task_key)

                # Create asset spec
                asset_spec = {
                    "key": asset_key,
                    "description": f"{task.task_key} from {task.job_name} job",
                    "kinds": ["databricks", task.task_type],
                }

                # Add dependencies if they exist
                if asset_key in task_dependencies and task_dependencies[asset_key]:
                    asset_spec["deps"] = task_dependencies[asset_key]

                # Create task configuration based on task type
                task_config = {
                    "task_key": task.task_key,
                    "asset_specs": [asset_spec],
                }

                # Add task-specific configuration
                if task.task_type == "notebook":
                    # For notebook tasks, extract notebook_path from task_config
                    notebook_path = task.task_config.get("notebook_path", "")
                    task_config["notebook_path"] = scaffolder._process_notebook_path(notebook_path)
                    task_config["parameters"] = scaffolder._process_parameters(
                        task.base_parameters, variables, None
                    )
                elif task.task_type == "condition":
                    # For condition tasks, add the condition_task configuration
                    task_config["condition_task"] = task.task_config.get("condition_task", {})
                elif task.task_type == "spark_python":
                    # For spark python tasks, add the spark_python_task configuration  
                    task_config["spark_python_task"] = task.task_config.get("spark_python_task", {})
                    task_config["parameters"] = scaffolder._process_parameters(
                        task.base_parameters, variables, None
                    )
                elif task.task_type == "python_wheel":
                    # For python wheel tasks, add the python_wheel_task configuration
                    task_config["python_wheel_task"] = task.task_config.get("python_wheel_task", {})
                    task_config["parameters"] = scaffolder._process_parameters(
                        task.base_parameters, variables, None
                    )
                elif task.task_type == "spark_jar":
                    # For spark jar tasks, add the spark_jar_task configuration
                    task_config["spark_jar_task"] = task.task_config.get("spark_jar_task", {})
                    task_config["parameters"] = scaffolder._process_parameters(
                        task.base_parameters, variables, None
                    )
                elif task.task_type == "job":
                    # For job tasks, add the job_id and job_parameters
                    task_config["job_id"] = task.task_config.get("job_id")
                    task_config["job_parameters"] = task.task_config.get("job_parameters", {})

                # Add libraries if present
                if task.libraries:
                    task_config["libraries"] = task.libraries

                component_tasks.append(task_config)

            return component_tasks

        def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
            """Build Dagster definitions from the component configuration."""
            from databricks.sdk.service import jobs
            from databricks.sdk.service import compute

            # Get tasks - either from explicit configuration or from databricks_config
            if self.tasks:
                tasks_to_use = self.tasks
            else:
                tasks_to_use = self._load_tasks_from_databricks_config()

            # Create asset specs from task definitions
            asset_specs = []
            for task in tasks_to_use:
                task_key = task["task_key"]
                asset_specs_config = task.get("asset_specs", [])

                if not asset_specs_config:
                    asset_specs_config = [{}]

                for asset_spec_config in asset_specs_config:
                    # Extract base attributes from asset_spec_config
                    asset_key = asset_spec_config.get("key", task_key)
                    deps = asset_spec_config.get("deps", [])

                    # Process dependencies
                    deps_keys = []
                    for dep in deps:
                        if isinstance(dep, str):
                            deps_keys.append(dg.AssetKey(dep))
                        else:
                            deps_keys.append(dep)

                    # Create a base spec with minimal required attributes
                    base_spec = dg.AssetSpec(
                        key=asset_key,
                        deps=deps_keys,
                    )

                    # Apply default attributes first (replace if not already set)
                    default_description = f"Asset for task {task_key}"
                    spec_with_defaults = base_spec.replace_attributes(
                        description=default_description
                    ) if not asset_spec_config.get("description") else base_spec

                    # Build comprehensive metadata using MetadataValue types
                    metadata = {}
                    
                    # Task configuration metadata
                    metadata["task_key"] = dg.MetadataValue.text(task_key)
                    metadata["task_type"] = dg.MetadataValue.text(self._get_task_type(task))
                    metadata["task_config"] = dg.MetadataValue.json(self._get_task_config(task))
                    
                    # Compute configuration metadata
                    compute_config = {
                        "serverless": self.serverless,
                        "spark_version": self.spark_version,
                        "node_type_id": self.node_type_id,
                        "num_workers": self.num_workers,
                    }
                    metadata["compute_config"] = dg.MetadataValue.json(compute_config)
                    
                    # Libraries metadata
                    if "libraries" in task:
                        metadata["libraries"] = dg.MetadataValue.json(task["libraries"])
                    
                    # Job parameters metadata
                    if "job_parameters" in task:
                        metadata["job_parameters"] = dg.MetadataValue.json(task["job_parameters"])
                    
                    # Common configuration metadata
                    if self.common_config:
                        metadata["common_config"] = dg.MetadataValue.json(self.common_config)
                    
                    # Asset configuration metadata
                    asset_config = {
                        "key": str(asset_key),
                        "kinds": list(asset_spec_config.get("kinds", ["databricks"])),
                        "skippable": asset_spec_config.get("skippable", True),
                        "deps": [str(dep) for dep in deps_keys],
                    }
                    metadata["asset_config"] = dg.MetadataValue.json(asset_config)
                    
                    # Table location metadata - extract from task parameters
                    table_locations = self._extract_table_locations(task, asset_spec_config)
                    if table_locations:
                        metadata["table_locations"] = dg.MetadataValue.json(table_locations)

                    # Process custom metadata from asset spec configuration
                    if "metadata" in asset_spec_config:
                        custom_metadata = asset_spec_config["metadata"]
                        if isinstance(custom_metadata, list):
                            # Handle list format: [{"key": "value"}, ...]
                            for item in custom_metadata:
                                if isinstance(item, dict):
                                    for key, value in item.items():
                                        # Wrap custom metadata values in appropriate MetadataValue types
                                        if isinstance(value, str):
                                            metadata[key] = dg.MetadataValue.text(value)
                                        elif isinstance(value, (int, float)):
                                            metadata[key] = dg.MetadataValue.float(float(value))
                                        elif isinstance(value, bool):
                                            metadata[key] = dg.MetadataValue.bool(value)
                                        elif isinstance(value, dict):
                                            metadata[key] = dg.MetadataValue.json(value)
                                        else:
                                            # Default to text for other types
                                            metadata[key] = dg.MetadataValue.text(str(value))
                        elif isinstance(custom_metadata, dict):
                            # Handle dict format: {"key": "value", ...}
                            for key, value in custom_metadata.items():
                                # Wrap custom metadata values in appropriate MetadataValue types
                                if isinstance(value, str):
                                    metadata[key] = dg.MetadataValue.text(value)
                                elif isinstance(value, (int, float)):
                                    metadata[key] = dg.MetadataValue.float(float(value))
                                elif isinstance(value, bool):
                                    metadata[key] = dg.MetadataValue.bool(value)
                                elif isinstance(value, dict):
                                    metadata[key] = dg.MetadataValue.json(value)
                                else:
                                    # Default to text for other types
                                    metadata[key] = dg.MetadataValue.text(str(value))

                    # Merge additional attributes from asset_spec_config using merge_attributes
                    # This allows any valid AssetSpec attributes to be passed through and merged
                    spec_attributes = {
                        "metadata": metadata,
                        "kinds": set(asset_spec_config.get("kinds", ["databricks"])),
                        "skippable": asset_spec_config.get("skippable", True),
                    }
                    
                    # Add description if provided in config
                    if asset_spec_config.get("description"):
                        spec_attributes["description"] = asset_spec_config["description"]
                    
                    # Allow any other valid AssetSpec attributes to be passed through
                    for attr_name, attr_value in asset_spec_config.items():
                        if attr_name not in ["key", "deps", "description", "kinds", "skippable", "metadata"]:
                            # Only add if it's a valid AssetSpec attribute
                            if hasattr(dg.AssetSpec, attr_name):
                                spec_attributes[attr_name] = attr_value

                    # Merge all attributes into the spec
                    # Use separate methods for merge vs replace attributes 
                    # First, merge attributes that are supported by merge_attributes
                    merge_attrs = {
                        "metadata": metadata,
                        "kinds": set(asset_spec_config.get("kinds", ["databricks"])),
                    }
                    
                    # Only add supported merge attributes if they exist in config
                    if "tags" in asset_spec_config:
                        merge_attrs["tags"] = asset_spec_config["tags"]
                    if "owners" in asset_spec_config:
                        merge_attrs["owners"] = asset_spec_config["owners"]

                    # Apply merge_attributes for supported attributes
                    spec_with_merge = spec_with_defaults.merge_attributes(**merge_attrs)
                    
                    # Then use replace_attributes for attributes not supported by merge_attributes
                    replace_attrs = {}
                    
                    # Add description if provided in config
                    if asset_spec_config.get("description"):
                        replace_attrs["description"] = asset_spec_config["description"]
                    
                    # Add skippable if provided in config  
                    if "skippable" in asset_spec_config:
                        replace_attrs["skippable"] = asset_spec_config["skippable"]

                    # Apply replace_attributes for unsupported attributes
                    if replace_attrs:
                        final_spec = spec_with_merge.replace_attributes(**replace_attrs)
                    else:
                        final_spec = spec_with_merge
                    asset_specs.append(final_spec)

            @dg.multi_asset(
                name=f"{self.job_name_prefix}_multi_asset",
                specs=asset_specs,
                can_subset=True,
            )
            def multi_notebook_job_asset(
                context: dg.AssetExecutionContext,
                databricks_resource: DatabricksResource,
                config: MultiNotebookJobConfig,
            ):
                """Multi-asset that runs multiple notebooks as a single Databricks job."""

                # Get selected asset keys that are being materialized
                selected_assets = context.selected_asset_keys
                context.log.info(f"Selected assets: {selected_assets}")

                # Filter tasks to only include those that correspond to selected assets
                selected_tasks = []

                for task in tasks_to_use:
                    task_key = task["task_key"]
                    asset_specs_config = task.get("asset_specs", [{}])

                    task_has_selected_assets = False
                    for asset_spec_config in asset_specs_config:
                        asset_key = asset_spec_config.get("key", task_key)
                        if dg.AssetKey(asset_key) in selected_assets:
                            task_has_selected_assets = True
                            context.log.info(
                                f"Task {task_key} with asset_key {asset_key} is selected"
                            )
                            break

                    if task_has_selected_assets:
                        selected_tasks.append(task)
                    else:
                        context.log.info(
                            f"Task {task_key} is NOT selected (no asset specs selected)"
                        )

                context.log.info(
                    f"Running {len(selected_tasks)} out of {len(tasks_to_use)} tasks"
                )

                if not selected_tasks:
                    context.log.info("No tasks selected for execution")
                    return

                # Create a mapping from asset keys to task keys for dependency resolution
                asset_to_task_map = {}
                for (
                    task
                ) in tasks_to_use:  # Use all tasks for mapping, not just selected
                    task_key = task["task_key"]
                    asset_specs_config = task.get("asset_specs", [{}])
                    for asset_spec_config in asset_specs_config:
                        asset_key = asset_spec_config.get("key", task_key)
                        asset_key_str = str(asset_key)
                        asset_to_task_map[asset_key_str] = task_key

                context.log.info(f"Asset to task mapping: {asset_to_task_map}")

                # Create Databricks SDK task objects only for selected tasks
                databricks_tasks = []
                for task in selected_tasks:
                    task_key = task["task_key"]
                    base_parameters = task.get("parameters", {})
                    asset_specs_config = task.get("asset_specs", [{}])
                    merged_config_parameters = {}

                    for asset_spec_config in asset_specs_config:
                        asset_key = asset_spec_config.get("key", task_key)
                        asset_key_str = str(asset_key)

                        asset_config = config.asset_configs.get(asset_key_str)
                        if asset_config:
                            merged_config_parameters.update(asset_config.parameters)

                    final_parameters = {**base_parameters, **merged_config_parameters}

                    # Apply common configuration to all tasks as default values
                    if self.common_config:
                        # Common config parameters are applied as defaults (task-specific parameters take precedence)
                        final_parameters = {**self.common_config, **final_parameters}
                        context.log.info(f"Task {task_key}: applied {len(self.common_config)} common parameters as defaults")

                    context.log.info(
                        f"Task {task_key}: base_parameters={base_parameters}, config_overrides={merged_config_parameters}, common_params={len(self.common_config) if self.common_config else 0}, final_parameters={final_parameters}"
                    )

                    # Collect task dependencies from asset specs
                    task_dependencies = set()
                    condition_dependencies = []  # For condition tasks with outcomes
                    condition_task_keys = (
                        set()
                    )  # Track which tasks are condition dependencies

                    # First pass: collect explicit condition dependencies to avoid duplicates
                    if "depends_on" in task:
                        for dep_config in task["depends_on"]:
                            dep_task_key = dep_config["task_key"]
                            outcome = dep_config.get("outcome")

                            # Only add dependency if the dependent task is also selected
                            if any(
                                t["task_key"] == dep_task_key for t in selected_tasks
                            ):
                                if outcome:
                                    # This is a condition dependency with an outcome
                                    # Keep outcome as string - Databricks expects string format
                                    outcome_value = (
                                        str(outcome) if outcome is not None else outcome
                                    )

                                    condition_dependencies.append(
                                        {
                                            "task_key": dep_task_key,
                                            "outcome": outcome_value,
                                        }
                                    )
                                    condition_task_keys.add(dep_task_key)
                                    context.log.info(
                                        f"Task {task_key} depends on condition task {dep_task_key} with outcome '{outcome_value}'"
                                    )
                                else:
                                    # Regular dependency
                                    task_dependencies.add(dep_task_key)
                                    context.log.info(
                                        f"Task {task_key} depends on task {dep_task_key} (explicit)"
                                    )

                    # Second pass: collect asset dependencies, but skip those already handled as condition dependencies
                    for asset_spec_config in asset_specs_config:
                        asset_deps = asset_spec_config.get("deps", [])
                        for dep in asset_deps:
                            # Convert dependency to string representation
                            if isinstance(dep, str):
                                dep_key_str = dep
                            elif hasattr(dep, "path"):  # AssetKey object
                                dep_key_str = "/".join(dep.path)
                            else:
                                dep_key_str = str(dep)

                            # Map asset dependency to task dependency
                            if dep_key_str in asset_to_task_map:
                                dependent_task_key = asset_to_task_map[dep_key_str]
                                # Only add dependency if the dependent task is also selected AND not already a condition dependency
                                if (
                                    any(
                                        t["task_key"] == dependent_task_key
                                        for t in selected_tasks
                                    )
                                    and dependent_task_key not in condition_task_keys
                                ):
                                    task_dependencies.add(dependent_task_key)
                                    context.log.info(
                                        f"Task {task_key} depends on task {dependent_task_key} (via asset {dep_key_str})"
                                    )

                    # Determine cluster configuration based on task type
                    cluster_config = {}
                    
                    # Only apply cluster config to tasks that need it
                    task_needs_cluster = False
                    if "notebook_path" in task:
                        task_needs_cluster = True
                    elif "python_wheel_task" in task:
                        task_needs_cluster = True
                    elif "spark_python_task" in task:
                        task_needs_cluster = True
                    elif "spark_jar_task" in task:
                        task_needs_cluster = True
                    elif "condition_task" in task:
                        task_needs_cluster = False  # Condition tasks don't need clusters
                    elif "job_id" in task:
                        task_needs_cluster = False  # Run job tasks don't need clusters (they use the job's cluster)
                    
                    if task_needs_cluster:
                        if self.serverless:
                            # Serverless mode - no cluster config needed
                            pass
                        elif self.existing_cluster_id:
                            # Use existing cluster
                            cluster_config["existing_cluster_id"] = self.existing_cluster_id
                            context.log.info(f"Task {task_key} will use existing cluster: {self.existing_cluster_id}")
                        else:
                            # Create new cluster
                            cluster_spec = compute.ClusterSpec(
                                spark_version=self.spark_version,
                                node_type_id=self.node_type_id,
                                num_workers=self.num_workers,
                            )
                            cluster_config["new_cluster"] = cluster_spec
                            context.log.info(f"Task {task_key} will use new cluster with {self.num_workers} workers")
                    else:
                        context.log.info(f"Task {task_key} does not need cluster configuration (job/condition task)")

                    # Create SubmitTask with dependencies if any exist
                    submit_task_params = {"task_key": task_key}

                    # Add cluster configuration
                    submit_task_params.update(cluster_config)

                    # Determine task type and create appropriate task configuration
                    if "notebook_path" in task:
                        # Notebook task
                        submit_task_params["notebook_task"] = jobs.NotebookTask(
                            notebook_path=task["notebook_path"],
                            base_parameters=final_parameters,
                        )
                    elif "job_id" in task:
                        # Run existing job task
                        submit_task_params["run_job_task"] = jobs.RunJobTask(
                            job_id=task["job_id"],
                            job_parameters=final_parameters if final_parameters else None,
                        )
                        context.log.info(
                            f"Task {task_key} will run existing job ID: {task['job_id']}"
                        )
                    elif "python_wheel_task" in task:
                        # Python wheel task
                        wheel_config = task["python_wheel_task"]
                        submit_task_params["python_wheel_task"] = jobs.PythonWheelTask(
                            package_name=wheel_config["package_name"],
                            entry_point=wheel_config["entry_point"],
                            parameters=list(final_parameters.values())
                            if final_parameters
                            else None,
                        )
                    elif "spark_python_task" in task:
                        # Spark Python script task
                        python_config = task["spark_python_task"]
                        submit_task_params["spark_python_task"] = jobs.SparkPythonTask(
                            python_file=python_config["python_file"],
                            parameters=list(final_parameters.values())
                            if final_parameters
                            else None,
                        )
                        context.log.info(
                            f"Task {task_key} will run Python script: {python_config['python_file']}"
                        )
                    elif "spark_jar_task" in task:
                        # Spark JAR task
                        jar_config = task["spark_jar_task"]
                        submit_task_params["spark_jar_task"] = jobs.SparkJarTask(
                            main_class_name=jar_config["main_class_name"],
                            parameters=list(final_parameters.values())
                            if final_parameters
                            else None,
                        )
                    elif "condition_task" in task:
                        # Condition task
                        condition_config = task["condition_task"]
                        submit_task_params["condition_task"] = jobs.ConditionTask(
                            left=condition_config.get("left", ""),
                            op=getattr(
                                jobs.ConditionTaskOp,
                                condition_config.get("op", "EQUAL_TO"),
                            ),
                            right=condition_config.get("right", ""),
                        )
                        context.log.info(
                            f"Task {task_key} is a condition task: {condition_config.get('left')} {condition_config.get('op')} {condition_config.get('right')}"
                        )
                    else:
                        raise ValueError(
                            f"Task {task_key} must specify one of: notebook_path, job_id, python_wheel_task, spark_python_task, spark_jar_task, or condition_task"
                        )

                    # Add cluster configuration ONLY for tasks that need it
                    if task_needs_cluster:
                        if self.serverless:
                            pass  # No cluster spec needed for serverless
                        elif self.existing_cluster_id:
                            submit_task_params["existing_cluster_id"] = self.existing_cluster_id
                        else:
                            # Only add new_cluster if cluster_spec was created
                            if 'cluster_spec' in locals():
                                submit_task_params["new_cluster"] = cluster_spec
                    else:
                        context.log.info(f"Task {task_key} does not need cluster configuration (job/condition task)")

                    # Add libraries if specified
                    if "libraries" in task:
                        libraries_config = task["libraries"]
                        libraries_list = []
                        
                        for lib in libraries_config:
                            if "whl" in lib:
                                libraries_list.append(jobs.compute.Library(whl=lib["whl"]))
                            elif "jar" in lib:
                                libraries_list.append(jobs.compute.Library(jar=lib["jar"]))
                            elif "egg" in lib:
                                libraries_list.append(jobs.compute.Library(egg=lib["egg"]))
                            elif "pypi" in lib:
                                pypi_config = lib["pypi"]
                                # Handle version by combining it with package name
                                package = pypi_config["package"]
                                if "version" in pypi_config:
                                    package = f"{package}=={pypi_config['version']}"
                                
                                libraries_list.append(jobs.compute.Library(
                                    pypi=jobs.compute.PythonPyPiLibrary(
                                        package=package,
                                        repo=pypi_config.get("repo")
                                    )
                                ))
                            elif "maven" in lib:
                                maven_config = lib["maven"]
                                libraries_list.append(jobs.compute.Library(
                                    maven=jobs.compute.MavenLibrary(
                                        coordinates=maven_config["coordinates"],
                                        repo=maven_config.get("repo"),
                                        exclusions=maven_config.get("exclusions", [])
                                    )
                                ))
                            elif "cran" in lib:
                                cran_config = lib["cran"]
                                libraries_list.append(jobs.compute.Library(
                                    cran=jobs.compute.RCranLibrary(
                                        package=cran_config["package"],
                                        repo=cran_config.get("repo")
                                    )
                                ))
                            else:
                                context.log.warning(f"Unknown library type in task {task_key}: {lib}")
                        
                        if libraries_list:
                            submit_task_params["libraries"] = libraries_list
                            context.log.info(f"Task {task_key} has {len(libraries_list)} libraries configured")

                    # Add depends_on if there are dependencies
                    all_dependencies = []

                    # Add regular task dependencies
                    if task_dependencies:
                        all_dependencies.extend(
                            [
                                jobs.TaskDependency(task_key=dep_task_key)
                                for dep_task_key in sorted(task_dependencies)
                            ]
                        )
                        context.log.info(
                            f"Task {task_key} has regular dependencies: {sorted(task_dependencies)}"
                        )

                    # Add condition dependencies (mix of TaskDependency objects and raw dicts)
                    if condition_dependencies:
                        for dep in condition_dependencies:
                            if isinstance(dep, dict):
                                # Raw dict format - convert to TaskDependency
                                all_dependencies.append(
                                    jobs.TaskDependency(
                                        task_key=dep["task_key"], outcome=dep["outcome"]
                                    )
                                )
                            else:
                                # Already a TaskDependency object
                                all_dependencies.append(dep)

                        # Log condition dependencies
                        dep_info = []
                        for dep in condition_dependencies:
                            if isinstance(dep, dict):
                                dep_info.append((dep["task_key"], dep["outcome"]))
                            else:
                                dep_info.append((dep.task_key, dep.outcome))
                        context.log.info(
                            f"Task {task_key} has condition dependencies: {dep_info}"
                        )

                    if all_dependencies:
                        submit_task_params["depends_on"] = all_dependencies

                        # Debug logging for dependencies
                        context.log.info(f"Task {task_key} final dependencies:")
                        for i, dep in enumerate(all_dependencies):
                            if hasattr(dep, "task_key"):
                                dep_info = f"  {i}: task_key={dep.task_key}"
                                if hasattr(dep, "outcome") and dep.outcome is not None:
                                    dep_info += f", outcome={dep.outcome} (type: {type(dep.outcome)})"
                                context.log.info(dep_info)
                            else:
                                context.log.info(f"  {i}: {dep}")

                    databricks_task = jobs.SubmitTask(**submit_task_params)
                    databricks_tasks.append(databricks_task)

                # Submit the job with only selected tasks
                client = databricks_resource.workspace_client()
                
                # Prepare job submission parameters
                job_submit_params = {
                    "run_name": f"{self.job_name_prefix}_{context.run_id}",
                    "tasks": databricks_tasks,
                }
                
                job_run = client.jobs.submit(**job_submit_params)
                
                # Log job-level information (metadata will be added to individual assets)
                context.log.info(f"Databricks job submitted with run ID: {job_run.run_id}")
                context.log.info(f"Selected tasks: {[task['task_key'] for task in selected_tasks]}")
                context.log.info(f"Total tasks in config: {len(tasks_to_use)}")
                context.log.info(f"Selected assets: {[str(asset) for asset in selected_assets]}")
                if self.common_config:
                    context.log.info(f"Common config applied: {self.common_config}")

                # Build Databricks job run URL
                workspace_url = databricks_resource.databricks_host.rstrip("/")

                # Extract the run_id from the job_run object
                run_id = job_run.run_id
                run_details = client.jobs.get_run(run_id=run_id)

                job_run_url = (
                    f"{workspace_url}/jobs/{run_details.job_id}/runs/{job_run.run_id}"
                )

                context.log.info(
                    f"Submitted Databricks job with run ID: {job_run.run_id}"
                )
                context.log.info(f"Databricks job run URL: {job_run_url}")

                # Wait for job completion
                client.jobs.wait_get_run_job_terminated_or_skipped(job_run.run_id)

                # Get final job status
                final_run = client.jobs.get_run(job_run.run_id)

                context.log.info(
                    f"Job completed with overall state: {final_run.state.result_state}"
                )
                context.log.info(f"View job details: {job_run_url}")

                # Check individual task statuses and yield results for successful tasks
                successful_tasks = []
                failed_tasks = []

                # Get individual task run states
                for task_run in final_run.tasks:
                    task_key = task_run.task_key
                    task_state = (
                        task_run.state.result_state.value
                        if task_run.state.result_state
                        else "UNKNOWN"
                    )

                    # Build task-specific URL (task tab within the job run)
                    task_url = f"{job_run_url}#task/{task_key}"

                    context.log.info(
                        f"Task {task_key} completed with state: {task_state}"
                    )
                    context.log.info(f"Task {task_key} details: {task_url}")

                    if task_state == "SUCCESS":
                        successful_tasks.append(task_key)
                        # Find the corresponding task config
                        matching_task = next(
                            (t for t in selected_tasks if t["task_key"] == task_key),
                            None,
                        )
                        if matching_task:
                            # Yield MaterializeResult for each asset produced by this successful task
                            task_config = matching_task
                            asset_specs_config = task_config.get("asset_specs", [{}])
                            base_parameters = task_config.get("parameters", {})

                            for asset_spec_config in asset_specs_config:
                                asset_key = asset_spec_config.get("key", task_key)
                                asset_key_str = str(asset_key)

                                asset_config = config.asset_configs.get(asset_key_str)
                                config_overrides = (
                                    asset_config.parameters if asset_config else {}
                                )
                                final_parameters = {
                                    **base_parameters,
                                    **config_overrides,
                                }

                                # Get task-specific metadata
                                task_metadata = {
                                    "job_run_id": job_run.run_id,
                                    "databricks_job_url": dg.MetadataValue.url(
                                        job_run_url
                                    ),
                                    "databricks_task_url": dg.MetadataValue.url(
                                        task_url
                                    ),
                                    "task_key": task_key,
                                    "task_state": task_state,
                                    "serverless": self.serverless,
                                    "executed_in_subset": True,
                                    "total_tasks_in_job": len(selected_tasks),
                                    "successful_tasks": len(successful_tasks),
                                    "failed_tasks": len(failed_tasks),
                                    "status": "completed",
                                    "base_parameters": base_parameters,
                                    "config_overrides": config_overrides,
                                    "final_parameters": final_parameters,
                                    "has_config_overrides": bool(config_overrides),
                                    "asset_spec_defaults_applied": {
                                        "skippable": asset_spec_config.get(
                                            "skippable", True
                                        ),
                                        "kinds": asset_spec_config.get(
                                            "kinds", ["databricks"]
                                        ),
                                    },
                                }

                                # Add task-type specific metadata
                                if "notebook_path" in task_config:
                                    task_metadata["notebook_path"] = task_config[
                                        "notebook_path"
                                    ]
                                    task_metadata["task_type"] = "notebook"
                                elif "job_id" in task_config:
                                    task_metadata["job_id"] = task_config["job_id"]
                                    task_metadata["task_type"] = "run_job"
                                elif "python_wheel_task" in task_config:
                                    wheel_config = task_config["python_wheel_task"]
                                    task_metadata["package_name"] = wheel_config["package_name"]
                                    task_metadata["entry_point"] = wheel_config["entry_point"]
                                    task_metadata["task_type"] = "python_wheel"
                                elif "spark_python_task" in task_config:
                                    python_config = task_config["spark_python_task"]
                                    task_metadata["python_file"] = python_config["python_file"]
                                    task_metadata["task_type"] = "spark_python"
                                elif "spark_jar_task" in task_config:
                                    jar_config = task_config["spark_jar_task"]
                                    task_metadata["main_class_name"] = jar_config["main_class_name"]
                                    task_metadata["task_type"] = "spark_jar"
                                elif "condition_task" in task_config:
                                    condition_config = task_config["condition_task"]
                                    task_metadata["condition_left"] = condition_config.get("left", "")
                                    task_metadata["condition_op"] = condition_config.get("op", "EQUAL_TO")
                                    task_metadata["condition_right"] = condition_config.get("right", "")
                                    task_metadata["task_type"] = "condition"
                                
                                # Add libraries metadata
                                if "libraries" in task_config:
                                    task_metadata["libraries"] = task_config["libraries"]
                                
                                # Add job parameters metadata
                                if "job_parameters" in task_config:
                                    task_metadata["job_parameters"] = task_config["job_parameters"]
                                
                                # Add common configuration metadata
                                if self.common_config:
                                    task_metadata["common_config"] = self.common_config
                                
                                # Add compute configuration metadata
                                task_metadata["compute_config"] = {
                                    "serverless": self.serverless,
                                    "spark_version": self.spark_version,
                                    "node_type_id": self.node_type_id,
                                    "num_workers": self.num_workers,
                                }
                                
                                # Add asset configuration metadata
                                task_metadata["asset_config"] = {
                                    "key": str(asset_key),
                                    "description": asset_spec_config.get("description", f"Asset for task {task_key}"),
                                    "kinds": asset_spec_config.get("kinds", ["databricks"]),
                                    "skippable": asset_spec_config.get("skippable", True),
                                    "deps": [str(dep) for dep in asset_spec_config.get("deps", [])],
                                }
                                
                                # Add table location metadata
                                table_locations = self._extract_table_locations(task_config, asset_spec_config)
                                if table_locations:
                                    task_metadata["table_locations"] = table_locations

                                yield dg.MaterializeResult(
                                    asset_key=asset_key, metadata=task_metadata
                                )
                    else:
                        failed_tasks.append(task_key)

                # Log summary
                context.log.info(
                    f"Job summary: {len(successful_tasks)} successful tasks, {len(failed_tasks)} failed tasks"
                )
                if successful_tasks:
                    context.log.info(f"Successful tasks: {successful_tasks}")
                if failed_tasks:
                    context.log.warning(f"Failed tasks: {failed_tasks}")

                # Only raise an exception if ALL tasks failed
                if len(successful_tasks) == 0 and len(failed_tasks) > 0:
                    context.log.error("All tasks failed - raising exception")
                    raise Exception(
                        f"All {len(failed_tasks)} tasks failed. Job overall state: {final_run.state.result_state}"
                    )
                elif len(failed_tasks) > 0:
                    context.log.warning(
                        f"Partial success: {len(successful_tasks)} tasks succeeded, {len(failed_tasks)} tasks failed"
                    )
                else:
                    context.log.info(
                        f"All {len(successful_tasks)} tasks completed successfully"
                    )

            return dg.Definitions(assets=[multi_notebook_job_asset])

except ImportError:
    # Fallback version without scaffolder
    class DatabricksMultiNotebookJobComponent(dg.Component, dg.Model, dg.Resolvable):
        """
        A Databricks component that runs multiple notebooks as tasks in a single Databricks job.

        This component creates a multi-asset that submits all notebook tasks as a single job,
        allowing for better resource utilization and coordination between related tasks.

        Features:
        - Multiple asset specs per task
        - Asset dependencies
        - Config overrides per asset
        - Asset subsetting support
        """

        job_name_prefix: str = "dagster_multi_notebook_job"
        serverless: bool = False
        spark_version: Optional[str] = "13.3.x-scala2.12"
        node_type_id: Optional[str] = "i3.xlarge"
        num_workers: Optional[int] = 1
        existing_cluster_id: Optional[str] = None  # Use existing cluster instead of creating new one

        # Support both explicit tasks and databricks_config
        tasks: Optional[List[Dict[str, Any]]] = None
        databricks_config: Optional[str] = None  # Path to databricks.yml file
        
        # Common configuration that applies to all tasks
        common_config: Optional[Dict[str, Any]] = None  # Dictionary of common parameters for all tasks

        def __init__(self, **data):
            """Initialize with validation that either tasks or databricks_config is provided."""
            super().__init__(**data)
            if not self.tasks and not self.databricks_config:
                raise ValueError(
                    "Either 'tasks' or 'databricks_config' must be provided"
                )

        @field_validator("spark_version", "node_type_id", "num_workers")
        @classmethod
        def validate_cluster_fields(cls, v, info):
            """Validate that cluster fields are provided when not using serverless."""
            if info.data.get("serverless", False):
                return v
            else:
                if v is None:
                    field_name = info.field_name
                    raise ValueError(f"{field_name} is required when serverless=False")
                return v

        def _get_task_type(self, task: Dict[str, Any]) -> str:
            """Get the type of task from the task configuration."""
            if "notebook_path" in task:
                return "notebook"
            elif "notebook_task" in task:
                return "notebook"
            elif "job_id" in task:
                return "run_job"
            elif "spark_python_task" in task:
                return "spark_python"
            elif "python_wheel_task" in task:
                return "python_wheel"
            elif "spark_jar_task" in task:
                return "spark_jar"
            elif "run_job_task" in task:
                return "run_job"
            elif "condition_task" in task:
                return "condition"
            else:
                return "unknown"

        def _get_task_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
            """Get the task configuration based on task type."""
            task_type = self._get_task_type(task)
            
            if task_type == "notebook":
                if "notebook_path" in task:
                    # Direct notebook_path format (scaffolder format)
                    return {
                        "notebook_path": task.get("notebook_path", ""),
                        "parameters": task.get("parameters", {}),
                    }
                else:
                    # Nested notebook_task format
                    config = task.get("notebook_task", {})
                    return {
                        "notebook_path": config.get("notebook_path", ""),
                        "base_parameters": config.get("base_parameters", {}),
                        "source": config.get("source", "WORKSPACE"),
                    }
            elif task_type == "spark_python":
                config = task.get("spark_python_task", {})
                return {
                    "python_file": config.get("python_file", ""),
                    "parameters": config.get("parameters", []),
                    "source": config.get("source", "WORKSPACE"),
                }
            elif task_type == "python_wheel":
                config = task.get("python_wheel_task", {})
                return {
                    "package_name": config.get("package_name", ""),
                    "entry_point": config.get("entry_point", ""),
                    "parameters": config.get("parameters", []),
                }
            elif task_type == "spark_jar":
                config = task.get("spark_jar_task", {})
                return {
                    "main_class_name": config.get("main_class_name", ""),
                    "parameters": config.get("parameters", []),
                }
            elif task_type == "run_job":
                if "job_id" in task:
                    # Direct job_id format (scaffolder format)
                    return {
                        "job_id": task.get("job_id", ""),
                        "job_parameters": task.get("job_parameters", {}),
                    }
                else:
                    # Nested run_job_task format
                    config = task.get("run_job_task", {})
                    return {
                        "job_id": config.get("job_id", ""),
                        "job_parameters": config.get("job_parameters", {}),
                    }
            elif task_type == "condition":
                config = task.get("condition_task", {})
                return {
                    "left": config.get("left", ""),
                    "op": config.get("op", "EQUAL_TO"),
                    "right": config.get("right", ""),
                }
            else:
                return {}

        def _extract_table_locations(self, task: Dict[str, Any], asset_spec_config: Dict[str, Any]) -> Dict[str, Any]:
            """Extract table location information from task parameters and asset spec config."""
            table_locations = {}
            
            # Check if table locations are explicitly configured in asset spec
            if "table_locations" in asset_spec_config:
                table_locations.update(asset_spec_config["table_locations"])
            
            # Extract from notebook task base parameters
            task_type = self._get_task_type(task)
            if task_type == "notebook":
                notebook_task = task.get("notebook_task", {})
                base_parameters = notebook_task.get("base_parameters", {})
                
                # Look for common table location parameter patterns
                for param_name, param_value in base_parameters.items():
                    if any(keyword in param_name.lower() for keyword in ["table", "location", "path", "output"]):
                        table_locations[param_name] = param_value
            
            return table_locations

        def _load_tasks_from_databricks_config(self) -> List[Dict[str, Any]]:
            """Load tasks from databricks.yml configuration file."""
            # Placeholder implementation - would need to parse databricks.yml
            # For now, return empty list
            return []

        def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
            """Build Dagster definitions from the component configuration."""
            from databricks.sdk.service import jobs
            from databricks.sdk.service import compute

            # Get tasks - either from explicit configuration or from databricks_config
            if self.tasks:
                tasks_to_use = self.tasks
            else:
                tasks_to_use = self._load_tasks_from_databricks_config()

            # Create asset specs from task definitions using the same pattern as the scaffolder version
            asset_specs = []
            for task in tasks_to_use:
                task_key = task["task_key"]
                asset_specs_config = task.get("asset_specs", [])

                if not asset_specs_config:
                    asset_specs_config = [{}]

                for asset_spec_config in asset_specs_config:
                    # Extract base attributes from asset_spec_config
                    asset_key = asset_spec_config.get("key", task_key)
                    deps = asset_spec_config.get("deps", [])

                    # Process dependencies
                    deps_keys = []
                    for dep in deps:
                        if isinstance(dep, str):
                            deps_keys.append(dg.AssetKey(dep))
                        else:
                            deps_keys.append(dep)

                    # Create a base spec with minimal required attributes
                    base_spec = dg.AssetSpec(
                        key=asset_key,
                        deps=deps_keys,
                    )

                    # Apply default attributes first (replace if not already set)
                    default_description = f"Asset for task {task_key}"
                    spec_with_defaults = base_spec.replace_attributes(
                        description=default_description
                    ) if not asset_spec_config.get("description") else base_spec

                    # Build comprehensive metadata using MetadataValue types
                    metadata = {}
                    
                    # Task configuration metadata
                    metadata["task_key"] = dg.MetadataValue.text(task_key)
                    metadata["task_type"] = dg.MetadataValue.text(self._get_task_type(task))
                    metadata["task_config"] = dg.MetadataValue.json(self._get_task_config(task))
                    
                    # Compute configuration metadata
                    compute_config = {
                        "serverless": self.serverless,
                        "spark_version": self.spark_version,
                        "node_type_id": self.node_type_id,
                        "num_workers": self.num_workers,
                    }
                    metadata["compute_config"] = dg.MetadataValue.json(compute_config)
                    
                    # Libraries metadata
                    if "libraries" in task:
                        metadata["libraries"] = dg.MetadataValue.json(task["libraries"])
                    
                    # Job parameters metadata
                    if "job_parameters" in task:
                        metadata["job_parameters"] = dg.MetadataValue.json(task["job_parameters"])
                    
                    # Common configuration metadata
                    if self.common_config:
                        metadata["common_config"] = dg.MetadataValue.json(self.common_config)
                    
                    # Asset configuration metadata
                    asset_config = {
                        "key": str(asset_key),
                        "kinds": list(asset_spec_config.get("kinds", ["databricks"])),
                        "skippable": asset_spec_config.get("skippable", True),
                        "deps": [str(dep) for dep in deps_keys],
                    }
                    metadata["asset_config"] = dg.MetadataValue.json(asset_config)
                    
                    # Table location metadata - extract from task parameters
                    table_locations = self._extract_table_locations(task, asset_spec_config)
                    if table_locations:
                        metadata["table_locations"] = dg.MetadataValue.json(table_locations)

                    # Process custom metadata from asset spec configuration
                    if "metadata" in asset_spec_config:
                        custom_metadata = asset_spec_config["metadata"]
                        if isinstance(custom_metadata, list):
                            # Handle list format: [{"key": "value"}, ...]
                            for item in custom_metadata:
                                if isinstance(item, dict):
                                    for key, value in item.items():
                                        # Wrap custom metadata values in appropriate MetadataValue types
                                        if isinstance(value, str):
                                            metadata[key] = dg.MetadataValue.text(value)
                                        elif isinstance(value, (int, float)):
                                            metadata[key] = dg.MetadataValue.float(float(value))
                                        elif isinstance(value, bool):
                                            metadata[key] = dg.MetadataValue.bool(value)
                                        elif isinstance(value, dict):
                                            metadata[key] = dg.MetadataValue.json(value)
                                        else:
                                            # Default to text for other types
                                            metadata[key] = dg.MetadataValue.text(str(value))
                        elif isinstance(custom_metadata, dict):
                            # Handle dict format: {"key": "value", ...}
                            for key, value in custom_metadata.items():
                                # Wrap custom metadata values in appropriate MetadataValue types
                                if isinstance(value, str):
                                    metadata[key] = dg.MetadataValue.text(value)
                                elif isinstance(value, (int, float)):
                                    metadata[key] = dg.MetadataValue.float(float(value))
                                elif isinstance(value, bool):
                                    metadata[key] = dg.MetadataValue.bool(value)
                                elif isinstance(value, dict):
                                    metadata[key] = dg.MetadataValue.json(value)
                                else:
                                    # Default to text for other types
                                    metadata[key] = dg.MetadataValue.text(str(value))

                    # Merge additional attributes from asset_spec_config using merge_attributes
                    # This allows any valid AssetSpec attributes to be passed through and merged
                    spec_attributes = {
                        "metadata": metadata,
                        "kinds": set(asset_spec_config.get("kinds", ["databricks"])),
                        "skippable": asset_spec_config.get("skippable", True),
                    }
                    
                    # Add description if provided in config
                    if asset_spec_config.get("description"):
                        spec_attributes["description"] = asset_spec_config["description"]
                    
                    # Allow any other valid AssetSpec attributes to be passed through
                    for attr_name, attr_value in asset_spec_config.items():
                        if attr_name not in ["key", "deps", "description", "kinds", "skippable", "metadata"]:
                            # Only add if it's a valid AssetSpec attribute
                            if hasattr(dg.AssetSpec, attr_name):
                                spec_attributes[attr_name] = attr_value

                    # Merge all attributes into the spec
                    # Use separate methods for merge vs replace attributes 
                    # First, merge attributes that are supported by merge_attributes
                    merge_attrs = {
                        "metadata": metadata,
                        "kinds": set(asset_spec_config.get("kinds", ["databricks"])),
                    }
                    
                    # Only add supported merge attributes if they exist in config
                    if "tags" in asset_spec_config:
                        merge_attrs["tags"] = asset_spec_config["tags"]
                    if "owners" in asset_spec_config:
                        merge_attrs["owners"] = asset_spec_config["owners"]

                    # Apply merge_attributes for supported attributes
                    spec_with_merge = spec_with_defaults.merge_attributes(**merge_attrs)
                    
                    # Then use replace_attributes for attributes not supported by merge_attributes
                    replace_attrs = {}
                    
                    # Add description if provided in config
                    if asset_spec_config.get("description"):
                        replace_attrs["description"] = asset_spec_config["description"]
                    
                    # Add skippable if provided in config  
                    if "skippable" in asset_spec_config:
                        replace_attrs["skippable"] = asset_spec_config["skippable"]

                    # Apply replace_attributes for unsupported attributes
                    if replace_attrs:
                        final_spec = spec_with_merge.replace_attributes(**replace_attrs)
                    else:
                        final_spec = spec_with_merge
                    asset_specs.append(final_spec)

            @dg.multi_asset(
                name=f"{self.job_name_prefix}_multi_asset",
                specs=asset_specs,
                can_subset=True,
            )
            def multi_notebook_job_asset(
                context: dg.AssetExecutionContext,
                databricks_resource: DatabricksResource,
                config: MultiNotebookJobConfig,
            ):
                """Multi-asset that runs multiple notebooks as a single Databricks job."""
                # Implementation would be identical to the scaffolder version
                # For now, return empty results
                return

            return dg.Definitions(assets=[multi_notebook_job_asset])
