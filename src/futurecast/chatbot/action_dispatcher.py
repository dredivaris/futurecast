# src/futurecast/chatbot/action_dispatcher.py
import logging
from typing import TYPE_CHECKING, Dict, Any, List

from .state_manager import StateManager
from .nlu_processor import NLUProcessor
from .llm_interaction import LLMInteraction
from .prediction_engine_interface import PredictionEngineInterface # Added import

if TYPE_CHECKING:
    # This block can be used for forward declarations if needed
    # to avoid circular imports, but the primary classes are now imported directly.
    pass

logger = logging.getLogger(__name__)

class ActionDispatcher:
    """
    Orchestrates the chatbot's response by dispatching actions based on NLU output.
    """

    def __init__(self,
                 state_manager: 'StateManager',
                 nlu_processor: 'NLUProcessor',
                 llm_interaction: 'LLMInteraction',
                 prediction_engine_interface: 'PredictionEngineInterface'): # Added parameter
        """
        Initializes the ActionDispatcher.

        Args:
            state_manager: An instance of StateManager.
            nlu_processor: An instance of NLUProcessor.
            llm_interaction: An instance of LLMInteraction.
            prediction_engine_interface: An instance of PredictionEngineInterface.
        """
        self.state_manager = state_manager
        self.nlu_processor = nlu_processor
        self.llm_interaction = llm_interaction
        self.prediction_engine_interface = prediction_engine_interface # Added assignment

    def dispatch(self, user_query: str, chat_history: List[Dict[str, Any]]) -> str:
        """
        Processes user query, determines action, and returns a response.
        The user's message is assumed to be already added to the chat_history.
        This method is responsible for adding the assistant's response to chat_history.
        """
        # User message is now added in app.py before calling dispatch.
        
        intent_data: Dict[str, Any] = self.nlu_processor.process_input(user_query)
        intent: str = intent_data.get("intent", "unknown")
        entities: Dict[str, Any] = intent_data.get("entities", {})
        
        logger.info(f"Dispatching action for intent: {intent}, entities: {entities}, using provided chat history (len: {len(chat_history)})")
        assistant_response: str

        if intent == "get_prompt":
            prompt = self.state_manager.futurecast_prompt
            assistant_response = f"The original prompt was: {prompt}" if prompt else "No prompt loaded yet."
        elif intent == "get_summary":
            summary = self.state_manager.futurecast_summary
            assistant_response = f"The futurecast summary is: {summary}" if summary else "No summary loaded yet."
        elif intent == "get_tree_overview":
            tree_loaded = bool(self.state_manager.effect_tree)
            assistant_response = "The effect tree is currently loaded and can be interacted with." if tree_loaded else "No effect tree loaded yet."
        elif intent == "modify_effect":
            effect_id = entities.get("effect_id")
            new_text = entities.get("new_text")

            if not effect_id or new_text is None: # new_text can be an empty string
                assistant_response = "I'm sorry, I can't modify the effect. Please provide both the effect ID and the new text."
                logger.warning(f"Modify effect failed: Missing effect_id ('{effect_id}') or new_text ('{new_text}').")
            elif not self.state_manager.effect_tree:
                 assistant_response = "Cannot modify effect: The effect tree is not loaded. Please generate or load a futurecast first."
            else:
                # Add a spinner or processing message here in app.py if this takes time
                logger.info(f"Attempting to modify effect '{effect_id}' with text '{new_text}'.")
                updated_tree = self.prediction_engine_interface.regenerate_downstream_effects(
                    current_tree=self.state_manager.effect_tree,
                    modified_effect_id=effect_id,
                    new_text=new_text
                )
                if updated_tree:
                    success = self.state_manager.update_effect_text_and_regenerate(effect_id, new_text, updated_tree)
                    if success:
                        assistant_response = f"Effect {effect_id} has been updated and downstream effects were regenerated."
                        logger.info(f"Successfully modified effect '{effect_id}'.")
                    else:
                        # This case might indicate an internal error in StateManager.
                        assistant_response = f"Effect {effect_id} was processed, but there was an issue confirming the state update with the StateManager."
                        logger.error(f"StateManager failed to confirm update for modified effect '{effect_id}'.")
                else:
                    # PredictionEngineInterface logs specific errors. This is a user-facing summary.
                    assistant_response = f"Sorry, I couldn't modify effect '{effect_id}'. It might not exist, or there was an issue regenerating the tree."
                    logger.warning(f"Failed to modify effect '{effect_id}' via PredictionEngineInterface.")
        elif intent == "expand_effect":
            effect_id = entities.get("effect_id")
            levels = entities.get("levels", 1) # Default to 1 level if not specified
            focus = entities.get("focus")

            if not effect_id:
                assistant_response = "I'm sorry, I can't expand the effect. Please provide the effect ID."
                logger.warning(f"Expand effect failed: Missing effect_id.")
            elif not self.state_manager.effect_tree:
                assistant_response = "Cannot expand effect: The effect tree is not loaded. Please generate or load a futurecast first."
            else:
                # Add a spinner or processing message here in app.py if this takes time
                logger.info(f"Attempting to expand effect '{effect_id}' by {levels} levels with focus '{focus}'.")
                expanded_tree = self.prediction_engine_interface.expand_leaf_effect(
                    current_tree=self.state_manager.effect_tree,
                    leaf_effect_id=effect_id,
                    levels=levels,
                    focus=focus
                )
                if expanded_tree:
                    operation_desc = f"Expanded effect '{effect_id}' by {levels} level(s)"
                    if focus:
                        operation_desc += f" with focus on '{focus}'"
                    
                    success = self.state_manager.update_effect_tree(expanded_tree, operation_desc)
                    if success:
                        assistant_response = f"Effect {effect_id} has been expanded by {levels} level(s)."
                        if focus:
                            assistant_response += f" Focused on: '{focus}'."
                        logger.info(f"Successfully expanded effect '{effect_id}'.")
                    else:
                        assistant_response = f"Effect {effect_id} was processed for expansion, but there was an issue confirming the state update with the StateManager."
                        logger.error(f"StateManager failed to confirm update for expanded effect '{effect_id}'.")
                else:
                    # PredictionEngineInterface logs specific errors. This is a user-facing summary.
                    # Common reasons: effect_id not found, or it's not a leaf node.
                    assistant_response = f"Sorry, I couldn't expand effect '{effect_id}'. Please ensure the ID is correct and that it's a leaf node (has no existing sub-effects)."
                    logger.warning(f"Failed to expand effect '{effect_id}' via PredictionEngineInterface. It might not be a leaf or not exist.")
        elif intent == "ask_general_question":
            full_context = self.state_manager.get_full_context()
            assistant_response = self.llm_interaction.answer_question(context=full_context, question=user_query)
        elif intent == "unknown":
            assistant_response = "I'm not sure how to help with that. Can you try rephrasing?"
        else: # Handles any other unrecognized intents as per the plan
            assistant_response = "I'm not sure how to help with that. Can you try rephrasing?"

        self.state_manager.add_chat_message(role="assistant", content=assistant_response)
        return assistant_response

if __name__ == '__main__':
    # --- Mock dependencies for example usage ---
    # StateManager, NLUProcessor, LLMInteraction are now imported at the top level.
    
    # Mock Config for LLMInteraction
    class MockConfig:
        def __init__(self, api_key="test_api_key", model_name="test_model"):
            self.api_key = api_key # Matches actual Config attribute
            self.model_name = model_name # Matches actual Config attribute
            self.available_models = [model_name, "another-model"] # Add available_models

    # Initialize components
    mock_config = MockConfig(api_key="test_key_for_dispatcher", model_name="gemini-test-dispatcher")
    state_mgr = StateManager()
    state_mgr.load_futurecast_data(
        prompt="The core idea is to explore the multifaceted impacts of decentralized autonomous organizations (DAOs) on traditional governance structures within the next decade.",
        tree={"root": "DAO Impact", "children": ["Economic", "Social", "Political"]},
        summary="DAOs present a paradigm shift, potentially disrupting established governance models through enhanced transparency and distributed decision-making, but face challenges in scalability and regulation."
    )
    nlu_proc = NLUProcessor()
    llm_interact = LLMInteraction(config=mock_config)

    # Mock PredictionEngine and PredictionEngineInterface for testing
    class MockPredictionEngine:
        pass # Add methods if PredictionEngineInterface actually calls them in test

    mock_pred_engine = MockPredictionEngine()
    # Assuming PredictionEngineInterface needs PredictionEngine and Config
    # Config is already mocked as mock_config
    pred_engine_interface = PredictionEngineInterface(prediction_engine=mock_pred_engine, config=mock_config)
    
    dispatcher = ActionDispatcher(
        state_manager=state_mgr,
        nlu_processor=nlu_proc,
        llm_interaction=llm_interact,
        prediction_engine_interface=pred_engine_interface # Pass the new dependency
    )

    # Test cases
    test_queries = [
        "Hello there!", # unknown
        "What is the futurecast prompt?",
        "Show me the summary of the futurecast.",
        "Can you show the effect tree?",
        "What did we talk about?", # chat history
        "Explain the main challenges for DAOs.", # llm general question
        "Update effect 1.1 to 'This is a new text for 1.1'", # modify_effect
        "Change effect 2 with \"Effect 2 new content\"",      # modify_effect
        "Modify effect 3.2.1 to 'Another update here'",    # modify_effect (will fail if tree not structured for it)
        "Expand effect 1.1 by 1 level", # expand_effect
        "Expand effect 1.2.1 by 2 levels with focus on 'technical challenges'", # expand_effect
        "Add 1 more effects under 2", # expand_effect (node 2 is a leaf)
        "Expand leaf node 1.2", # expand_effect (1.2 is not a leaf, should fail)
        "Expand effect 99" # expand_effect (non-existent)
    ]

    # For modify_effect and expand_effect tests to work, state_mgr.effect_tree needs a structure
    # that PredictionEngineInterface can navigate.
    # Using the sample_tree from prediction_engine_interface.py for this.
    state_mgr.effect_tree = {
        "1": {
            "id": "1", "text": "Effect 1",
            "children": [
                {"id": "1.1", "text": "Effect 1.1", "children": []},
                {"id": "1.2", "text": "Effect 1.2", "children": [
                    {"id": "1.2.1", "text": "Effect 1.2.1", "children": []}
                ]}
            ]
        },
        "2": {"id": "2", "text": "Effect 2", "children": []}
    }


    for query in test_queries:
        print(f"\nUser: {query}")
        bot_response = dispatcher.dispatch(query)
        print(f"Bot: {bot_response}")

    print("\nFinal Chat History:")
    for msg in dispatcher.state_manager.chat_history:
        print(f"  {msg['role']}: {msg['content']}")
    
    print("\nFinal Effect Tree (after modifications):")
    import json
    print(json.dumps(dispatcher.state_manager.effect_tree, indent=2))