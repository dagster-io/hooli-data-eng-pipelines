import json
import os

import dagster as dg
from dagster_openai import OpenAIResource
from langchain_core.documents import Document

from hooli_ai.assets.ingestion import (
    docs_embedding,
    docs_scrape_raw,
    github_discussions_embeddings,
    github_discussions_raw,
    github_issues_embeddings,
    github_issues_raw,
)
from hooli_ai.assets.retrieval import query
from hooli_ai.resources.github import github_resource
from hooli_ai.resources.pinecone import pinecone_resource
from hooli_ai.resources.scraper import scraper_resource
from upath import UPath


class DocumentIOManager(dg.IOManager):
    def __init__(self, base_dir):
        self.base_dir = UPath(base_dir)
        if not self.base_dir.exists():
            self.base_dir.fs.makedir(self.base_dir)

    def handle_output(self, context: dg.OutputContext, obj):
        # Convert documents to simple dicts
        file_path = self.base_dir.joinpath(f"{context.asset_key.path[-1]}.json")

        # Convert documents to simple dicts
        serialized_docs = [
            {"page_content": doc.page_content, "metadata": doc.metadata} for doc in obj
        ]

        # Save as JSON
        with file_path.open("w") as f:
            json.dump(serialized_docs, f)

        context.add_output_metadata(metadata={"path": str(file_path)})

    def load_input(self, context: dg.InputContext):
        file_path = self.base_dir.joinpath(f"{context.asset_key.path[-1]}.json")

        if not file_path.exists():
            return []

        # Load and reconstruct Documents
        with file_path.open() as f:
            data = json.load(f)

        return [
            Document(page_content=doc["page_content"], metadata=doc["metadata"])
            for doc in data
        ]


@dg.io_manager(config_schema={"base_dir": str})
def document_io_manager(init_context):
    return DocumentIOManager(base_dir=init_context.resource_config["base_dir"])


@dg.definitions
def defs():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "gtm20":
        # PROD
        base_dir = "s3://hooli-demo/hooli-ai/documents"
    elif os.getenv("DAGSTER_IS_DEV_CLI"):
        # LOCAL
        base_dir = "data/documents"
    else:
        # BRANCH
        base_dir = "s3://hooli-demo-branch/hooli-ai/documents"

    return dg.Definitions(
        assets=[
            docs_embedding,
            docs_scrape_raw,
            github_discussions_embeddings,
            github_discussions_raw,
            github_issues_embeddings,
            github_issues_raw,
            query,
        ],
        resources={
            "github": github_resource,
            "scraper": scraper_resource,
            "pinecone": pinecone_resource,
            "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
            "document_io_manager": document_io_manager.configured(
                {
                    "base_dir": base_dir,
                }
            ),
        },
    )
