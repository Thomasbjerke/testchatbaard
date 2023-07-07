import os
import json
from enum import Enum
from .azureblobstorage import AzureBlobStorageClient

CONFIG_CONTAINER_NAME = "config"

class ChunkingStrategy(Enum):
    LAYOUT = 'layout'
    PAGE = 'page'
    FIXED_SIZE_OVERLAP = 'fixed_size_overlap'
    PARAGRAPH = 'paragraph'

class Config:
    def __init__(self, config: dict):
        self.prompts = Prompts(config['prompts'])
        self.messages = Messages(config['messages'])
        self.chunking = [Chunking(x) for x in config['chunking']]
        self.logging = Logging(config['logging'])

class Prompts:
    def __init__(self, prompts: dict):
        self.condense_question_prompt = prompts['condense_question_prompt']
        self.answering_prompt = prompts['answering_prompt']
        self.post_answering_prompt = prompts['post_answering_prompt']
        
class Messages:
    def __init__(self, messages: dict):
        self.post_answering_filter = messages['post_answering_filter']

class Chunking:
    def __init__(self, chunking:dict):
        self.chunking_strategy = ChunkingStrategy(chunking['strategy'])
        self.chunk_size = chunking['size']
        self.chunk_overlap = chunking['overlap']

class Logging:
    def __init__(self, logging: dict):
        self.log_user_interactions = logging['log_user_interactions']
        self.log_tokens = logging['log_tokens']
        
class ConfigHelper:
    @staticmethod
    def get_active_config_or_default():
        try:
            blob_client = AzureBlobStorageClient(container_name=CONFIG_CONTAINER_NAME)
            config = blob_client.download_file("active.json")
            config = Config(json.loads(config))
        except: 
            print("Returning default config")
            config = ConfigHelper.get_default_config()
        return config 
    
    @staticmethod
    def save_config_as_active(config):
        blob_client = AzureBlobStorageClient(container_name=CONFIG_CONTAINER_NAME)
        blob_client = blob_client.upload_file(json.dumps(config, indent=2), "active.json", content_type='application/json')
        
    @staticmethod
    def get_default_config():
        default_config = {
            "prompts": {
                "condense_question_prompt": """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:""",
                "answering_prompt": """Context:
{summaries}

Please reply to the question using only the information Context section above. If you can't answer a question using the context, reply politely that the information is not in the knowledge base. DO NOT make up your own answers. You detect the language of the question and answer in the same language.  If asked for enumerations list all of them and do not invent any.

The context is structured like this:

Content:  <information>
Source: [url/to/file.pdf](url/to/file.pdf_SAS_TOKEN_PLACEHOLDER_)
<and more of them>

When you give your answer, you ALWAYS MUST include the source in your response in the following format: <answer> [[file.pdf]]
Always use double square brackets to reference the filename source, e.g. [[file.pdf]]. When using multiple sources, list each source separately, e.g. [[file1.pdf]][[file2.pdf]].

Question: {question}
Answer:""",
                "post_answering_prompt": """You help fact checking if the given answer for the question below is aligned to the sources. If the answer is correct, then reply with "True", if the answer is not correct, then reply with "False". DO NOT ANSWER with anything else.

Sources:
{summaries}

Question: {question}
Answer: {answer}""",
                },
            "messages": {
                "post_answering_filter": "I'm sorry, but I can't answer this question correctly. Please try again by altering or rephrasing your question."
            },
            "chunking": [{
                "strategy": ChunkingStrategy.FIXED_SIZE_OVERLAP,
                "size": 500,
                "overlap": 100
                }],
            "logging": {
                "log_user_interactions": True,
                "log_tokens": True
            }
        }
        return Config(default_config)