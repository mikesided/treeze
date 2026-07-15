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

    # Events are annoying to patch safely because the browser listener may need
    # to be removed/rebound. For now, replace the node if event bindings change.
    if old.get('events', {}) != new.get('events', {}):
        patches.append({
            'op': PatchOp.REPLACE_NODE,
            'target_id': target_id,
            'data': {
                'node': new,
            },
        })
        return

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
        for old_child, new_child in zip(old, new):
            _diff_node(old_child, new_child, patches)

        return

    if _is_simple_append(old_ids, new_ids):
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
        inserted_children = new[
            insert_index:insert_index + len(new_ids) - len(old_ids)
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