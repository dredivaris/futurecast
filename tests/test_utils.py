"""
Tests for the utility functions.
"""
import sys
import os
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.futurecast.utils import (
    get_cache_key,
    parse_effects_list,
    create_first_order_prompt,
    create_higher_order_prompt,
    create_summary_prompt,
)


class TestUtils(unittest.TestCase):
    """
    Tests for utility functions.
    """

    def test_get_cache_key(self):
        """Test generating a cache key."""
        prompt = "Test prompt"
        model = "test-model"
        params = {"temperature": 0.7, "top_p": 0.95}

        key1 = get_cache_key(prompt, model, params)

        # Same inputs should produce the same key
        key2 = get_cache_key(prompt, model, params)
        self.assertEqual(key1, key2)

        # Different inputs should produce different keys
        key3 = get_cache_key("Different prompt", model, params)
        self.assertNotEqual(key1, key3)

        key4 = get_cache_key(prompt, "different-model", params)
        self.assertNotEqual(key1, key4)

        key5 = get_cache_key(prompt, model, {"temperature": 0.8})
        self.assertNotEqual(key1, key5)

    def test_parse_effects_list(self):
        """Test parsing a list of effects from text."""
        # Test numbered list
        text1 = """
        1. First effect
        2. Second effect
        3. Third effect
        """

        effects1 = parse_effects_list(text1)
        self.assertEqual(len(effects1), 3)
        self.assertEqual(effects1[0], "First effect")
        self.assertEqual(effects1[1], "Second effect")
        self.assertEqual(effects1[2], "Third effect")

        # Test unnumbered list
        text2 = """
        First effect
        Second effect
        Third effect
        """

        effects2 = parse_effects_list(text2)
        self.assertEqual(len(effects2), 3)
        self.assertEqual(effects2[0], "First effect")
        self.assertEqual(effects2[1], "Second effect")
        self.assertEqual(effects2[2], "Third effect")

        # Test mixed format
        text3 = """
        1. First effect
        Second effect
        3. Third effect
        """

        effects3 = parse_effects_list(text3)
        self.assertEqual(len(effects3), 3)
        self.assertEqual(effects3[0], "First effect")
        self.assertEqual(effects3[1], "Second effect")
        self.assertEqual(effects3[2], "Third effect")

    def test_create_first_order_prompt(self):
        """Test creating a prompt for first-order effects."""
        context = "Test context"
        num_effects = 3

        prompt = create_first_order_prompt(context, num_effects)

        # Check that the prompt contains the context and number of effects
        self.assertIn(context, prompt)
        self.assertIn(str(num_effects), prompt)

    def test_create_higher_order_prompt(self):
        """Test creating a prompt for higher-order effects."""
        context = "Test context"
        parent_effect = "Parent effect"
        sibling_effects = ["Sibling 1", "Sibling 2"]
        previous_effects_by_order = {1: ["Previous effect 1", "Previous effect 2"]}
        num_effects = 3
        order = 2

        prompt = create_higher_order_prompt(
            context, parent_effect, sibling_effects, previous_effects_by_order, num_effects, order
        )

        # Check that the prompt contains all the required elements
        self.assertIn(context, prompt)
        self.assertIn(parent_effect, prompt)
        self.assertIn("Sibling 1", prompt)
        self.assertIn("Sibling 2", prompt)
        self.assertIn("Previous effect 1", prompt)
        self.assertIn("Previous effect 2", prompt)
        self.assertIn("First-order effects", prompt)
        self.assertIn(str(num_effects), prompt)
        self.assertIn(str(order), prompt)

    def test_create_summary_prompt(self):
        """Test creating a prompt for a summary."""
        context = "Test context"
        effects_by_order = {
            1: ["First-order effect 1", "First-order effect 2"],
            2: ["Second-order effect 1", "Second-order effect 2"],
        }

        prompt = create_summary_prompt(context, effects_by_order)

        # Check that the prompt contains the context and effects
        self.assertIn(context, prompt)
        self.assertIn("First-order effect 1", prompt)
        self.assertIn("First-order effect 2", prompt)
        self.assertIn("Second-order effect 1", prompt)
        self.assertIn("Second-order effect 2", prompt)


if __name__ == "__main__":
    unittest.main()
