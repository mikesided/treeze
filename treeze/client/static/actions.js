const actionHandlers = new Map([
    ['open_url', executeOpenUrl],
    ['reconnect', executeReconnect],
    ['emit_signal', executeEmitSignal],
]);


export function executeActions(actions) {
    for (const action of actions) {
        try {
            const handler = actionHandlers.get(action.type);

            if (!handler) {
                console.warn('Unknown Treeze client action:', action);
                continue;
            }

            handler(action);
        } catch (error) {
            console.error('Treeze client action failed:', action, error);
        }
    }
}


function executeOpenUrl(action) {
    const url = new URL(action.url, document.baseURI);

    if (!['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol)) {
        throw new Error(`Unsupported URL protocol: ${url.protocol}`);
    }

    if (action.new_tab) {
        window.open(url.href, '_blank', 'noopener,noreferrer');
    } else {
        window.location.assign(url.href);
    }
}

function executeReconnect(action) {
    window.dispatchEvent(new CustomEvent('treeze:reconnect', {
        detail: {
            query_params: action.query_params ?? {},
        },
    }));
}


function executeEmitSignal(action) {
    const element = document.querySelector(`[data-tz-id="${action.widget_id}"]`);
    if (!element || element.closest(':disabled, .tz-disabled')) {
        return;
    }
    element.dispatchEvent(new CustomEvent(action.browser_event, {
        detail: { args: action.args },
    }));
}
