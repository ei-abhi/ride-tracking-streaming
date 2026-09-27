variable "project" {
  description = "Project name used as a prefix for resources"
  type        = string
  default     = "ride-tracking"
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for the lakehouse"
  type        = string
}

variable "alert_email" {
  description = "Email that receives late-trip alerts from SNS"
  type        = string
}

variable "databricks_account_id" {
  description = "Databricks AWS account ID for cross-account role trust (leave default until you connect Databricks)"
  type        = string
  default     = "414351767826"
}

variable "databricks_external_id" {
  description = "External ID shown in Databricks when creating a storage credential"
  type        = string
  default     = "REPLACE_ME"
}
