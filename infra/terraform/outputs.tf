output "sqs_queue_url" {
  value = aws_sqs_queue.events.url
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.events.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.batcher.function_name
}

output "s3_bucket" {
  value = aws_s3_bucket.lake.bucket
}

output "sns_topic_arn" {
  value = aws_sns_topic.late_trip_alerts.arn
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
