from dagster_dbt import DbtCliResource
from typing import List, Optional
from dagster import OpExecutionContext

# NO LONGER USED IN PROJECT, BUT EXAMPLE OF CUSTOMIZING AN INTEGRATION RESOURCE


class DbtCli2(DbtCliResource):
    profiles_dir: str

    def cli(self, args: List[str], *, context: Optional[OpExecutionContext] = None):
        args = [*args, "--profiles-dir", self.profiles_dir]

        return super().cli(args=args, context=context)
