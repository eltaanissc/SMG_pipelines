"""
title: Azure OpenAI Knowledge Retrieval Pipeline
author: open-webui
date: 2024-11-26
version: 1.0
license: MIT
description: A pipeline for retrieving relevant information from an Azure-based knowledge base and synthesizing it using OpenAI's GPT model.
requirements: azure-ai-openai, azure-search-documents, azure-identity, azure-cosmos
"""

import os
import uuid
from typing import List, Union, Generator, Iterator
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorQuery
from azure.cosmos import CosmosClient
from openai import AzureOpenAI


class Pipeline:
    def __init__(self):
        self.search_client = None
        self.client = None
        self.documents = None
        self.conversation_id = None
        self.container = None

    async def on_startup(self):
        # Set the OpenAI API key
       # os.environ["AZURE_OPENAI_API_KEY"] = "https://scsccps-dsai-lab-dev-eastus-oai.openai.azure.com/"
       # os.environ["AZURE_OPENAI_ENDPOINT"] = '321ed4fcf1164d4eb751d089247520f6'
        
        # Set up Azure Search client
        self.search_client = SearchClient(
            endpoint="https://scsccps-dsai-turbosa-ais.search.windows.net",
            index_name="vector-indexturbosa",
            credential=AzureKeyCredential("40rAGgOU74ViVnMvFPH56HI6e4UfNQwF03qXeYqgXYAzSeC92785")
        )
        
        # Set up OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint="https://scsccps-dsai-lab-dev-eastus-oai.openai.azure.com/",
            api_key="321ed4fcf1164d4eb751d089247520f6",
            api_version="2024-08-01-preview"
        )
        
        # Set up Cosmos DB client
        cosmos_db_uri = "https://scscdsaiturbosacd.documents.azure.com:443/"
        cosmos_db_key = "Hn9yPCspaA2z8ddDM18IWG5b8tNFhzPFqPgGLcIEdgh2vVKFncoJ2bqXLnhY5g83ZzZnfI0yj8CgACDbhgFYiA=="
        cosmos_db_name = "cosmos_db_controls"
        cosmos_db_container = "control_history"
        
        cosmos_client = CosmosClient(url=cosmos_db_uri, credential=cosmos_db_key)
        database = cosmos_client.get_database_client(database=cosmos_db_name)
        self.container = database.get_container_client(container=cosmos_db_container)

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        This method retrieves relevant information from the Azure knowledge base, 
        and uses OpenAI's GPT model to synthesize the response.
        """
        print(f"User message: {user_message}")
        
        # Step 1: Search for relevant documents from Azure Search
        #vector_query = VectorQuery(vector=user_message, fields="text_vector", k_nearest_neighbors=5, kind="vector")
        search_results = self.search_client.search(
            search_text=user_message,
            query_type="semantic",
            select=["title", "chunk"],
            semantic_configuration_name="vector-indexturbosa-semantic-configuration",
            top=5
        )
        
        # Format search results to pass as context for GPT
        sources_formatted = "\n=================\n".join([f"TITLE: {document['title']}, CONTENT: {document['chunk']}" for document in search_results])
        
        # Step 2: Use GPT to synthesize the response from the retrieved information
        sys_prompt = f"""
        You are an expert in security controls and help people identify relevant controls for their situation based on document text.
        
        DOCUMENT TEXT: {sources_formatted}
        """
        
        chat_prompt = [
            {
                "role": "system",
                "content": sys_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        # Step 3: Call OpenAI's GPT model to generate a response
        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=chat_prompt,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95
        )

        gpt_result = completion.choices[0].message.content
        print("GPT response:", gpt_result)

        # Step 4: Store the response in Cosmos DB (optional)
        self.conversation_id = str(uuid.uuid4())
        self.container.create_item(body={"id": self.conversation_id, "content": gpt_result})

        return gpt_result
