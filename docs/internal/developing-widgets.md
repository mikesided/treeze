# Developing Widgets

This guide describes the standard process for adding a widget to Treeze.

Most widgets require:

1. A Python widget class
2. A rendered `Node`
3. A widget stylesheet
4. A public import
5. Tests

Most widgets do **not** require changes to the Treeze client or runtime.

---

## 1. Choose the Correct Base Class

Treeze widgets fall into three main categories.

### Primitive widget

Inherit directly from `Widget` when the widget renders one UI element and does not manage child widgets.

Examples:

* `Button`
* `Label`
* `Spacer`
* Future inputs, checkboxes, images, and progress bars

Place primitive widgets under:

```text
treeze/widgets/primitives/
```

### Container widget

Inherit from `Container` when the widget owns an arbitrary collection of child widgets.

A container is responsible for:

* Adding and removing children
* Maintaining parent relationships
* Propagating the active session
* Walking its child widget tree
* Building child nodes

Place general-purpose containers under:

```text
treeze/widgets/containers/
```

### Layout widget

Inherit from `Layout` when the widget is a container that arranges its children using Treeze layout behavior.

Examples:

* `HLayout`
* `VLayout`

`Layout` already provides common layout properties such as spacing and alignment.

Do not inherit directly from `Widget` and reimplement child management or layout behavior.

---

## 2. Create the Widget Module

For a new primitive widget named `Label`, create:

```text
treeze/widgets/primitives/label.py
```

A minimal widget looks like this:

```python
from ...core.node import Node
from ...core.validation import Validator
from ...core.widget import Widget


class Label(Widget):
    _CSS_CLASS = 'tz-label'

    def __init__(
        self,
        text: str = '',
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._text = Validator.ensure(text, str)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = Validator.ensure(text, str)

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='span',
            text=self.text,
            classes=self._classes(),
            styles=self._styles(),
        )
```

Every concrete widget must implement `_render()` and return a `Node`.

Widgets must not generate raw HTML strings.

---

## 3. Declare the Widget CSS Class

Every concrete widget must declare a stable Treeze CSS class:

```python
class Label(Widget):
    _CSS_CLASS = 'tz-label'
```

The base `Widget` class collects framework classes through the inheritance hierarchy.

The label above will receive:

```html
<span class="tz-widget tz-label">
```

Always use:

```python
classes=self._classes()
```

Do not hardcode the full class list inside `_render()`:

```python
# Avoid
classes=[
    'tz-widget',
    'tz-label',
]
```

Using `_classes()` preserves:

* Base widget classes
* Container and layout classes
* Style classes
* Variant classes
* User-added classes

Additional permanent framework classes can be declared with:

```python
_CSS_CLASSES = (
    'tz-clickable',
    'tz-focusable',
)
```

Use `_CSS_CLASS` for the widget’s main identity and `_CSS_CLASSES` only for additional framework behavior.

---

## 4. Render the Node

A `Node` describes the DOM element that Treeze should render.

Its main fields are:

```python
Node(
    id=...,
    tag=...,
    text=...,
    attributes=...,
    properties=...,
    classes=...,
    styles=...,
    events=...,
    children=...,
)
```

A normal widget should include at least:

```python
Node(
    id=self.id,
    tag='...',
    classes=self._classes(),
    styles=self._styles(),
)
```

### Text

Use `text` for an element’s text content:

```python
Node(
    id=self.id,
    tag='span',
    text=self.text,
)
```

Do not place user text into raw HTML.

### Attributes

Use `attributes` for HTML attributes:

```python
attributes={
    'type': 'button',
    'role': 'status',
    'aria-label': self.accessible_name,
}
```

### Properties

Use `properties` for live DOM state:

```python
properties={
    'value': self.value,
    'checked': self.checked,
    'disabled': not self.enabled,
}
```

Typical mutable form state such as `value` and `checked` belongs in `properties`, not only in HTML attributes.

### Classes and styles

Always include the inherited helpers:

```python
classes=self._classes(),
styles=self._styles(),
```

The base `_styles()` method already handles common widget state such as:

* Size policies
* Minimum size
* Maximum size
* Fixed size
* Margin
* Padding

A subclass extending `_styles()` must preserve the base styles:

```python
def _styles(self) -> dict[str, str]:
    styles = super()._styles()

    styles['some-property'] = 'some-value'

    return styles
```

---

## 5. Add Public Widget State

Render-affecting state should normally be exposed as public properties:

```python
@property
def text(self) -> str:
    return self._text


@text.setter
def text(self, text: str) -> None:
    self._text = Validator.ensure(text, str)
```

Treeze treats public assignments as render-affecting changes:

```python
label.text = 'Updated'
```

The base `Widget.__setattr__()` compares the previous and new values and marks the widget dirty when they differ.

Do not call `_mark_dirty()` again for an ordinary public assignment.

### Private attributes

Private attributes are considered internal state and do not normally mark the widget dirty:

```python
self._text = text
```

This is useful during construction and inside public property setters.

If a private attribute is intentionally changed directly after construction and affects rendering, either:

```python
self._mark_dirty()
```

or declare it:

```python
_DIRTY_PRIVATE_ATTRIBUTES = {
    '_render_state',
}
```

### In-place mutations

Treeze cannot detect in-place changes automatically:

```python
self._items.append(item)
self._options['key'] = value
```

Methods that mutate lists, dictionaries, sets, or widget structure in place must call:

```python
self._mark_dirty()
```

---

## 6. Validate Public Input

Use Treeze validation for values supplied through the public API:

```python
self._text = Validator.ensure(text, str)
```

Invalid framework-user input should raise an appropriate `TreezeException` subclass, such as:

* `TreezeTypeError`
* `TreezeValueError`

Examples include:

* Passing the wrong property type
* Using an unsupported variant
* Assigning a style enum belonging to another widget
* Adding an invalid child widget

Regular Python exceptions should be reserved for internal implementation errors and impossible framework states.

---

## 7. Add Signals and Browser Events

Declare signals at class level:

```python
from ...core.signals import Signal


class ActionLabel(Widget):
    activated = Signal()
```

Map a browser event to the signal in the rendered node:

```python
from ...core.enums import BrowserEvent
from ...core.events import EventBinding


def _render(self) -> Node:
    return Node(
        id=self.id,
        tag='button',
        text=self.text,
        classes=self._classes(),
        styles=self._styles(),
        events={
            BrowserEvent.CLICK: EventBinding(
                signal='activated',
            ),
        },
    )
```

Users can connect the signal through the normal Treeze API:

```python
label.activated.connect(on_activated)
```

The browser sends the widget ID and signal name to the active session. The session locates the retained Python widget and emits its bound signal.

### Sending browser data

`EventBinding.data` requests values from the browser event or DOM element:

```python
EventBinding(
    signal='changed',
    data=(
        EventData.VALUE,
    ),
)
```

The current client can collect:

* `value`
* `checked`
* `text`
* `event_type`

The signal declaration must accept the values sent by the binding:

```python
changed = Signal(str)
```

Only modify the JavaScript client when a widget needs browser information or behavior that the generic `Node` and `EventBinding` system cannot already express.

---

## 8. Support Styles

A style represents the widget’s visual treatment.

Styles are widget-specific. Each widget supports its own style enum:

```python
from enum import StrEnum


class LabelStyle(StrEnum):
    BODY = 'body'
    CAPTION = 'caption'
    HEADING = 'heading'
```

Declare the supported style type and its default on the widget:

```python
class Label(Widget):
    _CSS_CLASS = 'tz-label'

    _STYLE_TYPE = LabelStyle
    _DEFAULT_STYLE = LabelStyle.BODY
```

The common `Widget` implementation handles:

* Applying the default
* Validating the enum type
* Updating `style`
* Marking the widget dirty
* Generating the CSS class

For example:

```python
label = Label(
    'Treeze',
    style=LabelStyle.HEADING,
)
```

generates:

```html
<span class="tz-widget tz-label tz-label-heading">
```

Do not reimplement style validation or style class generation in each widget.

### Custom style prefix

By default, Treeze uses `_CSS_CLASS` as the style prefix.

Override `_STYLE_PREFIX` only when a different class namespace is necessary:

```python
_STYLE_PREFIX = 'tz-label-style'
```

This would generate:

```text
tz-label-style-heading
```

Prefer the default shorter form unless style and variant names could collide.

---

## 9. Support Variants

A variant represents semantic color or meaning:

```python
Variant.PRIMARY
Variant.SUCCESS
Variant.WARNING
Variant.DANGER
Variant.INFO
Variant.MUTED
```

All semantic variants are supported by default.

Restrict a widget to a meaningful subset when appropriate:

```python
_SUPPORTED_VARIANTS = (
    Variant.PRIMARY,
    Variant.SUCCESS,
    Variant.WARNING,
    Variant.DANGER,
)
```

Treeze always permits:

```python
Variant.DEFAULT
```

A non-default variant generates a class based on `_CSS_CLASS`:

```python
Label(
    'Saved',
    variant=Variant.SUCCESS,
)
```

generates:

```text
tz-label-success
```

Use `_VARIANT_PREFIX` only when the default prefix is unsuitable.

Keep the concepts separate:

```text
style   = visual treatment
variant = semantic color
```

For example:

```python
layout.style = LayoutStyle.ELEVATED
layout.variant = Variant.SUCCESS
```

The style supplies the shape and elevation. The variant supplies the semantic colors.

---

## 10. Developing a Container

A widget that manages children should inherit from `Container`.

Do not manually reproduce parent, session, traversal, or child-management logic.

A container render method should build its children through the shared helper:

```python
class Section(Container):
    _CSS_CLASS = 'tz-section'

    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='section',
            classes=self._classes(),
            styles=self._styles(),
        )

        self._build_children(node)

        return node
```

Use the inherited APIs to add and remove children:

```python
section.add_widget(widget)
section.remove_widget(widget)
```

These methods handle reparenting, session propagation, and dirty tracking.

---

## 11. Developing a Layout

A layout should inherit from `Layout`, which already inherits from `Container`.

A concrete layout normally declares:

* Its main CSS class
* Its orientation
* Its supported style enum
* Its render node

For example:

```python
class VLayout(Layout):
    _CSS_CLASS = 'tz-layout-vertical'
    _ORIENTATION = Orientation.VERTICAL

    _STYLE_TYPE = LayoutStyle
    _DEFAULT_STYLE = LayoutStyle.PLAIN

    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='div',
            classes=self._classes(),
            styles=self._styles(),
        )

        self._build_children(node)

        return node
```

The inheritance hierarchy will generate the common classes:

```html
<div class="tz-widget tz-layout tz-layout-vertical">
```

Do not hardcode only the orientation class, because doing so would discard inherited layout, style, variant, and user classes.

---

## 12. Add the Widget CSS

Primitive widget CSS belongs under:

```text
treeze/client/static/css/widgets/<widget-name>/
```

For the label:

```text
treeze/client/static/css/widgets/label/label.css
```

Example:

```css
.tz-label {
    font: inherit;
    color: inherit;
}

.tz-label-body {
    font-size: var(--tz-font-size);
}

.tz-label-caption {
    color: var(--tz-color-text-muted);
    font-size: 0.875em;
}

.tz-label-heading {
    font-size: 1.5em;
    font-weight: 600;
}
```

Layout CSS belongs under:

```text
treeze/client/static/css/layouts/
```

Treeze discovers component CSS recursively, so a new stylesheet placed in one of these directories is included automatically after restarting the server.

### CSS rules

* Use stable `tz-` classes for framework CSS.
* Do not target generated widget IDs.
* Keep widget selectors scoped to the widget.
* Keep styles and variants as separate classes.
* Avoid `!important`.
* Allow application CSS to override Treeze defaults.
* Do not add Python properties for arbitrary CSS rules.

---

## 13. Export the Widget

Add the widget to:

```text
treeze/widgets/__init__.py
```

For example:

```python
from .primitives.label import Label, LabelStyle
```

The intended public import should be:

```python
from treeze.widgets import Label
```

Users should not need to know the widget’s internal module path.

Also export the style enum when users need it:

```python
from treeze.widgets import Label, LabelStyle
```

---

## 14. Add Tests

Create:

```text
tests/widgets/test_label.py
```

At minimum, test:

* Constructor defaults
* Input validation
* Rendered tag and text
* Framework CSS classes
* Custom CSS classes
* Style classes
* Variant classes
* Attributes and properties
* Event bindings
* State changes
* Container child ordering, when applicable

Example:

```python
from treeze.widgets import Label


def test_label_renders_text() -> None:
    label = Label('Hello')

    node = label._build()

    assert node.tag == 'span'
    assert node.text == 'Hello'
    assert 'tz-widget' in node.classes
    assert 'tz-label' in node.classes
```

Style test:

```python
def test_label_renders_style_class() -> None:
    label = Label(
        'Title',
        style=LabelStyle.HEADING,
    )

    node = label._build()

    assert 'tz-label-heading' in node.classes
```

Invalid style test:

```python
import pytest

from treeze.core.exceptions import TreezeTypeError


def test_label_rejects_another_widget_style() -> None:
    with pytest.raises(TreezeTypeError):
        Label(
            'Invalid',
            style=LayoutStyle.PANEL,
        )
```

Treeze framework tests may call internal methods such as `_build()` because they test framework internals. Application code should not call them.

---

## 15. When Client Changes Are Necessary

Most new widgets should require only Python and CSS.

A client change may be necessary when the widget requires:

* New browser event data
* Browser-only measurements
* Focus or selection control
* File handling
* Canvas rendering
* A DOM operation not represented by existing patches
* A new protocol message type

Before adding widget-specific JavaScript, first determine whether the behavior can be represented using:

* `Node.attributes`
* `Node.properties`
* `Node.classes`
* `Node.styles`
* `Node.events`
* Existing patch operations

Avoid creating a separate JavaScript implementation for every Python widget.

---

## Widget Completion Checklist

Before considering a widget complete:

* [ ] It inherits from the correct base class.
* [ ] It has a stable `_CSS_CLASS`.
* [ ] Public values are validated.
* [ ] Render-affecting state uses public properties.
* [ ] In-place mutations call `_mark_dirty()`.
* [ ] `_render()` returns a `Node`.
* [ ] `_render()` uses `self._classes()`.
* [ ] `_render()` uses `self._styles()`.
* [ ] Containers call `_build_children()`.
* [ ] Signals are declared at class level.
* [ ] Browser events use `EventBinding`.
* [ ] Styles use a widget-specific enum.
* [ ] Variants are restricted when appropriate.
* [ ] CSS is placed in the correct asset directory.
* [ ] The widget is exported through `treeze.widgets`.
* [ ] Core behavior is tested.
* [ ] No client-side implementation was added unless necessary.
