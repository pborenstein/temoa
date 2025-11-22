"""
Model registry and configuration for sentence transformers.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
from ..config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ModelSpec:
    """Specification for a sentence transformer model."""
    name: str
    dimensions: int
    description: str
    use_case: str
    speed: str  # "fast", "medium", "slow"
    quality: str  # "good", "better", "best"
    max_sequence_length: int = 512


class ModelRegistry:
    """Registry of available sentence transformer models with their specifications."""
    
    # Fallback default model (used when no config exists)
    FALLBACK_DEFAULT_MODEL = "all-MiniLM-L6-v2"
    
    # Model specifications
    MODELS = {
        "all-MiniLM-L6-v2": ModelSpec(
            name="all-MiniLM-L6-v2",
            dimensions=384,
            description="Lightweight, fast model optimized for speed/quality balance",
            use_case="General purpose, development, fast iteration",
            speed="fast",
            quality="good",
            max_sequence_length=512
        ),
        "all-mpnet-base-v2": ModelSpec(
            name="all-mpnet-base-v2", 
            dimensions=768,
            description="Higher quality model with better semantic understanding",
            use_case="Production use, better accuracy, cross-domain connections",
            speed="medium",
            quality="better",
            max_sequence_length=514
        ),
        "all-MiniLM-L12-v2": ModelSpec(
            name="all-MiniLM-L12-v2",
            dimensions=384,
            description="Better quality than L6 while maintaining same dimensions",
            use_case="Improved quality without storage increase",
            speed="medium",
            quality="better", 
            max_sequence_length=512
        ),
        "paraphrase-albert-small-v2": ModelSpec(
            name="paraphrase-albert-small-v2",
            dimensions=768,
            description="Optimized for paraphrase and similarity detection",
            use_case="Finding similar content, paraphrase detection",
            speed="medium",
            quality="good",
            max_sequence_length=100
        ),
        "multi-qa-mpnet-base-cos-v1": ModelSpec(
            name="multi-qa-mpnet-base-cos-v1",
            dimensions=768,
            description="Optimized for question-answer similarity",
            use_case="Question-answer matching, query optimization",
            speed="medium",
            quality="better",
            max_sequence_length=512
        )
    }
    
    @classmethod
    def get_model(cls, model_name: str) -> Optional[ModelSpec]:
        """Get model specification by name."""
        return cls.MODELS.get(model_name)
    
    @classmethod
    def list_models(cls) -> Dict[str, ModelSpec]:
        """Get all available models."""
        return cls.MODELS.copy()
    
    @classmethod
    def validate_model(cls, model_name: str) -> bool:
        """Check if model name is valid."""
        return model_name in cls.MODELS
    
    @classmethod
    def get_compatible_models(cls, dimensions: int) -> List[ModelSpec]:
        """Get models with matching dimensions."""
        return [spec for spec in cls.MODELS.values() if spec.dimensions == dimensions]
    
    @classmethod
    def suggest_models(cls, current_model: str) -> List[ModelSpec]:
        """Suggest compatible models for comparison."""
        current_spec = cls.get_model(current_model)
        if not current_spec:
            return list(cls.MODELS.values())
        
        # Get models with same dimensions (directly comparable)
        compatible = cls.get_compatible_models(current_spec.dimensions)
        
        # Remove current model from suggestions
        return [spec for spec in compatible if spec.name != current_model]
    
    @classmethod
    def format_model_info(cls, model_name: str) -> str:
        """Format model information for display."""
        spec = cls.get_model(model_name)
        if not spec:
            return f"Unknown model: {model_name}"
        
        return f"""
Model: {spec.name}
  Dimensions: {spec.dimensions}
  Speed: {spec.speed} | Quality: {spec.quality}
  Use Case: {spec.use_case}
  Description: {spec.description}
  Max Sequence Length: {spec.max_sequence_length} tokens
"""
    
    @classmethod
    def get_default_model(cls) -> str:
        """Get the currently configured default model."""
        try:
            config_manager = ConfigManager()
            return config_manager.get_default_model()
        except Exception as e:
            logger.warning(f"Failed to load default model from config: {e}")
            return cls.FALLBACK_DEFAULT_MODEL
    
    @classmethod
    def set_default_model(cls, model_name: str) -> bool:
        """Set the default model in configuration.
        
        Args:
            model_name: Model name to set as default
            
        Returns:
            True if successfully saved
        """
        if not cls.validate_model(model_name):
            logger.error(f"Cannot set invalid model '{model_name}' as default")
            return False
        
        try:
            config_manager = ConfigManager()
            return config_manager.set_default_model(model_name)
        except Exception as e:
            logger.error(f"Failed to set default model: {e}")
            return False
    
    @classmethod
    def format_model_table(cls) -> str:
        """Format all models as a comparison table."""
        header = f"{'Model':<25} {'Dim':<4} {'Speed':<8} {'Quality':<8} {'Use Case':<30}"
        separator = "-" * len(header)
        
        rows = [header, separator]
        for spec in cls.MODELS.values():
            row = f"{spec.name:<25} {spec.dimensions:<4} {spec.speed:<8} {spec.quality:<8} {spec.use_case:<30}"
            rows.append(row)
        
        return "\n".join(rows)