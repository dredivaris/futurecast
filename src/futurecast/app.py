"""
Streamlit web interface for the prediction app.
"""
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv

from .config import Config
from .models import Effect, PredictionTree
from .prediction_engine import PredictionEngine
from .utils import debug_log, save_futurecast, load_futurecast


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
    # Simple markdown without frontmatter for better compatibility
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
        model_name = st.selectbox(
            "Model",
            options=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0,
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
                model_name=model_name,
                num_effects=num_effects,
                max_depth=max_depth,
                temperature=temperature,
                top_p=top_p,
                enable_caching=enable_caching,
            )

            # Create prediction engine
            engine = PredictionEngine(config)

            # Generate prediction
            tree, summary = asyncio.run(
                engine.generate_prediction(context, num_effects, max_depth)
            )

            # Store in session state
            st.session_state.prediction_tree = tree
            st.session_state.summary = summary

            # Save the futurecast to a file
            save_path = save_futurecast(tree, summary)
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
