"""
title: Azure OpenAI Knowledge Retrieval Pipeline
author: open-webui
date: 2024-11-26
version: 1.0
license: MIT
description: A pipeline for retrieving relevant information from an Azure-based knowledge base and synthesizing it using OpenAI's GPT model.
requirements:  azure-search-documents,  azure-cosmos

"""


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
        try:
            self.client_cosmosdb = CosmosClient(
                os.getenv("COSMOS_DB_URI"),
                os.getenv("COSMOS_DB_KEY")
            )
            print("Connected to Cosmos DB successfully.")
            
            self.database = self.client_cosmosdb.get_database_client(os.getenv("COSMOS_DB_NAME"))
            self.container = self.database.get_container_client(os.getenv("COSMOS_DB_CONTAINER"))
            print("Cosmos DB container connection successful.")
            
        except Exception as e:
            print(f"Failed to connect to Cosmos DB: {e}")

        try:
            self.client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-08-01-preview"
            )
            print("Connected to Azure OpenAI successfully.")
        except Exception as e:
            print(f"Failed to connect to Azure OpenAI: {e}")
        
        try:
            self.search_client = SearchClient(
                endpoint=os.getenv("AZURE_SEARCH_URI"),
                index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
                credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
            )
            print("Connected to Azure Search successfully.")
        except Exception as e:
            print(f"Failed to connect to Azure Search: {e}")

    async def on_shutdown(self):
        pass

    def fetch_cosmos_data(self, family: str, control_id: str):
        query = f"SELECT * FROM c WHERE c.Family = '{family}' AND c.ControlID = '{control_id}'"
        try:
            results = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            if results:
                print(f"Query successful: {len(results)} item(s) retrieved.")
                return results[0]
            else:
                print("Query executed, but no results found.")
                return None
        except Exception as e:
            print(f"Error executing query: {e}")
            return None




    def extract_family_and_control_id(self, message: str):
        # Extract Family (allow Family: AC and similar patterns)
        family_match = re.search(r"(Family|family):\s*([A-Za-z0-9\-]+)", message)
        
        # Extract Control ID (allow ControlID: 1 and similar patterns)
        control_id_match = re.search(r"(ControlID|controlid|ID|id):\s*(\d+)", message)
        
        # If matches found, extract the values
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

        # If search_results is not already a list, convert it into one
        if not isinstance(search_results, list):
            search_results = list(search_results)

        # Remove extra blank spaces between words in the chunk using regex
        for document in search_results:
            document['chunk'] = re.sub(r'\s+', ' ', document['chunk']).strip()

            
        sources_formatted = "\n=================\n".join(
            [
                f"FILE: {document['title']}\nCONTENT: {document['chunk']}"
                for document in search_results
            ]
        )

        # Sort by score in descending order and take the top three
        top_results = sorted(search_results, key=lambda doc: doc['@search.score'], reverse=True)[:3]

        
        # Formatting to lowercase and bold using ANSI escape codes
        source_list = "\n\n".join(
            [
                f"**title:** {document['title'].lower()}\n"
                f"**score:** {document['@search.score']:.2f}\n"
                f"**related text starts from:** {' '.join(document['chunk'].lower().split()[:20])}..."
                for document in top_results
            ]
        )

        source_list = "\n".join(
            [f"- {document['title']} (Score: {search_results['@search.score']}:.2f)" for document in search_results]
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
                    generated_questions = [q.strip() for q in generated_questions if q.strip()]       

                    all_answers = []

                    # Loop through the first 3 questions, sending one by one to the chat
                    for question in generated_questions:
                            question = question.strip()  # Clean any leading/trailing spaces
                            
                            if question:  # Skip empty questions if any
                                # Construct the search query for the specific question
                                search_query = f"{control_name} {question}"

                                # Perform search with both control name and question for specific chunks
                                search_results, source_list = self.run_search(search_query)

                                if  search_results:
                                    
                                    sys_prompt = f"""
                                    You are an expert in security controls. Respond to the following QUESTION based on the provided CONTROL NAME and DOCUMENT TEXT.
                                    Provide the company's name at the beginning. Verify if the QUESTION is answered in the DOCUMENT TEXT. Do not add any unnecessary explanations                                Provied the company's name at the begning. Verify if the  QUESTION was answerd in DOCUMENT TEXT.Don't add any unecessairy explanations.

                                    CONTROL NAME: {control_name}
                                    DOCUMENT TEXT: {search_results}
                                    QUESTION: {question}
                                    """

                                    chat_prompt = [
                                        {"role": "system", "content": sys_prompt},
                                        {"role": "user", "content": question},
                                    ]

                                    # Get the answer for the current question
                                    completion = self.client.chat.completions.create(
                                        model="gpt-4o",
                                        messages=chat_prompt,
                                        max_tokens=800,
                                        temperature=0.7,
                                        top_p=0.95
                                    )

                                    # Retrieve the response and store it
                                    gpt_result = completion.choices[0].message.content
                                    print(f"'{source_list}'")


                                # Store the result as a tuple (question, answer)
                                all_answers.append(f"**Q: {question}**\nA: {gpt_result}\nSources used:\n{source_list}")

                        # Combine all the answers into a single response
                            final_response = f"**Family:'{family}'**\n ControlID:'{control_id}'\n".join(all_answers)

            return f"'{final_response}'"
           
        else:
            # If no family and control_id are provided, fall back to regular search
            search_results, source_list = self.run_search(user_message)
            sys_prompt = f"""
            You are a semantic search assistant. Respond to the user’s query with relevant information from the retrieved DOCUMENT TEXT.
            Provide the company's name at the beginning. Verify if the query is answered in the DOCUMENT TEXT. Do not add any unnecessary explanations  

            DOCUMENT TEXT: {search_results}
            """
            chat_prompt = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_message},
            ]

            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=chat_prompt,
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
            )

            gpt_result = completion.choices[0].message.content
            gpt_result += f"\n\n---\nSources used:\n{source_list}"
            return gpt_result