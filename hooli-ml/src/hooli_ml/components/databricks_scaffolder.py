"""
Scaffolder for DatabricksMultiNotebookJobComponent that reads Databricks bundle configurations
and generates appropriate YAML structure.

This scaffolder reads a databricks.yml file and its associated resource files to automatically
generate a DatabricksMultiNotebookJobComponent YAML configuration following the schema in defs.yaml.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import dagster as dg
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel, Field


class DatabricksScaffoldParams(BaseModel):
    """Parameters for scaffolding DatabricksMultiNotebookJobComponent from Databricks bundle."""

    databricks_config: Optional[str] = Field(
        default=None,
        description="Path to the databricks.yml file. If not provided, will auto-discover in current directory and parents.",
    )


def snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Remove file extension if present
    name = Path(name).stem
    # Replace special characters and spaces with underscores
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    # Convert CamelCase to snake_case
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower().strip("_")


@dataclass
class DatabricksTask:
    """Represents a Databricks task with its configuration."""

    task_key: str
    task_type: str  # 'notebook', 'job', 'python_wheel', 'spark_jar', 'condition'
    task_config: Dict[
        str, Any
    ]  # The actual task configuration (notebook_path, job_id, etc.)
    base_parameters: Dict[str, Any]
    depends_on: List[str]
    job_name: str
    libraries: Optional[List[Dict[str, Any]]] = None


class DatabricksBundleScaffolder(dg.Scaffolder[DatabricksScaffoldParams]):
    """Scaffolds DatabricksMultiNotebookJobComponent from Databricks bundle configuration."""

    @classmethod
    def get_scaffold_params(cls) -> type[DatabricksScaffoldParams]:
        """Return the parameter model for this scaffolder."""
        return DatabricksScaffoldParams

    def scaffold(self, request: ScaffoldRequest[DatabricksScaffoldParams]) -> None:
        """Generate the component YAML from Databricks bundle configuration."""

        # Check if a specific databricks config path was provided via the parameters
        databricks_config_path = self._get_databricks_config_path(request)

        if not databricks_config_path:
            # Create a basic template if no Databricks config found
            self._create_basic_template(request)
            return

        # Parse Databricks configuration
        databricks_config = self._load_yaml(databricks_config_path)
        bundle_dir = databricks_config_path.parent

        # Extract variables and includes
        variables = databricks_config.get("variables", {})
        includes = databricks_config.get("include", [])
        targets = databricks_config.get("targets", {})
        bundle_info = databricks_config.get("bundle", {})

        # Parse all included resource files
        all_tasks = []
        all_job_level_parameters = {}
        for include_path in includes:
            resource_path = bundle_dir / include_path
            if resource_path.exists():
                tasks, job_level_parameters = self._extract_tasks_from_resource(resource_path, variables)
                all_tasks.extend(tasks)
                all_job_level_parameters.update(job_level_parameters)

        if not all_tasks:
            self._create_basic_template(request)
            return

        # Build dependency graph
        task_dependencies = self._build_dependency_graph(all_tasks)

        # Generate component YAML
        component_config = self._generate_component_config(
            all_tasks, task_dependencies, variables, targets, bundle_info, all_job_level_parameters
        )

        # Scaffold the component
        dg.scaffold_component(request, component_config)

        # Add template_vars_module to the generated YAML
        self._add_template_vars_module_to_yaml(request.target_path)

        # Create template_vars.py file for resolving Databricks variables
        self._create_template_vars(request.target_path, variables, targets)

        # Create additional documentation
        self._create_documentation(
            request.target_path, databricks_config_path, all_tasks
        )

    def _get_databricks_config_path(
        self, request: ScaffoldRequest[DatabricksScaffoldParams]
    ) -> Optional[Path]:
        """Get the databricks config path from request parameters or auto-discovery."""

        # Check if databricks_config was provided as a parameter
        if request.params and request.params.databricks_config:
            config_path = Path(request.params.databricks_config)
            if config_path.exists():
                print(f"Using specified databricks config: {config_path}")
                return config_path
            else:
                print(f"Warning: Specified databricks config not found: {config_path}")

        # Fall back to auto-discovery
        print("No --databricks_config specified, attempting auto-discovery...")
        return self._find_databricks_config(request.target_path)

    def _find_databricks_config(self, start_path: Path) -> Optional[Path]:
        """Find databricks.yml or databricks.yaml file."""
        current_path = Path(start_path)

        # Search up the directory tree
        for _ in range(10):  # Limit search depth
            for filename in ["databricks.yml", "databricks.yaml"]:
                config_path = current_path / filename
                if config_path.exists():
                    return config_path

            parent = current_path.parent
            if parent == current_path:  # Reached root
                break
            current_path = parent

        return None

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file with error handling."""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}")
            return {}

    def _extract_tasks_from_resource(
        self, resource_path: Path, variables: Dict[str, Any]
    ) -> List[DatabricksTask]:
        """Extract Databricks tasks from a resource YAML file."""
        resource_config = self._load_yaml(resource_path)
        tasks = []
        job_level_parameters = {}  # Collect job-level parameters from all jobs

        # Navigate to jobs section
        resources = resource_config.get("resources", {})
        jobs = resources.get("jobs", {})

        for job_name, job_config in jobs.items():
            # Extract job-level parameters for this job
            job_params = self._extract_job_level_parameters(job_config)
            if job_params:
                job_level_parameters[job_name] = job_params
            
            job_tasks = job_config.get("tasks", [])

            for task_config in job_tasks:
                task_key = task_config.get("task_key", "")
                if not task_key:
                    continue

                # Extract dependencies
                depends_on = task_config.get("depends_on", [])
                dependency_keys = []
                if depends_on:
                    for dep in depends_on:
                        if isinstance(dep, dict) and "task_key" in dep:
                            dependency_keys.append(dep["task_key"])
                        elif isinstance(dep, str):
                            dependency_keys.append(dep)

                # Determine task type and extract configuration
                task_type = None
                task_specific_config = {}
                base_parameters = {}

                if "notebook_task" in task_config:
                    task_type = "notebook"
                    notebook_task = task_config["notebook_task"]
                    task_specific_config = {
                        "notebook_path": notebook_task.get("notebook_path", "")
                    }
                    base_parameters = notebook_task.get("base_parameters", {})

                elif "run_job_task" in task_config:
                    task_type = "job"
                    run_job_task = task_config["run_job_task"]
                    task_specific_config = {
                        "job_id": run_job_task.get("job_id"),
                        "job_parameters": run_job_task.get("job_parameters", {}),
                    }
                    # For job tasks, parameters are in job_parameters
                    base_parameters = run_job_task.get("job_parameters", {})

                elif "python_wheel_task" in task_config:
                    task_type = "python_wheel"
                    python_wheel_task = task_config["python_wheel_task"]
                    task_specific_config = {"python_wheel_task": python_wheel_task}
                    # Python wheel tasks use parameters differently
                    base_parameters = python_wheel_task.get("parameters", [])

                elif "spark_jar_task" in task_config:
                    task_type = "spark_jar"
                    spark_jar_task = task_config["spark_jar_task"]
                    task_specific_config = {"spark_jar_task": spark_jar_task}
                    # Spark JAR tasks use parameters differently
                    base_parameters = spark_jar_task.get("parameters", [])

                elif "condition_task" in task_config:
                    task_type = "condition"
                    condition_task = task_config["condition_task"]
                    task_specific_config = {"condition_task": condition_task}
                    # Condition tasks don't have traditional parameters
                    base_parameters = {}

                else:
                    # Skip unknown task types
                    print(f"Warning: Unknown task type for task {task_key}, skipping")
                    continue

                # Extract libraries if present
                libraries = task_config.get("libraries")

                tasks.append(
                    DatabricksTask(
                        task_key=task_key,
                        task_type=task_type,
                        task_config=task_specific_config,
                        base_parameters=base_parameters,
                        depends_on=dependency_keys,
                        job_name=job_name,
                        libraries=libraries,
                    )
                )

        return tasks, job_level_parameters

    def _extract_job_level_parameters(self, job_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract job-level parameters from job configuration."""
        # Job-level parameters can be defined in several ways in Databricks bundle
        job_parameters = None
        
        # Check for job-level parameters in the job configuration
        if "parameters" in job_config:
            job_parameters = job_config["parameters"]
        elif "job_parameters" in job_config:
            job_parameters = job_config["job_parameters"]
        
        return job_parameters

    def _build_dependency_graph(
        self, tasks: List[DatabricksTask]
    ) -> Dict[str, List[str]]:
        """Build dependency graph mapping task keys to their dependencies."""
        # Create mapping from task_key to asset_key (snake_case)
        task_to_asset = {}
        for task in tasks:
            asset_key = snake_case(task.task_key)
            task_to_asset[task.task_key] = asset_key

        # Build dependency graph using asset keys
        dependencies = {}
        for task in tasks:
            asset_key = task_to_asset[task.task_key]
            deps = []
            for dep_task_key in task.depends_on:
                if dep_task_key in task_to_asset:
                    deps.append(task_to_asset[dep_task_key])
            dependencies[asset_key] = deps

        return dependencies

    def _generate_component_config(
        self,
        tasks: List[DatabricksTask],
        dependencies: Dict[str, List[str]],
        variables: Dict[str, Any],
        targets: Dict[str, Any],
        bundle_info: Dict[str, Any],
        job_level_parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate the component configuration dictionary."""

        # Group tasks by job name
        jobs_tasks = {}
        for task in tasks:
            if task.job_name not in jobs_tasks:
                jobs_tasks[task.job_name] = []
            jobs_tasks[task.job_name].append(task)

        # Determine default target (usually 'dev')
        default_target = None
        for target_name, target_config in targets.items():
            if target_config.get("default", False):
                default_target = target_name
                break
        if not default_target and targets:
            default_target = list(targets.keys())[0]

        # Build component tasks
        component_tasks = []

        # Create a mapping from task_key to task_type for dependency lookup
        task_key_to_type = {task.task_key: task.task_type for task in tasks}

        for job_name, job_tasks in jobs_tasks.items():
            for task in job_tasks:
                asset_key = snake_case(task.task_key)

                # Create asset spec with appropriate kinds based on task type
                task_kinds = ["databricks"]
                if task.task_type == "notebook":
                    task_kinds.append("notebook")
                elif task.task_type == "job":
                    task_kinds.append("job")
                elif task.task_type == "python_wheel":
                    task_kinds.extend(["python", "wheel"])
                elif task.task_type == "spark_jar":
                    task_kinds.extend(["spark", "jar"])
                elif task.task_type == "condition":
                    task_kinds.append("condition")

                asset_spec = {
                    "key": asset_key,
                    "description": f"{task.task_key} from {job_name} job ({task.task_type} task)",
                    "kinds": task_kinds,
                }

                # Add dependencies if they exist
                if asset_key in dependencies and dependencies[asset_key]:
                    asset_spec["deps"] = dependencies[asset_key]

                # Create task configuration based on task type
                task_config = {
                    "task_key": task.task_key,  # Keep original task_key, asset key will be snake_case
                    "asset_specs": [asset_spec],
                }

                # Add Databricks-specific depends_on field if this task depends on condition tasks
                databricks_depends_on = []
                for dep_task_key in task.depends_on:
                    if (
                        dep_task_key in task_key_to_type
                        and task_key_to_type[dep_task_key] == "condition"
                    ):
                        # Add depends_on entry for condition task dependency
                        databricks_depends_on.append(
                            {
                                "task_key": dep_task_key,
                                "outcome": "true",  # Use string format as expected by Databricks
                            }
                        )

                if databricks_depends_on:
                    task_config["depends_on"] = databricks_depends_on

                # Add task-specific configuration
                if task.task_type == "notebook":
                    task_config["notebook_path"] = self._process_notebook_path(
                        task.task_config["notebook_path"]
                    )
                    task_config["parameters"] = self._process_parameters(
                        task.base_parameters, variables, default_target
                    )

                elif task.task_type == "job":
                    task_config["job_id"] = self._process_job_id(
                        task.task_config["job_id"]
                    )
                    if task.task_config.get("job_parameters"):
                        task_config["job_parameters"] = self._process_parameters(
                            task.task_config["job_parameters"],
                            variables,
                            default_target,
                        )
                    if task.base_parameters:
                        task_config["parameters"] = self._process_parameters(
                            task.base_parameters, variables, default_target
                        )

                elif task.task_type == "python_wheel":
                    task_config["python_wheel_task"] = task.task_config[
                        "python_wheel_task"
                    ]
                    # Python wheel parameters are handled differently (list format)
                    if isinstance(task.base_parameters, list):
                        task_config["parameters"] = task.base_parameters
                    elif isinstance(task.base_parameters, dict):
                        task_config["parameters"] = self._process_parameters(
                            task.base_parameters, variables, default_target
                        )

                elif task.task_type == "spark_jar":
                    task_config["spark_jar_task"] = task.task_config["spark_jar_task"]
                    # Spark JAR parameters are handled differently (list format)
                    if isinstance(task.base_parameters, list):
                        task_config["parameters"] = task.base_parameters
                    elif isinstance(task.base_parameters, dict):
                        task_config["parameters"] = self._process_parameters(
                            task.base_parameters, variables, default_target
                        )

                elif task.task_type == "condition":
                    condition_config = task.task_config["condition_task"]
                    task_config["condition_task"] = {
                        "op": condition_config.get("op", "EQUAL_TO"),
                        "left": condition_config.get("left", ""),
                        "right": condition_config.get("right", ""),
                    }
                    # Process template variables in condition expressions
                    if isinstance(task_config["condition_task"]["left"], str):
                        task_config["condition_task"]["left"] = (
                            self._process_condition_expression(
                                task_config["condition_task"]["left"],
                                variables,
                                default_target,
                            )
                        )
                    if isinstance(task_config["condition_task"]["right"], str):
                        task_config["condition_task"]["right"] = (
                            self._process_condition_expression(
                                task_config["condition_task"]["right"],
                                variables,
                                default_target,
                            )
                        )

                # Add libraries if present
                if task.libraries:
                    task_config["libraries"] = task.libraries

                component_tasks.append(task_config)

        # Generate job name prefix from bundle name or use default
        bundle_name = bundle_info.get("name", "databricks_mlops")
        job_name_prefix = f"{bundle_name}_pipeline"

        component_config = {
            "job_name_prefix": job_name_prefix,
            "serverless": True,
            "tasks": component_tasks,
        }

        # Add job-level parameters if any were found
        if job_level_parameters:
            # Merge all job-level parameters into a single dict
            # If multiple jobs have parameters, we'll use the first one or merge them
            merged_job_params = {}
            for job_name, job_params in job_level_parameters.items():
                if isinstance(job_params, dict):
                    merged_job_params.update(job_params)
                elif isinstance(job_params, list):
                    # Handle list format job parameters
                    for param in job_params:
                        if isinstance(param, dict) and "name" in param:
                            merged_job_params[param["name"]] = param.get("default", "")
            
            if merged_job_params:
                component_config["job_parameters"] = merged_job_params

        return component_config

    def _process_parameters(
        self,
        parameters: Dict[str, Any],
        variables: Dict[str, Any],
        default_target: Optional[str],
    ) -> Dict[str, Any]:
        """Process parameters, converting Databricks variables to Dagster template syntax."""
        processed = {}

        for key, value in parameters.items():
            if isinstance(value, str):
                # Convert Databricks variable syntax to Dagster template syntax
                processed_value = value

                # Handle specific Databricks bundle variables
                processed_value = re.sub(
                    r"\$\{var\.([^}]+)\}", r"{{ \1 }}", processed_value
                )
                processed_value = re.sub(
                    r"\$\{bundle\.target\}", r"{{ env }}", processed_value
                )
                processed_value = re.sub(
                    r"\$\{bundle\.name\}", r"{{ bundle_name }}", processed_value
                )

                # Handle bundle.git variables - convert dots to underscores for template var names
                processed_value = re.sub(
                    r"\$\{bundle\.git\.origin_url\}",
                    r"{{ bundle_git_origin_url }}",
                    processed_value,
                )
                processed_value = re.sub(
                    r"\$\{bundle\.git\.branch\}",
                    r"{{ bundle_git_branch }}",
                    processed_value,
                )
                processed_value = re.sub(
                    r"\$\{bundle\.git\.commit\}",
                    r"{{ bundle_git_commit }}",
                    processed_value,
                )

                # General fallback for any other bundle variables
                processed_value = re.sub(
                    r"\$\{bundle\.([^}]+)\}", r"{{ bundle_\1 }}", processed_value
                )

                # Preserve job parameter references - these will be processed by the component
                # Don't convert {{job.parameters.param_name}} as it should remain as-is
                # This allows the component to handle job parameter references

                processed[key] = processed_value
            else:
                processed[key] = value

        return processed

    def _process_condition_expression(
        self, expression: str, variables: Dict[str, Any], default_target: Optional[str]
    ) -> str:
        """Process condition expressions, converting Databricks variables to Dagster template syntax."""
        if not isinstance(expression, str):
            return expression

        processed_expression = expression

        # IMPORTANT: Wrap Databricks runtime expressions like {{tasks.*.values.*}} in databricks_task_value
        # These should be evaluated by Databricks at runtime, not by Dagster template system
        databricks_runtime_match = re.search(
            r"\{\{(tasks\.[^}]+)\}\}", processed_expression
        )
        if databricks_runtime_match:
            # Extract the inner expression (without the outer braces)
            inner_expression = databricks_runtime_match.group(1)
            # Wrap it in the databricks_task_value template function
            return f'{{{{ databricks_task_value("{inner_expression}") }}}}'

        # Handle specific Databricks bundle variables (only if not a runtime expression)
        processed_expression = re.sub(
            r"\$\{var\.([^}]+)\}", r"{{ \1 }}", processed_expression
        )
        processed_expression = re.sub(
            r"\$\{bundle\.target\}", r"{{ env }}", processed_expression
        )
        processed_expression = re.sub(
            r"\$\{bundle\.name\}", r"{{ bundle_name }}", processed_expression
        )

        # Handle bundle.git variables - convert dots to underscores for template var names
        processed_expression = re.sub(
            r"\$\{bundle\.git\.origin_url\}",
            r"{{ bundle_git_origin_url }}",
            processed_expression,
        )
        processed_expression = re.sub(
            r"\$\{bundle\.git\.branch\}",
            r"{{ bundle_git_branch }}",
            processed_expression,
        )
        processed_expression = re.sub(
            r"\$\{bundle\.git\.commit\}",
            r"{{ bundle_git_commit }}",
            processed_expression,
        )

        # General fallback for any other bundle variables
        processed_expression = re.sub(
            r"\$\{bundle\.([^}]+)\}", r"{{ bundle_\1 }}", processed_expression
        )

        return processed_expression

    def _process_notebook_path(self, notebook_path: str) -> str:
        """Process notebook path to convert Databricks variables to Dagster template variables."""
        processed_path = notebook_path

        # Remove .py extension if present (Databricks notebooks don't use file extensions)
        if processed_path.endswith(".py"):
            processed_path = processed_path[:-3]

        # Convert Databricks bundle variables to Dagster template variables
        processed_path = re.sub(
            r"\$\{workspace\.current_user\.userName\}",
            "{{ workspace_user }}",
            processed_path,
        )
        processed_path = re.sub(
            r"\$\{bundle\.name\}", "{{ bundle_name }}", processed_path
        )
        processed_path = re.sub(r"\$\{bundle\.target\}", "{{ env }}", processed_path)

        # Handle relative paths
        if notebook_path.startswith("../"):
            # Convert relative path to bundle absolute path with template variables
            relative_path = notebook_path[3:]  # Remove ../
            if relative_path.endswith(".py"):
                relative_path = relative_path[:-3]
            return (
                "/Users/{{ workspace_user }}/.bundle/{{ bundle_name }}/{{ env }}/files/"
                + relative_path
            )
        elif not notebook_path.startswith("/"):
            # If it's a relative path without ../, assume it's from files directory
            clean_path = (
                notebook_path[:-3] if notebook_path.endswith(".py") else notebook_path
            )
            return (
                "/Users/{{ workspace_user }}/.bundle/{{ bundle_name }}/{{ env }}/files/"
                + clean_path
            )
        else:
            # Already an absolute path, process any variables
            return processed_path

    def _process_job_id(self, job_id: str) -> str:
        """Process job_id to replace Databricks bundle resource references with placeholders."""
        if not job_id:
            return job_id

        # Replace any Databricks bundle resource references with placeholder
        # Pattern to match ${resources.jobs.job_name.id} or similar resource references
        resource_pattern = r"\$\{resources\.jobs\.[^}]+\}"

        if re.search(resource_pattern, job_id):
            return "put job id here."

        # If it's not a resource reference, return as-is
        return job_id

    def _create_basic_template(
        self, request: ScaffoldRequest[DatabricksScaffoldParams]
    ) -> None:
        """Create a basic template when no Databricks config is found."""
        basic_config = {
            "job_name_prefix": "databricks_pipeline",
            "serverless": True,
            "job_parameters": {
                "environment": "{{ env }}",
                "orchestrator_job_run_id": "{{ run_id }}",
                "output_bucket_name": "{{ var.output_bucket_name }}",
                "profiler_enabled": False,
                "experiment_settings": "mlflow://databricks",
                "catalog_map": "{{ env }}.catalog",
                "log_level": "INFO",
                "llm_calls": "enabled",
                "git_sha": "{{ git_sha }}",
                "batch_size": 1000,
                "timeout_minutes": 30
            },
            "tasks": [
                {
                    "task_key": "example_task",
                    "notebook_path": "/path/to/your/notebook",
                    "parameters": {
                        "input_table": "{{ env }}.raw.example_data",
                        "output_table": "{{ env }}.processed.example_data",
                        "param1": "value1",
                        "env": "{{ env }}"
                    },
                    "job_parameters": [
                        {
                            "name": "orchestrator_job_run_id",
                            "default": "{{ run_id }}"
                        },
                        {
                            "name": "environment",
                            "default": "{{ env }}"
                        },
                        {
                            "name": "profiler_enabled",
                            "default": False
                        }
                    ],
                    "libraries": [
                        {
                            "whl": "dbfs:/FileStore/wheels/example_package-1.0.0-py3-none-any.whl"
                        },
                        {
                            "pypi": {
                                "package": "pandas",
                                "version": "2.0.0"
                            }
                        }
                    ],
                    "asset_specs": [
                        {
                            "key": "example_asset",
                            "description": "Example Databricks notebook asset with comprehensive metadata",
                            "kinds": ["databricks", "notebook"],
                            "table_location": "{{ env }}.processed.example_data",
                            "data_location": "/dbfs/data/processed/example/"
                        }
                    ],
                }
            ],
        }

        dg.scaffold_component(request, basic_config)

    def _create_documentation(
        self,
        target_path: Path,
        databricks_config_path: Path,
        tasks: List[DatabricksTask],
    ) -> None:
        """Create documentation about the scaffolded component."""

        # Handle relative path safely - if it's not in a subpath, just use the absolute path
        try:
            relative_config_path = databricks_config_path.relative_to(
                target_path.parent
            )
            config_path_display = f"`{relative_config_path}`"
        except ValueError:
            # If not in subpath, use absolute path
            config_path_display = f"`{databricks_config_path}` (absolute path)"

        readme_content = f"""# DatabricksMultiNotebookJobComponent

This component was automatically generated from Databricks bundle configuration.

## Source Configuration
- **Databricks Config**: {config_path_display}
- **Generated Tasks**: {len(tasks)}

## Generated Tasks

"""

        for task in tasks:
            task_type_display = task.task_type.upper().replace("_", " ")
            if task.task_type == "notebook":
                task_path = task.task_config.get("notebook_path", "")
            elif task.task_type == "job":
                task_path = f"Job ID: {task.task_config.get('job_id', 'N/A')}"
            elif task.task_type == "python_wheel":
                wheel_config = task.task_config.get("python_wheel_task", {})
                task_path = f"Package: {wheel_config.get('package_name', 'N/A')}, Entry: {wheel_config.get('entry_point', 'N/A')}"
            elif task.task_type == "spark_jar":
                jar_config = task.task_config.get("spark_jar_task", {})
                task_path = f"Main Class: {jar_config.get('main_class_name', 'N/A')}"
            elif task.task_type == "condition":
                condition_config = task.task_config.get("condition_task", {})
                task_path = f"Condition: {condition_config.get('left', '')} {condition_config.get('op', 'EQUAL_TO')} {condition_config.get('right', '')}"
            else:
                task_path = "Unknown task type"

            # Add information about new features
            features_info = []
            if task.libraries:
                features_info.append(f"**Libraries**: {len(task.libraries)} configured")
            if task.job_parameters:
                features_info.append(f"**Job Parameters**: {len(task.job_parameters)} configured")
            
            features_text = "; ".join(features_info) if features_info else "Standard configuration"
            
            readme_content += f"""### {task.task_key}
- **Job**: {task.job_name}
- **Type**: {task_type_display}
- **Config**: `{task_path}`
- **Asset Key**: `{snake_case(task.task_key)}`
- **Dependencies**: {", ".join(task.depends_on) if task.depends_on else "None"}
- **Features**: {features_text}

"""

        readme_content += """
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

## Features Extracted from Databricks Bundle

The scaffolder automatically extracts the following features from Databricks bundle configurations:

### Libraries (Databricks Supported)
- **Automatic Extraction**: Libraries from Databricks tasks are automatically included
- **Supported Types**: Python wheels (whl), JAR files (jar), PyPI packages (pypi), Maven packages (maven), CRAN packages (cran)
- **Configuration**: Libraries are preserved as-is from the original Databricks configuration

### Job Parameters (Databricks Supported)
- **Job-Level Parameters**: Job-level parameters from Databricks bundle are extracted and passed to the component
- **Job Parameter References**: Task parameters with `{{job.parameters.param_name}}` references are preserved
- **Template Variables**: Job parameters support template variables like `{{ env }}` and `{{ run_id }}`

### Table Location Metadata (Dagster Enhancement)
- **Automatic Extraction**: Table and data location information is automatically extracted from task parameters
- **Comprehensive Coverage**: Supports input/output tables, paths, and locations
- **Metadata Integration**: Table locations are included in asset metadata for lineage tracking

## Features to Add Manually

### Common Configuration (Dagster-Specific Feature)
- **Manual Addition**: Common configuration should be added manually to the generated component YAML
- **Bundle Variables**: Bundle variables can be used as a reference for creating common configuration
- **Format**: Use `--key=value` format for all tasks
- **Override**: Task-specific parameters take precedence over common configuration

## Command Line Options

- `--databricks_config`: Specify the path to your databricks.yml file
  - If not provided, the scaffolder will search for databricks.yml in the current directory and parent directories
  - Useful when your databricks.yml is in a non-standard location
"""

        readme_path = target_path / "README.md"
        readme_path.write_text(readme_content)

    def _create_template_vars(
        self, target_path: Path, variables: Dict[str, Any], targets: Dict[str, Any]
    ) -> None:
        """Create template_vars.py file for resolving Databricks variables."""

        # Extract variable names and default values from Databricks config
        var_defaults = {}
        for var_name, var_config in variables.items():
            if isinstance(var_config, dict):
                var_defaults[var_name] = var_config.get("default", "unknown")
            else:
                var_defaults[var_name] = var_config

        # Determine catalog names for different environments from targets
        env_catalogs = {}
        for target_name, target_config in targets.items():
            target_vars = target_config.get("variables", {})
            if "catalog_name" in target_vars:
                env_catalogs[target_name] = target_vars["catalog_name"]

        template_vars_content = '''"""
Template variables for Databricks MLOps component.
Auto-generated by DatabricksBundleScaffolder.
"""

import subprocess
from pathlib import Path
import dagster as dg


def get_env() -> str:
    """Get current environment based on Dagster deployment context."""
    import os
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "gtm20":
        # PROD
        return 'prod'
    elif os.getenv("DAGSTER_IS_DEV_CLI"):
        # LOCAL
        return 'dev'
    else:
        # BRANCH
        return 'staging'


def get_catalog_name() -> str:
    """Get catalog name based on environment."""
    env_val = get_env()'''

        # Add environment-specific catalog mappings
        for env_name, catalog in env_catalogs.items():
            template_vars_content += f'''
    if env_val == "{env_name}":
        return "{catalog}"'''

        template_vars_content += '''
    # Default fallback
    return env_val


@dg.template_var
def env(context):
    """Current environment."""
    return get_env()


@dg.template_var
def bundle_name(context):
    """Bundle name for the Databricks MLOps pipeline."""
    return "databricks_mlops"


@dg.template_var
def catalog_name(context):
    """Catalog name for the current environment."""
    return get_catalog_name()


@dg.template_var
def model_name(context):
    """Model name for MLOps pipeline."""
    return "databricks_mlops-model"


@dg.template_var
def experiment_name(context):
    """Experiment name for the current environment."""
    return "/Users/user/dev-databricks_mlops-experiment"


def _get_git_info():
    """Helper to get git information once and cache it."""
    try:
        # Try to get git info from current repo
        git_dir = Path.cwd()
        while git_dir != git_dir.parent:
            if (git_dir / ".git").exists():
                break
            git_dir = git_dir.parent
        
        if (git_dir / ".git").exists():
            # Get git origin URL
            try:
                origin_url = subprocess.check_output(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=git_dir,
                    text=True
                ).strip()
            except subprocess.CalledProcessError:
                origin_url = "unknown"
            
            # Get current branch
            try:
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=git_dir,
                    text=True
                ).strip()
            except subprocess.CalledProcessError:
                branch = "unknown"
            
            # Get current commit
            try:
                commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=git_dir,
                    text=True
                ).strip()
            except subprocess.CalledProcessError:
                commit = "unknown"
            
            return {
                "origin_url": origin_url,
                "branch": branch,
                "commit": commit
            }
        else:
            # No git repo found, return defaults
            return {
                "origin_url": "unknown",
                "branch": "main",
                "commit": "unknown"
            }
    except Exception:
        # Fallback if git commands fail
        return {
            "origin_url": "unknown",
            "branch": "main", 
            "commit": "unknown"
        }


@dg.template_var
def bundle_git(context):
    """Bundle git information as an object."""
    return _get_git_info()


# Individual git template variables for easier access in YAML
@dg.template_var  
def bundle_git_origin_url(context):
    """Git origin URL."""
    return _get_git_info()["origin_url"]


@dg.template_var
def bundle_git_branch(context):
    """Git branch name."""
    return _get_git_info()["branch"]


@dg.template_var
def bundle_git_commit(context):
    """Git commit hash."""
    return _get_git_info()["commit"]


@dg.template_var
def workspace_user(context):
    """Workspace current user name for notebook paths."""
    import os
    import subprocess
    import json
    from pathlib import Path
    
    # Option 1: Try to get from environment variable
    if os.getenv("DATABRICKS_WORKSPACE_USER"):
        return os.getenv("DATABRICKS_WORKSPACE_USER")
    
    # Option 2: Try to get from Databricks CLI configuration
    try:
        # Try to get from ~/.databrickscfg
        config_path = Path.home() / ".databrickscfg"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_content = f.read()
                # Look for username pattern in config
                import re
                username_match = re.search(r'username\\\\s*=\\\\s*(.+)', config_content)
                if username_match:
                    return username_match.group(1).strip()
    except Exception:
        pass
    
    # Option 3: Try to get from Databricks CLI profile
    try:
        result = subprocess.check_output(
            ["databricks", "auth", "describe", "--profile", "DEFAULT"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        auth_info = json.loads(result)
        if 'username' in auth_info:
            return auth_info['username']
    except Exception:
        pass
    
    # Option 4: Try to infer from system user (as email)
    try:
        import getpass
        system_user = getpass.getuser()
        # If it looks like an email, use it; otherwise append a domain
        if '@' in system_user:
            return system_user
        else:
            # Try to get from git config as fallback
            try:
                git_email = subprocess.check_output(
                    ["git", "config", "--get", "user.email"],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
                if git_email and '@' in git_email:
                    return git_email
            except Exception:
                pass
            
            # Last resort: use system user with a generic domain
            return system_user + "@company.com"
    except Exception:
        pass
    
    # Final fallback - use a placeholder that should be replaced
    return "${workspace.current_user.userName}"


@dg.template_var
def databricks_task_value(context):
    """
    Template function to pass Databricks runtime expressions through without resolution.
    
    This allows Databricks task runtime expressions like:
    tasks.monitored_metric_violation_check.values.is_metric_violated
    
    To be passed through to Databricks without being processed by Dagster's template system.
    """
    def _pass_through(expression: str) -> str:
        """Return the expression as-is for Databricks runtime evaluation."""
        # Use string concatenation to avoid Dagster template resolution
        left_brace = "{"
        right_brace = "}"
        return "{}{}{}{}{}".format(left_brace, left_brace, expression, right_brace, right_brace)
    
    return _pass_through
'''

        template_vars_path = target_path / "template_vars.py"
        template_vars_path.write_text(template_vars_content)

    def _add_template_vars_module_to_yaml(self, target_path: Path) -> None:
        """Add template_vars_module to the generated YAML configuration."""
        yaml_path = target_path / "defs.yaml"

        if not yaml_path.exists():
            print(f"Warning: YAML file not found for modification: {yaml_path}")
            return

        # Read the YAML file as text to preserve formatting
        try:
            with open(yaml_path, "r") as f:
                yaml_lines = f.readlines()
        except Exception as e:
            print(f"Warning: Could not read YAML file {yaml_path}: {e}")
            return

        # Find the first line after 'type:' and insert template_vars_module
        for i, line in enumerate(yaml_lines):
            if line.strip().startswith("type:"):
                # Insert template_vars_module after the type line
                yaml_lines.insert(i + 1, "template_vars_module: .template_vars\n")
                yaml_lines.insert(i + 2, "\n")  # Add blank line for readability
                break

        # Write back the modified YAML
        try:
            with open(yaml_path, "w") as f:
                f.writelines(yaml_lines)
            print(f"Updated YAML configuration with template_vars_module: {yaml_path}")
        except Exception as e:
            print(f"Warning: Could not write YAML file {yaml_path}: {e}")
