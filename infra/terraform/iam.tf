# --- Producer user: only allowed to write to the Kinesis stream ---------
resource "aws_iam_user" "producer" {
  name = "${var.project}-producer"
}

resource "aws_iam_access_key" "producer" {
  user = aws_iam_user.producer.name
}

data "aws_iam_policy_document" "producer" {
  statement {
    actions   = ["kinesis:PutRecord", "kinesis:PutRecords", "kinesis:DescribeStream"]
    resources = [aws_kinesis_stream.events.arn]
  }
}

resource "aws_iam_user_policy" "producer" {
  name   = "${var.project}-producer-policy"
  user   = aws_iam_user.producer.name
  policy = data.aws_iam_policy_document.producer.json
}

# --- Databricks role: Unity Catalog storage credential ---------------------
# Trust policy per Databricks docs: the UC master role assumes this role using
# the external ID shown when you create the storage credential, and the role
# must also be able to assume itself.
data "aws_caller_identity" "current" {}

locals {
  databricks_role_name = "${var.project}-databricks-role"
  databricks_role_arn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.databricks_role_name}"
}

data "aws_iam_policy_document" "databricks_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = [var.databricks_uc_master_role_arn, local.databricks_role_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.databricks_external_id]
    }
  }
}

resource "aws_iam_role" "databricks" {
  name               = local.databricks_role_name
  assume_role_policy = data.aws_iam_policy_document.databricks_trust.json
}

data "aws_iam_policy_document" "databricks" {
  statement {
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.lake.arn]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.lake.arn}/*"]
  }
  statement {
    actions   = ["sts:AssumeRole"]
    resources = [local.databricks_role_arn]
  }
  statement {
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.late_trip_alerts.arn]
  }
}

resource "aws_iam_role_policy" "databricks" {
  name   = "${var.project}-databricks-policy"
  role   = aws_iam_role.databricks.id
  policy = data.aws_iam_policy_document.databricks.json
}
