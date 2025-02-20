from transformers import AutoTokenizer
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path
import litellm
from dotenv import load_dotenv

class Model:
    def __init__(self, model: Optional[str], api_key: Optional[str], provider: Optional[str], test: bool = False) -> None:
        # retrieves the config path and creates list of model configs
        self.config_path: Path = self._get_config_path()
        self.model_configs: Dict[str, Any] = self._load_model_configs()

        # load api key from .env
        load_dotenv()
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # if test true then set model to test model
        if test:
            self.model: str = "meta-llama/llama-3-8b-instruct:free"
            self.provider: str = "openrouter"
            self.api_key: str = os.getenv("OPENROUTER_API_KEY", 
                openrouter_api_key)
        else:
            self.model = model if model is not None else ""
            self.provider = provider if provider is not None else ""
            self.api_key = api_key if api_key is not None else ""

        # Common initialization for both test and non-test cases
        try:
            self.current_config: Dict[str, Any] = self._get_model_config(self.model)
            self.tokenizer: AutoTokenizer = self.get_tokenizer()
            self.client: Dict[str, str] = self.initialize_client()
            self.max_context: int = self.current_config.get("max_context", 0)
            self.max_response: int = self.current_config.get("max_response", 0)
        except Exception as e:
            print(f"Error during model initialization: {str(e)}")
            raise

    def _get_config_path(self) -> Path:
        return Path(__file__).parent / "model_configs.json"

    def _load_model_configs(self) -> Any:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid configuration file: {str(e)}")

    def _get_model_config(self, model: str) -> Any:
        if model not in self.model_configs.get("models", {}):
            raise ValueError(f"Unsupported model: {model}")
        return self.model_configs["models"][model]

    def get_tokenizer(self) -> AutoTokenizer:
        try:
            return AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize tokenizer: {str(e)}")

    def initialize_client(self) -> Dict[str, str]:
        provider_configs: Dict[str, Dict[str, str]] = {
            "openrouter": {"base_url": "https://openrouter.ai/api/v1", "model_prefix": "openrouter/"},
            "fireworks": {"base_url": "https://api.fireworks.ai/inference/v1", "model_prefix": "fireworks_ai/"},  # Updated base URL
            "openai": {"base_url": "https://api.openai.com/v1", "model_prefix": ""},
            "huggingface": {"base_url": "https://api-inference.huggingface.co/models", "model_prefix": "huggingface/"}
        }

        if self.provider not in provider_configs:
            raise ValueError(f"Unsupported provider: {self.provider}")

        config = provider_configs[self.provider]
        litellm.api_key = self.api_key
        
        return {
            "api_key": self.api_key,
            "base_url": config["base_url"],
            "model_prefix": config["model_prefix"]
        }


    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client configuration is required."
        
        try:
            formatted_model = f"{self.client['model_prefix']}{self.model}"
            response = litellm.completion(
                model=formatted_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.client["api_key"]
            )
            return response.choices[0].message.content if response.choices else ""
        except Exception as e:
            return f"Error: {str(e)}"

    def get_token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def is_within_context_window(self, text: str) -> bool:
        return self.get_token_count(text) <= self.max_context

    def is_within_response_window(self, text: str) -> bool:
        return self.get_token_count(text) <= self.max_response
