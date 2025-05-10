"""
Data models for the prediction app.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Effect:
    """
    Represents a single predicted effect.
    """
    content: str
    order: int
    parent_id: Optional[str] = None
    id: Optional[str] = None
    children: List["Effect"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the effect to a dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "order": self.order,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Effect":
        """Create an Effect from a dictionary."""
        effect = cls(
            content=data["content"],
            order=data["order"],
            parent_id=data.get("parent_id"),
            id=data.get("id")
        )
        
        for child_data in data.get("children", []):
            effect.children.append(cls.from_dict(child_data))
            
        return effect


@dataclass
class PredictionTree:
    """
    Represents a tree of predicted effects.
    """
    context: str
    root_effects: List[Effect] = field(default_factory=list)
    
    def add_root_effect(self, effect: Effect) -> None:
        """Add a root effect to the tree."""
        self.root_effects.append(effect)
    
    def get_effects_by_order(self) -> Dict[int, List[Effect]]:
        """Get all effects grouped by their order."""
        result: Dict[int, List[Effect]] = {}
        
        def traverse(effect: Effect) -> None:
            if effect.order not in result:
                result[effect.order] = []
            result[effect.order].append(effect)
            
            for child in effect.children:
                traverse(child)
        
        for root in self.root_effects:
            traverse(root)
            
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the prediction tree to a dictionary."""
        return {
            "context": self.context,
            "root_effects": [effect.to_dict() for effect in self.root_effects]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredictionTree":
        """Create a PredictionTree from a dictionary."""
        tree = cls(context=data["context"])
        
        for effect_data in data.get("root_effects", []):
            tree.root_effects.append(Effect.from_dict(effect_data))
            
        return tree
