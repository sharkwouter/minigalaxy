# Translator Combinations Support Matrix

Minigalaxy supports flexible translator configurations for maximum compatibility across different platforms and game types.

## Supported Combinations

| ISA Translator | OS Translator | Use Case | Example Command |
|----------------|---------------|----------|-----------------|
| ✅ FEX | ✅ Proton-GE | Windows x86 games on ARM64 | `FEX Proton-GE game.exe` |
| ✅ FEX | ✅ Wine | Windows x86 games on ARM64 | `FEX wine game.exe` |
| ✅ QEMU | ✅ Wine | Windows x86 games on ARM64 (alternative) | `qemu-x86_64 wine game.exe` |
| ❌ None | ✅ Wine | Windows games on x86_64 | `wine game.exe` |
| ❌ None | ✅ Proton-GE | Windows games on x86_64 | `proton game.exe` |
| ✅ FEX | ❌ None | Native Linux x86 games on ARM64 | `FEX ./game` |
| ✅ QEMU | ❌ None | Native Linux x86 games on ARM64 | `qemu-x86_64 ./game` |
| ❌ None | ❌ None | Native Linux games (same arch) | `./game` |

## Execution Chain

The execution order is always:
```
[MangoHud] → [GameMode] → [ISA Translator] → [OS Translator] → [Game]
```

### Example 1: Full Stack (ARM64 with Windows game)
```bash
mangohud --dlsym gamemoderun FEXInterpreter proton game.exe
```

### Example 2: OS Translator Only (x86_64 with Windows game)
```bash
mangohud --dlsym gamemoderun wine game.exe
```

### Example 3: ISA Translator Only (ARM64 with Linux x86 game)
```bash
mangohud --dlsym gamemoderun FEXInterpreter ./game
```

### Example 4: Native (x86_64 with Linux game)
```bash
mangohud --dlsym gamemoderun ./game
```

## Platform-Specific Examples

### ARM64 Linux (e.g., Raspberry Pi 5, Apple Silicon)
- **Windows x86 games**: FEX + Wine/Proton
- **Linux x86 games**: FEX only
- **Native ARM64 games**: No translators

### x86_64 Linux (Standard PC)
- **Windows games**: Wine/Proton only
- **Native Linux games**: No translators

### RISC-V (Future support)
- **Windows x86 games**: QEMU + Wine/Proton
- **Linux x86 games**: QEMU only
- **Native RISC-V games**: No translators

## Configuration

### Via Properties Dialog
1. Right-click game → Properties
2. Set **OS Translator**: Browse to Wine/Proton executable
3. Set **ISA Translator**: Browse to FEX/QEMU executable
4. Click OK

### Supported Tools
- **Registry Editor**: Works with Wine/Proton
- **Configure OS Translator**: Runs winecfg
- **OS Translator Tools**: Auto-detects Winetricks/Protontricks

## Reset Options
- **Reset OS Translator**: Clears OS translator, reverts to system Wine
- **Reset ISA Translator**: Clears ISA translator

## Notes
- Both translators are completely optional
- Translators can be in PATH or custom paths
- Custom paths are validated for existence and execute permission
- Invalid paths are silently skipped (game may fail to launch)
