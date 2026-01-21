# Compatibility Layer Combinations Support Matrix

Minigalaxy supports flexible compatibility layer configurations for maximum compatibility across different platforms and game types.

## Supported Combinations

| ISA Compatibility Layer | OS Compatibility Layer | Use Case | Example Command |
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
[MangoHud] → [GameMode] → [ISA Compatibility Layer] → [OS Compatibility Layer] → [Game]
```

### Example 1: Full Stack (ARM64 with Windows game)
```bash
mangohud --dlsym gamemoderun FEXInterpreter proton game.exe
```

### Example 2: OS Compatibility Layer Only (x86_64 with Windows game)
```bash
mangohud --dlsym gamemoderun wine game.exe
```

### Example 3: ISA Compatibility Layer Only (ARM64 with Linux x86 game)
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
- **Native ARM64 games**: No compatibility layers

### x86_64 Linux (Standard PC)
- **Windows games**: Wine/Proton only
- **Native Linux games**: No compatibility layers

### RISC-V (Future support)
- **Windows x86 games**: QEMU + Wine/Proton
- **Linux x86 games**: QEMU only
- **Native RISC-V games**: No compatibility layers

## Configuration

### Via Properties Dialog
1. Right-click game → Properties
2. Set **OS Compatibility Layer**: Browse to Wine/Proton executable
3. Set **ISA Compatibility Layer**: Browse to FEX/QEMU executable
4. Click OK

### Supported Tools
- **Registry Editor**: Works with Wine/Proton
- **Configure OS Compatibility Layer**: Runs winecfg
- **OS Compatibility Layer Tools**: Auto-detects Winetricks/Protontricks

## Reset Options
- **Reset OS Compatibility Layer**: Clears OS compatibility layer, reverts to system Wine
- **Reset ISA Compatibility Layer**: Clears ISA compatibility layer

## Notes
- Both compatibility layers are completely optional
- Compatibility Layers can be in PATH or custom paths
- Custom paths are validated for existence and execute permission
- Invalid paths are silently skipped (game may fail to launch)
