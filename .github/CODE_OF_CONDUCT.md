# Contributing to Treeze

Thanks for contributing to Treeze.

Treeze is a Python-first UI framework rendered to the browser. The main design goal is to keep application logic in Python while keeping the browser client generic.

## Project principles

* Python widget state is the source of truth.
* Widgets render to serializable `Node` objects.
* The browser applies generic render and patch messages.
* Widgets should not talk directly to the websocket.
* Runtime/session code owns browser communication.
* Public widget attributes are treated as render-affecting state.
* Internal framework state should use private attributes.

## Development setup

Clone the repository:

```bash
git clone https://github.com/mikesided/treeze.git
cd treeze
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install in editable mode:

```bash
pip install -e .
```

Run an example:

```bash
python examples/hello.py
```

Then open the local URL printed by the server.

## Code style

Treeze code should be simple, explicit, and framework-friendly.

Preferred style:

* Use single quotes in Python.
* Keep public APIs clean and Pythonic.
* Prefer small methods over large hard-to-follow methods.
* Raise `TreezeException` subclasses for end-user errors.
* Raise regular Python exceptions for internal framework bugs.
* Avoid exposing browser concepts in the Python API unless necessary.

## Dirty tracking rules

Treeze uses dirty tracking to decide which widgets need to be re-rendered after a signal mutates widget state.

Convention:

* Public attributes are render-affecting and mark the widget dirty automatically.
* Private attributes are internal and do not mark the widget dirty unless explicitly allow-listed.
* In-place mutations are not detected by `__setattr__`, so methods like `add_widget()`, `remove_widget()`, `add_class()`, and `remove_class()` must call `_mark_dirty()` themselves.

## Runtime update flow

Treeze updates the browser through render messages and patches.

The normal signal flow is:

```text
client signal
→ Python signal handler mutates widget state
→ dirty widgets are collected
→ patch engine rebuilds/diffs dirty widgets
→ server sends patches
→ browser applies patches
```

Patch generation should stay centralized in the runtime. Individual widgets should not manually send websocket messages.

## Pull requests

Before opening a pull request:

* Keep the change focused.
* Link the related issue.
* Run a relevant example.
* Check the browser console.
* Check the Python server logs.
* Add tests or manual validation notes when useful.

## Issues

Use the provided issue templates for bugs, features, tasks, refactors, docs, tests, performance work, and investigations.

Small issues are preferred over large vague issues.
