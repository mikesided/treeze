# Contributing to Treeze

Thanks for contributing to Treeze.

Treeze is a Python-first UI framework rendered to the browser. The main design goal is to keep application logic in Python while keeping the browser client generic.

## Project principles

- Python widget state is the source of truth.
- Widgets render to serializable `Node` objects.
- The browser applies generic render and patch messages.
- Widgets should not talk directly to the websocket.
- Runtime/session code owns browser communication.
- Public widget attributes are treated as render-affecting state.
- Internal framework state should use private attributes.