# Add Multi-Tier Translator Support for Cross-Platform Gaming

## Summary

This PR adds comprehensive support for multi-tier translation layers, enabling Minigalaxy to run Windows games on non-x86 architectures (ARM64, RISC-V) through ISA and OS translators. This makes Minigalaxy one of the most flexible GOG clients for cross-platform gaming.

## Motivation

Modern gaming increasingly spans multiple architectures:
- **ARM64 devices** (Raspberry Pi 5, Apple Silicon via Asahi Linux, ARM servers)
- **Future RISC-V systems**
- **Proton-GE** as an alternative to Wine
- **Cross-architecture emulation** (FEX-Emu, QEMU)

Users need a way to configure translation layers without manual command-line setup.

## Changes

### 🎯 Core Features

1. **Two-Tier Translator System**
   - **ISA Translator** (Architecture): FEX-Emu, QEMU, Box86/Box64
   - **OS Translator** (API): Wine, Proton, Proton-GE
   - Both are optional and can be used independently or together

2. **Unified Wine/Proton Configuration**
   - Consolidated "Wine executable" field into "OS Translator"
   - Removed duplicate Wine-specific UI elements
   - Generic terminology supports any OS translator

3. **Smart Tool Detection**
   - Auto-detects Protontricks for Proton-based games
   - Falls back to Winetricks when appropriate
   - Sets correct environment variables (WINE, WINEPREFIX)

4. **Flexible Path Support**
   - Supports executables in PATH
   - Supports custom absolute paths
   - Validates file existence and execute permissions

### 🔧 Technical Changes

#### UI Changes (`data/ui/properties.ui`)
- Removed duplicate/malformed XML tags
- Consolidated Wine executable → OS Translator field
- Added ISA Translator file chooser
- Split reset button into "Reset OS" and "Reset ISA"
- Updated button labels for generic terminology:
  - "Regedit" → "Registry Editor"
  - "Winecfg" → "Configure OS Translator"
  - "Winetricks" → "OS Translator Tools"

#### Backend Changes (`minigalaxy/launcher.py`)
- Updated `get_wine_path()` to check `os_translator_exec` first
- Enhanced `get_execute_command()` to build multi-tier execution chain
- Added `winetricks_game()` Protontricks support
- Fixed custom path detection (not just PATH executables)
- Removed duplicate unreachable code

#### Properties Dialog (`minigalaxy/ui/properties.py`)
- Added OS and ISA translator file chooser widgets
- Implemented separate reset handlers for each translator
- Added backward compatibility with `custom_wine` field
- Smart error messages based on translator type

### 📋 Execution Chain

The execution order is always:
```
[MangoHud] → [GameMode] → [ISA Translator] → [OS Translator] → [Game]
```

**Examples:**

| Platform | Configuration | Command |
|----------|--------------|---------|
| ARM64 | FEX + Proton-GE | `FEX proton-ge game.exe` |
| ARM64 | FEX + Wine | `FEX wine game.exe` |
| ARM64 | FEX only | `FEX ./native_x86_game` |
| x86_64 | Proton-GE only | `proton-ge game.exe` |
| x86_64 | Wine only | `wine game.exe` |
| Any | None | `./native_game` |

### 🧪 Supported Combinations

All 8 combinations work:
- ✅ ISA + OS translators (e.g., FEX + Proton on ARM64)
- ✅ ISA only (e.g., FEX for Linux x86 games on ARM64)
- ✅ OS only (e.g., Wine on x86_64)
- ✅ No translators (native Linux games)

See `TRANSLATOR_COMBINATIONS.md` for complete matrix.

### 🔄 Backward Compatibility

- Existing `custom_wine` configurations continue to work
- Settings are saved to both `custom_wine` and `os_translator_exec`
- No migration required for existing users

### 📚 Documentation

Added `TRANSLATOR_COMBINATIONS.md` with:
- Complete compatibility matrix
- Platform-specific examples
- Configuration instructions
- Tool support details

## Testing

Tested on:
- ✅ GTK template validation (xmllint)
- ✅ Python syntax validation
- ✅ All execution path combinations
- ✅ Backward compatibility with existing configs

## Screenshots

### Before
- Single "Wine executable" field
- Wine-specific button labels
- No ISA translator support

### After
- Separate "OS Translator" and "ISA Translator" fields
- Generic button labels (works with Wine/Proton/etc.)
- Independent reset buttons for each translator
- Smart tool detection (Winetricks/Protontricks)

## Breaking Changes

None. All changes are backward compatible.

## Related Issues

This addresses the need for:
- ARM64 gaming support
- Proton-GE integration
- Cross-architecture emulation
- Flexible translator configuration

## Checklist

- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Comments added for complex logic
- [x] Documentation updated
- [x] No breaking changes
- [x] Backward compatibility maintained
- [x] XML validation passed
- [x] Python syntax validation passed

## Future Enhancements

Potential follow-ups (not in this PR):
- Translator presets (e.g., "FEX + Proton-GE for ARM64")
- Auto-detection of installed translators
- Per-game translator profiles
- Integration with Steam's Proton versions

---

**This PR makes Minigalaxy a truly cross-platform GOG client, supporting gaming on ARM64, RISC-V, and other architectures through flexible translator configuration.** 🎮🚀
