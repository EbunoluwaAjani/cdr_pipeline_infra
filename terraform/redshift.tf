resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "cdr-fakerdata-bucket" {
  bucket = "cdr-faker-data-${random_id.bucket_suffix.hex}"

  tags = merge(local.common_tags, {
    Name = "cdr-faker-data"
  })
}


resource "aws_iam_role" "redshift_role" {
  name = "RedshiftS3AccessRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      },
    ]
  })

}


resource "aws_iam_policy" "redshift_s3_read" {
  name        = "RedshiftS3ReadPolicy"
  description = "Allows Redshift to read from cdr-faker-bucket"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.cdr-fakerdata-bucket.arn,
          "${aws_s3_bucket.cdr-fakerdata-bucket.arn}/*"
        ]
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "redshift_policy_attach" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = aws_iam_policy.redshift_s3_read.arn
}



resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "XYZ0123456789%&*()-_=+"
}

data "aws_ssm_parameter" "redshift_master_username" {
  name            = "/redshift/master_username"
  with_decryption = true
}

resource "aws_ssm_parameter" "redshift_pswrd" {
  name        = "/dev/redshift-cluster/password/master"
  description = "The parameter description"
  type        = "SecureString"
  value       = random_password.password.result

  tags = local.common_tags
}

resource "aws_redshift_subnet_group" "redshift_subnet_group" {
  name       = "redshift-subnet-group"
  subnet_ids = [aws_subnet.public.id]

  tags = merge(local.common_tags, {
    Name = "Redshift Subnet Group"
  })
}

resource "aws_redshift_cluster" "new_cluster" {
  cluster_identifier        = var.cluster_config.cluster_identifier
  database_name             = var.cluster_config.database_name
  master_username           = data.aws_ssm_parameter.redshift_master_username.value
  master_password           = aws_ssm_parameter.redshift_pswrd.value
  node_type                 = var.cluster_config.node_type
  cluster_type              = var.cluster_config.cluster_type
  number_of_nodes           = var.cluster_config.number_of_nodes
  iam_roles                 = [aws_iam_role.redshift_role.arn]
  publicly_accessible       = true
  vpc_security_group_ids    = [aws_security_group.public_traffic.id]
  cluster_subnet_group_name = aws_redshift_subnet_group.redshift_subnet_group.name

  tags = local.common_tags
}


