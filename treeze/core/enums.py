"""
Name:         enums.py
Description:  A List of enums used by treeze
"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from enum import StrEnum, Enum, auto

# ______________________________________________________________________________________________________________________

class BrowserEvent(StrEnum):
    CLICK = 'click'

class Color(StrEnum):
    # ==========================================================================
    # Simple / Common
    # ==========================================================================

    WHITE = '#ffffff'
    BLACK = '#000000'

    RED = '#ef4444'
    ORANGE = '#f97316'
    AMBER = '#f59e0b'
    YELLOW = '#eab308'
    LIME = '#84cc16'
    GREEN = '#22c55e'
    EMERALD = '#10b981'
    TEAL = '#14b8a6'
    CYAN = '#06b6d4'
    SKY = '#0ea5e9'
    BLUE = '#3b82f6'
    INDIGO = '#6366f1'
    VIOLET = '#8b5cf6'
    PURPLE = '#a855f7'
    PINK = '#ec4899'
    ROSE = '#f43f5e'

    GRAY = '#6b7280'
    LIGHT_GRAY = '#d1d5db'
    DARK_GRAY = '#374151'

    SLATE = '#64748b'
    LIGHT_SLATE = '#cbd5e1'
    DARK_SLATE = '#1e293b'

    # ==========================================================================
    # Neutral / Slate
    # ==========================================================================

    SLATE_50 = '#f8fafc'
    SLATE_100 = '#f1f5f9'
    SLATE_200 = '#e2e8f0'
    SLATE_300 = '#cbd5e1'
    SLATE_400 = '#94a3b8'
    SLATE_500 = '#64748b'
    SLATE_600 = '#475569'
    SLATE_700 = '#334155'
    SLATE_800 = '#1e293b'
    SLATE_900 = '#0f172a'
    SLATE_950 = '#020617'

    GRAY_50 = '#f9fafb'
    GRAY_100 = '#f3f4f6'
    GRAY_200 = '#e5e7eb'
    GRAY_300 = '#d1d5db'
    GRAY_400 = '#9ca3af'
    GRAY_500 = '#6b7280'
    GRAY_600 = '#4b5563'
    GRAY_700 = '#374151'
    GRAY_800 = '#1f2937'
    GRAY_900 = '#111827'
    GRAY_950 = '#030712'

    # ==========================================================================
    # Red / Danger
    # ==========================================================================

    RED_50 = '#fef2f2'
    RED_100 = '#fee2e2'
    RED_200 = '#fecaca'
    RED_300 = '#fca5a5'
    RED_400 = '#f87171'
    RED_500 = '#ef4444'
    RED_600 = '#dc2626'
    RED_700 = '#b91c1c'
    RED_800 = '#991b1b'
    RED_900 = '#7f1d1d'

    ROSE_400 = '#fb7185'
    ROSE_500 = '#f43f5e'
    ROSE_600 = '#e11d48'
    ROSE_700 = '#be123c'

    # ==========================================================================
    # Orange / Amber / Warning
    # ==========================================================================

    ORANGE_400 = '#fb923c'
    ORANGE_500 = '#f97316'
    ORANGE_600 = '#ea580c'
    ORANGE_700 = '#c2410c'

    AMBER_300 = '#fcd34d'
    AMBER_400 = '#fbbf24'
    AMBER_500 = '#f59e0b'
    AMBER_600 = '#d97706'
    AMBER_700 = '#b45309'

    YELLOW_300 = '#fde047'
    YELLOW_400 = '#facc15'
    YELLOW_500 = '#eab308'
    YELLOW_600 = '#ca8a04'

    # ==========================================================================
    # Green / Success
    # ==========================================================================

    GREEN_300 = '#86efac'
    GREEN_400 = '#4ade80'
    GREEN_500 = '#22c55e'
    GREEN_600 = '#16a34a'
    GREEN_700 = '#15803d'
    GREEN_800 = '#166534'

    EMERALD_300 = '#6ee7b7'
    EMERALD_400 = '#34d399'
    EMERALD_500 = '#10b981'
    EMERALD_600 = '#059669'
    EMERALD_700 = '#047857'

    LIME_400 = '#a3e635'
    LIME_500 = '#84cc16'
    LIME_600 = '#65a30d'

    # ==========================================================================
    # Cyan / Teal / Info
    # ==========================================================================

    TEAL_300 = '#5eead4'
    TEAL_400 = '#2dd4bf'
    TEAL_500 = '#14b8a6'
    TEAL_600 = '#0d9488'
    TEAL_700 = '#0f766e'

    CYAN_300 = '#67e8f9'
    CYAN_400 = '#22d3ee'
    CYAN_500 = '#06b6d4'
    CYAN_600 = '#0891b2'
    CYAN_700 = '#0e7490'

    SKY_300 = '#7dd3fc'
    SKY_400 = '#38bdf8'
    SKY_500 = '#0ea5e9'
    SKY_600 = '#0284c7'
    SKY_700 = '#0369a1'

    # ==========================================================================
    # Blue / Primary
    # ==========================================================================

    BLUE_300 = '#93c5fd'
    BLUE_400 = '#60a5fa'
    BLUE_500 = '#3b82f6'
    BLUE_600 = '#2563eb'
    BLUE_700 = '#1d4ed8'
    BLUE_800 = '#1e40af'
    BLUE_900 = '#1e3a8a'

    INDIGO_300 = '#a5b4fc'
    INDIGO_400 = '#818cf8'
    INDIGO_500 = '#6366f1'
    INDIGO_600 = '#4f46e5'
    INDIGO_700 = '#4338ca'
    INDIGO_800 = '#3730a3'

    # ==========================================================================
    # Purple / Pink
    # ==========================================================================

    VIOLET_300 = '#c4b5fd'
    VIOLET_400 = '#a78bfa'
    VIOLET_500 = '#8b5cf6'
    VIOLET_600 = '#7c3aed'
    VIOLET_700 = '#6d28d9'

    PURPLE_400 = '#c084fc'
    PURPLE_500 = '#a855f7'
    PURPLE_600 = '#9333ea'
    PURPLE_700 = '#7e22ce'

    PINK_400 = '#f472b6'
    PINK_500 = '#ec4899'
    PINK_600 = '#db2777'
    PINK_700 = '#be185d'

class EventData(StrEnum):
    CHECKED = 'checked'
    EVENT_TYPE = 'event_type'
    TEXT = 'text'
    VALUE = 'value'

class LayoutAlignment(StrEnum):
    START = 'flex-start'
    CENTER = 'center'
    END = 'flex-end'

class InsertPosition(StrEnum):
    FIRST = 'first'
    LAST = 'last'

class Orientation(Enum):
    NONE = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()

class PatchOp(StrEnum):
    """Maps patches to client.js implementation"""
    REPLACE_NODE = 'replace_node'
    REMOVE_NODE = 'remove_node'

    REPLACE_CHILDREN = 'replace_children'
    APPEND_CHILD = 'append_child'
    INSERT_CHILD = 'insert_child'

    SET_ATTRIBUTE = 'set_attribute'
    SET_PROPERTY = 'set_property'
    SET_TEXT = 'set_text'
    SET_STYLE = 'set_style'

    ADD_CLASS = 'add_class'
    REMOVE_CLASS = 'remove_class'
    
class SizePolicy(StrEnum):
    EXPANDING = '1 1 0'
    FIXED = '0 0 auto'
    MINIMUM = '0 1 auto'
    PREFERRED = '0 1 auto'

class TreezeTheme(StrEnum):
    CUSTOM = 'custom'
    DARK = 'dark'
    LIGHT = 'light'
    TREEZE = 'treeze'

class Variant(StrEnum):
    DEFAULT = 'default'
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    TERTIARY = 'tertiary'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'
    INFO = 'info'
    MUTED = 'muted'