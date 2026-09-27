# Firehose reads from the Kinesis stream and lands raw JSON in S3, partitioned
# by hour. Databricks Auto Loader picks these files up as a streaming source.

data "aws_iam_policy_document" "firehose_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["firehose.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "firehose" {
  name               = "${var.project}-firehose-role"
  assume_role_policy = data.aws_iam_policy_document.firehose_trust.json
}

data "aws_iam_policy_document" "firehose" {
  statement {
    actions = [
      "kinesis:DescribeStream", "kinesis:GetShardIterator",
      "kinesis:GetRecords", "kinesis:ListShards"
    ]
    resources = [aws_kinesis_stream.events.arn]
  }
  statement {
    actions = [
      "s3:AbortMultipartUpload", "s3:GetBucketLocation", "s3:GetObject",
      "s3:ListBucket", "s3:ListBucketMultipartUploads", "s3:PutObject"
    ]
    resources = [aws_s3_bucket.lake.arn, "${aws_s3_bucket.lake.arn}/*"]
  }
  statement {
    actions   = ["logs:PutLogEvents"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "firehose" {
  name   = "${var.project}-firehose-policy"
  role   = aws_iam_role.firehose.id
  policy = data.aws_iam_policy_document.firehose.json
}

resource "aws_kinesis_firehose_delivery_stream" "to_s3" {
  name        = "${var.project}-to-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.events.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.lake.arn

    # Hive-style partitions so Auto Loader / Spark can prune by time
    prefix              = "raw-events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "firehose-errors/!{firehose:error-output-type}/"

    # Smallest buffers = lowest latency. Firehose flushes when either is hit.
    buffering_size     = 1  # MB
    buffering_interval = 60 # seconds
    compression_format = "GZIP"

    # One JSON object per line; Firehose does not add newlines by default
    processing_configuration {
      enabled = true
      processors {
        type = "AppendDelimiterToRecord"
        parameters {
          parameter_name  = "Delimiter"
          parameter_value = "\\n"
        }
      }
    }
  }
}
