const socket = new WebSocket('ws://localhost:8000/ws');


socket.onopen = () => {
    console.log('Connected to Treeze');
};


socket.onmessage = (event) => {
    const message = JSON.parse(event.data);

    handleMessage(message);
};


socket.onclose = () => {
    console.log('Disconnected from Treeze');
};


socket.onerror = (error) => {
    console.error('WebSocket error:', error);
};


// ============================================================================
// Protocol
// ============================================================================

function sendMessage(type, payload = {}) {
    socket.send(JSON.stringify({
        type,
        payload,
    }));
}


function sendSignal(widgetId, signalName, args = [], kwargs = {}) {
    sendMessage('client.signal', {
        widget_id: widgetId,
        signal: signalName,
        args,
        kwargs,
    });
}


function handleMessage(message) {
    if (!message || typeof message !== 'object') {
        console.warn('Invalid Treeze message:', message);
        return;
    }

    switch (message.type) {
        case 'server.render':
            handleRenderMessage(message.payload);
            return;

        case 'server.patches':
            handlePatchesMessage(message.payload);
            return;

        case 'server.dialog':
            handleDialogMessage(message.payload);
            return;

        default:
            console.warn('Unknown Treeze message:', message);
    }
}


function handleRenderMessage(payload) {
    const rootNode = payload.root;

    console.log('Received render:', rootNode);

    const element = createElement(rootNode);

    document
        .getElementById('tz-root')
        .replaceChildren(element);
}


function handlePatchesMessage(payload) {
    console.log('Received patches:', payload.patches);

    for (const patch of payload.patches ?? []) {
        applyPatch(patch);
    }
}


function handleDialogMessage(payload) {
    const title = payload.title ?? 'Treeze';
    const message = payload.message ?? 'An unknown error occurred.';

    alert(`${title}\n\n${message}`);
}


// ============================================================================
// Rendering
// ============================================================================

function createElement(node) {
    const element = document.createElement(node.tag);

    element.dataset.tzId = node.id;

    applyText(element, node.text);
    applyAttributes(element, node.attributes ?? {});
    applyProperties(element, node.properties ?? {});
    applyClasses(element, node.classes ?? []);
    applyStyles(element, node.styles ?? {});
    bindEvents(element, node.events ?? {}, node.id);

    for (const child of node.children ?? []) {
        element.appendChild(
            createElement(child)
        );
    }

    return element;
}


function applyText(element, text) {
    if (text === null || text === undefined) {
        return;
    }

    element.textContent = String(text);
}


function applyAttributes(element, attributes) {
    for (const [name, value] of Object.entries(attributes)) {
        applyAttribute(element, name, value);
    }
}


function applyAttribute(element, name, value) {
    if (value === false || value === null || value === undefined) {
        element.removeAttribute(name);
        return;
    }

    if (value === true) {
        element.setAttribute(name, '');
        return;
    }

    element.setAttribute(name, String(value));
}


function applyProperties(element, properties) {
    for (const [name, value] of Object.entries(properties)) {
        element[name] = value;
    }
}


function applyClasses(element, classes) {
    for (const className of classes) {
        element.classList.add(className);
    }
}


function applyStyles(element, styles) {
    for (const [name, value] of Object.entries(styles)) {
        applyStyle(element, name, value);
    }
}


function applyStyle(element, name, value) {
    if (value === null || value === undefined) {
        element.style.removeProperty(name);
        return;
    }

    element.style.setProperty(name, String(value));
}


// ============================================================================
// Events
// ============================================================================

function bindEvents(element, events, widgetId) {
    for (const [browserEvent, eventConfig] of Object.entries(events)) {
        element.addEventListener(browserEvent, (event) => {
            const signalConfig = normalizeSignalConfig(eventConfig);
            const eventArgs = collectEventArgs(
                element,
                event,
                signalConfig.data,
            );

            sendSignal(
                widgetId,
                signalConfig.signal,
                [
                    ...signalConfig.args,
                    ...eventArgs,
                ],
                signalConfig.kwargs,
            );
        });
    }
}


function normalizeSignalConfig(eventConfig) {
    if (typeof eventConfig === 'string') {
        return {
            signal: eventConfig,
            args: [],
            kwargs: {},
            data: [],
        };
    }

    return {
        signal: eventConfig.signal,
        args: eventConfig.args ?? [],
        kwargs: eventConfig.kwargs ?? {},
        data: eventConfig.data ?? [],
    };
}


function collectEventArgs(element, event, dataNames) {
    const args = [];

    for (const dataName of dataNames) {
        switch (dataName) {
            case 'value':
                if ('value' in element) {
                    args.push(element.value);
                }
                break;

            case 'checked':
                if ('checked' in element) {
                    args.push(element.checked);
                }
                break;

            case 'text':
                args.push(element.textContent ?? '');
                break;

            case 'event_type':
                args.push(event.type);
                break;

            default:
                console.warn('Unknown Treeze event data name:', dataName);
        }
    }

    return args;
}


// ============================================================================
// Patches
// ============================================================================

function applyPatch(patch) {
    switch (patch.op) {
        case 'set_text':
            applySetTextPatch(patch);
            return;

        case 'set_attribute':
            applySetAttributePatch(patch);
            return;

        case 'set_property':
            applySetPropertyPatch(patch);
            return;

        case 'set_style':
            applySetStylePatch(patch);
            return;

        case 'add_class':
            applyAddClassPatch(patch);
            return;

        case 'remove_class':
            applyRemoveClassPatch(patch);
            return;

        case 'append_child':
            applyAppendChildPatch(patch);
            return;

        default:
            console.warn('Unknown Treeze patch:', patch);
    }
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