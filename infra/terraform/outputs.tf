output "kinesis_stream_name" {
  value = aws_kinesis_stream.events.name
}

output "kinesis_stream_arn" {
  value = aws_kinesis_stream.events.arn
}

output "s3_bucket" {
  value = aws_s3_bucket.lake.bucket
}

output "sns_topic_arn" {
  value = aws_sns_topic.late_trip_alerts.arn
}

output "firehose_stream_name" {
  value = aws_kinesis_firehose_delivery_stream.to_s3.name
}

output "databricks_role_arn" {
  value = aws_iam_role.databricks.arn
}

output "producer_access_key_id" {
  value = aws_iam_access_key.producer.id
}

output "producer_secret_access_key" {
  value     = aws_iam_access_key.producer.secret
  sensitive = true
}
