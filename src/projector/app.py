"""
Streamlit web interface for the prediction app.
"""
import asyncio
import os
from typing import Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv

from .config import Config
from .models import Effect, PredictionTree
from .prediction_engine import PredictionEngine


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

    # Create main input area
    st.header("Input")
    context = st.text_area(
        "Enter a contextual event",
        height=100,
        placeholder="Example: A major technological breakthrough allows for the cost-effective removal of carbon dioxide from the atmosphere at scale.",
    )

    # Create button to generate prediction
    generate_button = st.button("Generate Prediction", type="primary")

    # Initialize session state
    if "prediction_tree" not in st.session_state:
        st.session_state.prediction_tree = None
    if "summary" not in st.session_state:
        st.session_state.summary = None

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

    # Display results if available
    if st.session_state.prediction_tree and st.session_state.summary:
        st.header("Results")

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Summary", "Effects by Order", "Tree View"])

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


if __name__ == "__main__":
    run_app()
