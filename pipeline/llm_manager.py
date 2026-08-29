import os
import sys
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Add parent directory to import pipeline_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pipeline_config

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages connection and query execution to the custom OpenAI-compatible API using LangChain."""
    
    def __init__(self, temperature: float = None):
        # Verify configuration
        if not getattr(pipeline_config, "API_KEY", None):
            raise ValueError("API_KEY not found in pipeline_config.py")

        if temperature is None:
            temperature = getattr(pipeline_config, "LLM_TEMPERATURE", 0.3)

        self.temperature = temperature
        logger.info(f"Connecting to LLM server at {pipeline_config.API_BASE_URL} using model '{pipeline_config.MODEL_NAME}' (temperature={self.temperature})...")

        self.llm = ChatOpenAI(
            openai_api_base=pipeline_config.API_BASE_URL,
            openai_api_key=pipeline_config.API_KEY,
            model_name=pipeline_config.MODEL_NAME,
            temperature=self.temperature,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        
    def process_node(self, system_prompt: str, user_content: str, max_retries: int = 3) -> str:
        """Executes a structured query prompt against the LLM with automatic retries for transient server errors."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{content}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Sending request to LLM (Attempt {attempt}/{max_retries})...")
                result = chain.invoke({"content": user_content})
                if not result or not str(result).strip():
                    raise ValueError("LLM returned an empty response.")
                return str(result).strip()
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_retries} failed querying LLM server: {e}")
                if attempt < max_retries:
                    sleep_time = attempt * 5
                    logger.info(f"Retrying LLM call in {sleep_time} seconds...")
                    import time
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All {max_retries} attempts to query LLM server failed.")
                    raise e
