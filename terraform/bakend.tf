terraform {
  backend "s3" {
    bucket = "maindev-statefile-bucket"
    key    = "state.tfstate"

    region = "eu-west-1"
  }
}