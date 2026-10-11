const actionHandlers = new Map([
    ['open_url', executeOpenUrl],
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
