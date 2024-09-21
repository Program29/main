provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket-name"  # Must be globally unique
  acl    = "private"

  versioning {
    enabled = true
  }
}

resource "aws_glue_catalog_database" "example" {
  name = "example_database"
}

resource "aws_glue_catalog_table" "example" {
  name          = "example_table"
  database_name = aws_glue_catalog_database.example.name

  storage_descriptor {
    location = "s3://${aws_s3_bucket.example.bucket}/data/"
    input_format = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveOutputFormat"
    
    columns {
      name = "id"
      type = "int"
    }

    columns {
      name = "name"
      type = "string"
    }
  }

  table_type = "EXTERNAL_TABLE"
}

resource "aws_databricks_workspace" "example" {
  name = "example-databricks"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.example.bucket
}

output "glue_database_name" {
  value = aws_glue_catalog_database.example.name
}

output "glue_table_name" {
  value = aws_glue_catalog_table.example.name
}

output "databricks_workspace_url" {
  value = aws_databricks_workspace.example.workspace_url
}
