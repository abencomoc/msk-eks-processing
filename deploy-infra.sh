#!/bin/bash
set -e

export TF_LOG_PROVIDER=ERROR

echo ""
echo "##### Deploying Infrastructure with Terraform #####"
echo ""

cd infra-tf

# Initialize Terraform
echo ""
echo "===== Initializing Terraform ====="
echo ""
terraform init

# Apply
echo ""
echo "===== Applying Terraform configuration ====="
echo ""
terraform apply -auto-approve

# Configure kubectl
echo ""
echo "===== Configuring kubectl ====="
echo ""
eval $(terraform output -raw configure_kubectl)
echo "✓ kubectl context updated to new EKS cluster"

# Wait for cluster to be ready
echo ""
echo "===== Waiting for cluster to be ready ====="
echo ""
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Get MSK bootstrap brokers
export MSK_BROKERS=$(terraform output -raw msk_bootstrap_brokers_iam)

cd ..

# Update .env file with MSK brokers
grep -v "KAFKA_BOOTSTRAP_SERVERS" .env > .env.tmp && mv .env.tmp .env
echo "KAFKA_BOOTSTRAP_SERVERS=$MSK_BROKERS" >> .env

echo ""
echo "===== Infrastructure Deployed ====="
echo ""
echo "Next steps:"
echo ""
echo "  1. Verify .env file has correct MSK bootstrap brokers:"
echo "     KAFKA_BOOTSTRAP_SERVERS=$MSK_BROKERS"
echo ""
echo "  2. Run ./deploy-consumer.sh"
echo ""
echo "  3. Run ./deploy-producer.sh"
echo ""
