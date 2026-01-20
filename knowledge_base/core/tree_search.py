"""
Tree search utilities for knowledge base retrieval.
Provides helper functions for traversing and searching tree structures.
"""

from typing import Dict, List, Optional, Any, Generator
import logging

logger = logging.getLogger(__name__)


class TreeSearch:
    """
    Tree search utility class for traversing and searching PageIndex tree structures.
    """

    @staticmethod
    def find_node_by_id(tree: List[Dict], node_id: str) -> Optional[Dict]:
        """
        Find a node in the tree by its node_id.

        Args:
            tree: Tree structure (list of root nodes)
            node_id: Node ID to search for (e.g., '0005')

        Returns:
            Node dictionary if found, None otherwise
        """
        for node in tree:
            if node.get("node_id") == node_id:
                return node

            # Search in children
            child_nodes = node.get("nodes")
            if child_nodes:
                result = TreeSearch.find_node_by_id(child_nodes, node_id)
                if result:
                    return result

        return None

    @staticmethod
    def get_all_nodes(tree: List[Dict]) -> Generator[Dict, None, None]:
        """
        Generator that yields all nodes in the tree.

        Args:
            tree: Tree structure (list of root nodes)

        Yields:
            Each node in the tree
        """
        for node in tree:
            yield node

            # Recursively yield child nodes
            child_nodes = node.get("nodes")
            if child_nodes:
                yield from TreeSearch.get_all_nodes(child_nodes)

    @staticmethod
    def count_nodes(tree: List[Dict]) -> int:
        """
        Count total number of nodes in the tree.

        Args:
            tree: Tree structure (list of root nodes)

        Returns:
            Total number of nodes
        """
        return sum(1 for _ in TreeSearch.get_all_nodes(tree))

    @staticmethod
    def get_max_depth(tree: List[Dict], current_depth: int = 0) -> int:
        """
        Get the maximum depth of the tree.

        Args:
            tree: Tree structure (list of root nodes)
            current_depth: Current depth level

        Returns:
            Maximum depth of the tree
        """
        max_depth = current_depth

        for node in tree:
            child_nodes = node.get("nodes")
            if child_nodes:
                child_depth = TreeSearch.get_max_depth(child_nodes, current_depth + 1)
                max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def extract_text_from_node(node: Dict) -> str:
        """
        Extract text content from a node.

        Args:
            node: Node dictionary

        Returns:
            Text content of the node
        """
        return node.get("text", "")

    @staticmethod
    def get_leaf_nodes(tree: List[Dict]) -> List[Dict]:
        """
        Get all leaf nodes (nodes without children).

        Args:
            tree: Tree structure (list of root nodes)

        Returns:
            List of leaf nodes
        """
        leaf_nodes = []

        for node in tree:
            child_nodes = node.get("nodes")
            if not child_nodes:
                leaf_nodes.append(node)
            else:
                leaf_nodes.extend(TreeSearch.get_leaf_nodes(child_nodes))

        return leaf_nodes

    @staticmethod
    def search_by_title(tree: List[Dict], keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search for nodes by title keyword.

        Args:
            tree: Tree structure (list of root nodes)
            keyword: Keyword to search for in titles
            case_sensitive: Whether the search should be case sensitive

        Returns:
            List of matching nodes
        """
        results = []

        if not case_sensitive:
            keyword = keyword.lower()

        for node in tree:
            title = node.get("title", "")
            search_title = title if case_sensitive else title.lower()

            if keyword in search_title:
                results.append(node)

            # Search in children
            child_nodes = node.get("nodes")
            if child_nodes:
                results.extend(TreeSearch.search_by_title(child_nodes, keyword, case_sensitive))

        return results

    @staticmethod
    def get_node_path(tree: List[Dict], node_id: str) -> Optional[List[Dict]]:
        """
        Get the path from root to a node.

        Args:
            tree: Tree structure (list of root nodes)
            node_id: Target node ID

        Returns:
            List of nodes from root to target (inclusive), or None if not found
        """
        for node in tree:
            if node.get("node_id") == node_id:
                return [node]

            child_nodes = node.get("nodes")
            if child_nodes:
                path = TreeSearch.get_node_path(child_nodes, node_id)
                if path:
                    return [node] + path

        return None

    @staticmethod
    def get_node_siblings(tree: List[Dict], node_id: str) -> Optional[List[Dict]]:
        """
        Get siblings of a node (other nodes with the same parent).

        Args:
            tree: Tree structure (list of root nodes)
            node_id: Target node ID

        Returns:
            List of sibling nodes (excluding the target node), or None if not found
        """
        # Check if node is at root level
        for node in tree:
            if node.get("node_id") == node_id:
                # Return other root nodes
                return [n for n in tree if n.get("node_id") != node_id]

        # Search in children
        for node in tree:
            child_nodes = node.get("nodes")
            if child_nodes:
                for child in child_nodes:
                    if child.get("node_id") == node_id:
                        # Return siblings
                        return [s for s in child_nodes if s.get("node_id") != node_id]

                # Recursively search
                result = TreeSearch.get_node_siblings(child_nodes, node_id)
                if result is not None:
                    return result

        return None

    @staticmethod
    def flatten_tree(tree: List[Dict]) -> List[Dict]:
        """
        Flatten the tree structure into a list of nodes with path information.

        Args:
            tree: Tree structure (list of root nodes)

        Returns:
            List of nodes with additional 'path' field containing titles to root
        """
        def _flatten_with_path(nodes: List[Dict], current_path: List[str] = None) -> List[Dict]:
            if current_path is None:
                current_path = []

            result = []

            for node in nodes:
                # Create a copy of the node with path information
                node_copy = node.copy()
                node_copy["path"] = current_path + [node.get("title", "")]
                node_copy["path_depth"] = len(current_path)

                result.append(node_copy)

                # Process children
                child_nodes = node.get("nodes")
                if child_nodes:
                    result.extend(_flatten_with_path(
                        child_nodes,
                        current_path + [node.get("title", "")]
                    ))

            return result

        return _flatten_with_path(tree)

    @staticmethod
    def filter_nodes_by_depth(tree: List[Dict], min_depth: int = 0, max_depth: int = None) -> List[Dict]:
        """
        Filter nodes by their depth level.

        Args:
            tree: Tree structure (list of root nodes)
            min_depth: Minimum depth (inclusive, 0 = root level)
            max_depth: Maximum depth (inclusive, None = no limit)

        Returns:
            List of nodes within the specified depth range
        """
        def _filter_by_depth(nodes: List[Dict], current_depth: int = 0) -> List[Dict]:
            result = []

            if max_depth is not None and current_depth > max_depth:
                return result

            for node in nodes:
                if current_depth >= min_depth:
                    result.append(node)

                child_nodes = node.get("nodes")
                if child_nodes:
                    result.extend(_filter_by_depth(child_nodes, current_depth + 1))

            return result

        return _filter_by_depth(tree)

    @staticmethod
    def get_tree_statistics(tree: List[Dict]) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the tree structure.

        Args:
            tree: Tree structure (list of root nodes)

        Returns:
            Dictionary containing tree statistics
        """
        all_nodes = list(TreeSearch.get_all_nodes(tree))

        # Count nodes at each depth
        depth_counts = {}

        def _count_depth(nodes: List[Dict], depth: int = 0):
            for node in nodes:
                depth_counts[depth] = depth_counts.get(depth, 0) + 1

                child_nodes = node.get("nodes")
                if child_nodes:
                    _count_depth(child_nodes, depth + 1)

        _count_depth(tree)

        return {
            "total_nodes": len(all_nodes),
            "max_depth": TreeSearch.get_max_depth(tree),
            "root_nodes": len(tree),
            "leaf_nodes": len(TreeSearch.get_leaf_nodes(tree)),
            "nodes_by_depth": depth_counts,
            "avg_nodes_per_level": sum(depth_counts.values()) / len(depth_counts) if depth_counts else 0,
        }
