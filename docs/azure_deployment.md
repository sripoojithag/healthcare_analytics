# Azure Cloud Architecture & Deployment Guide

This document outlines the production cloud deployment strategy for the **Healthcare Data Warehouse & Analytics Platform** on Microsoft Azure.

> **CRITICAL NOTICE**: Do **NOT** run provisioning commands or deploy to Azure without explicit approval. The platform is fully operational locally using SQLite and Docker without incurring any cloud costs.

---

## 1. Cloud Architecture Overview

```
                        ┌────────────────────────────────────────────────────────┐
                        │                   Users / Clinicians                   │
                        └───────────────────────────┬────────────────────────────┘
                                                    │ HTTPS (Port 443)
                                                    ▼
                        ┌────────────────────────────────────────────────────────┐
                        │             Azure Front Door / Application Gateway     │
                        │           (TLS Termination, DDoS, WAF Rules)           │
                        └─────────────┬────────────────────────────┬─────────────┘
                                      │                            │
                                      ▼ /                          ▼ /api/*
              ┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
              │      Azure Container Apps (Web)      │  │      Azure Container Apps (API)      │
              │         React + Nginx Frontend       │  │          FastAPI Microservices       │
              └──────────────────────────────────────┘  └──────────────────┬───────────────────┘
                                                                           │
                                            ┌──────────────────────────────┼──────────────────────────────┐
                                            │                              │                              │
                                            ▼                              ▼                              ▼
                         ┌───────────────────────┐     ┌───────────────────────┐      ┌───────────────────────┐
                         │   Azure Key Vault     │     │   Azure SQL Database  │      │  Azure Blob Storage   │
                         │ (DB creds, JWT keys)  │     │ (Star Schema Warehouse│      │ (CSV Ingestion Landing│
                         │                       │     │  Encounters, Dims)    │      │  & Model Artifacts)   │
                         └───────────────────────┘     └───────────────────────┘      └───────────────────────┘
```

---

## 2. Recommended Azure Services

| Tier | Service | Configuration / SKU | Justification |
| :--- | :--- | :--- | :--- |
| **Compute** | **Azure Container Apps** | Consumption Tier (Serverless, scale-to-zero) | Cost-effective container hosting with built-in HTTPS, revision management, and autoscaling. |
| **Data Warehouse** | **Azure SQL Database** | General Purpose Serverless (Auto-pause enabled) | ANSI SQL compliance, native support for Star Schema DDL, automatic indexing, and cost control when idle. |
| **Security** | **Azure Key Vault** | Standard Tier | Hardware-backed secret storage eliminating hardcoded credentials in git or containers. |
| **Artifacts** | **Azure Container Registry (ACR)** | Basic Tier | Private Docker registry with direct integration into Container Apps. |
| **Monitoring** | **Azure Application Insights** | Pay-as-you-go | Distributed telemetry, request tracing, and latency monitoring without logging patient PHI. |

---

## 3. Step-by-Step Deployment Procedure

### Step 1: Authentication & Resource Group Setup
```bash
# 1. Login to Azure CLI
az login

# 2. Set active subscription (if multiple)
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

# 3. Create dedicated resource group
az group create \
    --name rg-healthcare-analytics-prod \
    --location eastus
```

### Step 2: Provision Azure SQL Database
```bash
# Generate secure random admin password
SQL_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Create logical SQL Server
az sql server create \
    --name sql-healthcare-warehouse \
    --resource-group rg-healthcare-analytics-prod \
    --location eastus \
    --admin-user sqladmin \
    --admin-password "$SQL_ADMIN_PASSWORD"

# Configure firewall to allow Azure internal services
az sql server firewall-rule create \
    --resource-group rg-healthcare-analytics-prod \
    --server sql-healthcare-warehouse \
    --name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Create Serverless Azure SQL Database with auto-pause after 60 min idle
az sql db create \
    --resource-group rg-healthcare-analytics-prod \
    --server sql-healthcare-warehouse \
    --name HealthcareWarehouseDB \
    --edition GeneralPurpose \
    --compute-model Serverless \
    --family Gen5 \
    --capacity 2 \
    --auto-pause-delay 60
```

### Step 3: Configure Azure Key Vault for Secrets
```bash
# Create Key Vault
az keyvault create \
    --name kv-healthcare-analytics \
    --resource-group rg-healthcare-analytics-prod \
    --location eastus

# Assemble production connection string using ODBC Driver 18
SQL_CONN_STR="mssql+pyodbc://sqladmin:${SQL_ADMIN_PASSWORD}@sql-healthcare-warehouse.database.windows.net/HealthcareWarehouseDB?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

# Store connection string and API signing secret
az keyvault secret set --vault-name kv-healthcare-analytics --name "DatabaseUrl" --value "$SQL_CONN_STR"
az keyvault secret set --vault-name kv-healthcare-analytics --name "JwtSecretKey" --value "$(openssl rand -hex 32)"
```

### Step 4: Build and Push Containers to Azure Container Registry
```bash
# Create Azure Container Registry
az acr create \
    --name acrhealthcareprod \
    --resource-group rg-healthcare-analytics-prod \
    --sku Basic \
    --admin-enabled true

# Login to ACR
az acr login --name acrhealthcareprod

# Build and push Backend image
docker build -t acrhealthcareprod.azurecr.io/backend:v1 -f Dockerfile.backend .
docker push acrhealthcareprod.azurecr.io/backend:v1

# Build and push Frontend image
docker build -t acrhealthcareprod.azurecr.io/frontend:v1 -f Dockerfile.frontend .
docker push acrhealthcareprod.azurecr.io/frontend:v1
```

### Step 5: Deploy via Azure Container Apps
```bash
# Create Container Apps environment
az containerapp env create \
    --name env-healthcare-prod \
    --resource-group rg-healthcare-analytics-prod \
    --location eastus

# Retrieve ACR credentials
ACR_PASSWORD=$(az acr credential show --name acrhealthcareprod --query "passwords[0].value" -o tsv)

# Deploy Backend Container App
az containerapp create \
    --name app-healthcare-backend \
    --resource-group rg-healthcare-analytics-prod \
    --environment env-healthcare-prod \
    --image acrhealthcareprod.azurecr.io/backend:v1 \
    --target-port 8000 \
    --ingress external \
    --registry-server acrhealthcareprod.azurecr.io \
    --registry-username acrhealthcareprod \
    --registry-password "$ACR_PASSWORD" \
    --secrets \
        db-url=keyvaultref:https://kv-healthcare-analytics.vault.azure.net/secrets/DatabaseUrl \
        secret-key=keyvaultref:https://kv-healthcare-analytics.vault.azure.net/secrets/JwtSecretKey \
    --env-vars \
        ENVIRONMENT=production \
        DATABASE_URL=secretref:db-url \
        SECRET_KEY=secretref:secret-key \
        CORS_ORIGINS='["https://healthcare-analytics.azurewebsites.net"]'

# Retrieve backend FQDN
BACKEND_URL=$(az containerapp show --name app-healthcare-backend --resource-group rg-healthcare-analytics-prod --query "properties.configuration.ingress.fqdn" -o tsv)

# Deploy Frontend Container App
az containerapp create \
    --name app-healthcare-frontend \
    --resource-group rg-healthcare-analytics-prod \
    --environment env-healthcare-prod \
    --image acrhealthcareprod.azurecr.io/frontend:v1 \
    --target-port 80 \
    --ingress external \
    --registry-server acrhealthcareprod.azurecr.io \
    --registry-username acrhealthcareprod \
    --registry-password "$ACR_PASSWORD"
```

### Step 6: Initial Database Schema Migration
Once the backend container connects to Azure SQL, run the DDL schema script:
```bash
# Execute DDL migration on Azure SQL DB
sqlcmd -S sql-healthcare-warehouse.database.windows.net \
       -d HealthcareWarehouseDB \
       -U sqladmin \
       -P "$SQL_ADMIN_PASSWORD" \
       -i sql/warehouse_ddl.sql
```

---

## 4. Security & Compliance Checklist

- [x] **Zero Hardcoded Secrets**: All passwords, API tokens, and connection strings are managed via Key Vault secrets.
- [x] **Transport Layer Security**: HTTPS enforced on all endpoints via Azure Container Apps ingress.
- [x] **HIPAA Compliance Guidelines**:
  - Patient identifiers (`patient_nbr`) masked before presentation (`PT-***{suffix}`).
  - Audit logging records operational access without storing protected health information (PHI) in log text.
  - Role-Based Access Control restricts sensitive encounter tables to authorized Analyst and Admin roles.
- [x] **CORS Configuration**: Locked down in production to explicit frontend origins via the `CORS_ORIGINS` environment variable.
