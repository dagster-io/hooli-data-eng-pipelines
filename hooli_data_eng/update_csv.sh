#!/bin/bash
# Path to your CSV file
CSV_FILE="/Users/christian/code/hooli-data-eng-pipelines/my_observable_asset.csv"
# Function to update the CSV file
update_csv() {
    # Your update logic goes here
    echo "Updating CSV file at $(date)" 
    echo "1,2,3,$(date)" >> "$CSV_FILE"
}
# Update the CSV file
update_csv
# Wait for 30 seconds
sleep 30
# Update the CSV file again
update_csv