# TurboSA OpenUIWeb Pipeline Controls Evidence Retrieval

## **Overview**  
This pipeline is designed to integrate Azure's Cosmos DB, Azure Cognitive Search, and OpenAI’s GPT model to retrieve, process, and synthesize relevant information from a knowledge base. It responds to user queries by searching indexed documents, generating answers based on the retrieved content, and returning concise, context-specific responses.

---

## **Purpose**  
TurboSA OpenUIWeb Pipeline Controls Evidence Retrieval allows organizations to:  
- Efficiently retrieve specific information from large, Azure-hosted knowledge repositories.  
- Utilize advanced AI (OpenAI GPT) to generate human-like responses to queries.  
- Support enhanced decision-making by providing precise, document-supported answers.

---

## **Key Components**  

### 1. **Azure Cosmos DB**  
- **Purpose**: Storing structured data, particularly family and control information.  
- **Libraries**:  
  - `azure.cosmos`: Provides connection and querying capabilities for Cosmos DB.  
- **Key Functions**:  
  - `fetch_cosmos_data()`: Executes a query to retrieve records based on the provided Family and ControlID.  

---

### 2. **Azure Cognitive Search**  
- **Purpose**: Retrieves relevant document chunks from a knowledge base using semantic search capabilities.  
- **Libraries**:  
  - `azure.search.documents`: Used to interact with Azure Cognitive Search.  
  - `azure.core.credentials.AzureKeyCredential`: Manages authentication.  
- **Key Functions**:  
  - `run_search()`: Executes a semantic search, formats results, and retrieves top-matching documents.

---

### 3. **OpenAI GPT (via Azure OpenAI Service)**  
- **Purpose**: Synthesizes retrieved data and generates human-readable responses.  
- **Libraries**:  
  - `openai`: Used to interact with the Azure-hosted GPT model.  
- **Key Functions**:  
  - `pipe()`: Handles the primary logic, combining Cosmos DB queries, Azure Search, and OpenAI GPT responses.  

---

## **Pipeline Flow**  
1. **User Query Input**:  
   - Extracts **Family** and **ControlID** if specified in the query.  
   - If no identifiers are detected, defaults to a general semantic search.  
2. **Data Retrieval**:  
   - Queries Cosmos DB for relevant control metadata.  
   - Searches Azure Cognitive Search for document excerpts related to the query.  
3. **Response Generation**:  
   - Constructs a system prompt with retrieved data.  
   - Uses OpenAI GPT to generate answers by analyzing document excerpts.  
   - Returns answers with references to the corresponding documents.

---

## **Requirements**  

### **Python Libraries**  
- `azure-search-documents`  
- `azure-cosmos`  
- `openai`  
- `python-dotenv`  

### **Environment Variables** (via `.env` file)  
- `COSMOS_DB_URI`: Cosmos DB connection URI  
- `COSMOS_DB_KEY`: Cosmos DB access key  
- `COSMOS_DB_NAME`: Database name  
- `COSMOS_DB_CONTAINER`: Container name  
- `AZURE_SEARCH_URI`: Azure Search endpoint  
- `AZURE_SEARCH_KEY`: Azure Search key  
- `AZURE_SEARCH_INDEX_NAME`: Index name used in Azure Search  
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint  
- `AZURE_OPENAI_API_KEY`: API key for Azure OpenAI  

---

## **Usage Instructions**  
1. **Setup Environment**:  
   - Install the necessary Python libraries using:  
     ```bash  
     pip install azure-search-documents azure-cosmos openai python-dotenv  
     ```  
   - Configure environment variables in a `.env` file.  
2. **Run the Pipeline**:  
   - Execute the pipeline script, which connects to Azure services and responds to user queries.  

---

## **Output Format**  
- **Response**:  
  Generated answer based on control metadata and document context.  
- **Sources**:  
  Provides a reference list of document excerpts used in the response.  


# Virtual Machine Setup and Application Installation

## **1. Create a Linux Virtual Machine on Azure Portal**

Follow these steps to create a Linux Virtual Machine (VM) on the Azure Portal:

1. **Log in to Azure Portal**  
   Go to the [Azure Portal](https://portal.azure.com/) and log in with your credentials.

2. **Create a Virtual Machine**  
   - In the Azure Portal, click **"Create a resource"** in the left sidebar.
   - Under **"Compute"**, click **"Virtual Machine"**.
   - Click **"Create"** to start configuring your VM.

3. **Configure Basic Settings for the Virtual Machine**  
   - **Subscription:** Select your subscription.
   - **Resource Group:** Create or select an existing resource group.
   - **Virtual Machine Name:** Provide a name for your VM.
   - **Region:** Choose your preferred region.
   - **Image:** Select a Linux image (e.g., Ubuntu 20.04 LTS).
   - **Size:** Select an appropriate size based on your requirements.
   - **Authentication Type:** Select SSH public key.
   - **Username:** Set a username.
   - **SSH Public Key:** Paste your public SSH key.

4. **Configure Networking Settings**  
   - **Virtual Network:** Select an existing Virtual Network or create a new one.
   - **Subnet:** Select an existing subnet or create a new one.
   - **Public IP:** Ensure a public IP is assigned.
   - **Network Security Group (NSG):** Select **"Basic"** and configure the NSG in the next step.

## **2. Create Network Security Group (NSG) Inbound Port Rules**

To enable the necessary ports for communication with your VM, configure the NSG inbound rules as follows:

1. **Go to Network Security Group**  
   In the Azure portal, search for **"Network Security Group"** in the search bar.

2. **Configure Inbound Port Rules**  
   - Click on your NSG and go to the **"Inbound security rules"** section.
   - Click **"Add"** to create new rules for the following ports:
     - **8080**
     - **3000**
     - **3030**
     - **9090**
     - **6333-6334**
     - **9099**
   
   For each rule, enter the following details:
   - **Source:** Any
   - **Source port ranges:** *
   - **Destination:** Any
   - **Destination port ranges:** Enter one of the above port ranges.
   - **Protocol:** TCP
   - **Action:** Allow
   - **Priority:** Choose a unique priority.
   - **Name:** Provide a name for each rule (e.g., `Allow_8080`, `Allow_3000`, etc.).
   - Click **"Add"** to save each rule.

## **3. Connect to the Virtual Machine via SSH**

To connect to the newly created VM, use the following SSH command:

```bash
ssh -i /path/to/your/private-key.pem username@your-vm-ip-address



