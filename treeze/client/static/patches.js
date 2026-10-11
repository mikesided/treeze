// Rendering helpers are supplied by client.js to avoid circular imports.
export function createPatchHandler({ createElement, applyAttribute, applyStyle }) {
    // ============================================================================
    // Patches
    // ============================================================================

    const patchHandlers = new Map([
        ['set_text', applySetTextPatch],
        ['set_attribute', applySetAttributePatch],
        ['set_property', applySetPropertyPatch],
        ['set_style', applySetStylePatch],
        ['add_class', applyAddClassPatch],
        ['remove_class', applyRemoveClassPatch],
        ['append_child', applyAppendChildPatch],
        ['replace_node', applyReplaceNodePatch],
        ['replace_children', applyReplaceChildrenPatch],
        ['insert_child', applyInsertChildPatch],
        ['remove_node', applyRemoveNodePatch],
    ]);


    function applyPatch(patch) {
        const handler = patchHandlers.get(patch.op);

        if (!handler) {
            console.warn('Unknown Treeze patch:', patch);
            return;
        }

        handler(patch);
    }


    function findElementByWidgetId(widgetId) {
        return document.querySelector(`[data-tz-id="${widgetId}"]`);
    }


    function applySetTextPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.textContent = patch.data.value ?? '';
    }


    function applySetAttributePatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        applyAttribute(
            element,
            patch.data.name,
            patch.data.value,
        );
    }


    function applySetPropertyPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element[patch.data.name] = patch.data.value;
    }


    function applySetStylePatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        applyStyle(
            element,
            patch.data.name,
            patch.data.value,
        );
    }


    function applyAddClassPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.classList.add(patch.data.name);
    }


    function applyRemoveClassPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.classList.remove(patch.data.name);
    }


    function applyAppendChildPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        const child = createElement(patch.data.child);

        element.appendChild(child);
    }

    function applyReplaceNodePatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.replaceWith(
            createElement(patch.data.node),
        );
    }

    function applyReplaceChildrenPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.replaceChildren(
            ...patch.data.children.map((child) => createElement(child)),
        );
    }

    function applyInsertChildPatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        const child = createElement(patch.data.child);
        const index = patch.data.index;
        const referenceElement = element.children[index] ?? null;

        element.insertBefore(child, referenceElement);
    }


    function applyRemoveNodePatch(patch) {
        const element = findElementByWidgetId(patch.target_id);

        if (!element) {
            console.warn('Patch target not found:', patch);
            return;
        }

        element.remove();
    }

    return applyPatch;
}
