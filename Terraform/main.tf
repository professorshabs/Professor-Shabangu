##Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "af-south-1"
}

###############
variable "bucket-name" {
  default = "mybucket-lake-capetown2"
}

variable "arn-var" {
  default = "arn:aws:iam::618249149314:group/adminProf"
}
###############

##create S3
resource "aws_s3_bucket" "create-s3-bucket" {
  bucket = "${var.bucket-name}"
  acl="private"
  lifecycle_rule {
    id="archive"
    enabled = true
    transition {
      days=30
      storage_class = "STANDARD_IA"
    }
    transition {
      days = 60
      storage_class = "GLACIER"
    }
  }
  versioning { enabled = true}
  tags = {
    Environment: "Dev"
  }
}


##Budget:
resource "aws_budgets_budget" "Prof_Test_monthly-budget" {
  name              = "monthly-budget"
  budget_type       = "COST"
  limit_amount      = "10"
  limit_unit        = "USD"
  time_period_start = "2022-10-20_00:00"
  time_unit         = "MONTHLY"
  }

#######
#Data Source:
//resource "aws_rds_cluster" "postgresql" {
//  cluster_identifier      = "mycluster.cluster"
//  engine                  = "aurora-postgresql"
//  availability_zones      = ["us-west-2a", "us-west-2b", "us-west-2c"]
//  database_name           = "mydb"
//  master_username         = "postgres"
//  master_password         = "5Y67bg#r#"
//  backup_retention_period = 5
//  preferred_backup_window = "07:00-09:00"
//}

###########
#Load script
######################

 variable "file-name" {
   default = "etl.py"
 }

 resource "aws_s3_bucket_object" "object" {
   bucket = "${var.bucket-name}"
   key    = "Script/Glue/${var.file-name}"
   source = "/Users/profshabangu/PycharmProjects/fork-TerraFlo/Professor-Shabangu/Glue/${var.file-name}"

 }

//##################
//# Glue Catalog   #
//##################
//resource "aws_glue_catalog_table" "aws_glue_catalog_table" {
//  name          = "MyCatalogTable"
//  database_name = "MyCatalogDatabase"
//}
//

//
//##################
//# Glue Crawler   #
//##################
//resource "aws_glue_crawler" "example" {
//  database_name = aws_glue_catalog_database.example.name
//  name          = "example"
//  role          = aws_iam_role.example.arn
//
//  catalog_target {
//    database_name = aws_glue_catalog_database.example.name
//    tables        = [aws_glue_catalog_table.example.name]
//  }
//
//  schema_change_policy {
//    delete_behavior = "LOG"
//  }
//
//  configuration = <<EOF
//{
//  "Version":1.0,
//  "Grouping": {
//    "TableGroupingPolicy": "CombineCompatibleSchemas"
//  }
//}
//EOF
//}
//
//##################
//# Glue Job       #
//##################
//resource "aws_glue_job" "example" {
//  name     = "python-job"
//  description = "ETL to s3 from client aurora cluster"
//  role_arn = "${var.arn-var}"
//
//  command {
//    script_location = "s3://${var.bucket-name}/Script/Glue/${var.file-name}"
//    python_version = "3"
//  }
//}
