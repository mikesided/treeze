import { executeActions } from './actions.js';
import { createPatchHandler } from './patches.js';

const applyPatch = createPatchHandler({ createElement, applyAttribute, applyStyle });

const socketUrl = new URL('/ws', window.location.href);
socketUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

let socket = null;

//const socket = new WebSocket(socketUrl);


// ============================================================================
// Connection
// ============================================================================

function connect(queryParams = {}) {
    if (socket) {
        socket.onmessage = null;
        socket.onclose = null;
        socket.onerror = null;
        socket.close(1000, 'Reconnecting');
    }

    const socketUrl = new URL('/ws', window.location.href);
    socketUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    for (const [key, value] of Object.entries(queryParams)) {
        socketUrl.searchParams.set(key, value);
    }

    const nextSocket = new WebSocket(socketUrl);
    socket = nextSocket;

    nextSocket.onopen = () => {
        console.log('Connected to Treeze');
    };

    nextSocket.onmessage = (event) => {
        if (socket !== nextSocket) {
            return;
        }

        handleMessage(JSON.parse(event.data));
    };

    nextSocket.onclose = () => {
        console.log('Disconnected from Treeze');
    };

    nextSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

window.addEventListener('treeze:reconnect', (event) => {
    connect(event.detail?.query_params ?? {});
});

connect();


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

        case 'server.actions':
            executeActions(message.payload.actions ?? []);
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
    executeActions(payload.actions ?? []);
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
            if (element.matches(':disabled')) {
                return;
            }
            const signalConfig = normalizeSignalConfig(eventConfig);
            executeActions(signalConfig.actions);
            if (!signalConfig.signal) {
                return;
            }
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
            actions: [],
        };
    }

    return {
        signal: eventConfig.signal,
        args: eventConfig.args ?? [],
        kwargs: eventConfig.kwargs ?? {},
        data: eventConfig.data ?? [],
        actions: eventConfig.actions ?? [],
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
