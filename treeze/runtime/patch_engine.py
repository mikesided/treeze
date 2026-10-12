"""
Name:         patch_engine.py
Description:  Runtime engine to generate patches

"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .patches import Patch, SerializedNode, diff_subtrees

if TYPE_CHECKING:
    from ..core.node import Node
    from ..core.widget import Widget

# ______________________________________________________________________________________________________________________

class PatchEngine:
    def __init__(self) -> None:
        self._nodes: dict[str, SerializedNode] = {}
        self._parents: dict[str, str | None] = {}
        self._positions: dict[str, int] = {}

    def capture_tree(self, root: Node) -> None:
        self._parents.clear()
        self._positions.clear()
        self._nodes = self._index_tree(root.serialize())

    def create_patches_for_dirty_widgets(
        self,
        dirty_widgets: set[Widget],
    ) -> list[Patch]:
        if not dirty_widgets:
            return []

        dirty_ids = {widget.id for widget in dirty_widgets}
        roots = []
        # Choose non-overlapping boundaries using the previous ownership index.
        # Both source and destination are dirty when a child is transferred.
        for node_id in sorted(dirty_ids):
            if node_id not in self._nodes:
                continue
            parent_id = self._parents[node_id]
            while parent_id is not None and parent_id not in dirty_ids:
                parent_id = self._parents[parent_id]
            if parent_id is None:
                roots.append(node_id)
        if not roots:
            return []

        updates = {
            widget.id: widget._build().serialize()
            for widget in self._normalize_dirty_widgets(dirty_widgets)
        }

        def updated_subtree(node: SerializedNode) -> SerializedNode:
            if node['id'] in updates:
                return updates[node['id']]
            return {**node, 'children': [updated_subtree(child) for child in node.get('children', [])]}

        old_subtrees = [self._nodes[node_id] for node_id in roots]
        new_subtrees = [updated_subtree(node) for node in old_subtrees]
        patches = diff_subtrees(old_subtrees, new_subtrees)

        # Keep ancestor snapshots coherent by replacing the child reference.
        # No ancestor's other subtrees are rebuilt, diffed, or reindexed.
        owners = {node_id: (self._parents[node_id], self._positions.get(node_id)) for node_id in roots}
        for node in new_subtrees:
            parent_id, position = owners[node['id']]
            if parent_id is not None:
                self._nodes[parent_id]['children'][position] = node
        old_ids = set()
        for node in old_subtrees:
            old_ids.update(self._collect_ids(node))
        for node_id in old_ids:
            self._nodes.pop(node_id, None)
            self._parents.pop(node_id, None)
            self._positions.pop(node_id, None)
        for node in new_subtrees:
            parent_id, position = owners[node['id']]
            self._nodes.update(self._index_tree(node, parent_id, position))
        return patches

    def _normalize_dirty_widgets(
        self,
        dirty_widgets: set[Widget],
    ) -> list[Widget]:
        normalized: list[Widget] = []

        for widget in dirty_widgets:
            if self._has_dirty_ancestor(widget, dirty_widgets):
                continue

            normalized.append(widget)

        return sorted(normalized, key=lambda widget: widget.id)

    def _has_dirty_ancestor(
        self,
        widget: Widget,
        dirty_widgets: set[Widget],
    ) -> bool:
        parent = widget.parent

        while parent is not None:
            if parent in dirty_widgets:
                return True

            parent = parent.parent

        return False

    def _index_tree(
        self,
        node: SerializedNode,
        parent_id: str | None = None,
        position: int | None = None,
    ) -> dict[str, SerializedNode]:
        nodes = {node['id']: node}
        self._parents[node['id']] = parent_id
        if position is not None:
            self._positions[node['id']] = position
        for index, child in enumerate(node.get('children', [])):
            nodes.update(self._index_tree(child, node['id'], index))
        return nodes

    def _collect_ids(self, node: SerializedNode) -> set[str]:
        ids = {
            node['id'],
        }

        for child in node.get('children', []):
            ids.update(
                self._collect_ids(child)
            )

        return ids