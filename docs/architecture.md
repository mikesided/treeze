# Treeze Architecture

## Vision

Treeze is a **Python-first retained-mode UI framework** that renders natively to the web.

Applications are written entirely in Python. Treeze is responsible for synchronizing the application state with the browser through a lightweight renderer.

The browser is treated as a rendering engine, not as the application's source of truth.

---

# Core Principles

## Python First

The public API should always feel like writing Python, not HTML or JavaScript.

Good:

```python
layout = VLayout()
layout.add_widget(Button(text="Save"))
```

Avoid exposing browser concepts unless necessary.

---

## Web Only

Treeze targets modern web browsers exclusively.

This allows Treeze to leverage:

* HTML
* CSS
* Flexbox
* Grid
* Browser animations
* Browser accessibility
* Browser performance

Treeze does **not** attempt to implement its own rendering engine.

---

## Retained Mode

Treeze uses a retained widget tree.

Widgets remain alive for the lifetime of the application.

Example:

```
Widget Tree

App
└── VLayout
    ├── Button
    ├── Label
    └── Button
```

Widgets own state.

The browser simply reflects that state.

---

# Rendering Pipeline

```
Python Widgets
        │
        ▼
Node Tree
        │
        ▼
Serialized JSON
        │
        ▼
WebSocket
        │
        ▼
JavaScript Renderer
        │
        ▼
DOM
        │
        ▼
CSS
        │
        ▼
Browser
```

Each widget builds a retained `Node`.

The JavaScript renderer is intentionally generic and knows nothing about Treeze widgets.

---

# Widget Hierarchy

```
Widget
│
├── Button
├── Label
├── .....
│
└── Container
    │
    ├── Layout
    │   ├── VLayout
    │   ├── HLayout
    │   ├── HLayout
    │   └── ....
    │
    ├── ...
```

Every widget has at most one parent.

Only containers may own children.

---

# Ownership

Containers own widgets.

Users manipulate the tree using:

```python
layout.add_widget(button)
layout.remove_widget(button)
```

Widgets expose a read-only `parent`.

Changing parent relationships is managed internally.

---

# Node

A `Node` is the low-level representation of a widget.

It is renderer-agnostic.

Example:

```python
Node(
    tag="button",
    classes=["tz-button"],
    styles={
        "--tz-padding": "8px"
    },
    properties={
        "textContent": "Save"
    }
)
```

Nodes are serialized and sent to the browser.

---

# Styling

Treeze uses CSS as its styling engine.

Python describes intent.

CSS describes appearance.

Example:

```python
layout.set_spacing(10)
layout.set_alignment(Alignment.CENTER)
```

becomes CSS variables:

```css
--tz-spacing: 10px;
--tz-alignment: center;
```

Framework widgets provide stable CSS class names.

Example:

```
tz-button
tz-label
tz-vertical-layout
```

Applications may provide their own CSS to override framework defaults.

---

# JavaScript Renderer

The JavaScript renderer is intentionally small.

Its responsibilities are:

* Create DOM elements
* Apply properties
* Apply classes
* Apply inline styles
* Attach events
* Update the DOM

It should never contain widget-specific logic.

If a new widget requires changes to the renderer, the widget design should be reconsidered.

---

# Events

Treeze supports two categories of events.

## Server-side events

Used when Python application logic should execute.

Example:

```python
button.clicked.connect(
    on_save_clicked
)
```

The browser sends an event through the WebSocket.

Python updates widget state.

Treeze synchronizes the browser.

---

## Client-side events

Used for immediate browser interaction.

Examples:

* Hover effects
* Focus
* Animations
* Drag feedback
* Smooth transitions

These should remain in the browser whenever possible.

---

# CSS Philosophy

Treeze should never attempt to replace CSS.

Instead it provides semantic Python APIs that generate HTML and CSS.

Users remain free to provide custom CSS.

Treeze ships with a default stylesheet.

Applications may load additional stylesheets that override the defaults.

---

# Design Goals

Treeze should strive to be:

* Pythonic
* Predictable
* Declarative
* Extensible
* Lightweight
* Renderer-independent at the Node level
* Easy to debug

---

# Non-Goals

Treeze is not:

* A replacement for HTML
* A replacement for CSS
* A JavaScript framework
* A game engine
* A browser implementation

The browser already solves those problems.

Treeze focuses on providing an excellent Python developer experience.

---

# Future Ideas

Potential future additions include:

* Incremental DOM patching
* Reactive state bindings
* Theme engine
* Asset management
* Routing
* Hot reload
* Async task integration
* Developer tools
* Widget inspector
* Component packaging
