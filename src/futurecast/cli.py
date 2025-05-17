"""
Command-line interface for the FutureCast application.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from .app import run_app
from .config import Config
from .models import PredictionTree
from .utils import debug_log, load_futurecast


# Load environment variables
load_dotenv()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """FutureCast - Predict cascading effects of events using AI."""
    # If no subcommand is provided, run the app by default
    if ctx.invoked_subcommand is None:
        ctx.invoke(app)


@cli.command()
def app():
    """Run the FutureCast web application."""
    run_app()


@cli.command()
@click.option(
    "--file", "-f",
    help="Path to a saved futurecast file. If not provided, loads the latest.",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
def load(file: Optional[str] = None):
    """
    Load a previously saved futurecast without making LLM calls.

    This is useful for testing or when you want to view a previous futurecast
    without using your LLM quota.
    """
    # Check if API key is set (still needed for Streamlit app)
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        click.echo("Warning: Gemini API key not found. Set the GEMINI_API_KEY environment variable.")

    # Load the futurecast
    result = load_futurecast(file)
    if result is None:
        click.echo("Error: Failed to load futurecast.")
        sys.exit(1)

    tree, summary = result

    # Set environment variables for the Streamlit app to use
    # These need to be set BEFORE running the app
    os.environ["FUTURECAST_PRELOADED"] = "true"
    os.environ["FUTURECAST_LOAD_TREE"] = "true"
    os.environ["FUTURECAST_CONTEXT"] = tree.context
    os.environ["FUTURECAST_SUMMARY"] = summary
    os.environ["FUTURECAST_TREE"] = str(file or "latest")

    # Show info to the user
    click.echo(f"Loaded futurecast with context: {tree.context}")
    click.echo("Starting Streamlit app...")

    # Run the app
    run_app()


if __name__ == "__main__":
    cli()
