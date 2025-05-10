"""
Core prediction engine for the app.
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Tuple

from .config import Config
from .models import Effect, PredictionTree
from .utils import (
    debug_log,
    generate_text,
    generate_texts_parallel,
    create_first_order_prompt,
    create_higher_order_prompt,
    create_summary_prompt,
    parse_effects_list,
    setup_gemini_api,
)


class PredictionEngine:
    """
    Engine for generating predictions using LLM calls.
    """

    def __init__(self, config: Config):
        """
        Initialize the prediction engine.

        Args:
            config: The configuration object.
        """
        self.config = config
        setup_gemini_api(config)

    async def generate_first_order_effects(
        self, context: str, num_effects: int
    ) -> List[Effect]:
        """
        Generate first-order effects for a given context.

        Args:
            context: The initial context.
            num_effects: The number of effects to generate.

        Returns:
            The list of first-order effects.
        """
        # Create prompt
        prompt = create_first_order_prompt(context, num_effects)

        # Generate text
        response = await generate_text(prompt, self.config, prompt_description="Initial prompt for 1st order effects")

        # Parse effects
        effect_texts = parse_effects_list(response)

        # Create Effect objects
        effects = []
        for i, text in enumerate(effect_texts):
            effect_id = str(uuid.uuid4())
            effect = Effect(
                id=effect_id,
                content=text,
                order=1,
                parent_id=None,
            )
            effects.append(effect)

        return effects

    async def generate_higher_order_effects(
        self,
        context: str,
        parent_effect: Effect,
        sibling_effects: List[Effect],
        previous_effects_by_order: Dict[int, List[str]],
        num_effects: int,
    ) -> List[Effect]:
        """
        Generate higher-order effects for a given parent effect.

        Args:
            context: The initial context.
            parent_effect: The parent effect.
            sibling_effects: The list of sibling effects.
            previous_effects_by_order: Dictionary of previous effects grouped by order.
            num_effects: The number of effects to generate.

        Returns:
            The list of higher-order effects.
        """
        # Create prompt
        sibling_texts = [effect.content for effect in sibling_effects if effect.id != parent_effect.id]
        next_order = parent_effect.order + 1
        prompt = create_higher_order_prompt(
            context,
            parent_effect.content,
            sibling_texts,
            previous_effects_by_order,
            num_effects,
            next_order,
        )

        # Generate text
        prompt_description = f"Prompt for depth {parent_effect.order}, effect '{parent_effect.content}'"
        response = await generate_text(prompt, self.config, prompt_description=prompt_description)

        # Parse effects
        effect_texts = parse_effects_list(response)

        # Create Effect objects
        effects = []
        for i, text in enumerate(effect_texts):
            effect_id = str(uuid.uuid4())
            effect = Effect(
                id=effect_id,
                content=text,
                order=parent_effect.order + 1,
                parent_id=parent_effect.id,
            )
            effects.append(effect)

        return effects

    async def generate_effects_recursive(
        self,
        context: str,
        parent_effect: Optional[Effect] = None,
        sibling_effects: Optional[List[Effect]] = None,
        previous_effects_by_order: Optional[Dict[int, List[str]]] = None,
        current_depth: int = 0,
        max_depth: int = 3,
        num_effects: int = 5,
    ) -> List[Effect]:
        """
        Recursively generate effects.

        Args:
            context: The initial context.
            parent_effect: The parent effect, or None for first-order effects.
            sibling_effects: The list of sibling effects, or None for first-order effects.
            previous_effects_by_order: Dictionary of previous effects grouped by order, or None for first-order effects.
            current_depth: The current depth level.
            max_depth: The maximum depth level.
            num_effects: The number of effects to generate per level.

        Returns:
            The list of generated effects.
        """
        # Initialize previous effects if not provided
        if previous_effects_by_order is None:
            previous_effects_by_order = {}

        # Check if we've reached the maximum depth
        if current_depth >= max_depth:
            return []

        # Generate effects
        if parent_effect is None:
            # First-order effects
            effects = await self.generate_first_order_effects(context, num_effects)
        else:
            # Log recursive call
            debug_log(f"generate_effects_recursive called at depth {current_depth} for effect: {parent_effect.content}")

            # Higher-order effects
            effects = await self.generate_higher_order_effects(
                context, parent_effect, sibling_effects or [], previous_effects_by_order, num_effects
            )

        # Update previous effects for next level
        if current_depth > 0 and sibling_effects:
            if current_depth not in previous_effects_by_order:
                previous_effects_by_order[current_depth] = []
            # Add sibling effects to previous effects
            for effect in sibling_effects:
                if effect.content not in previous_effects_by_order[current_depth]:
                    previous_effects_by_order[current_depth].append(effect.content)

        # Recursively generate child effects
        if current_depth + 1 < max_depth:
            for effect in effects:
                # Create a copy of previous effects to avoid modifying the original
                next_previous_effects = {k: v.copy() for k, v in previous_effects_by_order.items()}

                child_effects = await self.generate_effects_recursive(
                    context,
                    effect,
                    effects,
                    next_previous_effects,
                    current_depth + 1,
                    max_depth,
                    num_effects,
                )
                effect.children = child_effects

        return effects

    async def generate_summary(
        self, context: str, tree: PredictionTree
    ) -> str:
        """
        Generate a summary for a prediction tree.

        Args:
            context: The initial context.
            tree: The prediction tree.

        Returns:
            The summary text.
        """
        # Get effects by order
        effects_by_order = tree.get_effects_by_order()

        # Convert to text format for the prompt
        effects_by_order_text = {}
        for order, effects in effects_by_order.items():
            effects_by_order_text[order] = [effect.content for effect in effects]

        # Create prompt
        prompt = create_summary_prompt(context, effects_by_order_text)

        # Generate text
        response = await generate_text(prompt, self.config, prompt_description="Prompt for summary")

        return response

    async def generate_prediction(
        self, context: str, num_effects: int = None, max_depth: int = None
    ) -> Tuple[PredictionTree, str]:
        """
        Generate a complete prediction for a given context.

        Args:
            context: The initial context.
            num_effects: The number of effects to generate per level, or None to use the default.
            max_depth: The maximum depth level, or None to use the default.

        Returns:
            A tuple of (prediction_tree, summary).
        """
        # Use default values if not provided
        num_effects = num_effects or self.config.num_effects
        max_depth = max_depth or self.config.max_depth

        # Create prediction tree
        tree = PredictionTree(context=context)

        # Generate first-order effects
        root_effects = await self.generate_first_order_effects(context, num_effects)

        # Initialize previous effects with first-order effects
        previous_effects_by_order = {1: [effect.content for effect in root_effects]}

        # Generate higher-order effects recursively
        for effect in root_effects:
            child_effects = await self.generate_effects_recursive(
                context,
                effect,
                root_effects,
                previous_effects_by_order,
                1,  # Start at depth 1 (second-order effects)
                max_depth,
                num_effects,
            )
            effect.children = child_effects
            tree.add_root_effect(effect)

        # Generate summary
        summary = await self.generate_summary(context, tree)

        return tree, summary
