# Terminology Refactoring: "Translator" → "Compatibility Layer"

## Summary
This refactoring updates the codebase terminology from "translator" to "compatibility layer" while maintaining full backward compatibility with existing user configurations and saved game data.

## Changes Made

### 1. New Module: `minigalaxy/compatibility_layer.py`
- Created new canonical module with `CompatibilityLayer` class and `CompatibilityLayerType` enum
- This is now the primary implementation

### 2. Backward Compatibility Shim: `minigalaxy/translator.py`
- Converted to a compatibility shim that re-exports the new classes
- Old code using `Translator` and `TranslatorType` will continue to work
- Can be removed in a future major version

### 3. Config (`minigalaxy/config.py`)
- **New properties:**
  - `compatibility_layers` (reads from new key, falls back to old `translators` key)
  - `add_compatibility_layer()`, `remove_compatibility_layer()`

- **Backward compatibility:**
  - When writing, both new and old keys are written (allows downgrades)
  - When reading, new keys are tried first, then old keys
  - Old property names kept as deprecated aliases

- **Note:** Per-game compatibility layer settings are stored in each game's `minigalaxy-info.json` file (not in global config), accessed via the Game class helper methods.

### 4. Game (`minigalaxy/game.py`)
- **New methods:**
  - `get_os_compat_layer_exec()` - reads from new key, falls back to `os_translator_exec`, then `custom_wine`
  - `set_os_compat_layer_exec()` - writes to all three keys for backward compatibility
  - `get_isa_compat_layer_exec()` - reads from new key, falls back to `isa_translator_exec`
  - `set_isa_compat_layer_exec()` - writes to both keys for backward compatibility

- **Storage location:**
  - Settings are stored per-game in `<game_install_dir>/minigalaxy-info.json`
  - Uses existing `get_info()` / `set_info()` infrastructure

- **Backward compatibility:**
  - All writes go to both old and new keys
  - Reads try new keys first, then fall back to old keys

### 5. Launcher (`minigalaxy/launcher.py`)
- **Updated functions:**
  - `add_compatibility_layers_to_command()` (new name)
  - `add_translators_to_command()` (kept as deprecated wrapper)
  - Updated all docstrings to use "compatibility layer" terminology
  - Now uses `game.get_os_compat_layer_exec()` and `game.get_isa_compat_layer_exec()`

### 6. Properties UI (`minigalaxy/ui/properties.py`)
- Updated to use new helper methods:
  - `game.get_os_compat_layer_exec()` / `game.set_os_compat_layer_exec()`
  - `game.get_isa_compat_layer_exec()` / `game.set_isa_compat_layer_exec()`
- Updated comments to use "compatibility layer" terminology
- Fixed bug: now uses empty string `""` instead of `None` when clearing settings

### 7. UI Labels (`data/ui/properties.ui`)
- Already uses "OS Compatibility Layer" and "ISA Compatibility Layer" labels
- Widget IDs kept unchanged (`button_properties_os_translator`, etc.) to avoid breaking UI code

## Backward Compatibility Strategy

### For Existing Users (Upgrading)
- Old config keys (`translators`, `game_translators`) are automatically read
- Old per-game keys (`os_translator_exec`, `isa_translator_exec`, `custom_wine`) are automatically read
- No data migration needed - works transparently

### For Users Downgrading
- New code writes to both old and new keys
- Old versions of Minigalaxy will still see the old keys and work correctly
- No data loss on downgrade

### Persisted Data Keys

**Config file (`config.json`):**
- New: `compatibility_layers`
- Old: `translators` (still written for compatibility)

**Per-game data (`minigalaxy-info.json`):**
- New: `os_compat_layer_exec`, `isa_compat_layer_exec`
- Old: `os_translator_exec`, `isa_translator_exec`, `custom_wine` (still written for compatibility)

## Testing Recommendations

1. **Fresh install:** Verify new keys are created and used
2. **Upgrade from old version:** Verify old keys are read correctly
3. **Downgrade after upgrade:** Verify old version still works with dual-key data
4. **Properties dialog:** Test setting/clearing OS and ISA compatibility layers
5. **Game launch:** Verify Wine/Proton games still launch correctly
6. **Config tools:** Test winecfg, regedit, winetricks still work

## Future Cleanup (Optional)

In a future major version (e.g., 2.0.0), you could:
1. Remove the `translator.py` shim
2. Remove deprecated method aliases
3. Stop writing old config keys
4. Eventually remove support for reading old keys

For now, all backward compatibility is maintained.
