
# /// script
# dependencies = [
#   "polars",
#   "httpx",
#   "rich",
#   "dagster-pipes"
# ]
# ///
#!/usr/bin/env python3
"""Data fetching and processing script using httpx, polars, and rich libraries with Dagster Pipes."""

import asyncio
from typing import Dict, Any, List

import httpx
import polars as pl
from rich.console import Console
from rich.table import Table
from rich.progress import track
from dagster_pipes import PipesContext, open_dagster_pipes

console = Console()


async def fetch_data() -> List[Dict[str, Any]]:
    """Fetch sample data from a public API using httpx."""
    console.print("[bold green]Starting data fetch process...[/bold green]")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://jsonplaceholder.typicode.com/posts?_limit=10")
            response.raise_for_status()
            data = response.json()
            
            console.print(f"[bold blue]Successfully fetched {len(data)} records[/bold blue]")
            return data
            
        except httpx.RequestError as e:
            console.print(f"[bold red]Error fetching data: {e}[/bold red]")
            return []


def process_with_polars(data: List[Dict[str, Any]]) -> pl.DataFrame:
    """Process fetched data using Polars for data manipulation."""
    if not data:
        console.print("[bold red]No data to process[/bold red]")
        return pl.DataFrame()
    
    console.print("[bold yellow]Processing data with Polars...[/bold yellow]")
    
    # Convert to Polars DataFrame
    df = pl.DataFrame(data)
    
    # Perform some data processing with null handling
    processed_df = df.with_columns([
        # Add title length column with null handling
        pl.col("title").fill_null("").str.len_chars().alias("title_length"),
        # Add word count column with null handling  
        pl.col("title").fill_null("").str.split(" ").list.len().alias("word_count"),
        # Extract first word from title with null handling
        pl.col("title").fill_null("").str.split(" ").list.get(0).alias("first_word")
    ]).with_columns([
        # Categorize posts by length
        pl.when(pl.col("title_length") > 50)
        .then(pl.lit("Long"))
        .when(pl.col("title_length") > 25)
        .then(pl.lit("Medium"))
        .otherwise(pl.lit("Short"))
        .alias("length_category")
    ])
    
    console.print(f"[bold green]Processed {len(processed_df)} records with Polars[/bold green]")
    return processed_df


def display_processed_data(df: pl.DataFrame) -> None:
    """Display processed data in a rich table format."""
    if df.is_empty():
        console.print("[bold red]No data to display[/bold red]")
        return
    
    table = Table(title="Processed Posts Data (Polars)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("User ID", style="green")
    table.add_column("Length", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Words", style="red")
    
    # Convert to list of dictionaries for display
    data_list = df.to_dicts()
    
    for item in track(data_list, description="Displaying processed records..."):
        title = item.get("title", "N/A")
        truncated_title = title[:40] + "..." if len(title) > 40 else title
        
        table.add_row(
            str(item.get("id", "N/A")),
            truncated_title,
            str(item.get("userId", "N/A")),
            str(item.get("title_length", "N/A")),
            item.get("length_category", "N/A"),
            str(item.get("word_count", "N/A"))
        )
    
    console.print(table)


def calculate_statistics(df: pl.DataFrame) -> Dict[str, Any]:
    """Calculate statistics using Polars aggregations."""
    if df.is_empty():
        return {}
    
    stats = df.select([
        pl.len().alias("total_records"),
        pl.col("title_length").mean().alias("avg_title_length"),
        pl.col("title_length").max().alias("max_title_length"),
        pl.col("title_length").min().alias("min_title_length"),
        pl.col("word_count").mean().alias("avg_word_count"),
        pl.col("userId").n_unique().alias("unique_users")
    ]).to_dicts()[0]
    
    # Count by category
    category_counts = df.group_by("length_category").agg(pl.len().alias("count")).to_dicts()
    stats["category_distribution"] = {item["length_category"]: item["count"] for item in category_counts}
    
    return stats


async def run_processing(context: PipesContext = None):
    """Run the data processing workflow."""
    try:
        # Fetch raw data
        raw_data = await fetch_data()
        
        if not raw_data:
            if context:
                context.report_asset_materialization(
                    asset_key="fetched_posts_data",
                    metadata={
                        "status": "failed",
                        "error": "No data fetched",
                        "records_count": 0
                    }
                )
            console.print("[bold red]No data fetched, exiting[/bold red]")
            return
        
        # Process data with Polars
        processed_df = process_with_polars(raw_data)
        
        # Calculate statistics
        stats = calculate_statistics(processed_df)
        
        # Display processed data
        display_processed_data(processed_df)
        
        # Report to Dagster if context is available
        if context:
            # Convert numeric values to native Python types for JSON serialization
            # Flatten category_distribution into separate metadata keys
            category_dist = stats.get("category_distribution", {})
            
            metadata = {
                "records_processed": int(stats.get("total_records", 0)),
                "avg_title_length": float(round(stats.get("avg_title_length", 0), 2)) if stats.get("avg_title_length") else 0.0,
                "max_title_length": int(stats.get("max_title_length", 0)) if stats.get("max_title_length") else 0,
                "min_title_length": int(stats.get("min_title_length", 0)) if stats.get("min_title_length") else 0,
                "avg_word_count": float(round(stats.get("avg_word_count", 0), 2)) if stats.get("avg_word_count") else 0.0,
                "unique_users": int(stats.get("unique_users", 0)) if stats.get("unique_users") else 0,
                "category_long_count": int(category_dist.get("Long", 0)),
                "category_medium_count": int(category_dist.get("Medium", 0)),
                "category_short_count": int(category_dist.get("Short", 0)),
                "processing_library": "polars",
                "data_source": "jsonplaceholder.typicode.com",
                "status": "success"
            }
            
            context.report_asset_materialization(
                asset_key="fetched_posts_data",
                metadata=metadata
            )
            
            # Report custom message with summary
            context.report_custom_message(
                f"Successfully processed {len(processed_df)} posts with average title length of {stats.get('avg_title_length', 0):.1f} characters"
            )
            
            console.print(f"[bold green]Reported asset materialization to Dagster with {len(processed_df)} records[/bold green]")
        else:
            console.print("[bold yellow]Running in standalone mode (no Dagster Pipes context)[/bold yellow]")
        
    except Exception as e:
        console.print(f"[bold red]Error in processing: {e}[/bold red]")
        if context:
            context.report_asset_materialization(
                asset_key="fetched_posts_data",
                metadata={
                    "status": "error",
                    "error_message": str(e),
                    "records_count": 0
                }
            )
        raise


def main():
    """Main function to orchestrate data fetching, processing, and reporting to Dagster."""
    console.print("[bold yellow]Data Fetcher Script Started[/bold yellow]")
    
    # Try to use Dagster Pipes context if available, otherwise run standalone
    try:
        with open_dagster_pipes() as context:
            asyncio.run(run_processing(context))
    except Exception:
        # If Dagster Pipes is not available, run in standalone mode
        console.print("[bold yellow]Dagster Pipes not available, running in standalone mode[/bold yellow]")
        asyncio.run(run_processing(None))
    
    console.print("[bold yellow]Data Fetcher Script Completed[/bold yellow]")


if __name__ == "__main__":
    main()