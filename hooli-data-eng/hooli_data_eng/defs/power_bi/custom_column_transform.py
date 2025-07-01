from typing import Callable
import dagster as dg

@dg.template_var
def customized_column_schema(context):
  return lambda data: dg.TableSchema(
                    columns=[
                        dg.TableColumn(
                            name=col["name"],
                            type=col["dataType"],
                            tags={"PII": ""} if col["name"] == "USER_ID" else None,
                        )
                        for col in data.properties["tables"][0]["columns"]
                    ]
                )