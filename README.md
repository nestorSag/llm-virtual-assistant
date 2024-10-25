# RAG template on AWS using Terraform

This repository was forked from the [AWS template](https://github.com/aws-samples/terraform-rag-template-using-amazon-bedrock). Refer to the original repo's README for more details

It deploys a RAG system in AWS using S3 for ingestion, Lambda for preprocessing, AWS Aurora as a vector DB, and a containerised RAG server one ECS. It also initialises a VPN for testing purposes.

# Requirements

* Python

* Terraform

* AWS CLI

* Appropriate AWS permissions

* Docker with a running Docker daemon

# Usage

Use the Makefile rules to build or destroy the infrastructure or associated Docker images.