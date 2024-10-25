




## Build back end infrastucture using Terraform
build-backend:
	cd terraform & terraform init & terraform apply -var-file=commons.tfvars -auto-approve

## Build back end infrastucture using Terraform
build-rag-image:
	cd python/src/handlers/rag && docker build -t rag-server:1.0 .