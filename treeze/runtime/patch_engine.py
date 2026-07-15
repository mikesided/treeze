"""
Name:         patch_engine.py
Description:  Runtime engine to generate patches

"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .patches import Patch, SerializedNode, diff_nodes

if TYPE_CHECKING:
    from ..core.node import Node
    from ..core.widget import Widget

# ______________________________________________________________________________________________________________________

class PatchEngine:
    def __init__(self) -> None:
        self._nodes: dict[str, SerializedNode] = {}

    def capture_tree(self, root: Node) -> None:
        self._nodes = self._index_tree(root.serialize())

    def create_patches_for_dirty_widgets(
        self,
        dirty_widgets: set[Widget],
    ) -> list[Patch]:
        patches: list[Patch] = []

        for widget in self._normalize_dirty_widgets(dirty_widgets):
            new_node = widget._build()
            new_serialized = new_node.serialize()
            old_serialized = self._nodes.get(new_serialized['id'])

            if old_serialized is None:
                continue

            patches.extend(
                diff_nodes(old_serialized, new_serialized)
            )

            self._replace_indexed_subtree(
                old_serialized=old_serialized,
                new_serialized=new_serialized,
            )

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

    def _replace_indexed_subtree(
        self,
        old_serialized: SerializedNode,
        new_serialized: SerializedNode,
    ) -> None:
        for node_id in self._collect_ids(old_serialized):
            self._nodes.pop(node_id, None)

        self._nodes.update(
            self._index_tree(new_serialized)
        )

    def _index_tree(
        self,
        node: SerializedNode,
    ) -> dict[str, SerializedNode]:
        nodes = {
            node['id']: node,
        }

        for child in node.get('children', []):
            nodes.update(
                self._index_tree(child)
            )

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