# Lambda drains the SQS queue in batches and writes one gzipped JSON-lines
# file per batch to S3, partitioned by hour. Always-free: 1M invocations.

data "archive_file" "batcher" {
  type        = "zip"
  source_file = "${path.module}/../lambda/batcher.py"
  output_path = "${path.module}/.build/batcher.zip"
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "batcher" {
  name               = "${var.project}-batcher-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "batcher" {
  statement {
    actions = [
      "sqs:ReceiveMessage", "sqs:DeleteMessage",
      "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"
    ]
    resources = [aws_sqs_queue.events.arn]
  }
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.lake.arn}/raw-events/*"]
  }
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "batcher" {
  name   = "${var.project}-batcher-policy"
  role   = aws_iam_role.batcher.id
  policy = data.aws_iam_policy_document.batcher.json
}

resource "aws_lambda_function" "batcher" {
  function_name    = "${var.project}-batcher"
  role             = aws_iam_role.batcher.arn
  runtime          = "python3.12"
  handler          = "batcher.handler"
  filename         = data.archive_file.batcher.output_path
  source_code_hash = data.archive_file.batcher.output_base64sha256
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      BUCKET = aws_s3_bucket.lake.bucket
      PREFIX = "raw-events"
    }
  }
}

# Pull up to 500 messages or wait up to 10 s, whichever comes first,
# then invoke Lambda once. This sets the end-to-end ingestion latency.
resource "aws_lambda_event_source_mapping" "sqs_to_batcher" {
  event_source_arn                   = aws_sqs_queue.events.arn
  function_name                      = aws_lambda_function.batcher.arn
  batch_size                         = 500
  maximum_batching_window_in_seconds = 10
  function_response_types            = ["ReportBatchItemFailures"]
}
