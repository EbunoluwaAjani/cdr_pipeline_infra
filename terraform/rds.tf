resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-west-1a"
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "public_subnet_a"
  })
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "eu-west-1b"
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "public_subnet_b"
  })
}


resource "aws_db_subnet_group" "rds" {
  name = "rds-subnet-group-dev"
  subnet_ids = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id
  ]

  tags = merge(local.common_tags, {
    Name = "rds_subnet_group_dev"
  })
}



resource "aws_route_table" "public_rds" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "public_route_table"
  })
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "rds" {
  name        = "rds_sg"
  description = "Allow access to RDS from trusted IP"
  vpc_id      = aws_vpc.main.id


  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["102.89.22.212/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "rds_security_group"
  })
}

data "aws_ssm_parameter" "rds_username" {
  name            = "/dev/rds_instance/username"
  with_decryption = true
}

resource "aws_ssm_parameter" "rds_pswrd" {
  name        = "/dev/rds_instance/password/master"
  description = "The parameter description"
  type        = "SecureString"
  value       = random_password.password.result

  tags = local.common_tags
}

resource "aws_db_instance" "dev" {
  identifier             = var.rds_config.identifier
  engine                 = var.rds_config.engine
  instance_class         = var.rds_config.instance_class
  allocated_storage      = var.rds_config.allocated_storage
  db_name                = var.rds_config.db_name
  username               = data.aws_ssm_parameter.rds_username.value
  password               = aws_ssm_parameter.rds_pswrd.value
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = var.rds_config.publicly_accessible
  skip_final_snapshot    = var.rds_config.skip_final_snapshot

  tags = merge(local.common_tags, {
    Name = "dev_rds_instance"
  })
}

