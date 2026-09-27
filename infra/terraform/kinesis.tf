# One shard = 1 MB/s in, 2 MB/s out. Free tier covers this for 12 months.
resource "aws_kinesis_stream" "events" {
  name             = "${var.project}-events"
  shard_count      = 1
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}
