# CDR Transaction Pipeline with Terraform & Airflow

This project provisions a scalable end-to-end data pipeline for telecom data and synthetic user profiles using AWS services, Terraform, and Apache Airflow.

## Overview

There are two legs in this pipeline:

### 1. CDR Data Pipeline:
- Generates 500,000 to 1,000,000 synthetic CDR (Call Detail Records) daily using the Faker API
- Stores data in an S3 data lake in Parquet format
- Loads data into Amazon Redshift for analytics
- Orchestrated using Apache Airflow
- Infrastructure is provisioned using Terraform

### 2. Random User Data Pipeline:
- Fetches random user profile data from the RandomUser API
- Loads the data into an RDS (MySQL) instance
- Airbyte is used to extract data from RDS and load it into Redshift

---

## Infrastructure Provisioned with Terraform

### Core AWS Resources:
- S3 Bucket for CDR data lake
- Redshift Cluster with subnet group and IAM role
- RDS MySQL instance
- VPC with public subnets and Internet Gateway
- Security Groups for Redshift and RDS
- IAM Roles and Policies for Redshift to access S3
- SSM Parameter Store for managing secrets (passwords & usernames)
- Remote S3 backend for Terraform state management
- Extensive use of variables for flexibility

---

## Data Pipeline Workflow (Airflow)

### CDR DAG:

Tasks:
1. `load_to_s3`: Generates random CDR data and uploads to S3
2. `get_s3_key`: Constructs the S3 key for the current run
3. `load_to_redshift`: Uses `S3ToRedshiftOperator` to copy data to Redshift

```python
Task Flow:
load_to_s3 >> get_s3_key >> load_to_redshift
```

Schedule: `@daily`

### Random User DAG:

- Uses Python requests to fetch random user data
- Loads it into RDS using PyMySQL
- Credentials and parameters are pulled securely from Airflow Variables and SSM Parameter Store
- Airbyte performs ELT from RDS to Redshift


---

## CDR Schema (Sample Columns)

- `caller_number`, `receiver_number`, `caller_imei`, `receiver_imei`
- `call_start`, `call_end`, `duration_seconds`
- `caller_network`, `receiver_network`, `billing_type`, `promo_code`
- `call_quality`, `cost`, `data_usage_mb`, `connection_status`

---

## Requirements

- Python 3.8+
- Apache Airflow with Amazon provider
- Terraform >= 1.0
- AWS CLI configured
- Boto3, Pandas, AWS Wrangler, PyMySQL

```bash
pip install -r requirements.txt
```

---

## Terraform Usage

```bash
terraform init      # Initialize Terraform
terraform plan      # Preview changes
terraform apply     # Apply infrastructure
```

### Terraform Variables

```hcl
variable "cluster_config" {
  type = object({ ... })
  default = { ... }
}

variable "rds_config" {
  type = object({ ... })
  default = { ... }
}
```

Uses remote S3 bucket for Terraform state storage.

---

## Secrets Management

Passwords and usernames are stored in AWS SSM Parameter Store:

- `/dev/redshift-cluster/password/master`
- `/dev/rds_instance/password/master`

Secrets are pulled dynamically into Airflow and Python code using Airflow Variables and Boto3.

---

## Airflow Configuration

Ensure Airflow includes the following:

- Connections: `aws_default`, `redshift_default`
- Variables:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `RDS_SSM_USER_PARAM`
  - `RDS_SSM_PASSWORD_PARAM`

To trigger DAGs:
```bash
airflow dags trigger cdr_pipeline
airflow dags trigger randomuser_pipeline
```

---

## Cleanup

```bash
terraform destroy
```


## Author

Built by Ebunoluwa Ajani


