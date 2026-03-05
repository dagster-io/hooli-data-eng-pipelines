"""
Hello World Spark Python Script

This is a simple example of a Spark Python script that can be run as a spark_python_task
in a Databricks job. It demonstrates basic Spark functionality and parameter handling.
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp


def main():
    """Main function that runs the Spark hello world example."""
    
    # Check if we're running in Databricks
    is_databricks = False
    try:
        # Try to access dbutils - this will only work in Databricks
        dbutils  # This will be available in Databricks global namespace
        is_databricks = True
        print("🏢 Running in Databricks environment")
    except NameError:
        print("💻 Running in local/non-Databricks environment")
    
    # Initialize Spark session
    if is_databricks:
        # In Databricks, use the existing Spark session
        spark = SparkSession.getActiveSession()
        if spark is None:
            spark = SparkSession.builder.appName("HelloWorldSpark").getOrCreate()
    else:
        # In local environments, create a new session
        spark = SparkSession.builder \
            .appName("HelloWorldSpark") \
            .getOrCreate()
    
    print("🚀 Hello World from Spark Python Task!")
    print(f"📊 Spark version: {spark.version}")
    
    # Parse command line parameters
    if len(sys.argv) > 1:
        message = sys.argv[1]
        print(f"💬 Custom message: {message}")
    else:
        message = "Hello from Dagster + Databricks!"
    
    # Get environment parameter if provided
    env = sys.argv[2] if len(sys.argv) > 2 else "development"
    print(f"🌍 Environment: {env}")
    
    # Create a simple DataFrame to demonstrate Spark functionality
    data = [
        ("Dagster", "Orchestration", "Awesome"),
        ("Databricks", "Analytics", "Powerful"),
        ("Spark", "Processing", "Fast"),
        ("Python", "Language", "Versatile")
    ]
    
    columns = ["technology", "category", "description"]
    
    df = spark.createDataFrame(data, columns)
    
    # Add some computed columns
    df_enhanced = df \
        .withColumn("message", lit(message)) \
        .withColumn("environment", lit(env)) \
        .withColumn("timestamp", current_timestamp()) \
        .withColumn("tech_category", 
                   col("technology").cast("string") + " - " + col("category").cast("string"))
    
    print("\n📋 Generated DataFrame:")
    df_enhanced.show(truncate=False)
    
    # Perform some basic analytics
    print(f"\n📈 Analytics Results:")
    print(f"   - Total technologies: {df_enhanced.count()}")
    print(f"   - Unique categories: {df_enhanced.select('category').distinct().count()}")
    
    # Group by category and count
    category_counts = df_enhanced.groupBy("category").count().orderBy("count", ascending=False)
    print(f"\n📊 Technologies by category:")
    category_counts.show()
    
    # Demonstrate saving to temporary view (in real scenarios you might save to Delta tables)
    df_enhanced.createOrReplaceTempView("hello_world_results")
    
    # Query using SQL
    result = spark.sql("""
        SELECT 
            technology,
            category,
            description,
            message,
            environment,
            DATE_FORMAT(timestamp, 'yyyy-MM-dd HH:mm:ss') as formatted_timestamp
        FROM hello_world_results
        ORDER BY technology
    """)
    
    print("\n🔍 SQL Query Results:")
    result.show(truncate=False)
    
    # Return task values that can be used by downstream tasks
    task_values = {
        "total_technologies": df_enhanced.count(),
        "unique_categories": df_enhanced.select('category').distinct().count(),
        "message": message,
        "environment": env,
        "status": "completed"
    }
    
    print(f"\n✅ Task completed successfully!")
    print(f"📤 Task values: {task_values}")
    
    # In Databricks, you can set task values using dbutils
    if is_databricks:
        try:
            # Set individual task values that can be referenced by downstream tasks
            # These can be referenced as: tasks.{task_key}.values.{key}
            dbutils.jobs.taskValues.set(key="status", value="completed")
            dbutils.jobs.taskValues.set(key="total_technologies", value=str(df_enhanced.count()))
            dbutils.jobs.taskValues.set(key="unique_categories", value=str(df_enhanced.select('category').distinct().count()))
            dbutils.jobs.taskValues.set(key="message", value=message)
            dbutils.jobs.taskValues.set(key="environment", value=env)
            
            print("📋 Task values set for downstream tasks:")
            print(f"   - status: completed")
            print(f"   - total_technologies: {df_enhanced.count()}")
            print(f"   - unique_categories: {df_enhanced.select('category').distinct().count()}")
            print(f"   - message: {message}")
            print(f"   - environment: {env}")
        except Exception as e:
            print(f"📋 Error setting task values: {e}")
    else:
        print("📋 Task values would be set in Databricks environment")
    
    # Don't stop Spark session in Databricks - it's managed by the platform
    # In local environments, you would call spark.stop(), but not in Databricks
    if not is_databricks:
        spark.stop()
        print("🏁 Spark session stopped. Goodbye!")
    else:
        print("🏁 Task completed successfully. Goodbye!")


if __name__ == "__main__":
    main()
