# """
# title: Azure OpenAI Knowledge Retrieval Pipeline
# author: open-webui
# date: 2024-11-26
# version: 1.0
# license: MIT
# description: A pipeline for retrieving relevant information from an Azure-based knowledge base and synthesizing it using OpenAI's GPT model.
# requirements:  azure-search-documents, azure-identity, azure-cosmos
# test
# """

# import os
# import uuid
# from typing import List, Union, Generator, Iterator
# from azure.search.documents import SearchClient
# from azure.core.credentials import AzureKeyCredential
# from azure.search.documents.models import VectorQuery
# from azure.cosmos import CosmosClient
# from openai import AzureOpenAI
# from dotenv import load_dotenv


# class Pipeline:
#     def __init__(self):

#         pass
       

#     async def on_startup(self):
#         # Set the OpenAI API key
#         self.search_client = SearchClient(
#                 endpoint=os.getenv("AZURE_SEARCH_URI"),
#                 index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
#                 credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
#         )
        
#         # # Set up OpenAI client
#         # self.client = AzureOpenAI(
#         #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         #     api_key=os.getenv("AZURE_OPENAI_API_KEY") ,
#         #     api_version="2024-08-01-preview"
#         # )
        
#         # Set up Cosmos DB client
#         # cosmos_db_uri = os.getenv("COSMOS_DB_URI")
#         # cosmos_db_key = os.getenv("COSMOS_DB_KEY")
#         # cosmos_db_name = os.getenv("cosmos_db_controls")
#         # cosmos_db_container = os.getenv("cosmos_db_container")
        
#         # cosmos_client = CosmosClient(url=cosmos_db_uri, credential=cosmos_db_key)
#         # database = cosmos_client.get_database_client(database=cosmos_db_name)
#         # self.container = database.get_container_client(container=cosmos_db_container)
#         pass

#     async def on_shutdown(self):
#         # This function is called when the server is stopped.
#         pass

#     def pipe(
#         self, user_message: str, model_id: str, messages: List[dict], body: dict
#     ) -> Union[str, Generator, Iterator]:
        
#         load_dotenv()
        
#         # Set up Azure Search client
#         try :
#             search_client = SearchClient(
#                     endpoint=os.getenv("AZURE_SEARCH_URI"),
#                     index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
#                     credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
#             )
#             msg= "Search client initialized successfully"
#         except Exception as e:
#             msg= f"Error initializing SearchClient: {e}"

#         try:
#             self.client = AzureOpenAI(
#                 azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#                 api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#                 api_version="2024-08-01-preview"
#             )
#             msg1= "Azure OpenAI client initialized successfully"
#         except Exception as e:
#             msg1=f"Error initializing AzureOpenAI client: {e}"
#         """
#         This method retrieves relevant information from the Azure knowledge base, 
#         and uses OpenAI's GPT model to synthesize the response.
#         """
#         print(f"User message: {user_message}")
        
#         # Step 1: Search for relevant documents from Azure Search
#         # #vector_query = VectorQuery(vector=user_message, fields="text_vector", k_nearest_neighbors=5, kind="vector")
#         # try:
#         # # Perform the search operation
#         search_results = self.search_client.search(
#                 search_text=user_message,
#                 query_type="semantic",
#                 select=["title", "chunk"],
#                 semantic_configuration_name="vector-indexturbosa-semantic-configuration",
#                 top=5
#             )
            

#         # # Format search results to pass as context for GPT
#         used_sources = []
#         sources_formatted = "\n=================\n".join(
#             [
#                 f"FILE: {document['title']}\nCONTENT: {document['chunk']}"
#                 for document in search_results
#                 if used_sources.append((document['title'], document.get("@search.score", 0))) or True
#             ])
        
#         # # Step 2: Use GPT to synthesize the response from the retrieved information
#         sys_prompt = f"""
#         You are an expert in security controls and help people identify relevant controls for their situation based on document text.
        
#         DOCUMENT TEXT: {sources_formatted}
#         """
        
#         chat_prompt = [
#             {
#                 "role": "system",
#                 "content": sys_prompt
#             },
#             {
#                 "role": "user",
#                 "content": user_message
#             }
#         ]
        
#         # # Step 3: Call OpenAI's GPT model to generate a response
#         completion = self.client.chat.completions.create(
#             model="gpt-4o",
#             messages=chat_prompt,
#             max_tokens=800,
#             temperature=0.7,
#             top_p=0.95
#         )

#         gpt_result = completion.choices[0].message.content
#         # Append the titles and relevant scores at the bottom of the response
#         source_list = "\n".join(
#             [f"- {title} (Score: {score:.2f})" for title, score in set(used_sources)]
#         )
#         gpt_result += f"\n\n---\nSources used:\n{source_list}"
        
#         return gpt_result

import os
import re
from typing import List, Union, Generator, Iterator
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv


class Pipeline:
    def __init__(self):
        pass

    async def on_startup(self):
        load_dotenv()
        self.client_cosmosdb = CosmosClient(
                os.getenv("COSMOS_DB_URI"),
                os.getenv("COSMOS_DB_KEY")
            )
        self.database = self.client_cosmosdb.get_database_client(os.getenv("COSMOS_DB_NAME"))
        self.container = self.database.get_container_client(os.getenv("COSMOS_DB_CONTAINER"))

        self.client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-08-01-preview"
            )
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_URI"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )


 



    async def on_shutdown(self):
        pass

    def fetch_cosmos_data(self, family: str, control_id: str):

        query = f"SELECT * FROM c WHERE c.Family = '{family}' AND c.ControlID = '{control_id}'"
        results = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        return results[0] if results else None

    def extract_family_and_control_id (self, message: str):
        # Extract Family
        family_match = re.search(r"(Family|family):\s*([A-Za-z]+)", message)
        # Extract Control ID
        control_id_match = re.search(r"(ControlID|controlid|ID|id):\s*(\d+)", message)


        family = family_match.group(2) if family_match else None
        control_id = control_id_match.group(2) if control_id_match else None


        return family, control_id

    def run_search(self, query_text: str):
        search_results = self.search_client.search(
            search_text=query_text,
            query_type="semantic",
            select=["title", "chunk"],
            semantic_configuration_name="vector-indexturbosa-semantic-configuration",
            top=5,
        )
        sources_formatted = "\n=================\n".join(
            [
                f"FILE: {document['title']}\nCONTENT: {document['chunk']}"
                for document in search_results
            ]
        )
        source_list = "\n".join(
            [f"- {document['title']} (Score: {document['@search.score']:.2f})" for document in search_results]
        )
        return sources_formatted, source_list

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        
        
        # Extract Family and ControlID from user message
        family, control_id = self.extract_family_and_control_id(user_message)

        if family and control_id:
            control_data = self.fetch_cosmos_data(family, control_id)
            if control_data:
                control_name = control_data["Name"]
                generated_questions = control_data["GeneratedQuestions"].split("\n")  # List of questions

                # Limit to the first 3 questions if they exist
                first_questions = generated_questions[:1]
        return first_questions

            #     all_answers = []

            #     # Loop through the first 3 questions, sending one by one to the chat
            #     for question in first_questions:
            #         question = question.strip()  # Clean any leading/trailing spaces

            #         if question:  # Skip empty questions if any
            #             # Construct the search query for the specific question
            #             search_query = f"{control_name} {question}"

            #             # Perform search with both control name and question for specific chunks
            #             search_results, source_list = self.run_search(search_query)

            #             sys_prompt = f"""
            #             You are an expert in security controls. Respond to the following question based on the provided control and document text.

            #             CONTROL NAME: {control_name}
            #             DOCUMENT TEXT: {search_results}
            #             QUESTION: {question}
            #             """

            #             chat_prompt = [
            #                 {"role": "system", "content": sys_prompt},
            #                 {"role": "user", "content": question},
            #             ]

            #             # Get the answer for the current question
            #             completion = self.client.chat.completions.create(
            #                 model="gpt-4o",
            #                 messages=chat_prompt,
            #                 max_tokens=800,
            #                 temperature=0.7,
            #                 top_p=0.95
            #             )

            #             # Retrieve the response and store it
            #             gpt_result = completion["choices"][0]["message"]["content"]

            #             # Store the result as a tuple (question, answer)
            #             all_answers.append(f"**Q: {question}**\nA: {gpt_result}\n")

            #     # Combine all the answers into a single response
            #     final_response = "\n".join(all_answers)

            #     # Add sources at the end
            #     final_response += f"\n\n---\nSources used:\n{source_list}"

            #     return final_response
        else:
            return f"No control data found for Family: '{family}' and ControlID: '{control_id}'."
            
        # else:
        #     # If no family and control_id are provided, fall back to regular search
        #     search_results, source_list = self.run_search(user_message)
        #     sys_prompt = f"""
        #     You are a semantic search assistant. Respond to the user’s query with relevant information from the retrieved content.

        #     DOCUMENT TEXT: {search_results}
        #     """
        #     chat_prompt = [
        #         {"role": "system", "content": sys_prompt},
        #         {"role": "user", "content": user_message},
        #     ]

        #     completion = self.client.chat.completions.create(
        #         model="gpt-4o",
        #         messages=chat_prompt,
        #         max_tokens=800,
        #         temperature=0.7,
        #         top_p=0.95,
        #     )

        #     gpt_result = completion.choices[0].message.content
        #     gpt_result += f"\n\n---\nSources used:\n{source_list}"
        #     return gpt_result