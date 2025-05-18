from dataclasses import field
"""
Configuration management for the prediction app.
"""
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """
    Configuration for the prediction app.
    """
    # API settings
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    available_models: list[str] = field(default_factory=lambda: ["gemini-1.0-pro", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-2.5-flash-preview-04-17"])
    model_name: Optional[str] = field(default=None, init=False) # Not an init arg, __post_init__ can set default
    
    # Prediction settings
    num_effects: int = 5  # Default number of effects per level
    max_depth: int = 3    # Default maximum depth
    
    # Performance settings
    max_parallel_calls: int = 5
    enable_caching: bool = True
    cache_ttl: int = 3600  # Cache time-to-live in seconds
    
    # Prompt settings
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40

    def __post_init__(self):
        if not hasattr(self, 'model_name') or not self.model_name: # Check if model_name is already set (e.g. by from_env)
            if self.available_models:
                self.model_name = self.available_models[0]
            else:
                # This case should ideally not happen if available_models has a default factory
                self.model_name = "gemini-2.0-flash" # Fallback if list is empty

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create a Config instance from environment variables.
        """
        # available_models could also be loaded from ENV if needed, e.g., as a comma-separated string
        # For now, we use the default_factory list.
        config = cls(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            # model_name is set in __post_init__ or overridden by GEMINI_MODEL
            num_effects=int(os.getenv("NUM_EFFECTS", "5")),
            max_depth=int(os.getenv("MAX_DEPTH", "3")),
            max_parallel_calls=int(os.getenv("MAX_PARALLEL_CALLS", "5")),
            enable_caching=os.getenv("ENABLE_CACHING", "True").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            top_p=float(os.getenv("TOP_P", "0.95")),
            top_k=int(os.getenv("TOP_K", "40")),
        )
        # Override model_name if GEMINI_MODEL is set
        env_model_name = os.getenv("GEMINI_MODEL")
        if env_model_name:
            if env_model_name not in config.available_models:
                # Optionally, add it to available_models or raise an error/warning
                # For now, we'll allow it but it won't be in the "selectable" list unless added there
                pass
            config.model_name = env_model_name
        elif not config.model_name and config.available_models: # if not set by env and __post_init__ didn't set (e.g. if available_models was empty then)
             config.model_name = config.available_models[0]

        return config
    
    def validate(self) -> Optional[str]:
        """
        Validate the configuration.
        
        Returns:
            Optional[str]: Error message if validation fails, None otherwise.
        """
        if not self.api_key:
            return "API key is required. Please set the GEMINI_API_KEY environment variable."

        if not self.available_models:
            return "Available models list cannot be empty."

        if self.model_name not in self.available_models and not os.getenv("GEMINI_MODEL"):
             # Only raise error if model_name is not in available_models AND it wasn't set by an environment variable
             # This allows users to use a model via ENV var even if it's not in the default list
            return f"Selected model_name '{self.model_name}' is not in the list of available_models: {self.available_models}."
        
        if self.num_effects <= 0:
            return "Number of effects must be positive."
        
        if self.max_depth <= 0:
            return "Maximum depth must be positive."
        
        if self.temperature < 0 or self.temperature > 1:
            return "Temperature must be between 0 and 1."
        
        if self.top_p < 0 or self.top_p > 1:
            return "Top-p must be between 0 and 1."
        
        if self.top_k <= 0:
            return "Top-k must be positive."
        
        return None
