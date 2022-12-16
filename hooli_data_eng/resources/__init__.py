from dagster import (
    AssetMaterialization,
    Field,
    StringSource
)
from dagster import _check as check
from dagster import io_manager
from dagster_aws.s3 import PickledObjectS3IOManager
import pandas as pd
import io
import pickle
from dagster._utils import PICKLE_PROTOCOL

class MLErrPickledObjectS3IOManager(PickledObjectS3IOManager):
    
    def handle_output(self, context, obj):
        if context.dagster_type.typing_type == type(None):
            check.invariant(
                obj is None,
                "Output had Nothing type or 'None' annotation, but handle_output received value "
                f"that was not None and was of type {type(obj)}.",
            )
            return None
        
        if not isinstance(obj, pd.DataFrame):
            check.failed(f"Outputs of type {type(obj)} not supported.")

        key = self._get_path(context)
        path = self._uri_for_key(key)
        context.log.debug(f"Writing S3 object at: {path}")

        if self._has_object(key):
            context.log.warning(f"Removing existing S3 key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        pickled_obj_bytes = io.BytesIO(pickled_obj)
        self.s3.upload_fileobj(pickled_obj_bytes, self.bucket, key)
    
        context.log_event(
            AssetMaterialization(
                asset_key=context.asset_key,
                description="Error (Obs - Pred)",
                metadata={
                    "numeric_metadata": obj.iloc[0,0]
                },
            )
        )
        

    

@io_manager(
    config_schema={
        "s3_bucket": Field(StringSource),
        "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"s3"},
)
def ml_err_s3_pickle_io_manager(init_context):
    """Based on the s3_pickle_io_manager, but adds metadata with the model error
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.resource_config["s3_bucket"]
    s3_prefix = init_context.resource_config.get("s3_prefix")  # s3_prefix is optional
    pickled_io_manager = MLErrPickledObjectS3IOManager(s3_bucket, s3_session, s3_prefix=s3_prefix)
    return pickled_io_manager
