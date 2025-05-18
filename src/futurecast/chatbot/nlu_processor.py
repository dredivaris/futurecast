# src/futurecast/chatbot/nlu_processor.py
import re
import logging
from typing import Dict, Any

# Configure basic logging if not already configured by a higher-level module
# This is a simple configuration; in a larger app, this might be centralized.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NLUProcessor:
    """Processes natural language input to understand user intent and extract entities."""

    def __init__(self):
        """Initializes the NLUProcessor."""
        # In a real scenario, this might load models or rules.
        pass

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Processes the user's input string to determine intent and entities.
        Uses simple keyword-based rules to identify basic question intents.
        """
        user_input_lower = user_input.lower()
        intent = "unknown"
        entities: Dict[str, Any] = {}

        # Regex for modify_effect intent
        # Examples: "Change effect 3.1 to 'new text'", "Modify the text of effect 1.2.1", "Update effect 2 with 'another new text'"
        modify_effect_pattern = re.compile(
            r"(change|modify|update)\s+(?:effect|the text of effect)\s+([\w.]+)\s+(?:to|with)\s+['\"](.*?)['\"]",
            re.IGNORECASE
        )
        modify_match = modify_effect_pattern.search(user_input)

        # Regex for expand_effect intent
        # Examples: "Expand effect 3.1.2 by 2 levels", "Add 3 more effects under 1.2", "Expand leaf node 4.1"
        # "Expand effect 3.1.2 by 2 levels with focus on 'economic impact'"
        expand_effect_pattern = re.compile(
            r"(expand|add)\s+(?:effect|leaf node)\s+([\w.]+)\s*(?:by|more effects under|under)?\s*(\d*)\s*(?:levels?)?\s*(?:with focus on\s*['\"](.*?)['\"])?",
            re.IGNORECASE
        )
        expand_match = expand_effect_pattern.search(user_input)

        if modify_match:
            intent = "modify_effect"
            entities["effect_id"] = modify_match.group(2)
            entities["new_text"] = modify_match.group(3)
        elif expand_match:
            intent = "expand_effect"
            entities["effect_id"] = expand_match.group(2)
            levels_str = expand_match.group(3)
            entities["levels"] = int(levels_str) if levels_str and levels_str.isdigit() else 1
            entities["focus"] = expand_match.group(4) if expand_match.group(4) else None
            # Basic validation: NLU can't truly validate if it's a leaf node without the tree,
            # but we can note that this intent implies a leaf node.
            # Actual validation will be in ActionDispatcher or PredictionEngineInterface.
        else:
            # Keywords for get_prompt
            prompt_keywords = ["original prompt", "the prompt", "initial prompt", "show prompt"]
            # Keywords for get_summary
            summary_keywords = ["the summary", "summary of", "show summary", "what's the summary"]
            # Keywords for get_tree_overview
            tree_keywords = ["effect tree", "the tree", "tree look like", "describe tree", "tree overview"]

            if any(keyword in user_input_lower for keyword in prompt_keywords):
                intent = "get_prompt"
            elif any(keyword in user_input_lower for keyword in summary_keywords):
                intent = "get_summary"
            elif any(keyword in user_input_lower for keyword in tree_keywords):
                intent = "get_tree_overview"
            # Basic check for a general question if no specific intent is matched
            # This is a very simplistic check and can be improved.
            elif "?" in user_input or \
                 user_input_lower.startswith("what") or \
                 user_input_lower.startswith("how") or \
                 user_input_lower.startswith("why") or \
                 user_input_lower.startswith("explain") or \
                 user_input_lower.startswith("tell me"):
                intent = "ask_general_question"
                # For general questions, we might pass the original input as an entity
                # but the task specifies entities are not required for these basic intents.
                # For now, entities remain empty.
                # entities["query"] = user_input
        
        if intent == "unknown":
            logger.warning(f"NLUProcessor: Could not determine intent for input: '{user_input}'")
            # Optionally, you could also log if entities were partially matched but intent was still unknown.

        return {"intent": intent, "entities": entities}

if __name__ == '__main__':
    processor = NLUProcessor()

    test_inputs = [
        "What is the FutureCast prompt?",
        "Show me the summary.",
        "Can you display the effect tree?",
        "What was our conversation about?",
        "Explain the impact of AI on jobs.",
        "Tell me about the root cause.", # Might be an LLM question or specific node
        "This is a random statement.",
        "Change effect 3.1 to 'new effect text'",
        "Modify the text of effect 1.2.1 with \"another new text here\"",
        "Update effect 2 to 'updated text for effect 2'",
        "Expand effect 3.1.2 by 2 levels",
        "Add 3 more effects under 1.2",
        "Expand leaf node 4.1",
        "Expand effect 2.2.1 with focus on 'social impact'",
        "Expand effect 1 by 3 levels with focus on 'environmental factors'"
    ]

    for text in test_inputs:
        result = processor.process_input(text)
        print(f"Input: \"{text}\"")
        print(f"  Intent: {result['intent']}")
        print(f"  Entities: {result['entities']}\n")