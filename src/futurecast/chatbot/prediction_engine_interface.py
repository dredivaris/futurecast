# src/futurecast/chatbot/prediction_engine_interface.py
import copy
import logging
from typing import Dict, Any, Optional
from src.futurecast.prediction_engine import PredictionEngine
from src.futurecast.config import Config

logger = logging.getLogger(__name__)

class PredictionEngineInterface:
    """
    Interface to interact with the main PredictionEngine for chatbot-specific operations,
    like regenerating parts of the effect tree.
    """

    def __init__(self, prediction_engine: PredictionEngine, config: Config):
        """
        Initializes the PredictionEngineInterface.

        Args:
            prediction_engine: An instance of the main PredictionEngine.
            config: The application's configuration.
        """
        self.prediction_engine = prediction_engine
        self.config = config

    def _find_node_by_id_recursive(self, current_element: Any, target_id: str) -> Optional[Dict[str, Any]]:
        """
        Recursively searches for a node with the given target_id within the tree or sub-tree.
        Assumes node IDs are unique and stored in an 'id' field.
        The tree structure can be a dictionary of nodes (at the top level) or a single node
        which might have a 'children' list.
        """
        if isinstance(current_element, dict):
            # Check if the current_element itself is the target node
            if current_element.get('id') == target_id:
                return current_element

            # If current_element is a collection of top-level nodes (e.g., initial tree call)
            # Iterate through its values if they are dicts (potential nodes or branches)
            # This handles the case where current_element is like {"1": node1_data, "2": node2_data}
            is_top_level_dict_of_nodes = True
            # Check if all values in the dict are themselves dicts (a heuristic for top-level tree structure)
            if not all(isinstance(v, dict) for v in current_element.values()):
                is_top_level_dict_of_nodes = False
            
            if is_top_level_dict_of_nodes and target_id.split('.')[0] in current_element:
                 # This part is for the initial call where current_element is the main tree dict
                for key, value_node in current_element.items(): # Iterate through branches like "1", "2"
                    if isinstance(value_node, dict):
                        # Check if this top-level node is the one
                        if value_node.get('id') == target_id:
                            return value_node
                        # If not, recurse into its children
                        if 'children' in value_node and isinstance(value_node['children'], list):
                            for child_node_in_branch in value_node['children']:
                                found = self._find_node_by_id_recursive(child_node_in_branch, target_id)
                                if found:
                                    return found
                return None # Searched all top-level branches from main dict if target_id was not a key itself

            # If current_element is a single node (already identified or a child node from previous recursion)
            if 'children' in current_element and isinstance(current_element['children'], list):
                for child_node in current_element['children']:
                    found = self._find_node_by_id_recursive(child_node, target_id)
                    if found:
                        return found
        
        # If current_element is a list (e.g. a 'children' list passed directly)
        elif isinstance(current_element, list):
            for item_node in current_element: # Iterate through nodes in the list
                found = self._find_node_by_id_recursive(item_node, target_id)
                if found:
                    return found
        
        return None

    def expand_leaf_effect(self, current_tree: dict, leaf_effect_id: str, levels: int = 1, focus: str | None = None) -> dict | None:
        """
        Expands a leaf effect node by adding new child effects.

        Args:
            current_tree: The current effect tree.
            leaf_effect_id: The ID of the leaf effect to expand (e.g., "1.2.1").
            levels: The number of levels to expand by (default 1).
            focus: Optional focus for the expansion.

        Returns:
            The updated effect tree with new effects, or None if an error occurs.
        """
        if levels < 1:
            logger.error(f"Expansion levels must be 1 or greater. Received {levels}.")
            return None

        # It's crucial to work on a deep copy to avoid modifying the original tree directly
        # if the operation fails or if the caller expects the original to remain unchanged.
        updated_tree = copy.deepcopy(current_tree)
        
        node_to_expand = self._find_node_by_id_recursive(updated_tree, leaf_effect_id)

        if not node_to_expand:
            logger.error(f"Effect ID '{leaf_effect_id}' not found in the tree for expansion.")
            return None

        # Validate it's a leaf node (no children or empty children list)
        if 'children' in node_to_expand and node_to_expand['children']:
            logger.error(f"Effect ID '{leaf_effect_id}' is not a leaf node. Cannot expand a non-leaf node.")
            return None
        
        # Ensure 'children' list exists for adding new effects
        if 'children' not in node_to_expand or not isinstance(node_to_expand['children'], list):
            node_to_expand['children'] = []
        
        # Simulate PredictionEngine generating new effects
        current_parent_node_for_expansion = node_to_expand
        current_base_id_for_new_children = leaf_effect_id # This is the ID of the node we are expanding

        for i in range(levels):
            # Determine the number of existing children for the current parent in this expansion iteration
            num_children_at_this_level = len(current_parent_node_for_expansion['children'])
            
            new_child_local_suffix = str(num_children_at_this_level + 1)
            # The new child's full ID is based on its parent's full ID
            new_child_full_id = f"{current_base_id_for_new_children}.{new_child_local_suffix}"
            
            new_generated_child_node = {
                "id": new_child_full_id, # Store the full, unique ID
                "text": f"Generated Effect {new_child_full_id} (L{i+1} Focus: {focus if focus else 'N/A'})",
                "children": []  # New nodes are initially leaves
            }
            
            current_parent_node_for_expansion['children'].append(new_generated_child_node)
            
            # For the next level of expansion, the newly created child becomes the parent
            current_parent_node_for_expansion = new_generated_child_node
            # The base ID for the next level's children is the ID of the node just created
            current_base_id_for_new_children = new_child_full_id
            
        return updated_tree

    def _find_and_update_effect(self, tree_node: Dict[str, Any], effect_id_parts: list[str], new_text: str) -> bool:
        """
        Recursively finds an effect in the tree and updates its text.
        """
        current_id_part = effect_id_parts[0]
        
        # Check if the current node matches the first part of the ID
        # This assumes IDs are stored in a way that can be matched (e.g., node has an 'id' key or similar)
        # For this example, let's assume the keys of the dictionary are the first level of IDs,
        # and deeper levels are nested under a 'children' key which is a list of dicts.
        # This logic will need to be adapted to the actual structure of your effect_tree.

        if 'id' in tree_node and tree_node['id'] == current_id_part:
            if len(effect_id_parts) == 1: # This is the target node
                tree_node['text'] = new_text # Or however the text is stored
                return True
            else: # Target is deeper
                if 'children' in tree_node and isinstance(tree_node['children'], list):
                    for child_node in tree_node['children']:
                        if self._find_and_update_effect(child_node, effect_id_parts[1:], new_text):
                            return True
        # If the current node is a dictionary and the ID part is a key (for top-level effects)
        elif isinstance(tree_node, dict) and current_id_part in tree_node:
            if len(effect_id_parts) == 1: # This is the target node (e.g. "1", "2")
                # This assumes the value at tree_node[current_id_part] is the effect object
                # or a dict that contains the text.
                # Let's assume it's a dict with a 'text' key.
                if isinstance(tree_node[current_id_part], dict) and 'text' in tree_node[current_id_part]:
                    tree_node[current_id_part]['text'] = new_text
                    return True
                # If it's just the text directly (less likely for complex trees)
                # elif isinstance(tree_node[current_id_part], str):
                #     tree_node[current_id_part] = new_text # This would replace the whole node if it's just text
                #     return True
            else: # Target is deeper, e.g. "1.2" where "1" is current_id_part
                # This assumes tree_node[current_id_part] is the parent node for "2"
                if isinstance(tree_node[current_id_part], dict):
                     # We need to find the child that matches the next part of the ID.
                     # This requires knowing how children are stored. If 'children' is a list:
                    if 'children' in tree_node[current_id_part] and isinstance(tree_node[current_id_part]['children'], list):
                        for child_node in tree_node[current_id_part]['children']:
                            if self._find_and_update_effect(child_node, effect_id_parts[1:], new_text):
                                return True
                    # If children are keyed by their sub-ID part directly in a dict (e.g. effect_tree["1"]["children"]["2"])
                    # This part is highly dependent on the tree structure.
                    # For now, let's assume the list approach for children.
        return False


    def regenerate_downstream_effects(self, current_tree: Dict[str, Any], modified_effect_id: str, new_text: str) -> Optional[Dict[str, Any]]:
        """
        Finds the modified effect, updates its text, and simulates regeneration of downstream effects.

        Args:
            current_tree: The current effect tree.
            modified_effect_id: The ID of the effect that was modified (e.g., "1.2.3").
            new_text: The new text for the modified effect.

        Returns:
            The updated effect tree if successful, None otherwise.
        """
        import copy
        updated_tree = copy.deepcopy(current_tree)
        
        effect_id_parts = modified_effect_id.split('.')

        # Helper function to recursively find and update, then mark downstream
        def find_update_and_mark_downstream(node: Dict[str, Any], id_parts: list[str], text_to_update: str, is_downstream_of_modified: bool) -> bool:
            node_id_key = 'id' # Assuming 'id' key stores the comparable part of the ID. Adjust if different.
                               # For example, if node keys are "Effect 1", "Effect 1.1", this needs parsing.
                               # Or, if the node itself is keyed by its full ID in a flat dict, this is simpler.
                               # Given the example "1.2.3", it implies a nested structure.

            current_id_part_to_match = id_parts[0]
            
            # This is a simplified matching. Real matching depends on how IDs are stored and structured.
            # If node keys are "1", "2" at top level, and children have "1.1", "1.2"
            
            # Attempt to match the current part of the ID.
            # This logic needs to be robust based on actual tree structure.
            # For now, let's assume 'id' field holds the last segment of its ID, e.g., "3" for "1.2.3"
            # and we navigate based on the path.
            
            # This is a placeholder for finding the node.
            # Let's assume we have a function that can find a node by its full ID path.
            # For this simulation, we'll try a simplified recursive search.

            found_and_updated = False

            # If the node itself is the target (simplified for top-level or direct children)
            if node.get(node_id_key) == modified_effect_id: # If full ID is stored
                node['text'] = text_to_update
                # Mark all children as regenerated
                if 'children' in node and isinstance(node['children'], list):
                    for child in node['children']:
                        mark_all_downstream(child)
                return True

            # If we are trying to match parts of an ID path:
            if node.get(node_id_key) == current_id_part_to_match: # Matched a segment
                if len(id_parts) == 1: # This is the target node
                    node['text'] = text_to_update
                    found_and_updated = True
                    # Mark children as regenerated
                    if 'children' in node and isinstance(node['children'], list):
                        for child in node['children']:
                            mark_all_downstream(child) # Mark its direct children and their descendants
                    return True # Successfully updated
                else: # Need to go deeper
                    if 'children' in node and isinstance(node['children'], list):
                        for child_node in node['children']:
                            if find_update_and_mark_downstream(child_node, id_parts[1:], text_to_update, is_downstream_of_modified):
                                return True # Found and updated in a child path
            
            # If not matched by ID part, iterate through children if any
            if 'children' in node and isinstance(node['children'], list):
                for child_node in node['children']:
                     # If we already found and updated the target, all subsequent siblings at this level are NOT downstream of the *modified* node itself.
                     # However, if the current node *is* downstream of modified, its children also are.
                    if find_update_and_mark_downstream(child_node, id_parts, text_to_update, is_downstream_of_modified or found_and_updated):
                        # If the recursive call found and updated the node, propagate true
                        # This part of logic is tricky: once updated, how to mark only true downstream?
                        # The `is_downstream_of_modified` flag should be set true *after* the modified node is processed.
                        return True 
            
            # If the current node itself is downstream of the modified one (passed by parent)
            if is_downstream_of_modified and not found_and_updated: # and it's not the one we just updated
                if 'text' in node and isinstance(node['text'], str):
                    node['text'] += " (regenerated)"
                if 'children' in node and isinstance(node['children'], list):
                    for child_node in node['children']:
                        mark_all_downstream(child_node) # All its children are also downstream
            return found_and_updated


        def mark_all_downstream(node: Dict[str, Any]):
            if 'text' in node and isinstance(node['text'], str):
                node['text'] += " (regenerated)"
            if 'children' in node and isinstance(node['children'], list):
                for child in node['children']:
                    mark_all_downstream(child)

        # More robust way to find and update:
        def find_and_update_node_by_id_path(current_node_or_tree: Any, id_path_list: list[str], new_text_val: str) -> tuple[Optional[Dict[str, Any]], bool]:
            """
            Finds a node by its ID path (list of ID segments) and updates its text.
            Returns the found node (or None) and a flag indicating if it was the modified node.
            This function assumes a tree structure where children are in a 'children' list
            and each node has an 'id' that corresponds to a segment of the full ID path.
            Or, for the root, keys are the first ID segment.
            """
            if not id_path_list:
                return None, False

            current_id_segment = id_path_list[0]
            remaining_id_path = id_path_list[1:]

            if isinstance(current_node_or_tree, dict):
                # Case 1: Top level of the tree (e.g., current_tree is {'1': ..., '2': ...})
                if current_id_segment in current_node_or_tree:
                    target_branch = current_node_or_tree[current_id_segment]
                    if not remaining_id_path: # This is the target node
                        if isinstance(target_branch, dict) and 'text' in target_branch:
                            target_branch['text'] = new_text_val
                            return target_branch, True # Return the modified node and True
                        return None, False # Target found but not a valid effect node
                    else: # Go deeper into this branch
                        if isinstance(target_branch, dict) and 'children' in target_branch:
                             # Search within the children list of this branch
                            for child_node in target_branch['children']:
                                # Child IDs are expected to match the next segment
                                if isinstance(child_node, dict) and child_node.get('id') == remaining_id_path[0]:
                                    found_node, was_modified = find_and_update_node_by_id_path(child_node, remaining_id_path, new_text_val)
                                    if found_node:
                                        return found_node, was_modified
                        return None, False # Path not fully navigable
                # Case 2: current_node_or_tree is a node itself, not the whole tree dict
                elif current_node_or_tree.get('id') == current_id_segment:
                    if not remaining_id_path: # This node is the target
                        if 'text' in current_node_or_tree:
                            current_node_or_tree['text'] = new_text_val
                            return current_node_or_tree, True
                        return None, False # Target found but no text field
                    else: # Go deeper into children of this node
                        if 'children' in current_node_or_tree and isinstance(current_node_or_tree['children'], list):
                            for child_node in current_node_or_tree['children']:
                                # Child IDs are expected to match the next segment
                                if isinstance(child_node, dict) and child_node.get('id') == remaining_id_path[0]:
                                    found_node, was_modified = find_and_update_node_by_id_path(child_node, remaining_id_path, new_text_val)
                                    if found_node:
                                        return found_node, was_modified
                        return None, False # Path not fully navigable
            
            # If current_node_or_tree is a list (e.g. a 'children' list)
            elif isinstance(current_node_or_tree, list):
                for item_node in current_node_or_tree:
                    if isinstance(item_node, dict) and item_node.get('id') == current_id_segment:
                        # Found a node matching the current segment in the list
                        found_node, was_modified = find_and_update_node_by_id_path(item_node, id_path_list, new_text_val) # Pass full id_path_list again
                        if found_node:
                            return found_node, was_modified
            
            return None, False

        modified_node, _ = find_and_update_node_by_id_path(updated_tree, effect_id_parts, new_text)

        if modified_node:
            # Now, if a node was successfully modified, mark its children as "regenerated"
            # This assumes `modified_node` is a reference within `updated_tree`
            if 'children' in modified_node and isinstance(modified_node['children'], list):
                for child in modified_node['children']:
                    mark_all_downstream(child)
            return updated_tree
        else:
            # If the effect_id was not found or couldn't be updated.
            logger.error(f"Effect ID '{modified_effect_id}' not found or structure mismatch during regeneration.")
            return None


    # Fallback simplified find and update if the above is too complex for initial setup
    # This is a very basic placeholder and likely won't work for nested IDs like "1.2.3"
    # without significant adaptation to the tree's specific structure.
    def _simple_find_and_update(self, tree: Dict[str, Any], effect_id: str, new_text: str) -> bool:
        """A much simpler, likely insufficient, placeholder for finding/updating."""
        if effect_id in tree: # Only works for top-level IDs that are keys
            if isinstance(tree[effect_id], dict) and 'text' in tree[effect_id]:
                tree[effect_id]['text'] = new_text
                # Simulate regeneration for direct children if they exist
                if 'children' in tree[effect_id] and isinstance(tree[effect_id]['children'], list):
                    for child in tree[effect_id]['children']:
                        if isinstance(child, dict) and 'text' in child:
                            child['text'] += " (regenerated)"
                return True
            # If the effect_id points directly to text (less likely for complex structure)
            # elif isinstance(tree[effect_id], str):
            #     tree[effect_id] = new_text # This would overwrite the node if it's just text
            #     return True
        
        # Try to find in children recursively (very basic)
        for key, value in tree.items():
            if isinstance(value, dict):
                if self._simple_find_and_update(value, effect_id, new_text): # This won't work well with ID path
                    return True 
                if 'children' in value and isinstance(value['children'], list):
                    for child_node in value['children']:
                        if isinstance(child_node, dict):
                             # This recursive call needs to handle sub-parts of ID correctly
                             # For "1.2.3", if current node is "1", child might be "2" or "1.2"
                             # This simple recursion is not robust for path-based IDs.
                            if self._simple_find_and_update_child(child_node, effect_id, new_text): # Pass to a child-specific helper
                                return True
        return False

    def _simple_find_and_update_child(self, node: Dict[str, Any], effect_id: str, new_text: str) -> bool:
        """Helper for _simple_find_and_update to check a child node."""
        # This assumes child node 'id' might match the full effect_id, or part of it.
        # This is where the logic for ID "1.2.3" vs node ID "3" (if parent is "1.2") would go.
        # Highly dependent on actual tree structure.
        if node.get('id') == effect_id: # If child has a matching 'id' field
            if 'text' in node:
                node['text'] = new_text
                if 'children' in node and isinstance(node['children'], list):
                    for child in node['children']:
                        if isinstance(child, dict) and 'text' in child:
                            child['text'] += " (regenerated)"
                return True
        
        if 'children' in node and isinstance(node['children'], list):
            for child_node in node['children']:
                if isinstance(child_node, dict):
                    if self._simple_find_and_update_child(child_node, effect_id, new_text):
                        return True
        return False

if __name__ == '__main__':
    # Example Usage (requires PredictionEngine and Config instances)
    class MockPredictionEngine:
        def generate_initial_tree(self, *args, **kwargs): return {}
        def regenerate_branch(self, *args, **kwargs): return {}

    mock_config = Config() # Assuming Config can be instantiated simply
    
    # Sample effect tree structure (adjust to your actual structure)
    sample_tree = {
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

    # Simplified tree for testing find_and_update_node_by_id_path
    # where node 'id's are the last segment of their path.
    # This is a common way to represent trees if you also navigate by path.
    test_tree_structure = {
        "id": "root", # Dummy root
        "children": [
            {
                "id": "1", "text": "Effect 1",
                "children": [
                    {"id": "1", "text": "Effect 1.1"}, # ID here should be "1" if parent is "1"
                                                       # or "1.1" if full path. Let's use last segment.
                                                       # For "1.1", id is "1" (child of "1")
                                                       # For "1.1.1", id is "1" (child of "1.1")
                                                       # This means find_and_update_node_by_id_path needs careful ID segment matching.
                                                       # Let's assume node 'id' is the *last part* of its full ID.
                    {"id": "1", "text": "Effect 1.1", "full_id_debug": "1.1"}, # child of node with id "1"
                    {
                        "id": "2", "text": "Effect 1.2", "full_id_debug": "1.2", # child of node with id "1"
                        "children": [
                            {"id": "1", "text": "Effect 1.2.1", "full_id_debug": "1.2.1"} # child of node with id "2" (which is 1.2)
                        ]
                    }
                ]
            },
            {
                "id": "2", "text": "Effect 2", "full_id_debug": "2",
                "children": []
            }
        ]
    }
    # The find_and_update_node_by_id_path is designed for a tree where you pass the whole tree (or a sub-branch)
    # and a list of ID segments.
    # If tree is {'id':'root', children: [{'id':'1', ...}, {'id':'2', ...}]}
    # To find "1.2.1": path is ["1", "2", "1"]
    # 1. Look for "1" in root's children. Found. Recurse on this node with path ["2", "1"].
    # 2. Node "1" (Effect 1). Look for "2" in its children. Found (Effect 1.2). Recurse with path ["1"].
    # 3. Node "2" (Effect 1.2). Look for "1" in its children. Found (Effect 1.2.1). Path is empty. Update.

    # Let's refine the test_tree_structure to be more directly usable by the function
    # The function expects to match `current_id_segment` with `node.get('id')` when inside a children list,
    # or with a key if at the top level of a dict-based tree.

    # Test tree where keys are first ID part, and 'id' in node is the last part.
    # This is closer to `sample_tree` structure.
    interface = PredictionEngineInterface(MockPredictionEngine(), mock_config)

    print("Original Tree:")
    import json
    print(json.dumps(sample_tree, indent=2))

    # Test 1: Modify "1.2.1"
    updated_tree_1 = interface.regenerate_downstream_effects(sample_tree, "1.2.1", "NEW TEXT for 1.2.1")
    if updated_tree_1:
        print("\nTree after modifying 1.2.1:")
        print(json.dumps(updated_tree_1, indent=2))
    else:
        print("\nFailed to modify 1.2.1")

    # Test 2: Modify "2" (a top-level, no children to regenerate in this sample)
    updated_tree_2 = interface.regenerate_downstream_effects(sample_tree, "2", "NEW TEXT for 2")
    if updated_tree_2:
        print("\nTree after modifying 2:")
        print(json.dumps(updated_tree_2, indent=2))
    else:
        print("\nFailed to modify 2")

    # Test 3: Modify "1.1" (should regenerate its non-existent children, so just updates text)
    updated_tree_3 = interface.regenerate_downstream_effects(sample_tree, "1.1", "NEW TEXT for 1.1")
    if updated_tree_3:
        print("\nTree after modifying 1.1:")
        print(json.dumps(updated_tree_3, indent=2))
    else:
        print("\nFailed to modify 1.1")
        
    # Test 4: Non-existent ID
    updated_tree_4 = interface.regenerate_downstream_effects(sample_tree, "3.3.3", "TEXT for non-existent")
    if updated_tree_4:
        print("\nTree after modifying 3.3.3 (should not happen):")
        print(json.dumps(updated_tree_4, indent=2))
    else:
        print("\nFailed to modify 3.3.3 (as expected)")

    # Test 5: Modify "1.2" which has children
    # Create a fresh copy for this test
    tree_for_test5 = copy.deepcopy(sample_tree)
    updated_tree_5 = interface.regenerate_downstream_effects(tree_for_test5, "1.2", "NEW TEXT for 1.2")
    if updated_tree_5:
        print("\nTree after modifying 1.2 (child 1.2.1 should be regenerated):")
        print(json.dumps(updated_tree_5, indent=2))
        # Expected: Effect 1.2.1 text becomes "Effect 1.2.1 (regenerated)"
    else:
        print("\nFailed to modify 1.2")

    print("\n--- Testing expand_leaf_effect ---")

    # Test 6: Expand leaf node "1.1" by 1 level
    tree_for_test6 = copy.deepcopy(sample_tree)
    expanded_tree_6 = interface.expand_leaf_effect(tree_for_test6, "1.1", levels=1, focus="initial expansion")
    if expanded_tree_6:
        print("\nTree after expanding '1.1' by 1 level:")
        print(json.dumps(expanded_tree_6, indent=2))
    else:
        print("\nFailed to expand '1.1'")

    # Test 7: Expand leaf node "1.2.1" by 2 levels with focus
    tree_for_test7 = copy.deepcopy(sample_tree)
    expanded_tree_7 = interface.expand_leaf_effect(tree_for_test7, "1.2.1", levels=2, focus="deep dive")
    if expanded_tree_7:
        print("\nTree after expanding '1.2.1' by 2 levels with focus 'deep dive':")
        print(json.dumps(expanded_tree_7, indent=2))
    else:
        print("\nFailed to expand '1.2.1'")

    # Test 8: Attempt to expand a non-leaf node "1.2"
    tree_for_test8 = copy.deepcopy(sample_tree)
    expanded_tree_8 = interface.expand_leaf_effect(tree_for_test8, "1.2", levels=1)
    if expanded_tree_8:
        print("\nTree after attempting to expand non-leaf '1.2' (should not happen):")
        print(json.dumps(expanded_tree_8, indent=2))
    else:
        print("\nFailed to expand '1.2' (as expected, it's not a leaf node).")

    # Test 9: Attempt to expand a non-existent node "3"
    tree_for_test9 = copy.deepcopy(sample_tree)
    expanded_tree_9 = interface.expand_leaf_effect(tree_for_test9, "3", levels=1)
    if expanded_tree_9:
        print("\nTree after attempting to expand non-existent '3' (should not happen):")
        print(json.dumps(expanded_tree_9, indent=2))
    else:
        print("\nFailed to expand '3' (as expected, node not found).")
    
    # Test 10: Expand leaf node "2" by 1 level (no initial children)
    tree_for_test10 = copy.deepcopy(sample_tree)
    expanded_tree_10 = interface.expand_leaf_effect(tree_for_test10, "2", levels=1, focus="side effect")
    if expanded_tree_10:
        print("\nTree after expanding '2' by 1 level:")
        print(json.dumps(expanded_tree_10, indent=2))
    else:
        print("\nFailed to expand '2'")