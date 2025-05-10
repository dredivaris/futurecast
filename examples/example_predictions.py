"""
Example usage of the prediction engine.
"""
import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv

from futurecast.config import Config
from futurecast.models import Effect, PredictionTree
from futurecast.prediction_engine import PredictionEngine


# Load environment variables
load_dotenv()


async def run_example():
    """
    Run an example prediction.
    """
    # Create configuration
    config = Config.from_env()

    # Validate configuration
    error = config.validate()
    if error:
        print(f"Error: {error}")
        return

    # Create prediction engine
    engine = PredictionEngine(config)

    # Example context
    context = "A major technological breakthrough allows for the cost-effective removal of carbon dioxide from the atmosphere at scale."

    print(f"Generating prediction for: {context}")
    print(f"Number of effects per level: {config.num_effects}")
    print(f"Maximum depth: {config.max_depth}")
    print()

    # Generate prediction
    tree, summary = await engine.generate_prediction(context)

    # Display effects by order
    effects_by_order = tree.get_effects_by_order()

    for order in sorted(effects_by_order.keys()):
        effects = effects_by_order[order]

        # Get order name
        order_name = {1: "First", 2: "Second", 3: "Third"}.get(order, f"{order}th")

        # Display order header
        print(f"{order_name}-order Effects:")

        # Display effects
        for i, effect in enumerate(effects, 1):
            print(f"{i}. {effect.content}")

        print()

    # Display summary
    print("Summary:")
    print(summary)


if __name__ == "__main__":
    asyncio.run(run_example())
