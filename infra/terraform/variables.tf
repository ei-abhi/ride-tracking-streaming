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

variable "databricks_uc_master_role_arn" {
  description = "Unity Catalog master role that assumes our role (static value from Databricks docs)"
  type        = string
  default     = "arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-14S5ZJVKOTYTL"
}

variable "databricks_external_id" {
  description = "External ID shown in Databricks when creating a storage credential"
  type        = string
  default     = "0000"
}
