resource "aws_sns_topic" "late_trip_alerts" {
  name = "${var.project}-late-trip-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.late_trip_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
