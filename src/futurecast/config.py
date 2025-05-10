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
    model_name: str = "gemini-2.0-flash"
    
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
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Create a Config instance from environment variables.
        """
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            num_effects=int(os.getenv("NUM_EFFECTS", "5")),
            max_depth=int(os.getenv("MAX_DEPTH", "3")),
            max_parallel_calls=int(os.getenv("MAX_PARALLEL_CALLS", "5")),
            enable_caching=os.getenv("ENABLE_CACHING", "True").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            top_p=float(os.getenv("TOP_P", "0.95")),
            top_k=int(os.getenv("TOP_K", "40")),
        )
    
    def validate(self) -> Optional[str]:
        """
        Validate the configuration.
        
        Returns:
            Optional[str]: Error message if validation fails, None otherwise.
        """
        if not self.api_key:
            return "API key is required. Please set the GEMINI_API_KEY environment variable."
        
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
