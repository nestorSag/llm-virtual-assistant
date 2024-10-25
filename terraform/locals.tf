# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
locals {
  path_include  = ["**"]
  path_exclude  = ["**/__pycache__/**"]

  # Preproc files hash (tracks changes in preproc source code)
  preproc_source_path   = "${path.root}/../python/src/handlers/data_ingestion_processor"
  preproc_files_include = setunion([for f in local.path_include : fileset(local.preproc_source_path, f)]...)
  preproc_files_exclude = setunion([for f in local.path_exclude : fileset(local.preproc_source_path, f)]...)
  preproc_files         = sort(setsubtract(local.preproc_files_include, local.preproc_files_exclude))
  preproc_dir_sha = sha1(join("", [for f in local.preproc_files : filesha1("${local.preproc_source_path}/${f}")]))

  # Server files hash (tracks changes in server source code)
  server_source_path   = "${path.root}/../python/src/handlers/rag"
  server_files_include = setunion([for f in local.path_include : fileset(local.server_source_path, f)]...)
  server_files_exclude = setunion([for f in local.path_exclude : fileset(local.server_source_path, f)]...)
  server_files         = sort(setsubtract(local.server_files_include, local.server_files_exclude))
  server_dir_sha = sha1(join("", [for f in local.server_files : filesha1("${local.server_source_path}/${f}")]))

  image_tag = "latest-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  ssm_parameter_for_sagamaker = {
    PG_VECTOR_SECRET_ARN = module.aurora.cluster_master_user_secret[0].secret_arn
    PG_VECTOR_DB_NAME    = module.aurora.cluster_database_name
    PG_VECTOR_DB_HOST    = module.aurora.cluster_endpoint
    PG_VECTOR_PORT       = 5432
    CHUNK_SIZE           = 200
    CHUNK_OVERLAP        = 20
    VECTOR_DB_INDEX      = "sample-index"
    EMBEDDING_MODEL_ID   = var.embedding_model_id
    S3_BUCKET_NAME       = module.s3.s3_bucket_id
  }

  text_generation_model_arns = formatlist("arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/%s", var.text_generation_model_ids)

  vpc_endpoints = {
    s3              = "Gateway",
    bedrock-runtime = "Interface",
    secretsmanager  = "Interface",
  }
}
