# PR Title:
Add Multi-Tier Translator Support (ISA + OS) for Cross-Platform Gaming

# PR Description:

## 🎯 What does this PR do?

Adds support for configurable ISA and OS translators, enabling Minigalaxy to run Windows games on ARM64, RISC-V, and other non-x86 architectures.

## 🚀 Key Features

- **Two-tier translator system**: ISA (FEX, QEMU) + OS (Wine, Proton-GE)
- **Flexible configuration**: Use both, one, or neither translator
- **Smart tool detection**: Auto-detects Protontricks for Proton, Winetricks for Wine
- **Generic UI**: Renamed Wine-specific labels to support any translator
- **Custom paths**: Supports both PATH executables and absolute paths

## 💡 Use Cases

| Platform | Setup | Example |
|----------|-------|---------|
| ARM64 | FEX + Proton-GE | Windows x86 games on Raspberry Pi 5 |
| ARM64 | FEX only | Native Linux x86 games on ARM |
| x86_64 | Proton-GE only | Windows games with Proton |
| x86_64 | Wine only | Traditional Wine setup |
| Any | None | Native Linux games |

## 🔧 Technical Changes

### UI (`properties.ui`)
- Consolidated Wine executable → OS Translator
- Added ISA Translator field
- Split reset button (Reset OS / Reset ISA)
- Generic button labels (Registry Editor, Configure OS Translator, OS Translator Tools)

### Backend (`launcher.py`)
- Multi-tier execution chain: `ISA → OS → Game`
- Custom path validation (not just PATH)
- Protontricks support
- Backward compatible with `custom_wine`

### Properties Dialog (`properties.py`)
- File choosers for both translators
- Independent reset handlers
- Smart error messages

## 📋 Execution Chain

```
[MangoHud] → [GameMode] → [ISA Translator] → [OS Translator] → [Game]
```

**Example on ARM64:**
```bash
mangohud gamemoderun FEXInterpreter proton-ge game.exe
```

## ✅ Backward Compatibility

- Existing `custom_wine` configs work unchanged
- No migration needed
- Settings saved to both old and new fields

## 📚 Documentation

Added `TRANSLATOR_COMBINATIONS.md` with complete compatibility matrix and examples.

## 🧪 Testing

- ✅ XML validation (xmllint)
- ✅ Python syntax validation
- ✅ All translator combinations tested
- ✅ Backward compatibility verified

## 🎮 Impact

Makes Minigalaxy one of the most flexible GOG clients, supporting:
- ARM64 gaming (Raspberry Pi, Apple Silicon via Asahi)
- Future RISC-V systems
- Proton-GE as Wine alternative
- Cross-architecture emulation

---

**Ready for review!** This enables true cross-platform gaming on Minigalaxy. 🚀
