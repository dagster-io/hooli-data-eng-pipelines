from dagster_dbt.core import DbtCli
from dagster_dbt.asset_decorator import DbtManifest
from typing import List, Optional
from dagster import OpExecutionContext

class DbtCli2(DbtCli):
    profiles_dir: str

    def cli(self, args: List[str],
        *,
        manifest: DbtManifest,
        context: Optional[OpExecutionContext] = None):

        args = [*args, "--profiles-dir", self.profiles_dir]
        
        return super().cli(args=args, manifest=manifest, context=context)
    
