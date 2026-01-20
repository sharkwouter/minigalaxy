<!-- Note: Only PRs where the automated tests pass will be reviewed, so make sure they pass -->
## Description

This PR adds comprehensive support for multi-tier translation layers (ISA + OS translators), enabling Minigalaxy to run Windows games on non-x86 architectures like ARM64 and RISC-V.

### What Changed

**Core Features:**
- Added two-tier translator system: ISA translator (FEX, QEMU) + OS translator (Wine, Proton-GE)
- Both translators are optional and can be used independently or together
- Consolidated "Wine executable" field into generic "OS Translator" field
- Added "ISA Translator" field for architecture translation (x86 on ARM64)
- Smart tool detection: auto-detects Protontricks for Proton, Winetricks for Wine

**UI Changes:**
- Unified Wine/Proton configuration under "OS Translator"
- Added ISA Translator file chooser
- Split reset button into "Reset OS Translator" and "Reset ISA Translator"
- Generic button labels: "Registry Editor", "Configure OS Translator", "OS Translator Tools"
- Fixed malformed XML tags in properties.ui

**Backend Changes:**
- Updated execution chain: `[ISA Translator] → [OS Translator] → [Game]`
- Enhanced path detection to support custom absolute paths (not just PATH)
- Added Protontricks support with proper environment variables
- Backward compatible with existing `custom_wine` configurations

**Use Cases:**
- ARM64 + Windows games: FEX + Proton-GE → `FEX proton-ge game.exe`
- ARM64 + Linux x86 games: FEX only → `FEX ./game`
- x86_64 + Windows games: Proton-GE only → `proton-ge game.exe`
- x86_64 + Windows games: Wine only → `wine game.exe`
- Native Linux games: No translators → `./game`

**Documentation:**
- Added `TRANSLATOR_COMBINATIONS.md` with complete compatibility matrix
- Platform-specific examples (ARM64, x86_64, RISC-V)
- Configuration instructions

### Why This Matters

This makes Minigalaxy one of the most flexible GOG clients, supporting:
- **ARM64 gaming** (Raspberry Pi 5, Apple Silicon via Asahi Linux)
- **Future RISC-V systems**
- **Proton-GE** as a Wine alternative
- **Cross-architecture emulation** without manual command-line setup

### Backward Compatibility

✅ Fully backward compatible:
- Existing `custom_wine` configurations continue to work
- Settings saved to both `custom_wine` (legacy) and `os_translator_exec` (new)
- No migration required

### Testing

- ✅ XML validation passed (xmllint)
- ✅ Python syntax validation passed
- ✅ All translator combinations tested (ISA+OS, ISA only, OS only, none)
- ✅ Backward compatibility verified

## Checklist
 
 - [x] _CHANGELOG.md_ was updated (**format**: - Change made (thanks to github_username))
