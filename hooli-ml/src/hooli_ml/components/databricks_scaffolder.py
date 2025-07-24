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
        description="Path to the databricks.yml file. If not provided, will auto-discover in current directory and parents."
    )


def snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Remove file extension if present
    name = Path(name).stem
    # Replace special characters and spaces with underscores
    name = re.sub(r'[^a-zA-Z0-9]+', '_', name)
    # Convert CamelCase to snake_case
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower().strip('_')


@dataclass
class DatabricksTask:
    """Represents a Databricks task with its configuration."""
    task_key: str
    notebook_path: str
    base_parameters: Dict[str, Any]
    depends_on: List[str]
    job_name: str


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
        variables = databricks_config.get('variables', {})
        includes = databricks_config.get('include', [])
        targets = databricks_config.get('targets', {})
        bundle_info = databricks_config.get('bundle', {})
        
        # Parse all included resource files
        all_tasks = []
        for include_path in includes:
            resource_path = bundle_dir / include_path
            if resource_path.exists():
                tasks = self._extract_tasks_from_resource(resource_path, variables)
                all_tasks.extend(tasks)
        
        if not all_tasks:
            self._create_basic_template(request)
            return
            
        # Build dependency graph
        task_dependencies = self._build_dependency_graph(all_tasks)
        
        # Generate component YAML
        component_config = self._generate_component_config(all_tasks, task_dependencies, variables, targets, bundle_info)
        
        # Scaffold the component
        dg.scaffold_component(request, component_config)
        
        # Add template_vars_module to the generated YAML
        self._add_template_vars_module_to_yaml(request.target_path)
        
        # Create template_vars.py file for resolving Databricks variables
        self._create_template_vars(request.target_path, variables, targets)
        
        # Create additional documentation
        self._create_documentation(request.target_path, databricks_config_path, all_tasks)
    
    def _get_databricks_config_path(self, request: ScaffoldRequest[DatabricksScaffoldParams]) -> Optional[Path]:
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
            for filename in ['databricks.yml', 'databricks.yaml']:
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
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}")
            return {}
    
    def _extract_tasks_from_resource(self, resource_path: Path, variables: Dict[str, Any]) -> List[DatabricksTask]:
        """Extract Databricks tasks from a resource YAML file."""
        resource_config = self._load_yaml(resource_path)
        tasks = []
        
        # Navigate to jobs section
        resources = resource_config.get('resources', {})
        jobs = resources.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            job_tasks = job_config.get('tasks', [])
            
            for task_config in job_tasks:
                task_key = task_config.get('task_key', '')
                if not task_key:
                    continue
                
                # Extract notebook task info
                notebook_task = task_config.get('notebook_task', {})
                notebook_path = notebook_task.get('notebook_path', '')
                base_parameters = notebook_task.get('base_parameters', {})
                
                # Extract dependencies
                depends_on = task_config.get('depends_on', [])
                dependency_keys = []
                if depends_on:
                    for dep in depends_on:
                        if isinstance(dep, dict) and 'task_key' in dep:
                            dependency_keys.append(dep['task_key'])
                        elif isinstance(dep, str):
                            dependency_keys.append(dep)
                
                tasks.append(DatabricksTask(
                    task_key=task_key,
                    notebook_path=notebook_path,
                    base_parameters=base_parameters,
                    depends_on=dependency_keys,
                    job_name=job_name
                ))
        
        return tasks
    
    def _build_dependency_graph(self, tasks: List[DatabricksTask]) -> Dict[str, List[str]]:
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
    
    def _generate_component_config(self, tasks: List[DatabricksTask], 
                                 dependencies: Dict[str, List[str]], 
                                 variables: Dict[str, Any],
                                 targets: Dict[str, Any],
                                 bundle_info: Dict[str, Any]) -> Dict[str, Any]:
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
            if target_config.get('default', False):
                default_target = target_name
                break
        if not default_target and targets:
            default_target = list(targets.keys())[0]
        
        # Build component tasks
        component_tasks = []
        
        for job_name, job_tasks in jobs_tasks.items():
            for task in job_tasks:
                asset_key = snake_case(task.task_key)
                
                # Create asset spec
                asset_spec = {
                    "key": asset_key,
                    "description": f"{task.task_key} from {job_name} job",
                    "kinds": ["databricks", "notebook"]
                }
                
                # Add dependencies if they exist
                if asset_key in dependencies and dependencies[asset_key]:
                    asset_spec["deps"] = dependencies[asset_key]
                
                # Create task configuration
                task_config = {
                    "task_key": task.task_key,  # Keep original task_key, asset key will be snake_case
                    "notebook_path": self._process_notebook_path(task.notebook_path),
                    "asset_specs": [asset_spec],
                    "parameters": self._process_parameters(task.base_parameters, variables, default_target)
                }
                
                component_tasks.append(task_config)
        
        # Generate job name prefix from bundle name or use default
        bundle_name = bundle_info.get('name', 'databricks_mlops')
        job_name_prefix = f"{bundle_name}_pipeline"
        
        return {
            "job_name_prefix": job_name_prefix,
            "serverless": True,
            "tasks": component_tasks
        }
    
    def _process_parameters(self, parameters: Dict[str, Any], 
                          variables: Dict[str, Any], 
                          default_target: Optional[str]) -> Dict[str, Any]:
        """Process parameters, converting Databricks variables to Dagster template syntax."""
        processed = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Convert Databricks variable syntax to Dagster template syntax
                processed_value = value
                
                # Handle specific Databricks bundle variables
                processed_value = re.sub(r'\$\{var\.([^}]+)\}', r'{{ \1 }}', processed_value)
                processed_value = re.sub(r'\$\{bundle\.target\}', r'{{ env }}', processed_value)
                processed_value = re.sub(r'\$\{bundle\.name\}', r'{{ bundle_name }}', processed_value)
                
                # Handle bundle.git variables - convert dots to underscores for template var names
                processed_value = re.sub(r'\$\{bundle\.git\.origin_url\}', r'{{ bundle_git_origin_url }}', processed_value)
                processed_value = re.sub(r'\$\{bundle\.git\.branch\}', r'{{ bundle_git_branch }}', processed_value)
                processed_value = re.sub(r'\$\{bundle\.git\.commit\}', r'{{ bundle_git_commit }}', processed_value)
                
                # General fallback for any other bundle variables
                processed_value = re.sub(r'\$\{bundle\.([^}]+)\}', r'{{ bundle_\1 }}', processed_value)
                
                processed[key] = processed_value
            else:
                processed[key] = value
        
        return processed
    
    def _process_notebook_path(self, notebook_path: str) -> str:
        """Process notebook path to convert Databricks variables to Dagster template variables."""
        processed_path = notebook_path
        
        # Remove .py extension if present (Databricks notebooks don't use file extensions)
        if processed_path.endswith('.py'):
            processed_path = processed_path[:-3]
        
        # Convert Databricks bundle variables to Dagster template variables
        processed_path = re.sub(r'\$\{workspace\.current_user\.userName\}', '{{ workspace_user }}', processed_path)
        processed_path = re.sub(r'\$\{bundle\.name\}', '{{ bundle_name }}', processed_path)
        processed_path = re.sub(r'\$\{bundle\.target\}', '{{ env }}', processed_path)
        
        # Handle relative paths
        if notebook_path.startswith("../"):
            # Convert relative path to bundle absolute path with template variables
            relative_path = notebook_path[3:]  # Remove ../
            if relative_path.endswith('.py'):
                relative_path = relative_path[:-3]
            return "/Users/{{ workspace_user }}/.bundle/{{ bundle_name }}/{{ env }}/files/" + relative_path
        elif not notebook_path.startswith("/"):
            # If it's a relative path without ../, assume it's from files directory
            clean_path = notebook_path[:-3] if notebook_path.endswith('.py') else notebook_path
            return "/Users/{{ workspace_user }}/.bundle/{{ bundle_name }}/{{ env }}/files/" + clean_path
        else:
            # Already an absolute path, process any variables
            return processed_path
    
    def _create_basic_template(self, request: ScaffoldRequest[DatabricksScaffoldParams]) -> None:
        """Create a basic template when no Databricks config is found."""
        basic_config = {
            "job_name_prefix": "databricks_pipeline",
            "serverless": True,
            "tasks": [
                {
                    "task_key": "example_task",
                    "notebook_path": "/path/to/your/notebook",
                    "asset_specs": [
                        {
                            "key": "example_asset",
                            "description": "Example Databricks notebook asset",
                            "kinds": ["databricks", "notebook"]
                        }
                    ],
                    "parameters": {
                        "param1": "value1",
                        "env": "{{ env }}"
                    }
                }
            ]
        }
        
        dg.scaffold_component(request, basic_config)
    
    def _create_documentation(self, target_path: Path, databricks_config_path: Path, 
                            tasks: List[DatabricksTask]) -> None:
        """Create documentation about the scaffolded component."""
        
        # Handle relative path safely - if it's not in a subpath, just use the absolute path
        try:
            relative_config_path = databricks_config_path.relative_to(target_path.parent)
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
            readme_content += f"""### {task.task_key}
- **Job**: {task.job_name}
- **Notebook**: `{task.notebook_path}`
- **Asset Key**: `{snake_case(task.task_key)}`
- **Dependencies**: {', '.join(task.depends_on) if task.depends_on else 'None'}

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

## Command Line Options

- `--databricks_config`: Specify the path to your databricks.yml file
  - If not provided, the scaffolder will search for databricks.yml in the current directory and parent directories
  - Useful when your databricks.yml is in a non-standard location
"""
        
        readme_path = target_path / "README.md"
        readme_path.write_text(readme_content)
    
    def _create_template_vars(self, target_path: Path, variables: Dict[str, Any], targets: Dict[str, Any]) -> None:
        """Create template_vars.py file for resolving Databricks variables."""
        
        # Extract variable names and default values from Databricks config
        var_defaults = {}
        for var_name, var_config in variables.items():
            if isinstance(var_config, dict):
                var_defaults[var_name] = var_config.get('default', 'unknown')
            else:
                var_defaults[var_name] = var_config
        
        # Determine catalog names for different environments from targets
        env_catalogs = {}
        for target_name, target_config in targets.items():
            target_vars = target_config.get('variables', {})
            if 'catalog_name' in target_vars:
                env_catalogs[target_name] = target_vars['catalog_name']
        
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
        
        template_vars_content += f'''
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
    return "{var_defaults.get('model_name', 'databricks_mlops-model')}"


@dg.template_var
def experiment_name(context):
    """Experiment name for the current environment."""
    return "{var_defaults.get('experiment_name', '/Users/user/{{env}}-databricks_mlops-experiment').replace('${{bundle.target}}', '{{env}}').replace('${{workspace.current_user.userName}}', 'user')}"


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
            
            return {{
                "origin_url": origin_url,
                "branch": branch,
                "commit": commit
            }}
        else:
            # No git repo found, return defaults
            return {{
                "origin_url": "unknown",
                "branch": "main",
                "commit": "unknown"
            }}
    except Exception:
        # Fallback if git commands fail
        return {{
            "origin_url": "unknown",
            "branch": "main", 
            "commit": "unknown"
        }}


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
                username_match = re.search(r'username\\s*=\\s*(.+)', config_content)
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
            return f"{{system_user}}@company.com"
    except Exception:
        pass
    
    # Final fallback - use a placeholder that should be replaced
    return "${{workspace.current_user.userName}}"
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
            with open(yaml_path, 'r') as f:
                yaml_lines = f.readlines()
        except Exception as e:
            print(f"Warning: Could not read YAML file {yaml_path}: {e}")
            return
        
        # Find the first line after 'type:' and insert template_vars_module
        for i, line in enumerate(yaml_lines):
            if line.strip().startswith('type:'):
                # Insert template_vars_module after the type line
                yaml_lines.insert(i + 1, 'template_vars_module: .template_vars\n')
                yaml_lines.insert(i + 2, '\n')  # Add blank line for readability
                break
        
        # Write back the modified YAML
        try:
            with open(yaml_path, 'w') as f:
                f.writelines(yaml_lines)
            print(f"Updated YAML configuration with template_vars_module: {yaml_path}")
        except Exception as e:
            print(f"Warning: Could not write YAML file {yaml_path}: {e}")
