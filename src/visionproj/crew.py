from together import Together
import os
import sys
from pathlib import Path
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import logging
import openai
import yaml
from dotenv import load_dotenv
load_dotenv()
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.storage.knowledge_storage import KnowledgeStorage

# from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
# from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
# from crewai.memory.storage.rag_storage import RAGStorage
# from typing import List, Optional

# 1. Long-term Memory: Persistent storage using SQLite
# 2. Short-term Memory: RAG-based memory for recent context
# 3. Entity Memory: Tracks and maintains information about specific entities
# # print(getsource(RAGStorage))

# crew storage directory path
#crewai_storage_dir = os.getenv("CREWAI_STORAGE_DIR")
#print(crewai_storage_dir)  # Should output: D:/crewai_storage or D:\crewai_storage

openai.api_key = os.getenv("OPENAI_API_KEY")


embedder_config={
            "provider": "openai",
            "config": {
                "model": "text-embedding-ada-002",
                "api_key": os.environ["OPENAI_API_KEY"],
            }
        }

# Define the data directory for memory storage
#long term sqlite db [for short term and entity memory we need different directiry]
# Path for the long-term memory SQLite database
# long_term_memory_db_path = "D:/crewai_storage/long_term_memory.db"

# # Define Long-Term Memory storage
# long_term_memory = LongTermMemory(
#     storage=LTMSQLiteStorage(db_path=long_term_memory_db_path)  # Long-term memory storage
# )


text_source = TextFileKnowledgeSource(
    file_paths=["Businessrulex.txt"],
    storage=KnowledgeStorage(
        collection_name="text_file_rules",
        embedder=embedder_config
        )
)


# Create an LLM with a temperature of 0 to ensure deterministic outputs
llm = LLM(model="gpt-4o-mini", temperature=0)

# Define Short-Term Memory
# short_term_memory = ShortTermMemory(
#     storage=RAGStorage(type="short_term"),
#     embedder_config=embedder_config,
#     path=f"{crewai_storage_dir}/short_term_memory.db"  # Specify path for short-term memory
# )



@CrewBase
class Visionproj():
    """Visionproj crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    @agent
    def reviewagent(self) -> Agent:   
        logging.info(f"Initializing Review Agent")
        return Agent(
            config=self.agents_config['reviewagent'],
            verbose=True,
            # memory=True,
            #short_term_memory=short_term_memory,
            # long_term_memory=long_term_memory,
            # llm=llm,
        )
        
    @agent
    def claimagent(self) -> Agent:   
        logging.info(f"Initializing Agent with knowledge sources: {text_source}") 
        return Agent(
            config=self.agents_config['claimagent'],
            knowledge_sources=[text_source],
            verbose=True,
            # memory=True,
            #short_term_memory=short_term_memory,
            # long_term_memory=long_term_memory,
            # llm=llm,
            embedder=embedder_config
        )
        
    @agent
    def finalagent(self) -> Agent:   
        return Agent(
            config=self.agents_config['finalagent'],
            knowledge_sources=[text_source],
            verbose=True,
            # memory=True,
            #short_term_memory=short_term_memory,
            # long_term_memory=long_term_memory,
            # llm=llm,
        )

    @task
    def reviewtask(self) -> Task:
        return Task(
            config=self.tasks_config['reviewtask'],
            verbose=True,
            #memory=True,
            output_file="review.md"
        )
    
    @task
    def claimtask(self) -> Task:
        logging.debug(f"Loaded Knowledge Source: {text_source}")
        logging.debug(f"Knowledge sources: {text_source.__dict__}")  # This should show the content and usage
    
        return Task(
            config=self.tasks_config['claimtask'],
            verbose=True,
            #memory=True,
            output_file="output.md"
        )
        
    @task
    def finaltask(self) -> Task:
        return Task(
            config=self.tasks_config['finaltask'],
            verbose=True,
            #memory=True,
            output_file="final.md"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Visionproj crew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            #memory = True,
            # short_term_memory=short_term_memory,
            #long_term_memory=long_term_memory,
            knowledge_sources=[text_source],
            embedder=embedder_config,    
        )

