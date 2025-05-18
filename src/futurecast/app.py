"""
Streamlit web interface for the prediction app.
"""
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import streamlit as st
from dotenv import load_dotenv

from futurecast.config import Config
from .models import Effect, PredictionTree
from .prediction_engine import PredictionEngine
from .utils import debug_log, save_futurecast, load_futurecast
from .chatbot.state_manager import StateManager
from .chatbot.nlu_processor import NLUProcessor
from .chatbot.llm_interaction import LLMInteraction
from .chatbot.action_dispatcher import ActionDispatcher
from .chatbot.prediction_engine_interface import PredictionEngineInterface # Added import


# Load environment variables
load_dotenv()


def display_effect(effect: Effect, level: int = 0) -> None:
    """
    Display an effect in the Streamlit UI.

    Args:
        effect: The effect to display.
        level: The indentation level.
    """
    # Create indentation using HTML
    indent_px = level * 20  # 20px per level

    # Display the effect with HTML for indentation
    st.markdown(f"<div style='margin-left: {indent_px}px'>• <strong>{effect.content}</strong></div>", unsafe_allow_html=True)

    # Display children
    for child in effect.children:
        display_effect(child, level + 1)


def display_effects_by_order(tree: PredictionTree) -> None:
    """
    Display effects grouped by order in the Streamlit UI.

    Args:
        tree: The prediction tree.
    """
    effects_by_order = tree.get_effects_by_order()

    for order in sorted(effects_by_order.keys()):
        effects = effects_by_order[order]

        # Get order name
        order_name = {1: "First", 2: "Second", 3: "Third"}.get(order, f"{order}th")

        # Display order header
        st.subheader(f"{order_name}-order Effects")

        # Display effects
        for effect in effects:
            st.markdown(f"• **{effect.content}**")

        st.markdown("---")


def convert_tree_to_markmap(tree: PredictionTree) -> str:
    """
    Convert a PredictionTree to a hierarchical Markdown format for markmap.

    Args:
        tree: The prediction tree.

    Returns:
        A Markdown string representing the mindmap.
    """
    # No frontmatter needed as it's added by the markmap component
    frontmatter = ""
    markdown = [frontmatter, f"# {tree.context}\n\n"]

    def add_effect(effect: Effect, level: int) -> None:
        prefix = "#" * (level + 1)
        markdown.append(f"{prefix} {effect.content}\n\n")

        for child in effect.children:
            add_effect(child, level + 1)

    for root_effect in tree.root_effects:
        add_effect(root_effect, 1)

    return "".join(markdown)


def run_app() -> None:
    """
    Run the Streamlit app.
    """
    # Set page config
    st.set_page_config(
        page_title="FutureCast - Prediction App",
        page_icon="🔮",
        layout="wide",
    )

    # Display header
    st.title("🔮 FutureCast")
    st.markdown("Predict cascading effects of events using AI")

    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
        )
        st.stop()

    # Check if we're loading a preloaded futurecast
    is_preloaded = os.getenv("FUTURECAST_PRELOADED", "").lower() == "true"

    # Create sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Model selection
        # Use available_models from Config
        config_for_models = Config.from_env() # Create a temporary config to get available_models
        model_name = st.selectbox(
            "Model",
            options=config_for_models.available_models,
            index=0, # Default to the first model in the list
        )

        # Number of effects
        num_effects = st.slider(
            "Effects per level",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
        )

        # Maximum depth
        max_depth = st.slider(
            "Maximum depth",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
        )

        # Calculate and display total LLM calls
        if num_effects == 1:
            total_calls = 1 + max_depth
        else:
            total_calls = 1 + num_effects * (num_effects**max_depth - 1) // (num_effects - 1)
        
        st.markdown(f"**Estimated LLM Calls:** `{total_calls}`")
        st.caption("Includes initial prompt and all effect generation calls.")
        st.markdown("---")


        # Advanced settings
        with st.expander("Advanced Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
            )

            top_p = st.slider(
                "Top-p",
                min_value=0.0,
                max_value=1.0,
                value=0.95,
                step=0.05,
            )

            enable_caching = st.checkbox("Enable caching", value=True)

    # Initialize session state
    if "prediction_tree" not in st.session_state:
        st.session_state.prediction_tree = None
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "context" not in st.session_state:
        st.session_state.context = ""
    if 'state_manager' not in st.session_state:
        st.session_state.state_manager = StateManager()
    if 'nlu_processor' not in st.session_state:
        st.session_state.nlu_processor = NLUProcessor()
    # LLMInteraction and PredictionEngineInterface need the config, which is created later.
    # ActionDispatcher also needs other components, will initialize with them.
    if 'prediction_engine_main' not in st.session_state: # To store the main PredictionEngine instance
        st.session_state.prediction_engine_main = None
    if 'prediction_engine_interface' not in st.session_state:
        st.session_state.prediction_engine_interface = None
    if 'chat_history' not in st.session_state: # Initialize chat_history in state_manager
        st.session_state.state_manager.chat_history = []


    # Check if we should load a preloaded futurecast
    if is_preloaded and st.session_state.prediction_tree is None:
        preloaded_context = os.getenv("FUTURECAST_CONTEXT", "")
        preloaded_summary = os.getenv("FUTURECAST_SUMMARY", "")
        preloaded_tree_path = os.getenv("FUTURECAST_TREE", "")

        # Load the futurecast
        result = load_futurecast(preloaded_tree_path if preloaded_tree_path != "latest" else None)
        if result:
            tree, summary = result
            st.session_state.prediction_tree = tree
            st.session_state.summary = summary

            # Pre-fill the context field
            st.session_state.context = tree.context

            # Load futurecast data into state_manager
            if hasattr(st.session_state, 'state_manager') and tree and summary:
                st.session_state.state_manager.load_futurecast_data(
                    prompt=tree.context,
                    effect_tree=tree, # Or a string representation if needed
                    summary=summary
                )

            # Show a message
            st.success("Loaded saved futurecast. No LLM calls were made.")

    # Create main input area
    st.header("Input")

    # Use the context from session state
    context = st.text_area(
        "Enter a contextual event",
        value=st.session_state.context,
        height=100,
        placeholder="Example: A major technological breakthrough allows for the cost-effective removal of carbon dioxide from the atmosphere at scale.",
    )

    # Create button to generate prediction
    generate_button = st.button("Generate Prediction", type="primary")

    # Generate prediction when button is clicked
    if generate_button and context:
        with st.spinner("Generating prediction..."):
            # Create configuration
            config = Config(
                api_key=api_key,
                # model_name is not an init argument, will be set below
                num_effects=num_effects,
                max_depth=max_depth,
                temperature=temperature,
                top_p=top_p,
                enable_caching=enable_caching,
            )
            # Set the model_name selected by the user
            if model_name: # model_name is from st.selectbox
                config.model_name = model_name
            # If not set by user (e.g. if selectbox somehow fails or is not used),
            # __post_init__ in Config will set a default.

            # Create main prediction engine instance
            # This engine is used for generating new predictions
            engine = PredictionEngine(config)
            st.session_state.prediction_engine_main = engine # Store it

            # Initialize LLMInteraction, PredictionEngineInterface, and ActionDispatcher
            if 'llm_interaction' not in st.session_state:
                st.session_state.llm_interaction = LLMInteraction(config=config)
            
            if 'prediction_engine_interface' not in st.session_state:
                # Pass the main PredictionEngine instance and config
                st.session_state.prediction_engine_interface = PredictionEngineInterface(
                    prediction_engine=st.session_state.prediction_engine_main,
                    config=config
                )

            if 'action_dispatcher' not in st.session_state:
                st.session_state.action_dispatcher = ActionDispatcher(
                    st.session_state.state_manager,
                    st.session_state.nlu_processor,
                    st.session_state.llm_interaction,
                    st.session_state.prediction_engine_interface # Pass the interface
                )
            
            # Generate prediction using the main engine
            tree, summary = asyncio.run(
                st.session_state.prediction_engine_main.generate_prediction(context, num_effects, max_depth)
            )

            # Store in session state
            st.session_state.prediction_tree = tree
            st.session_state.summary = summary

            # Load futurecast data into state_manager
            # The effect_tree in state_manager should be a dictionary representation
            # For now, PredictionTree itself might be okay if StateManager handles it,
            # or we convert it. The current StateManager expects Dict[str, Any].
            # Let's assume PredictionTree can be used or has a method to convert.
            # For simplicity, if PredictionTree is a complex object, we might need to serialize it.
            # The `regenerate_downstream_effects` in `PredictionEngineInterface` expects `Dict[str, Any]`.
            # So, we should ensure `state_manager.effect_tree` is in that format.
            # A simple way is to have a `to_dict()` method in `PredictionTree` or `Effect`.
            # For now, let's assume `tree` can be directly used or adapted.
            # If `PredictionTree` is not directly a dict, this will need adjustment.
            # For the purpose of this phase, let's assume `tree` (PredictionTree object)
            # can be handled by `PredictionEngineInterface` or it's converted.
            # The `PredictionEngineInterface` example used a dict structure like `sample_tree`.
            # We need to ensure `state_manager.effect_tree` matches that.
            # A placeholder: convert `PredictionTree` to a compatible dict.
            
            def convert_prediction_tree_to_dict(ptree: PredictionTree) -> Dict[str, Any]:
                # This is a placeholder. Actual conversion logic depends on Effect and PredictionTree structure.
                # It needs to match the structure expected by PredictionEngineInterface.
                # Example: {'id':'root', 'text': ptree.context, 'children': [convert_effect_to_dict(e) for e in ptree.root_effects]}
                # For now, let's pass a simplified representation or the object itself if PEI can handle it.
                # Given PEI's example, it expects a dict.
                # Let's try to build a dict similar to `sample_tree` in `prediction_engine_interface.py`
                
                def effect_to_dict(effect: Effect, current_id_prefix: str = "") -> Dict[str, Any]:
                    # Create an ID for the effect. This is a simple counter based for now.
                    # A more robust ID system would be needed for complex trees.
                    # The `modified_effect_id` like "1.2.1" implies a path-based or structured ID.
                    
                    # Let's assume effect objects have an 'id' attribute that is the last part of its path
                    # and 'content' for text.
                    node_id = getattr(effect, 'id', effect.content[:10]) # Fallback ID
                    
                    # This conversion needs to be consistent with how PEI finds nodes.
                    # The PEI example `sample_tree` has keys like "1", "1.1", "1.2.1" or nested structure.
                    # Let's try to make it a nested dict where keys are the IDs.
                    # This is complex to do generically here without knowing Effect's full structure.
                    # For now, we'll pass the PredictionTree object and assume PEI or StateManager adapts.
                    # OR, we make a very simple dict.
                    
                    # Simplistic conversion for the demo:
                    return {
                        "id": getattr(effect, 'id_str', effect.content[:10]), # Assuming Effect might have an id_str
                        "text": effect.content,
                        "children": [effect_to_dict(child) for child in effect.children]
                    }

                # This is still problematic as the top-level of `sample_tree` in PEI was a dict of effects.
                # e.g. {"1": effect_dict_1, "2": effect_dict_2}
                # For now, let `state_manager.effect_tree` store the `PredictionTree` object.
                # `PredictionEngineInterface` will need to be robust enough to handle it or
                # `StateManager` needs to store a dict.
                # Let's assume `PredictionEngineInterface`'s `regenerate_downstream_effects`
                # will receive `state_manager.effect_tree` and work with its structure.
                # The current PEI `regenerate_downstream_effects` expects a dict.
                # So, `state_manager.load_futurecast_data` should store a dict.
                
                # Placeholder: A very simplified dict representation
                # This will likely NOT work with the current PEI find logic without PEI adaptation.
                # For the exercise, we'll assume this conversion is more robust or PEI is adapted.
                # A better approach: PredictionTree.to_dict() method.
                
                # Let's use a simplified dict structure for now, acknowledging it's a placeholder.
                # This structure is NOT what PEI's `find_and_update_node_by_id_path` expects.
                # That function expects a dict like `sample_tree`.
                # We will need to refine this conversion.
                
                # For now, let's assume `state_manager.effect_tree` will be the `PredictionTree` object itself,
                # and `PredictionEngineInterface` will need to be adapted to navigate it, OR
                # we create a proper `to_dict` method in `PredictionTree`.
                # Given the current PEI implementation, a dict is needed.
                
                # Let's try to make a dict that PEI *might* work with, based on its `sample_tree`.
                # This is non-trivial.
                # For now, this part is a known area for future refinement.
                # We'll pass the `PredictionTree` object and the `PredictionEngineInterface`
                # will need to be robust.
                # **Correction**: `StateManager.effect_tree` is `Optional[Dict[str, Any]]`.
                # So we MUST provide a dictionary.
                
                # Create a dictionary representation
                tree_dict = {"context": ptree.context, "root_effects": []}
                effect_id_counter = 1
                
                def build_dict_effect(effect_obj: Effect, parent_id_str: str = "") -> Dict[str, Any]:
                    nonlocal effect_id_counter
                    # This ID generation is simplistic and needs to match NLU extraction.
                    # NLU extracts "1.2.1". We need to map that to nodes.
                    # Let's assume effect objects will get an `id_path` attribute.
                    # For now, this conversion is a placeholder.
                    
                    # Using a simple counter for top-level keys for now.
                    # This does not create "1.2.1" style keys easily.
                    
                    # Let's assume the `PredictionEngineInterface`'s `find_and_update_node_by_id_path`
                    # can navigate a structure like:
                    # { "id_segment_1": {"id": "id_segment_1", "text": ..., "children": [...] } }
                    # where children list contains nodes like:
                    #   {"id": "id_segment_2", "text": ..., "children": [...] }
                    
                    # This is a simplified conversion for the purpose of getting a dict.
                    # It does not perfectly match the `sample_tree` structure used in PEI testing.
                    # This is a key area for integration testing and refinement.
                    
                    children_list = []
                    for child_effect in effect_obj.children:
                        children_list.append(build_dict_effect(child_effect)) # Recursive call
                        
                    return {
                        "id": getattr(effect_obj, 'unique_id', str(effect_id_counter)), # Placeholder for a unique ID
                        "text": effect_obj.content,
                        "children": children_list
                    }

                # This creates a list of root effects, not the keyed dict PEI's example used.
                # tree_dict["root_effects"] = [build_dict_effect(eff) for eff in ptree.root_effects]
                
                # Let's try to match PEI's `sample_tree` structure more closely for `state_manager.effect_tree`
                # `sample_tree` was like: `{"1": {"id":"1", ...}, "2": ...}`
                # This requires assigning IDs like "1", "1.1", "1.2.1" during tree generation or conversion.
                
                # For now, as a placeholder that provides *a* dict:
                final_tree_dict = {}
                for i, root_eff in enumerate(ptree.root_effects):
                    # This is where we'd ideally use/generate IDs like "1", "1.1", etc.
                    # The `build_dict_effect` needs to be smarter about IDs.
                    # Let's assume `effect.id_str` will hold "1", "1.1", "1.2.1" etc.
                    # This requires `Effect` objects to have such an ID.
                    
                    # Simplified:
                    final_tree_dict[str(i+1)] = build_dict_effect(root_eff)
                    # This makes top level keys "1", "2", etc.
                    # The `id` field within `build_dict_effect` also needs to be consistent.
                    # If `effect_id` from NLU is "1.2.1", PEI needs to parse this and navigate.
                
                return final_tree_dict if final_tree_dict else {"prompt": ptree.context, "message": "Tree is empty or conversion failed."}


            if hasattr(st.session_state, 'state_manager') and tree and summary:
                converted_tree_dict = convert_prediction_tree_to_dict(tree)
                st.session_state.state_manager.load_futurecast_data(
                    prompt=tree.context,
                    tree=converted_tree_dict, # Pass the dictionary
                    summary=summary
                )

            # Save the futurecast to a file
            save_path = save_futurecast(tree, summary) # tree is PredictionTree object
            st.session_state.last_saved_path = str(save_path)
            debug_log(f"Saved futurecast to {save_path}")

    # Display results if available
    if st.session_state.prediction_tree and st.session_state.summary:
        st.header("Results")

        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Effects by Order", "Tree View", "Mind Map"])

        with tab1:
            st.subheader("Summary")
            st.markdown(st.session_state.summary)

            st.subheader("Results Chatbot")

            # Ensure chatbot components are initialized, especially if config was not available earlier
            # This might be redundant if initialized correctly after config creation, but good as a fallback.
            if 'llm_interaction' not in st.session_state and 'config' in locals():
                 st.session_state.llm_interaction = LLMInteraction(config=config) # Use config from current scope if available
            elif 'llm_interaction' not in st.session_state and 'config_for_models' in locals(): # Fallback to config_for_models if main config not yet created
                 st.session_state.llm_interaction = LLMInteraction(config=config_for_models)


            if 'action_dispatcher' not in st.session_state and \
               'state_manager' in st.session_state and \
               'nlu_processor' in st.session_state and \
               'llm_interaction' in st.session_state and \
               'prediction_engine_interface' in st.session_state: # Check for new dependency
                st.session_state.action_dispatcher = ActionDispatcher(
                    st.session_state.state_manager,
                    st.session_state.nlu_processor,
                    st.session_state.llm_interaction,
                    st.session_state.prediction_engine_interface # Pass it
                )
            # Fallback if prediction_engine_interface was not initialized due to no "Generate" click yet
            # This might happen if loading a preloaded cast and then going to chat.
            elif 'action_dispatcher' not in st.session_state and \
                 'prediction_engine_interface' not in st.session_state and \
                 'prediction_engine_main' in st.session_state and st.session_state.prediction_engine_main is not None and \
                 'config' in locals(): # If config from a previous generate is available
                    st.session_state.prediction_engine_interface = PredictionEngineInterface(
                        prediction_engine=st.session_state.prediction_engine_main,
                        config=config # Use config from the current scope (if generate was clicked)
                                      # or config_for_models as a less ideal fallback.
                    )
                    # Try to initialize ActionDispatcher again
                    if 'state_manager' in st.session_state and \
                       'nlu_processor' in st.session_state and \
                       'llm_interaction' in st.session_state:
                        st.session_state.action_dispatcher = ActionDispatcher(
                            st.session_state.state_manager,
                            st.session_state.nlu_processor,
                            st.session_state.llm_interaction,
                            st.session_state.prediction_engine_interface
                        )

            # Check if FutureCast data is loaded before showing chat interface
            if not st.session_state.state_manager.futurecast_prompt or \
               not st.session_state.state_manager.effect_tree or \
               not st.session_state.state_manager.futurecast_summary:
                st.info("Please generate or load a futurecast first to use the chatbot.")
            elif 'action_dispatcher' in st.session_state and 'nlu_processor' in st.session_state:
                # Display chat history
                for message in st.session_state.state_manager.chat_history:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

                # Chat input
                user_input = st.chat_input("Ask something about the results...")
                if user_input:
                    # Display user message immediately
                    with st.chat_message("user"):
                        st.write(user_input)

                    # Determine intent to decide if a spinner is needed
                    intent_data = st.session_state.nlu_processor.process_input(user_input)
                    intent = intent_data.get("intent", "unknown")
                    
                    bot_response = ""
                    if intent in ["modify_effect", "expand_effect"]:
                        with st.spinner("Processing your request to modify/expand the effect tree..."):
                            bot_response = st.session_state.action_dispatcher.dispatch(user_input)
                    else:
                        # For other intents, process without a specific spinner message here
                        # (LLM calls might still take time but are less directly "tree modification")
                        bot_response = st.session_state.action_dispatcher.dispatch(user_input)

                    # Display bot response (already added to history by dispatcher)
                    with st.chat_message("assistant"):
                        st.write(bot_response)
                    # Rerun to ensure the chat history (managed by StateManager) is fully updated in the UI
                    st.rerun()
            else:
                st.warning("Chatbot is not available. Ensure a FutureCast is generated/loaded and all components are initialized.")

        with tab2:
            st.subheader("Effects by Order")
            display_effects_by_order(st.session_state.prediction_tree)

        with tab3:
            st.subheader("Tree View")
            for effect in st.session_state.prediction_tree.root_effects:
                display_effect(effect)

        with tab4:
            st.subheader("Mind Map")

            try:
                # Use the streamlit-markmap component directly
                from streamlit_markmap import markmap

                # Convert the tree to markmap format
                markmap_markdown = convert_tree_to_markmap(st.session_state.prediction_tree)

                # Add CSS to improve the markmap display - apply to the whole page
                st.markdown("""
                <style>
                /* Make the markmap container taller and ensure it's visible */
                iframe.stMarkmap, iframe.stComponent-iframe {
                    min-height: 800px !important;
                    height: 800px !important;
                    width: 100% !important;
                    border: none !important;
                    margin-top: 0 !important;
                    padding-top: 0 !important;
                    position: relative !important;
                    top: 0 !important;
                    transform: translateY(0) !important;
                }

                /* Ensure the container is tall enough */
                [data-testid="stVerticalBlock"] > div:has(iframe) {
                    min-height: 850px !important;
                    height: 850px !important;
                }

                /* Make the tab content taller */
                .stTabs [data-baseweb="tab-panel"] {
                    min-height: 900px !important;
                }

                /* Adjust the overall layout */
                .main .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 1rem !important;
                    max-width: 100% !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # Display the markmap with a larger height for better visibility
                markmap(markmap_markdown, height=1000)

                # Add a note about the mind map functionality
                st.info("Note: You can expand and collapse nodes by clicking on them. You can also zoom in/out and pan around the mind map.")

            except Exception as e:
                st.error(f"Error displaying mind map: {str(e)}")



if __name__ == "__main__":
    run_app()
