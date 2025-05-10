"""
Tests for the data models.
"""
import sys
import os
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.futurecast.models import Effect, PredictionTree


class TestEffect(unittest.TestCase):
    """
    Tests for the Effect class.
    """

    def test_effect_creation(self):
        """Test creating an Effect."""
        effect = Effect(content="Test effect", order=1)
        self.assertEqual(effect.content, "Test effect")
        self.assertEqual(effect.order, 1)
        self.assertIsNone(effect.parent_id)
        self.assertEqual(effect.children, [])

    def test_effect_to_dict(self):
        """Test converting an Effect to a dictionary."""
        effect = Effect(content="Test effect", order=1, id="test-id", parent_id="parent-id")
        effect_dict = effect.to_dict()

        self.assertEqual(effect_dict["content"], "Test effect")
        self.assertEqual(effect_dict["order"], 1)
        self.assertEqual(effect_dict["id"], "test-id")
        self.assertEqual(effect_dict["parent_id"], "parent-id")
        self.assertEqual(effect_dict["children"], [])

    def test_effect_from_dict(self):
        """Test creating an Effect from a dictionary."""
        effect_dict = {
            "content": "Test effect",
            "order": 1,
            "id": "test-id",
            "parent_id": "parent-id",
            "children": []
        }

        effect = Effect.from_dict(effect_dict)

        self.assertEqual(effect.content, "Test effect")
        self.assertEqual(effect.order, 1)
        self.assertEqual(effect.id, "test-id")
        self.assertEqual(effect.parent_id, "parent-id")
        self.assertEqual(effect.children, [])

    def test_effect_with_children(self):
        """Test an Effect with children."""
        child1 = Effect(content="Child 1", order=2, id="child-1", parent_id="parent-id")
        child2 = Effect(content="Child 2", order=2, id="child-2", parent_id="parent-id")

        parent = Effect(content="Parent", order=1, id="parent-id")
        parent.children = [child1, child2]

        self.assertEqual(len(parent.children), 2)
        self.assertEqual(parent.children[0].content, "Child 1")
        self.assertEqual(parent.children[1].content, "Child 2")

        # Test to_dict with children
        parent_dict = parent.to_dict()
        self.assertEqual(len(parent_dict["children"]), 2)
        self.assertEqual(parent_dict["children"][0]["content"], "Child 1")
        self.assertEqual(parent_dict["children"][1]["content"], "Child 2")


class TestPredictionTree(unittest.TestCase):
    """
    Tests for the PredictionTree class.
    """

    def test_tree_creation(self):
        """Test creating a PredictionTree."""
        tree = PredictionTree(context="Test context")
        self.assertEqual(tree.context, "Test context")
        self.assertEqual(tree.root_effects, [])

    def test_add_root_effect(self):
        """Test adding a root effect to a PredictionTree."""
        tree = PredictionTree(context="Test context")
        effect = Effect(content="Root effect", order=1, id="root-id")

        tree.add_root_effect(effect)

        self.assertEqual(len(tree.root_effects), 1)
        self.assertEqual(tree.root_effects[0].content, "Root effect")

    def test_get_effects_by_order(self):
        """Test getting effects by order from a PredictionTree."""
        tree = PredictionTree(context="Test context")

        # Create effects
        root1 = Effect(content="Root 1", order=1, id="root-1")
        root2 = Effect(content="Root 2", order=1, id="root-2")

        child1 = Effect(content="Child 1", order=2, id="child-1", parent_id="root-1")
        child2 = Effect(content="Child 2", order=2, id="child-2", parent_id="root-1")
        child3 = Effect(content="Child 3", order=2, id="child-3", parent_id="root-2")

        grandchild1 = Effect(content="Grandchild 1", order=3, id="grandchild-1", parent_id="child-1")

        # Build tree
        root1.children = [child1, child2]
        root2.children = [child3]
        child1.children = [grandchild1]

        tree.root_effects = [root1, root2]

        # Get effects by order
        effects_by_order = tree.get_effects_by_order()

        self.assertEqual(len(effects_by_order), 3)  # 3 orders
        self.assertEqual(len(effects_by_order[1]), 2)  # 2 first-order effects
        self.assertEqual(len(effects_by_order[2]), 3)  # 3 second-order effects
        self.assertEqual(len(effects_by_order[3]), 1)  # 1 third-order effect

    def test_to_dict(self):
        """Test converting a PredictionTree to a dictionary."""
        tree = PredictionTree(context="Test context")
        effect = Effect(content="Root effect", order=1, id="root-id")
        tree.add_root_effect(effect)

        tree_dict = tree.to_dict()

        self.assertEqual(tree_dict["context"], "Test context")
        self.assertEqual(len(tree_dict["root_effects"]), 1)
        self.assertEqual(tree_dict["root_effects"][0]["content"], "Root effect")

    def test_from_dict(self):
        """Test creating a PredictionTree from a dictionary."""
        tree_dict = {
            "context": "Test context",
            "root_effects": [
                {
                    "content": "Root effect",
                    "order": 1,
                    "id": "root-id",
                    "parent_id": None,
                    "children": []
                }
            ]
        }

        tree = PredictionTree.from_dict(tree_dict)

        self.assertEqual(tree.context, "Test context")
        self.assertEqual(len(tree.root_effects), 1)
        self.assertEqual(tree.root_effects[0].content, "Root effect")


if __name__ == "__main__":
    unittest.main()
