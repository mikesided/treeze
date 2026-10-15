"""
Name:         patches.py
Description:  Runtime module to generate widget patches
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

from typing import Any

from ..core.enums import PatchOp

SerializedNode = dict[str, Any]
Patch = dict[str, Any]
# ______________________________________________________________________________________________________________________


def diff_subtrees(old: list[SerializedNode], new: list[SerializedNode]) -> list[Patch]:
    """Compare affected subtree snapshots together to recognize transferred IDs.

    The roots must be unchanged ownership boundaries, with no overlapping
    subtrees in either snapshot. The synthetic parent never reaches the client.
    """
    boundary_id = '__patch_forest__'

    def index_tree(roots):
        nodes = {boundary_id: {'id': boundary_id, 'tag': 'div', 'children': roots}}
        parents = {boundary_id: None}

        def visit(node, parent_id):
            nodes[node['id']] = node
            parents[node['id']] = parent_id
            for child in node.get('children', []):
                visit(child, node['id'])

        for root in roots:
            visit(root, boundary_id)
        return nodes, parents

    old_nodes, current_parents = index_tree(old)
    new_nodes, new_parents = index_tree(new)
    positions = {
        child['id']: index
        for node in new_nodes.values()
        for index, child in enumerate(node.get('children', []))
    }
    children = {
        node_id: [child['id'] for child in node.get('children', [])]
        for node_id, node in old_nodes.items()
    }
    patches: list[Patch] = []
    updates: list[Patch] = []

    # Visit parents before children so new destinations exist before a move.
    for node_id, node in new_nodes.items():
        if node_id == boundary_id:
            continue
        shallow = {**node, 'children': []}
        previous = old_nodes.get(node_id)
        if previous is None:
            parent_id = new_parents[node_id]
            patches.append({
                'op': PatchOp.APPEND_CHILD, 'target_id': parent_id,
                'data': {'child': shallow},
            })
            children[node_id] = []
            children[parent_id].append(node_id)
            current_parents[node_id] = parent_id
        elif previous.get('tag') != node.get('tag'):
            patches.append({
                'op': PatchOp.REPLACE_NODE, 'target_id': node_id,
                'data': {'node': shallow, 'preserve_children': True},
            })
        else:
            updates.extend(diff_nodes({**previous, 'children': []}, shallow))

        parent_id = new_parents[node_id]
        if parent_id == boundary_id:
            continue
        position = positions[node_id]
        siblings = children[parent_id]
        if current_parents[node_id] != parent_id or siblings.index(node_id) != position:
            patches.append({
                'op': PatchOp.MOVE_CHILD, 'target_id': node_id,
                'data': {'parent_id': parent_id, 'index': position},
            })
            children[current_parents[node_id]].remove(node_id)
            siblings.insert(position, node_id)
            current_parents[node_id] = parent_id

    # Save surviving descendants before removing their former parent nodes.
    removed = old_nodes.keys() - new_nodes.keys()
    for node_id in old_nodes:
        if node_id in removed and current_parents[node_id] not in removed:
            patches.append({'op': PatchOp.REMOVE_NODE, 'target_id': node_id, 'data': {}})
    return patches + updates


def diff_nodes(old: SerializedNode, new: SerializedNode) -> list[Patch]:
    patches: list[Patch] = []
    _diff_node(old, new, patches)
    return patches


def _diff_node(
    old: SerializedNode,
    new: SerializedNode,
    patches: list[Patch],
) -> None:
    old_id = old['id']
    new_id = new['id']

    if old_id != new_id or old.get('tag') != new.get('tag'):
        patches.append({
            'op': PatchOp.REPLACE_NODE,
            'target_id': old_id,
            'data': {
                'node': new,
            },
        })
        return

    target_id = new_id

    if old.get('events', {}) != new.get('events', {}):
        patches.append({
            'op': PatchOp.SET_EVENTS,
            'target_id': target_id,
            'data': {'events': new.get('events', {})},
        })

    if old.get('text') != new.get('text'):
        patches.append({
            'op': PatchOp.SET_TEXT,
            'target_id': target_id,
            'data': {
                'value': new.get('text'),
            },
        })

    _diff_mapping(
        patches=patches,
        op=PatchOp.SET_ATTRIBUTE,
        target_id=target_id,
        old=old.get('attributes', {}),
        new=new.get('attributes', {}),
    )

    _diff_mapping(
        patches=patches,
        op=PatchOp.SET_PROPERTY,
        target_id=target_id,
        old=old.get('properties', {}),
        new=new.get('properties', {}),
    )

    _diff_mapping(
        patches=patches,
        op=PatchOp.SET_STYLE,
        target_id=target_id,
        old=old.get('styles', {}),
        new=new.get('styles', {}),
    )

    _diff_classes(
        patches=patches,
        target_id=target_id,
        old=old.get('classes', []),
        new=new.get('classes', []),
    )

    _diff_children(
        patches=patches,
        target_id=target_id,
        old=old.get('children', []),
        new=new.get('children', []),
    )


def _diff_mapping(
    patches: list[Patch],
    op: PatchOp,
    target_id: str,
    old: dict[str, Any],
    new: dict[str, Any],
) -> None:
    names = set(old) | set(new)

    for name in sorted(names):
        old_value = old.get(name)
        new_value = new.get(name)

        if old_value == new_value:
            continue

        patches.append({
            'op': op,
            'target_id': target_id,
            'data': {
                'name': name,
                'value': new_value,
            },
        })


def _diff_classes(
    patches: list[Patch],
    target_id: str,
    old: list[str],
    new: list[str],
) -> None:
    old_classes = set(old)
    new_classes = set(new)

    for class_name in sorted(new_classes - old_classes):
        patches.append({
            'op': PatchOp.ADD_CLASS,
            'target_id': target_id,
            'data': {
                'name': class_name,
            },
        })

    for class_name in sorted(old_classes - new_classes):
        patches.append({
            'op': PatchOp.REMOVE_CLASS,
            'target_id': target_id,
            'data': {
                'name': class_name,
            },
        })

def _diff_children(
    patches: list[Patch],
    target_id: str,
    old: list[SerializedNode],
    new: list[SerializedNode],
) -> None:
    old_ids = [
        child['id']
        for child in old
    ]

    new_ids = [
        child['id']
        for child in new
    ]

    if old_ids == new_ids:
        _diff_shared_children(old, new, patches)
        return

    if _is_simple_append(old_ids, new_ids):
        _diff_shared_children(old, new, patches)

        for child in new[len(old):]:
            patches.append({
                'op': PatchOp.APPEND_CHILD,
                'target_id': target_id,
                'data': {
                    'child': child,
                },
            })

        return

    insert_index = _simple_insert_index(old_ids, new_ids)

    if insert_index is not None:
        _diff_shared_children(old, new, patches)

        inserted_count = len(new_ids) - len(old_ids)
        inserted_children = new[
            insert_index:insert_index + inserted_count
        ]

        for offset, child in enumerate(inserted_children):
            patches.append({
                'op': PatchOp.INSERT_CHILD,
                'target_id': target_id,
                'data': {
                    'index': insert_index + offset,
                    'child': child,
                },
            })

        return

    removed_ids = _simple_removed_ids(old_ids, new_ids)

    if removed_ids is not None:
        _diff_shared_children(old, new, patches)

        for removed_id in removed_ids:
            patches.append({
                'op': PatchOp.REMOVE_NODE,
                'target_id': removed_id,
                'data': {},
            })

        return

    patches.append({
        'op': PatchOp.REPLACE_CHILDREN,
        'target_id': target_id,
        'data': {
            'children': new,
        },
    })

def _diff_shared_children(
    old: list[SerializedNode],
    new: list[SerializedNode],
    patches: list[Patch],
) -> None:
    old_by_id = {
        child['id']: child
        for child in old
    }

    for new_child in new:
        old_child = old_by_id.get(new_child['id'])

        if old_child is None:
            continue

        _diff_node(old_child, new_child, patches)

def _is_simple_append(old_ids: list[str], new_ids: list[str]) -> bool:
    if len(new_ids) <= len(old_ids):
        return False

    return new_ids[:len(old_ids)] == old_ids


def _simple_insert_index(
    old_ids: list[str],
    new_ids: list[str],
) -> int | None:
    if len(new_ids) <= len(old_ids):
        return None

    inserted_count = len(new_ids) - len(old_ids)

    for index in range(len(new_ids)):
        without_inserted = (
            new_ids[:index]
            + new_ids[index + inserted_count:]
        )

        if without_inserted == old_ids:
            return index

    return None


def _simple_removed_ids(
    old_ids: list[str],
    new_ids: list[str],
) -> list[str] | None:
    if len(new_ids) >= len(old_ids):
        return None

    removed_count = len(old_ids) - len(new_ids)

    for index in range(len(old_ids)):
        removed_ids = old_ids[index:index + removed_count]

        without_removed = (
            old_ids[:index]
            + old_ids[index + removed_count:]
        )

        if without_removed == new_ids:
            return removed_ids

    return None
