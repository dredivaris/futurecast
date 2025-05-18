# src/futurecast/chatbot/state_manager.py
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class StateManager:
    """Manages the state of the chatbot conversation."""
    futurecast_prompt: Optional[str] = None
    effect_tree: Optional[Dict[str, Any]] = None
    futurecast_summary: Optional[str] = None
    chat_history: List[Dict[str, str]] = field(default_factory=list)

    def load_futurecast_data(self, prompt: str, tree: Dict[str, Any], summary: str) -> None:
        """Loads the initial FutureCast data."""
        self.futurecast_prompt = prompt
        self.effect_tree = tree
        self.futurecast_summary = summary
        # Initialize chat history with a system message indicating data load
        self.chat_history = [{"role": "system", "content": "FutureCast data has been loaded."}]

    def add_chat_message(self, role: str, content: str) -> None:
        """Adds a message to the chat history."""
        # Basic validation for role, can be expanded
        if role not in ["user", "assistant", "system"]:
            logger.warning(f"Invalid role '{role}' used for chat message: '{content}'")
            # Optionally, one might choose to not add the message or raise an error.
            # For now, we log a warning and still add it.
        self.chat_history.append({"role": role, "content": content})

    def get_full_context(self) -> str:
        """
        Constructs a string that includes the futurecast_prompt,
        a brief representation of the effect_tree, the futurecast_summary,
        and the recent chat_history. This context will be used by the LLM.
        Handles cases where some data might be None.
        """
        context_parts = []

        if self.futurecast_prompt:
            context_parts.append(f"Original FutureCast Prompt: {self.futurecast_prompt}")
        else:
            context_parts.append("Original FutureCast Prompt: Not available.")

        if self.effect_tree is not None: # Check for None explicitly
            context_parts.append("Effect Tree: Effect tree is loaded.")
        else:
            context_parts.append("Effect Tree: Not available.")

        if self.futurecast_summary:
            context_parts.append(f"FutureCast Summary: {self.futurecast_summary}")
        else:
            context_parts.append("FutureCast Summary: Not available.")

        if self.chat_history:
            history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.chat_history])
            context_parts.append(f"\nRecent Conversation:\n{history_str}")
        else:
            context_parts.append("\nRecent Conversation: No history yet.")

        return "\n\n".join(context_parts)

    def get_chat_history_str(self) -> str: # Retaining this as it might be useful elsewhere or for different formatting
        """Returns a string representation of the chat history, typically for display."""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history])

    def update_effect_text_and_regenerate(self, effect_id: str, new_text: str, updated_tree: Dict[str, Any]) -> bool:
        """
        Updates the effect_tree with the updated_tree and logs the modification.

        Args:
            effect_id: The ID of the effect that was modified.
            new_text: The new text for the modified effect.
            updated_tree: The new effect tree after regeneration.

        Returns:
            True if successful, False otherwise.
        """
        if updated_tree is None:
            # This case should ideally be caught before calling this method,
            # but as a safeguard:
            self.add_chat_message(
                "system",
                f"Error: Attempted to update effect tree with None for effect {effect_id}."
            )
            return False

        self.effect_tree = updated_tree
        log_message = f"Effect '{effect_id}' was updated to '{new_text}'. Downstream effects have been regenerated."
        self.add_chat_message("system", log_message)
        # Potentially, one might want to log this to a more persistent log file as well.
        logger.info(f"StateManager: {log_message}")
        return True

    def update_effect_tree(self, new_tree: Dict[str, Any], operation_description: str) -> bool:
        """
        Replaces the current effect_tree with a new one and logs the update.
        This is a generic method for updating the tree after operations like expansion.

        Args:
            new_tree: The new, complete effect tree.
            operation_description: A string describing the operation that led to this update
                                   (e.g., "Effects expanded under node 1.2.1").

        Returns:
            True if successful.
        """
        if new_tree is None:
            self.add_chat_message(
                "system",
                f"Error: Attempted to update effect tree with None. Operation: {operation_description}"
            )
            return False
        
        self.effect_tree = new_tree
        log_message = f"Effect tree updated. Operation: {operation_description}"
        self.add_chat_message("system", log_message)
        logger.info(f"StateManager: {log_message}")
        return True

if __name__ == '__main__':
    # Example Usage
    state = StateManager()
    state.load_futurecast_data(
        prompt="Initial prompt about AI development.",
        tree={"root": {"child1": {}, "child2": {}}},
        summary="Summary of AI development futurecast."
    )
    state.add_chat_message("user", "What is the main risk?")
    state.add_chat_message("assistant", "The main risk is unforeseen consequences.")
    
    print("Current State:")
    print(f"  Prompt: {state.futurecast_prompt}")
    print(f"  Summary: {state.futurecast_summary}")
    print("  Chat History:")
    for message in state.chat_history:
        print(f"    {message['role']}: {message['content']}")
    
    print("\nFull Context for LLM:")
    print(state.get_full_context())
    print("\nChat History String:")
    print(state.get_chat_history_str())

    # Test update_effect_tree
    print("\n--- Testing update_effect_tree ---")
    new_sample_tree = {
        "root": {"child1": {"text": "Updated C1"}, "child2": {}, "child3": {"text": "New C3"}}
    }
    state.update_effect_tree(new_sample_tree, "Manual tree replacement for testing.")
    print("Updated Effect Tree in State:")
    import json # Make sure json is imported if not already
    print(json.dumps(state.effect_tree, indent=2))
    print("Chat History after tree update:")
    for message in state.chat_history:
        print(f"    {message['role']}: {message['content']}")