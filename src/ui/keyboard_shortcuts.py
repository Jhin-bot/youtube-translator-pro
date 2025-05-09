"""
Keyboard shortcuts manager for YouTube Translator Pro.
Provides a centralized system for registering and handling keyboard shortcuts.
"""

import logging
from typing import Dict, Callable, Any, List, Optional, Tuple, Set
from enum import Enum

try:
    from PyQt6.QtCore import Qt, QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import Qt, QObject, pyqtSignal

try:
    from PyQt6.QtGui import QKeySequence, QShortcut, QKeyEvent
except ImportError:
    from PyQt5.QtGui import QKeySequence, QShortcut, QKeyEvent

try:
    from PyQt6.QtWidgets import QWidget, QApplication
except ImportError:
    from PyQt5.QtWidgets import QWidget, QApplication

from src.utils.localization import get_string

# Set up logging
logger = logging.getLogger(__name__)

class ShortcutScope(Enum):
    """Scope for keyboard shortcuts."""
    GLOBAL = "global"       # Available everywhere in the application
    MAIN_WINDOW = "main"    # Available only in the main window
    EDITOR = "editor"       # Available in the editor
    DIALOG = "dialog"       # Available in dialog windows
    BATCH = "batch"         # Available in batch processing window

class ShortcutCategory(Enum):
    """Category for keyboard shortcuts."""
    FILE = "file"               # File operations
    EDIT = "edit"               # Editing operations
    VIEW = "view"               # View operations
    NAVIGATION = "navigation"   # Navigation operations
    TOOLS = "tools"             # Tools operations
    PLAYBACK = "playback"       # Media playback operations
    SYSTEM = "system"           # System operations

class ShortcutAction:
    """Represents a shortcut action that can be triggered."""
    
    def __init__(self, id: str, 
                 default_keys: List[QKeySequence], 
                 name: str,
                 description: str, 
                 category: ShortcutCategory,
                 scope: ShortcutScope,
                 callback: Callable = None):
        """
        Initialize a shortcut action.
        
        Args:
            id: Unique identifier for the action
            default_keys: Default key sequences
            name: Display name for the action
            description: Longer description of what the action does
            category: Category for grouping in settings
            scope: Where the shortcut is available
            callback: Function to call when shortcut is triggered
        """
        self.id = id
        self.default_keys = default_keys
        self.current_keys = default_keys.copy()
        self.name = name
        self.description = description
        self.category = category
        self.scope = scope
        self.callback = callback
        self.shortcuts: List[QShortcut] = []
    
    def trigger(self) -> None:
        """Trigger the shortcut action."""
        if self.callback:
            try:
                self.callback()
                logger.debug(f"Triggered shortcut action: {self.id}")
            except Exception as e:
                logger.error(f"Error executing shortcut action {self.id}: {e}")

class KeyboardShortcutsManager(QObject):
    """
    Manages keyboard shortcuts throughout the application.
    Allows for registration, customization and triggering of shortcuts.
    """
    
    shortcut_triggered = pyqtSignal(str)  # Signal emitted when shortcut is triggered
    
    def __init__(self):
        """Initialize the keyboard shortcuts manager."""
        super().__init__()
        
        # Dictionary of all registered actions
        self.actions: Dict[str, ShortcutAction] = {}
        
        # Mapping of key sequences to action ids
        self.key_map: Dict[str, str] = {}
        
        # Track active widgets for scoped shortcuts
        self.active_widgets: Dict[ShortcutScope, Set[QWidget]] = {
            scope: set() for scope in ShortcutScope
        }
        
        # Set of enabled scopes
        self.enabled_scopes: Set[ShortcutScope] = {
            ShortcutScope.GLOBAL
        }
        
        # Register all standard shortcuts
        self._register_default_shortcuts()
        
        logger.info("Keyboard shortcuts manager initialized")
    
    def _register_default_shortcuts(self) -> None:
        """Register all default shortcuts."""
        # File operations
        self.register_action(
            "file.new", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N)],
            "New", 
            "Create a new file",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.open", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_O)],
            "Open", 
            "Open a file",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.save", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S)],
            "Save", 
            "Save the current file",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.save_as", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_S)],
            "Save As", 
            "Save the current file with a new name",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.export", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_E)],
            "Export", 
            "Export the current file",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.close", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_W)],
            "Close", 
            "Close the current file",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "file.exit", 
            [QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_F4)],
            "Exit", 
            "Exit the application",
            ShortcutCategory.FILE,
            ShortcutScope.GLOBAL
        )
        
        # Edit operations
        self.register_action(
            "edit.undo", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Z)],
            "Undo", 
            "Undo the last action",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.redo", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_Z)],
            "Redo", 
            "Redo the last undone action",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.cut", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_X)],
            "Cut", 
            "Cut the selected text",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.copy", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_C)],
            "Copy", 
            "Copy the selected text",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.paste", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_V)],
            "Paste", 
            "Paste from clipboard",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.delete", 
            [QKeySequence(Qt.Key.Key_Delete)],
            "Delete", 
            "Delete the selected item",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "edit.select_all", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_A)],
            "Select All", 
            "Select all items",
            ShortcutCategory.EDIT,
            ShortcutScope.GLOBAL
        )
        
        # View operations
        self.register_action(
            "view.toggle_dark_mode", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.ALT | Qt.Key.Key_D)],
            "Toggle Dark Mode", 
            "Switch between light and dark mode",
            ShortcutCategory.VIEW,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "view.zoom_in", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Plus)],
            "Zoom In", 
            "Increase the zoom level",
            ShortcutCategory.VIEW,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "view.zoom_out", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus)],
            "Zoom Out", 
            "Decrease the zoom level",
            ShortcutCategory.VIEW,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "view.reset_zoom", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_0)],
            "Reset Zoom", 
            "Reset the zoom level to default",
            ShortcutCategory.VIEW,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "view.performance_monitor", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_P)],
            "Performance Monitor", 
            "Show the performance monitor",
            ShortcutCategory.VIEW,
            ShortcutScope.GLOBAL
        )
        
        # Tools operations
        self.register_action(
            "tools.settings", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Comma)],
            "Settings", 
            "Open the settings dialog",
            ShortcutCategory.TOOLS,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "tools.download", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_D)],
            "Download Video", 
            "Download a YouTube video",
            ShortcutCategory.TOOLS,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "tools.transcribe", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_T)],
            "Transcribe", 
            "Transcribe a video",
            ShortcutCategory.TOOLS,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "tools.translate", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R)],
            "Translate", 
            "Translate a transcript",
            ShortcutCategory.TOOLS,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "tools.batch", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_B)],
            "Batch Processing", 
            "Open batch processing dialog",
            ShortcutCategory.TOOLS,
            ShortcutScope.MAIN_WINDOW
        )
        
        # Playback operations
        self.register_action(
            "playback.play_pause", 
            [QKeySequence(Qt.Key.Key_Space)],
            "Play/Pause", 
            "Toggle play/pause",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "playback.stop", 
            [QKeySequence(Qt.Key.Key_S)],
            "Stop", 
            "Stop playback",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "playback.forward", 
            [QKeySequence(Qt.Key.Key_Right)],
            "Forward", 
            "Skip forward 5 seconds",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "playback.backward", 
            [QKeySequence(Qt.Key.Key_Left)],
            "Backward", 
            "Skip backward 5 seconds",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "playback.volume_up", 
            [QKeySequence(Qt.Key.Key_Up)],
            "Volume Up", 
            "Increase volume",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        self.register_action(
            "playback.volume_down", 
            [QKeySequence(Qt.Key.Key_Down)],
            "Volume Down", 
            "Decrease volume",
            ShortcutCategory.PLAYBACK,
            ShortcutScope.MAIN_WINDOW
        )
        
        # Help and system
        self.register_action(
            "system.help", 
            [QKeySequence(Qt.Key.Key_F1)],
            "Help", 
            "Show help",
            ShortcutCategory.SYSTEM,
            ShortcutScope.GLOBAL
        )
        
        self.register_action(
            "system.shortcuts", 
            [QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_F1)],
            "Keyboard Shortcuts", 
            "Show keyboard shortcuts",
            ShortcutCategory.SYSTEM,
            ShortcutScope.GLOBAL
        )
        
        logger.info(f"Registered {len(self.actions)} default keyboard shortcuts")
    
    def register_action(self, 
                       id: str, 
                       default_keys: List[QKeySequence], 
                       name: str, 
                       description: str, 
                       category: ShortcutCategory,
                       scope: ShortcutScope,
                       callback: Callable = None) -> ShortcutAction:
        """
        Register a new shortcut action.
        
        Args:
            id: Unique identifier for the action
            default_keys: Default key sequences
            name: Display name for the action
            description: Longer description of what the action does
            category: Category for grouping in settings
            scope: Where the shortcut is available
            callback: Function to call when shortcut is triggered
            
        Returns:
            Registered ShortcutAction
        """
        # Try to use localized strings if available
        localized_name = get_string(f"shortcut.{id}.name", name)
        localized_description = get_string(f"shortcut.{id}.description", description)
        
        # Create the action
        action = ShortcutAction(
            id=id,
            default_keys=default_keys,
            name=localized_name,
            description=localized_description,
            category=category,
            scope=scope,
            callback=callback
        )
        
        # Register the action
        self.actions[id] = action
        
        # Update key map
        for key in default_keys:
            key_str = key.toString()
            if key_str:
                self.key_map[key_str] = id
        
        logger.debug(f"Registered shortcut action: {id} with keys {[k.toString() for k in default_keys]}")
        
        return action
    
    def register_shortcuts_with_widget(self, widget: QWidget) -> None:
        """
        Register QShortcut objects with a widget.
        
        Args:
            widget: Widget to register shortcuts with
        """
        for action_id, action in self.actions.items():
            # Only register shortcuts for enabled scopes
            if action.scope not in self.enabled_scopes:
                continue
            
            # Create a shortcut for each key sequence
            for key_seq in action.current_keys:
                shortcut = QShortcut(key_seq, widget)
                shortcut.activated.connect(lambda aid=action_id: self._on_shortcut_activated(aid))
                action.shortcuts.append(shortcut)
        
        logger.debug(f"Registered shortcuts with widget: {widget.__class__.__name__}")
    
    def _on_shortcut_activated(self, action_id: str) -> None:
        """
        Called when a shortcut is activated.
        
        Args:
            action_id: ID of the triggered action
        """
        if action_id in self.actions:
            action = self.actions[action_id]
            action.trigger()
            self.shortcut_triggered.emit(action_id)
    
    def set_shortcut_enabled(self, action_id: str, enabled: bool) -> None:
        """
        Enable or disable a shortcut.
        
        Args:
            action_id: ID of the action to enable/disable
            enabled: Whether to enable or disable
        """
        if action_id in self.actions:
            action = self.actions[action_id]
            for shortcut in action.shortcuts:
                shortcut.setEnabled(enabled)
    
    def set_scope_enabled(self, scope: ShortcutScope, enabled: bool) -> None:
        """
        Enable or disable all shortcuts in a scope.
        
        Args:
            scope: Scope to enable/disable
            enabled: Whether to enable or disable
        """
        if enabled:
            self.enabled_scopes.add(scope)
        else:
            self.enabled_scopes.discard(scope)
            
        # Update all shortcuts
        for action_id, action in self.actions.items():
            if action.scope == scope:
                self.set_shortcut_enabled(action_id, enabled)
    
    def activate_widget_scope(self, widget: QWidget, scope: ShortcutScope) -> None:
        """
        Activate shortcuts for a widget in a specific scope.
        
        Args:
            widget: Widget to activate shortcuts for
            scope: Scope to activate
        """
        # Add the widget to the active set for this scope
        self.active_widgets[scope].add(widget)
        
        # Enable the scope
        self.set_scope_enabled(scope, True)
    
    def deactivate_widget_scope(self, widget: QWidget, scope: ShortcutScope) -> None:
        """
        Deactivate shortcuts for a widget in a specific scope.
        
        Args:
            widget: Widget to deactivate shortcuts for
            scope: Scope to deactivate
        """
        # Remove the widget from the active set for this scope
        self.active_widgets[scope].discard(widget)
        
        # If no more widgets are active in this scope, disable it
        if not self.active_widgets[scope]:
            self.set_scope_enabled(scope, False)
    
    def update_shortcut(self, action_id: str, new_keys: List[QKeySequence]) -> None:
        """
        Update the key sequences for a shortcut.
        
        Args:
            action_id: ID of the action to update
            new_keys: New key sequences
        """
        if action_id not in self.actions:
            logger.warning(f"Cannot update shortcut for unknown action: {action_id}")
            return
            
        action = self.actions[action_id]
        
        # Remove old shortcuts
        for shortcut in action.shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        
        action.shortcuts.clear()
        
        # Remove old key mappings
        for key in action.current_keys:
            key_str = key.toString()
            if key_str in self.key_map and self.key_map[key_str] == action_id:
                del self.key_map[key_str]
        
        # Update with new keys
        action.current_keys = new_keys.copy()
        
        # Update key map
        for key in new_keys:
            key_str = key.toString()
            if key_str:
                self.key_map[key_str] = action_id
        
        logger.info(f"Updated shortcut {action_id} with keys {[k.toString() for k in new_keys]}")
    
    def reset_shortcuts(self) -> None:
        """Reset all shortcuts to their default values."""
        for action_id, action in self.actions.items():
            self.update_shortcut(action_id, action.default_keys)
            
        logger.info("Reset all keyboard shortcuts to defaults")
    
    def get_all_shortcuts(self) -> Dict[str, ShortcutAction]:
        """
        Get all registered shortcut actions.
        
        Returns:
            Dictionary of action ID to ShortcutAction
        """
        return self.actions.copy()
    
    def get_shortcuts_by_category(self) -> Dict[ShortcutCategory, List[ShortcutAction]]:
        """
        Get shortcuts grouped by category.
        
        Returns:
            Dictionary of category to list of actions
        """
        result = {category: [] for category in ShortcutCategory}
        
        for action in self.actions.values():
            result[action.category].append(action)
            
        return result
    
    def get_shortcuts_by_scope(self) -> Dict[ShortcutScope, List[ShortcutAction]]:
        """
        Get shortcuts grouped by scope.
        
        Returns:
            Dictionary of scope to list of actions
        """
        result = {scope: [] for scope in ShortcutScope}
        
        for action in self.actions.values():
            result[action.scope].append(action)
            
        return result
    
    def get_action(self, action_id: str) -> Optional[ShortcutAction]:
        """
        Get a shortcut action by ID.
        
        Args:
            action_id: ID of the action to get
            
        Returns:
            ShortcutAction or None if not found
        """
        return self.actions.get(action_id)
    
    def get_action_for_key(self, key_sequence: QKeySequence) -> Optional[ShortcutAction]:
        """
        Get the action associated with a key sequence.
        
        Args:
            key_sequence: Key sequence to look up
            
        Returns:
            ShortcutAction or None if not found
        """
        key_str = key_sequence.toString()
        if key_str in self.key_map:
            action_id = self.key_map[key_str]
            return self.actions.get(action_id)
        return None

# Create a global instance
shortcut_manager = KeyboardShortcutsManager()

# Helper function to connect a shortcut to a callback
def connect_shortcut(action_id: str, callback: Callable) -> bool:
    """
    Connect a callback to a shortcut action.
    
    Args:
        action_id: ID of the action to connect
        callback: Function to call when shortcut is triggered
        
    Returns:
        True if connected successfully, False otherwise
    """
    action = shortcut_manager.get_action(action_id)
    if action:
        action.callback = callback
        return True
    return False

# Helper to get human-readable key sequence text
def get_shortcut_text(action_id: str) -> str:
    """
    Get a human-readable text of the shortcut key sequence.
    
    Args:
        action_id: ID of the action to get shortcut text for
        
    Returns:
        Text representation of the shortcut or empty string if not found
    """
    action = shortcut_manager.get_action(action_id)
    if action and action.current_keys:
        return action.current_keys[0].toString()
    return ""
