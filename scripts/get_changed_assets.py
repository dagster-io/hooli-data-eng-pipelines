#!/usr/bin/env python3
"""Script to detect changed assets in a Dagster Cloud branch deployment.

Queries a branch deployment's GraphQL API for assets with changedReasons of NEW
or CODE_VERSION, and outputs them grouped by code location — ready for
`dagster-cloud job launch` invocations.

Example usage:
    # Output dagster-cloud job launch commands (default)
    python get_changed_assets.py \
        --deployment my-branch-deployment

    # Filter to specific change types
    python get_changed_assets.py \
        --deployment my-branch-deployment \
        --change-types NEW,CODE_VERSION

    # Output as JSON
    python get_changed_assets.py \
        --deployment my-branch-deployment \
        --output-format json

    # Output as tab-separated lines
    python get_changed_assets.py \
        --deployment my-branch-deployment \
        --output-format lines

    # Verbose mode (diagnostics to stderr, commands to stdout)
    python get_changed_assets.py \
        --deployment my-branch-deployment \
        --verbose

    # Pipe directly to bash
    python get_changed_assets.py --deployment my-branch-deployment | bash

    # Environment variables:
    #   DAGSTER_CLOUD_ORGANIZATION  - Dagster Cloud organization name
    #   DAGSTER_CLOUD_API_TOKEN     - API token for authentication
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Optional

import requests

CHANGED_ASSETS_QUERY = """
query GetChangedAssets {
    assetNodes {
        assetKey { path }
        changedReasons
        repository {
            name
            location { name }
        }
    }
}
"""

VALID_CHANGE_TYPES = {
    "NEW",
    "CODE_VERSION",
    "DEPENDENCIES",
    "PARTITIONS_DEFINITION",
    "TAGS",
    "METADATA",
    "REMOVED",
}


class DagsterAPIClient:
    """Client for interacting with Dagster Cloud's GraphQL API."""

    def __init__(self, organization: str, deployment: str, api_token: str):
        self.graphql_url = (
            f"https://{organization}.dagster.cloud/{deployment}/graphql"
        )
        self.api_token = api_token

    def execute_query(
        self, query: str, variables: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Dagster-Cloud-Api-Token": self.api_token,
        }

        response = requests.post(
            self.graphql_url,
            json={"query": query, "variables": variables or {}},
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data


def get_changed_assets(
    client: DagsterAPIClient,
    change_types: set[str],
    verbose: bool = False,
) -> dict[tuple[str, str], list[str]]:
    """Query the branch deployment for assets with the specified change reasons.

    Returns a dict mapping (location_name, repository_name) to sorted lists of
    asset key strings (path components joined with '/').
    """
    result = client.execute_query(CHANGED_ASSETS_QUERY)
    asset_nodes = result["data"]["assetNodes"]

    if verbose:
        print(f"Fetched {len(asset_nodes)} total asset nodes", file=sys.stderr)

    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    matched_count = 0

    for node in asset_nodes:
        reasons = set(node.get("changedReasons") or [])
        if not reasons & change_types:
            continue

        matched_count += 1
        asset_key = "/".join(node["assetKey"]["path"])
        location_name = node["repository"]["location"]["name"]
        repository_name = node["repository"]["name"]
        grouped[(location_name, repository_name)].append(asset_key)

        if verbose:
            print(
                f"  Changed: {asset_key} ({', '.join(sorted(reasons))})"
                f" in {location_name}/{repository_name}",
                file=sys.stderr,
            )

    # Sort asset keys within each group for deterministic output
    for key in grouped:
        grouped[key].sort()

    if verbose:
        print(
            f"Found {matched_count} changed assets across"
            f" {len(grouped)} code location(s)",
            file=sys.stderr,
        )

    return dict(grouped)


def format_commands(
    grouped: dict[tuple[str, str], list[str]],
    job: str,
) -> str:
    lines = []
    for (location, repository), asset_keys in sorted(grouped.items()):
        asset_args = " ".join(f"--asset-key 'key:\"{key}\"'" for key in asset_keys)
        lines.append(
            f"dagster-cloud job launch"
            f" --location {location}"
            f" --job {job}"
            f" {asset_args}"
        )
    return "\n".join(lines)


def format_json(grouped: dict[tuple[str, str], list[str]]) -> str:
    # Key by "location_name/repository_name" for readability
    out = {}
    for (location, repository), asset_keys in sorted(grouped.items()):
        key = f"{location}/{repository}" if repository != "__repository__" else location
        out[key] = asset_keys
    return json.dumps(out, indent=2)


def format_lines(grouped: dict[tuple[str, str], list[str]]) -> str:
    lines = []
    for (location, repository), asset_keys in sorted(grouped.items()):
        for asset_key in asset_keys:
            lines.append(f"{location}\t{repository}\t{asset_key}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Detect changed assets in a Dagster Cloud branch deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--deployment",
        required=True,
        help="Branch deployment name (the slug used in the URL path)",
    )
    parser.add_argument(
        "--organization",
        default=os.environ.get("DAGSTER_CLOUD_ORGANIZATION"),
        help="Dagster Cloud organization name (default: $DAGSTER_CLOUD_ORGANIZATION)",
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("DAGSTER_CLOUD_API_TOKEN"),
        help="Dagster Cloud API token (default: $DAGSTER_CLOUD_API_TOKEN)",
    )
    parser.add_argument(
        "--change-types",
        default="NEW,CODE_VERSION",
        help="Comma-separated change types to filter on (default: NEW,CODE_VERSION)",
    )
    parser.add_argument(
        "--output-format",
        choices=["commands", "json", "lines"],
        default="commands",
        help="Output format (default: commands)",
    )
    parser.add_argument(
        "--job",
        default="__ASSET_JOB",
        help="Job name for launch commands (default: __ASSET_JOB)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print diagnostics to stderr",
    )

    args = parser.parse_args()

    if not args.organization:
        print(
            "Error: --organization or DAGSTER_CLOUD_ORGANIZATION env var is required",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.api_token:
        print(
            "Error: --api-token or DAGSTER_CLOUD_API_TOKEN env var is required",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse and validate change types
    change_types = {ct.strip().upper() for ct in args.change_types.split(",")}
    invalid = change_types - VALID_CHANGE_TYPES
    if invalid:
        print(
            f"Error: invalid change type(s): {', '.join(sorted(invalid))}. "
            f"Valid types: {', '.join(sorted(VALID_CHANGE_TYPES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        print(
            f"Querying {args.organization}/{args.deployment}"
            f" for change types: {', '.join(sorted(change_types))}",
            file=sys.stderr,
        )

    client = DagsterAPIClient(args.organization, args.deployment, args.api_token)

    try:
        grouped = get_changed_assets(client, change_types, verbose=args.verbose)
    except Exception as e:
        print(f"Error querying branch deployment: {e}", file=sys.stderr)
        sys.exit(1)

    if not grouped:
        if args.verbose:
            print("No changed assets found", file=sys.stderr)
        sys.exit(0)

    if args.output_format == "json":
        output = format_json(grouped)
    elif args.output_format == "lines":
        output = format_lines(grouped)
    else:
        output = format_commands(grouped, args.job)

    print(output)


if __name__ == "__main__":
    main()
