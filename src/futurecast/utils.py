"""
Utility functions for the prediction app.
"""
import asyncio
import datetime
import hashlib
import json
import os
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import google.generativeai as genai

from .config import Config
from .models import PredictionTree


def debug_log(message: str) -> None:
    """
    Print a debug log message to stdout.

    Args:
        message: The message to log.
    """
    print(f"DEBUG: {message}", flush=True)


def setup_gemini_api(config: Config) -> None:
    """
    Set up the Gemini API with the provided configuration.

    Args:
        config: The configuration object.
    """
    genai.configure(api_key=config.api_key)


def get_cache_key(prompt: str, model: str, params: Dict[str, Any]) -> str:
    """
    Generate a cache key for an API call.

    Args:
        prompt: The prompt text.
        model: The model name.
        params: The model parameters.

    Returns:
        A string cache key.
    """
    # Create a string representation of the parameters
    params_str = json.dumps(params, sort_keys=True)

    # Combine prompt, model, and parameters
    combined = f"{prompt}|{model}|{params_str}"

    # Generate a hash
    return hashlib.md5(combined.encode()).hexdigest()


def get_cache_path(cache_key: str) -> str:
    """
    Get the file path for a cache entry.

    Args:
        cache_key: The cache key.

    Returns:
        The file path.
    """
    os.makedirs(".cache", exist_ok=True)
    return os.path.join(".cache", f"{cache_key}.json")


def save_to_cache(cache_key: str, response: Any, ttl: int) -> None:
    """
    Save a response to the cache.

    Args:
        cache_key: The cache key.
        response: The response to cache.
        ttl: Time-to-live in seconds.
    """
    cache_path = get_cache_path(cache_key)

    # Convert response to a serializable format
    if hasattr(response, "text"):
        response_data = response.text
    elif isinstance(response, (list, tuple)) and hasattr(response[0], "text"):
        response_data = [r.text for r in response]
    else:
        response_data = str(response)

    cache_data = {
        "data": response_data,
        "expires_at": time.time() + ttl
    }

    with open(cache_path, "w") as f:
        json.dump(cache_data, f)


def load_from_cache(cache_key: str) -> Optional[Any]:
    """
    Load a response from the cache.

    Args:
        cache_key: The cache key.

    Returns:
        The cached response, or None if not found or expired.
    """
    cache_path = get_cache_path(cache_key)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r") as f:
            cache_data = json.load(f)

        # Check if the cache entry has expired
        if cache_data["expires_at"] < time.time():
            os.remove(cache_path)
            return None

        return cache_data["data"]
    except (json.JSONDecodeError, KeyError, OSError):
        # If there's any error reading the cache, ignore it
        if os.path.exists(cache_path):
            os.remove(cache_path)
        return None


async def generate_text(
    prompt: str,
    config: Config,
    use_cache: bool = True,
    prompt_description: str = None
) -> str:
    """
    Generate text using the Gemini API.

    Args:
        prompt: The prompt text.
        config: The configuration object.
        use_cache: Whether to use caching.
        prompt_description: A description of the prompt for logging purposes.

    Returns:
        The generated text.
    """
    # Prepare model parameters
    params = {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "top_k": config.top_k,
    }

    # Log the prompt
    if prompt_description:
        debug_log(f"{prompt_description}:\n{prompt}")

    # Check cache if enabled
    if use_cache and config.enable_caching:
        cache_key = get_cache_key(prompt, config.model_name, params)
        cached_response = load_from_cache(cache_key)

        if cached_response is not None:
            if prompt_description:
                debug_log(f"Gemini response for {prompt_description} (from cache):\n{cached_response}")
            return cached_response

    # Generate text
    model = genai.GenerativeModel(config.model_name)
    response = model.generate_content(prompt, generation_config=params)
    response_text = response.text

    # Log the response
    if prompt_description:
        debug_log(f"Gemini response for {prompt_description}:\n{response_text}")

    # Save to cache if enabled
    if use_cache and config.enable_caching:
        cache_key = get_cache_key(prompt, config.model_name, params)
        save_to_cache(cache_key, response, config.cache_ttl)

    return response_text


async def generate_texts_parallel(
    prompts: List[str],
    config: Config,
    use_cache: bool = True,
    prompt_descriptions: List[str] = None
) -> List[str]:
    """
    Generate multiple texts in parallel using the Gemini API.

    Args:
        prompts: The list of prompts.
        config: The configuration object.
        use_cache: Whether to use caching.
        prompt_descriptions: List of descriptions for each prompt for logging purposes.

    Returns:
        The list of generated texts.
    """
    # Split prompts into batches to respect max_parallel_calls
    batch_size = config.max_parallel_calls
    batches = [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]

    # Split descriptions into batches if provided
    description_batches = None
    if prompt_descriptions:
        description_batches = [prompt_descriptions[i:i + batch_size] for i in range(0, len(prompt_descriptions), batch_size)]

    results = []

    for i, batch in enumerate(batches):
        # Create tasks for each prompt in the batch
        if description_batches:
            tasks = [generate_text(prompt, config, use_cache, desc)
                    for prompt, desc in zip(batch, description_batches[i])]
        else:
            tasks = [generate_text(prompt, config, use_cache) for prompt in batch]

        # Run tasks in parallel
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    return results


def create_first_order_prompt(context: str, num_effects: int) -> str:
    """
    Create a prompt for generating first-order effects.

    Args:
        context: The initial context.
        num_effects: The number of effects to generate.

    Returns:
        The prompt text.
    """
    return f"""
You are an expert at predicting the effects of events. Given an initial event, your task is to predict the most likely immediate effects that would result from this event.

Initial Event: {context}

Generate {num_effects} different immediate likely effects that would result from this event. Each effect should be distinct, plausible, and directly connected to the initial event.

Format your response as a numbered list with each effect on a new line. Be concise but specific. Do not include any explanations or additional text beyond the numbered list of effects.

Example format:
1. [First effect]
2. [Second effect]
3. [Third effect]
...
"""


def create_higher_order_prompt(
    context: str,
    parent_effect: str,
    sibling_effects: List[str],
    previous_effects_by_order: Dict[int, List[str]],
    num_effects: int,
    order: int
) -> str:
    """
    Create a prompt for generating higher-order effects.

    Args:
        context: The initial context.
        parent_effect: The parent effect.
        sibling_effects: The list of sibling effects.
        previous_effects_by_order: Dictionary of previous effects grouped by order.
        num_effects: The number of effects to generate.
        order: The order level.

    Returns:
        The prompt text.
    """
    siblings_text = "\n".join([f"- {effect}" for effect in sibling_effects])

    # Format previous effects by order
    previous_effects_text = ""
    for prev_order in sorted(previous_effects_by_order.keys()):
        order_name = {1: "First", 2: "Second", 3: "Third"}.get(prev_order, f"{prev_order}th")
        effects = previous_effects_by_order[prev_order]
        previous_effects_text += f"\n{order_name}-order effects that have already occurred:\n"
        for effect in effects:
            previous_effects_text += f"- {effect}\n"

    return f"""
You are an expert at predicting the cascading effects of events. Given an initial event and a specific effect that resulted from it, your task is to predict the next level of effects.

Initial Event: {context}
{previous_effects_text if previous_effects_text else ''}
Effect to analyze: {parent_effect}

Other concurrent effects happening at the same time:
{siblings_text}

Generate {num_effects} different likely {order}nd/rd/th-order effects that would result specifically from the "Effect to analyze" above, while taking into account the initial event, {'' if not previous_effects_text else 'the timeline of previous effects, '}and other concurrent effects. Each effect should be distinct, plausible, and directly connected to the effect being analyzed.

Format your response as a numbered list with each effect on a new line. Be concise but specific. Do not include any explanations or additional text beyond the numbered list of effects.

Example format:
1. [First effect]
2. [Second effect]
3. [Third effect]
...
"""


def create_summary_prompt(context: str, effects_by_order: Dict[int, List[str]]) -> str:
    """
    Create a prompt for generating a summary.

    Args:
        context: The initial context.
        effects_by_order: The dictionary of effects grouped by order.

    Returns:
        The prompt text.
    """
    effects_text = ""

    for order in sorted(effects_by_order.keys()):
        effects = effects_by_order[order]
        order_name = {1: "First", 2: "Second", 3: "Third"}.get(order, f"{order}th")

        effects_text += f"\n{order_name}-order effects:\n"
        for i, effect in enumerate(effects, 1):
            effects_text += f"{i}. {effect}\n"

    return f"""
You are an expert at synthesizing complex scenarios and their implications. Given an initial event and its cascading effects at different levels, your task is to create a comprehensive summary of how this scenario would likely unfold over time.

Initial Event: {context}

Cascading Effects:{effects_text}

Create a comprehensive summary that integrates the initial event and all of these effects into a coherent narrative. The summary should:
1. Explain how the initial event would unfold over time through these various effects
2. Highlight the most significant developments and their implications
3. Identify any potential feedback loops or compounding effects
4. Present a balanced view of both positive and negative outcomes
5. Be written in a clear, engaging style accessible to a general audience

Your summary should be 3-5 paragraphs long and should integrate all the major effects while maintaining logical coherence.
"""


def parse_effects_list(text: str) -> List[str]:
    """
    Parse a list of effects from generated text.

    Args:
        text: The generated text.

    Returns:
        The list of effects.
    """
    # Clean up the text
    text = text.strip()

    # Split by newlines and filter out empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Extract effects (remove numbering)
    effects = []
    for line in lines:
        # Try to match numbered list format (e.g., "1. Effect")
        if line[0].isdigit() and '. ' in line:
            effect = line.split('. ', 1)[1].strip()
            effects.append(effect)
        else:
            # If not in numbered format, just add the whole line
            effects.append(line)

    return effects


def get_futurecasts_dir() -> Path:
    """
    Get the directory for saved futurecasts.

    Returns:
        The directory path.
    """
    # Create a directory in the user's home directory
    futurecasts_dir = Path.home() / ".futurecast" / "saved"
    futurecasts_dir.mkdir(parents=True, exist_ok=True)
    return futurecasts_dir


def save_futurecast(tree: PredictionTree, summary: str) -> Path:
    """
    Save a futurecast to a file.

    Args:
        tree: The prediction tree.
        summary: The summary text.

    Returns:
        The path to the saved file.
    """
    # Create a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the data to save
    data = {
        "tree": tree.to_dict(),
        "summary": summary,
        "timestamp": timestamp,
        "version": "0.1.0"
    }

    # Save to file
    futurecasts_dir = get_futurecasts_dir()
    filepath = futurecasts_dir / f"futurecast_{timestamp}.json"

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    # Also save as latest.json for easy access
    latest_path = futurecasts_dir / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(data, f, indent=2)

    debug_log(f"Saved futurecast to {filepath}")
    return filepath


def load_futurecast(filepath: Optional[str] = None) -> Optional[Tuple[PredictionTree, str]]:
    """
    Load a futurecast from a file.

    Args:
        filepath: The path to the file, or None to load the latest.

    Returns:
        A tuple of (prediction_tree, summary), or None if the file doesn't exist.
    """
    if filepath is None:
        # Load the latest futurecast
        filepath = get_futurecasts_dir() / "latest.json"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        debug_log(f"Futurecast file not found: {filepath}")
        return None

    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        tree = PredictionTree.from_dict(data["tree"])
        summary = data["summary"]

        debug_log(f"Loaded futurecast from {filepath}")
        return tree, summary
    except (json.JSONDecodeError, KeyError, OSError) as e:
        debug_log(f"Error loading futurecast: {e}")
        return None
