# Azure Setup for Flask Applications

## Polling Azure for Relevant Variables
Before proceeding with the setup, you can use the following Azure CLI commands to retrieve the necessary variables for your deployment. These variables include resource group names, storage account details, VM private IPs, and more.

### Retrieve subscription id (active)
```bash
az account show --query "id" --output tsv
```

### Retrieve Resource Group Details
```bash
az group list --query "[?name=='g2p2-rg']" --output table
```

### Retrieve Storage Account Details
```bash
az storage account list --resource-group g2p2-rg --query "[?name=='g2p2-sa']" --output table
```

### Retrieve PostgreSQL Server Details
```bash
az postgres flexible-server list --resource-group g2p2-rg --query "[?name=='g2p2-postgres-db']" --output table
```

### Retrieve VM Details
```bash
az vm list --resource-group g2p2-rg --query "[].{Name:name, PrivateIP:privateIps, PublicIP:publicIps}" --output table
```

### Retrieve VM's public ip's
```bash
az vm list-ip-addresses \
    --resource-group <resource-group-name> \
    --name <vm-name> \
    --query "[].virtualMachine.network.publicIpAddresses[].ipAddress" \
    --output tsv
```

### Retrieve Application Gateway Details
```bash
az network application-gateway list --resource-group g2p2-rg --query "[?name=='g2p2-app-gateway']" --output table
```

### Retrieve AG's public ip
```bash
az network public-ip show \
    --resource-group <resource-group-name> \
    --name <public-ip-name> \
    --query "ipAddress" \
    --output tsv
```
### Retrieve all public ip's
```bash
az network public-ip list --query "[].ipAddress" --output tsv
```

Use these commands to verify the existence and details of the resources before proceeding with the setup steps.

### Check firewall rules for PG server
```bash
az postgres flexible-server firewall-rule list \
    --resource-group <resource-group-name> \
    --server-name <server-name> \
    --output table
```

### Check network rules for SA
```bash
az storage account network-rule list \
    --resource-group <resource-group-name> \
    --account-name <storage-account-name> \
    --output table
```

### Check NSG rules for VM
```bash
az vm show \
    --resource-group <resource-group-name> \
    --name <vm-name> \
    --query "networkProfile.networkInterfaces[0].id" \
    --output tsv
```

based on NSG name
```bash
az network nsg rule list \
    --resource-group <resource-group-name> \
    --nsg-name <nsg-name> \
    --output table
```

---

## Overview
This document outlines the steps to set up two Flask applications on Azure. One app is used to add data to a PostgreSQL database, and the other queries data from the database and writes a report to Azure Blob Storage. The setup includes dedicated VMs for each app, an Azure PostgreSQL database, and Azure Blob Storage.

---

## Azure Concepts

### Resource Group
A resource group is a container that holds related resources for an Azure solution. All resources in this setup are grouped under a single resource group for easier management.

### Azure PostgreSQL Database
Azure Database for PostgreSQL is a managed database service that provides high availability, scalability, and security.

### Azure Blob Storage
Azure Blob Storage is a service for storing large amounts of unstructured data, such as text or binary data.

### Virtual Machines (VMs)
Azure Virtual Machines are on-demand, scalable computing resources. Each Flask app runs on its own VM.

### Virtual Network (VNet)
A Virtual Network is a logically isolated network in Azure. It allows secure communication between resources.

**Secure Communication:**

* The VNet allows secure communication between the Azure resources (e.g., VMs, PostgreSQL database, Application Gateway) without exposing them to the public internet.
Resources within the same VNet can communicate directly using private IP addresses.
Controlled Access:

* By using subnets and Network Security Groups (NSGs), you can control inbound and outbound traffic to the resources, ensuring only authorized access.
Integration with Azure Services:

* The PostgreSQL database can be configured to allow access only from the VNet, enhancing security by restricting access to trusted resources.
Scalability:

* As your application grows, you can add more resources (e.g., additional VMs, storage accounts) to the same VNet, ensuring they can communicate securely.

### Azure Active Directory (AAD)
AAD is a cloud-based identity and access management service. It is used to manage access to Azure resources.

---

## Step-by-Step Setup

### Step 1: Install and Configure Azure CLI
1. Install Azure CLI:
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```
   For Windows, download and install from [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows).

2. Log in to Azure:
   ```bash
   az login
   ```

3. Set your subscription:
   ```bash
   az account set --subscription "<your-subscription-id>"
   ```

### Step 2: Create Azure Resources

#### 2.1 Create Azure PostgreSQL Database
1. Create a resource group:
   ```bash
   az group create --name g2p2-rg --location northeurope
   ```

2. Create a PostgreSQL flexible server:
   ```bash
   az postgres flexible-server create \
       --resource-group g2p2-rg \
       --name g2p2-postgres-db \
       --admin-user adminuser \
       --admin-password <your-password> \
       --location northeurope \
       --public-access 0.0.0.0
   ```

   **(optional)**
   ```bash
   az postgres flexible-server firewall-rule create \
        --resource-group <resource-group-name> \
        --name <server-name> \
        --rule-name AllowIP1 \
        --start-ip-address 203.0.113.1 \
        --end-ip-address 203.0.113.1
    ```

3. Note the connection string:
   ```bash
   az postgres flexible-server show-connection-string --server-name g2p2-postgres-db
   ```

#### 2.2 Create Azure Blob Storage
1. Create a storage account with hierarchical namespace enabled:
   ```bash
   az storage account create \
       --name g2p2-sa \
       --resource-group g2p2-rg \
       --location northeurope \
       --sku Standard_LRS \
       --kind StorageV2 \
       --hns true
   ```

2. Create a container for storing reports:
   ```bash
   az storage container create \
       --account-name g2p2-sa \
       --name reports
   ```

#### 2.3 Create Virtual Machines
1. Create a Virtual Network:
   ```bash
   az network vnet create \
       --resource-group g2p2-rg \
       --name g2p2-vnet \
       --address-prefix 10.0.0.0/16 \
       --subnet-name g2p2-subnet \
       --subnet-prefix 10.0.1.0/24
   ```

2. Create two VMs:
   ```bash
   az vm create \
       --resource-group g2p2-rg \
       --name g2p2-app1-vm \
       --image UbuntuLTS \
       --vnet-name g2p2-vnet \
       --subnet g2p2-subnet \
       --admin-username azureuser \
       #--generate-ssh-keys \
       --ssh-key-values ~/.ssh/id_ed25519.pub \
       --size Standard_B2s
       --location northeurope

   az vm create \
       --resource-group g2p2-rg \
       --name g2p2-app2-vm \
       --image UbuntuLTS \
       --vnet-name g2p2-vnet \
       --subnet g2p2-subnet \
       --admin-username azureuser \
       #--generate-ssh-keys \
       --ssh-key-values ~/.ssh/id_ed25519.pub \
       --size Standard_B2s
       --location northeurope
   ```

3. Open HTTP ports for the VMs:
   ```bash
   az vm open-port --resource-group g2p2-rg --name g2p2-app1-vm --port 80
   az vm open-port --resource-group g2p2-rg --name g2p2-app2-vm --port 80
   ```

### Step 3: Configure Networking
1. Ensure the VMs can communicate with the database:
   ```bash
   az postgres flexible-server vnet-rule create \
       --resource-group g2p2-rg \
       --server g2p2-postgres-db \
       --name g2p2-vnet-rule \
       --vnet g2p2-vnet \
       --subnet g2p2-subnet
   ```

2. Secure the VMs with NSGs:
   ```bash
   az network nsg rule create \
       --resource-group g2p2-rg \
       --nsg-name g2p2-app1-vmNSG \
       --name AllowSSH \
       --priority 1000 \
       --access Allow \
       --protocol Tcp \
       --direction Inbound \
       --source-address-prefixes '*' \
       --source-port-ranges '*' \
       --destination-address-prefixes '*' \
       --destination-port-ranges 22

   az network nsg rule create \
       --resource-group g2p2-rg \
       --nsg-name g2p2-app1-vmNSG \
       --name AllowHTTP \
       --priority 1001 \
       --access Allow \
       --protocol Tcp \
       --direction Inbound \
       --source-address-prefixes '*' \
       --source-port-ranges '*' \
       --destination-address-prefixes '*' \
       --destination-port-ranges 80

   az network nsg rule create \
       --resource-group g2p2-rg \
       --nsg-name g2p2-app1-vmNSG \
       --name AllowFlask \
       --priority 1002 \
       --access Allow \
       --protocol Tcp \
       --direction Inbound \
       --source-address-prefixes '*' \
       --source-port-ranges '*' \
       --destination-address-prefixes '*' \
       --destination-port-ranges 5000
   ```

3. Allow access to Blob Storage:
   - Assign roles to users or groups for accessing the storage account:
     ```bash
     az role assignment create \
         --assignee <user-or-group-id> \
         --role "Storage Blob Data Contributor" \
         --scope /subscriptions/<subscription-id>/resourceGroups/g2p2-rg/providers/Microsoft.Storage/storageAccounts/g2p2-sa
     ```

---

### Step 6: Use Azure Application Gateway as a Reverse Proxy
1. Create an Application Gateway:
   ```bash
   az network application-gateway create \
       --resource-group g2p2-rg \
       --name g2p2-app-gateway \
       --sku Standard_v2 \
       --capacity 2 \
       --vnet-name g2p2-vnet \
       --subnet g2p2-subnet \
       --frontend-port 80 \
       --http-settings-port 5000 \
       --http-settings-protocol Http \
       --routing-rule-type Basic \
       --location northeurope
   ```

2. Add backend pools for the VMs:
   ```bash
   az network application-gateway address-pool create \
       --gateway-name g2p2-app-gateway \
       --resource-group g2p2-rg \
       --name app1-backend-pool \
       --servers <app1-vm-private-ip>

   az network application-gateway address-pool create \
       --gateway-name g2p2-app-gateway \
       --resource-group g2p2-rg \
       --name app2-backend-pool \
       --servers <app2-vm-private-ip>
   ```

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
       --port 5000 \
       --protocol Http

   az network application-gateway rule create \
       --gateway-name g2p2-app-gateway \
       --resource-group g2p2-rg \
       --name app1-rule \
       --http-listener app1-listener \
       --rule-type Basic \
       --http-settings app1-http-settings \
       --address-pool app1-backend-pool

   az network application-gateway rule create \
       --gateway-name g2p2-app-gateway \
       --resource-group g2p2-rg \
       --name app2-rule \
       --http-listener app2-listener \
       --rule-type Basic \
       --http-settings app2-http-settings \
       --address-pool app2-backend-pool
   ```

4. Access the apps through the Application Gateway's public IP address.

---

## Conclusion
This document provides a comprehensive guide to setting up Azure resources for two Flask applications. Follow the steps to ensure a secure and scalable deployment.