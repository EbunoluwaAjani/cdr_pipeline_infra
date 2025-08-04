import awswrangler as wr

# Replace with your S3 path
path = "s3://cdr-faker-data-dfad0cb7/cdr_2025-08-02.parquet/78c2e08fb01d4b559aec2aecc8f21af3.snappy.parquet"

# This returns a tuple: (columns_types: Dict[str, str], path: str)
columns_types, _ = wr.s3.read_parquet_metadata(path)

# Print the actual types
print(columns_types)