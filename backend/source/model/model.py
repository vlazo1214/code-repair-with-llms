from transformers import AutoTokenizer
from typing import Dict, Any, Optional
import json
import os
import logging
from pathlib import Path
import litellm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Model:
    def __init__(self, model: Optional[str], api_key: Optional[str], provider: Optional[str], test: bool = False) -> None:
        logger.info("Initializing Model class")
        # retrieves the config path and creates list of model configs
        self.config_path: Path = self._get_config_path()
        logger.debug(f"Config path set to: {self.config_path}")
        self.model_configs: Dict[str, Any] = self._load_model_configs()

        # if test true then set model to test model
        if test:
            logger.info("Initializing in test mode")
            self.model: str = "meta-llama/llama-3-8b-instruct:free"
            self.provider: str = "openrouter"
            self.api_key: str = os.getenv("OPENROUTER_API_KEY", 
                "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")
            logger.debug(f"Test mode settings - Model: {self.model}, Provider: {self.provider}")
        else:
            logger.info("Initializing in production mode")
            self.model = model if model is not None else ""
            self.provider = provider if provider is not None else ""
            self.api_key = api_key if api_key is not None else ""
            logger.debug(f"Production settings - Model: {self.model}, Provider: {self.provider}")

        # Common initialization for both test and non-test cases
        try:
            logger.debug("Starting common initialization")
            self.current_config: Dict[str, Any] = self._get_model_config(self.model)
            self.tokenizer: AutoTokenizer = self.get_tokenizer()
            self.client: Dict[str, str] = self.initialize_client()
            self.max_context: int = self.current_config.get("max_context", 0)
            self.max_response: int = self.current_config.get("max_response", 0)
            logger.debug(f"Initialized with max_context: {self.max_context}, max_response: {self.max_response}")
        except Exception as e:
            logger.error(f"Error during model initialization: {str(e)}")
            raise

    def _get_config_path(self) -> Path:
        logger.debug("Getting config path")
        return Path(__file__).parent / "model_configs.json"

    def _load_model_configs(self) -> Any:
        logger.debug(f"Loading model configs from {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                configs = json.load(f)
                logger.info("Successfully loaded model configs")
                return configs
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid configuration file: {str(e)}")
            raise ValueError(f"Invalid configuration file: {str(e)}")

    def _get_model_config(self, model: str) -> Any:
        logger.debug(f"Getting configuration for model: {model}")
        if model not in self.model_configs.get("models", {}):
            logger.error(f"Unsupported model: {model}")
            raise ValueError(f"Unsupported model: {model}")
        logger.debug("Successfully retrieved model configuration")
        return self.model_configs["models"][model]

    def get_tokenizer(self) -> AutoTokenizer:
        logger.debug("Initializing tokenizer")
        try:
            tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
            logger.info("Successfully initialized tokenizer")
            return tokenizer
        except Exception as e:
            logger.error(f"Failed to initialize tokenizer: {str(e)}")
            raise RuntimeError(f"Failed to initialize tokenizer: {str(e)}")

    def initialize_client(self) -> Dict[str, str]:
        logger.debug(f"Initializing client for provider: {self.provider}")
        provider_configs: Dict[str, Dict[str, str]] = {
            "openrouter": {"base_url": "https://openrouter.ai/api/v1", "model_prefix": "openrouter/"},
            "fireworks": {"base_url": "https://api.fireworks.ai/inference/v1", "model_prefix": "fireworks_ai/"},
            "openai": {"base_url": "https://api.openai.com/v1", "model_prefix": ""},
            "huggingface": {"base_url": "https://api-inference.huggingface.co/models", "model_prefix": "huggingface/"}
        }

        if self.provider not in provider_configs:
            logger.error(f"Unsupported provider: {self.provider}")
            raise ValueError(f"Unsupported provider: {self.provider}")

        config = provider_configs[self.provider]
        litellm.api_key = self.api_key
        logger.info(f"Successfully initialized client for provider: {self.provider}")
        
        return {
            "api_key": self.api_key,
            "base_url": config["base_url"],
            "model_prefix": config["model_prefix"]
        }

    def generate_response(self, prompt: str) -> str:
        logger.debug("Starting response generation")
        if not self.client:
            logger.error("Missing client configuration")
            return "Error: Client configuration is required."
        
        try:
            formatted_model = f"{self.client['model_prefix']}{self.model}"
            logger.debug(f"Using formatted model name: {formatted_model}")
            
            logger.debug("Sending completion request to model")
            response = litellm.completion(
                model=formatted_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.client["api_key"]
            )
            
            result = response.choices[0].message.content if response.choices else ""
            if result:
                logger.info("Successfully generated response")
            else:
                logger.warning("Generated empty response")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"

    def get_token_count(self, text: str) -> int:
        logger.debug("Calculating token count")
        try:
            count = len(self.tokenizer.encode(text))
            logger.debug(f"Token count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error calculating token count: {str(e)}")
            raise

    def is_within_context_window(self, text: str) -> bool:
        logger.debug("Checking if text is within context window")
        try:
            token_count = self.get_token_count(text)
            result = token_count <= self.max_context
            logger.debug(f"Token count {token_count} {'is' if result else 'is not'} within context window of {self.max_context}")
            return result
        except Exception as e:
            logger.error(f"Error checking context window: {str(e)}")
            raise

    def is_within_response_window(self, text: str) -> bool:
        logger.debug("Checking if text is within response window")
        try:
            token_count = self.get_token_count(text)
            result = token_count <= self.max_response
            logger.debug(f"Token count {token_count} {'is' if result else 'is not'} within response window of {self.max_response}")
            return result
        except Exception as e:
            logger.error(f"Error checking response window: {str(e)}")
            raise
