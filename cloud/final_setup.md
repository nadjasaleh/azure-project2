# Setup process for g2p2 project

* Flask app app1/app.py is running in vm1 and connecting to azure postgres server.
* Flask app app2/app.py is running in vm2 and connecting to azure storage blob
* Both apps are containerized inside vm's using docker
* DB, VM's and storage are all in the same virtual network, and only accessible from my/admin ip.
* App's are also accessible publicly through the azure application gateway.

> **Commentary**: The setup ensures secure communication between resources via a virtual network. Public access is restricted to the Application Gateway, which acts as a reverse proxy.

This document details the setting up of the entire cloud environment.

## resource group

```bash
az group create --name g2p2-rg --location northeurope 
```
> **Commentary**: Resource group `g2p2-rg` acts as a logical container for all Azure resources.

## Postgres service

Check the available SKU's:
```bash
az postgres flexible-server list-skus --location northeurope --output table
```

Setup the server:
```bash
az postgres flexible-server create --resource-group g2p2-rg --name g2p2-postgres-db --admin-user postgres --admin-password pgsecret --location northeurope --public-access 0.0.0.0 --sku-name Standard_B1ms --tier Burstable
```
> **Commentary**: PostgreSQL server is configured with public access disabled for enhanced security. Admin IP access is explicitly allowed.

Setup additional direct access for admin (if you need it):
```bash
az postgres flexible-server firewall-rule create --resource-group g2p2-rg --name g2p2-postgres-db --rule-name adminIP --start-ip-address 80.221.17.16 --end-ip-address 80.221.17.16
```

You can also save the conn string like this:
```bash
PG_CONN_STRING="$(az postgres flexible-server show-connection-string --server-name g2p2-postgres-db)"
```

### Test connection for admin

```bash
psql "host=g2p2-postgres-db.postgres.database.azure.com port=5432 dbname=postgres user=postgres password=pgsecret sslmode=require"
```

or if your PGVARS are set in the env, just call psql:
```bash
psql # -h $PGHOST -U $PGUSER -d $PGDATABASE -p $PGPORT
```
> **Commentary**: Testing ensures the database is reachable and credentials are correct.

## Create Azure Blob Storage

1. Create a storage account with hierarchical namespace enabled:
```bash
az storage account create --name g2p2sa --resource-group g2p2-rg --location northeurope --sku Standard_LRS --kind StorageV2 --hns true --access-tier Hot
```

2. Get storage account key:
```bash
STORAGE_ACCOUNT_KEY="$(az storage account keys list --account-name g2p2sa --resource-group g2p2-rg --query "[0].value" --output tsv)"
```


3. Create a container for storing reports:
```bash
az storage container create  --account-name g2p2sa --name data --account-key $STORAGE_ACCOUNT_KEY
```

## Create Virtual Machines

1. Create a Virtual Network:
```bash
az network vnet create --resource-group g2p2-rg --name g2p2-vnet --address-prefix 10.0.0.0/16 --subnet-name g2p2-subnet --subnet-prefix 10.0.1.0/24
```
> **Commentary**: Virtual network `g2p2-vnet` isolates resources and enables secure communication.

2. Create two VMs (you need to have the rsa file):
```bash
az vm create --resource-group g2p2-rg --name g2p2-app1-vm --image Ubuntu2404 --vnet-name g2p2-vnet --subnet g2p2-subnet --admin-username azureuser --ssh-key-values ~/.ssh/id_rsa.pub --size Standard_B2s --location northeurope

az vm create --resource-group g2p2-rg --name g2p2-app2-vm --image Ubuntu2404 --vnet-name g2p2-vnet --subnet g2p2-subnet --admin-username azureuser --ssh-key-values ~/.ssh/id_rsa.pub --size Standard_B2s --location northeurope
```
> **Commentary**: VMs `g2p2-app1-vm` and `g2p2-app2-vm` are provisioned within the virtual network.

3. Open HTTP and SSH ports for the VMs:
```bash
az vm open-port --resource-group g2p2-rg --name g2p2-app1-vm --port 80
az vm open-port --resource-group g2p2-rg --name g2p2-app2-vm --port 80
```
> **Commentary**: Ports are opened to allow HTTP traffic and SSH access for management.

### Step 3: Configure Networking

1. Create a private endpoint for postgres (requires admin rights -> Ville):
```bash
az network private-endpoint create --resource-group g2p2-rg --name g2p2-postgres-private-endpoint --vnet-name g2p2-vnet --subnet g2p2-subnet --private-connection-resource-id "/subscriptions/23b183d5-a30f-46b8-b418-ad060fb67787/resourceGroups/g2p2-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/g2p2-postgres-db" --group-id postgresServer --connection-name g2p2-postgres-connection
```
> **Commentary**: Private endpoint ensures secure access to the PostgreSQL server within the VNet.

2. Approve private endpoint (Ville):
```bash
az network private-link-resource list --name g2p2-postgres-db --resource-group g2p2-rg --type Microsoft.DBforPostgreSQL/flexibleServers
```

3. Secure the VMs with NSGs (Ville):
```bash
az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app1-vmNSG --name AllowSSH --priority 1000 --access Allow --protocol Tcp --direction Inbound  --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 22

az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app1-vmNSG --name AllowHTTP --priority 1001 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 80

az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app1-vmNSG --name AllowFlask --priority 1002 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 5000

az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app2-vmNSG --name AllowSSH --priority 1000 --access Allow --protocol Tcp --direction Inbound  --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 22

az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app2-vmNSG --name AllowHTTP --priority 1001 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 80

az network nsg rule create --resource-group g2p2-rg --nsg-name g2p2-app2-vmNSG --name AllowFlask --priority 1002 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes '*' --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 1
```
> **Commentary**: NSGs enforce traffic rules, ensuring only allowed traffic reaches the VMs.

## LAST TASK: Use Azure Application Gateway as a Reverse Proxy

First, create a new subnet:
```bash
az network vnet subnet create \
    --resource-group g2p2-rg \
    --vnet-name g2p2-vnet \
    --name g2p2-app-gateway-subnet \
    --address-prefix 10.0.2.0/24
```
> **Commentary**: Subnet `g2p2-app-gateway-subnet` is dedicated to the Application Gateway.

1. Create an Application Gateway:
```bash
az network application-gateway create \
    --resource-group g2p2-rg \
    --name g2p2-app-gateway \
    --sku Standard_v2 \
    --capacity 2 \
    --vnet-name g2p2-vnet \
    --subnet g2p2-app-gateway-subnet \
    --frontend-port 80 \
    --http-settings-port 5000 \
    --http-settings-protocol Http \
    --routing-rule-type Basic \
    --location northeurope \
    --public-ip-address g2p2-app-gateway-public-ip \
    --priority 100
```
> **Commentary**: Application Gateway provides load balancing and acts as a reverse proxy for the apps.

**The Gateway's public ip can be polled with:**
```bash
az network public-ip show \
    --resource-group g2p2-rg \
    --name g2p2-app-gateway-public-ip \
    --query "ipAddress" \
    --output tsv

    #20.123.34.18
```

**If at any point you are confused about your ip address space, you can check it with:**
```bash
az vm list-ip-addresses --resource-group g2p2-rg --query "[].virtualMachine.network.privateIpAddresses" --output table
```

2. Add backend pools for the VMs:
```bash
az network application-gateway address-pool create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app1-backend-pool \
    --servers 10.0.0.4 #<app1-vm-private-ip>

az network application-gateway address-pool create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app2-backend-pool \
    --servers 10.0.0.5 #<app2-vm-private-ip>
```
> **Commentary**: Backend pools link the VMs to the Application Gateway.

3. Configure routing rules:
```bash
az network application-gateway http-settings create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app1-http-settings \
    --port 5000 \
    --protocol Http

az network application-gateway http-settings create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app2-http-settings \
    --port 5001 \
    --protocol 

# HTTP listeners for the gateway are problem...

az network application-gateway frontend-port create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app1-frontend-port \
    --port 5000


az network application-gateway http-listener create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app1-http-listener \
    --frontend-ip appGatewayFrontendIP \
    --frontend-port app1-frontend-port \


az network application-gateway rule create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app1-routing-rule \
    --http-listener app1-http-listener \
    --rule-type Basic \
    --address-pool app1-backend-pool \
    --http-settings app1-http-settings \
    --priority 101


## trust but verify
az network application-gateway http-listener list \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --output table

az network application-gateway address-pool list \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --output table

az network application-gateway rule list \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --output table

# diagnostics
az monitor diagnostic-settings create \
    --name app-gateway-logs \
    --resource <application-gateway-resource-id> \
    --logs '[{"category": "ApplicationGatewayAccessLog", "enabled": true}]'

## same for app2

az network application-gateway frontend-port create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app2-frontend-port \
    --port 5001


az network application-gateway http-listener create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app2-http-listener \
    --frontend-ip appGatewayFrontendIP \
    --frontend-port app2-frontend-port


az network application-gateway rule create \
    --gateway-name g2p2-app-gateway \
    --resource-group g2p2-rg \
    --name app2-routing-rule \
    --http-listener app2-http-listener \
    --rule-type Basic \
    --address-pool app2-backend-pool \
    --http-settings app2-http-settings \
    --priority 103



###


**Access the apps through the Application Gateway's public IP address: http://20.123.34.18**
