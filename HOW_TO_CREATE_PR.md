# How to Create the Pull Request

## Step 1: Verify Your Fork is Up to Date

Your fork is at: `https://github.com/mateusbentes/minigalaxy`

Check that all commits are pushed:
```bash
cd /home/mateus/minigalaxy
git log --oneline -10
```

You should see:
- `98a42d0` docs: update CHANGELOG.md for v1.4.2 translator features
- `0e9c381` Add comprehensive translator combinations documentation
- `1d76eb0` Fix custom translator path detection and remove duplicate code
- `1fccbf6` Implement full Protontricks support for Proton-based games
- `d3462cb` Add Protontricks support and improve OS Translator Tools detection
- `568ffb9` Make translator configuration more generic and add ISA reset button
- `1d107ca` Refactor: Consolidate Wine executable with OS Translator field

## Step 2: Go to GitHub

1. Open your browser and go to: `https://github.com/mateusbentes/minigalaxy`
2. You should see a yellow banner saying "This branch is X commits ahead of sharkwouter:master"
3. Click the **"Contribute"** button
4. Click **"Open pull request"**

## Step 3: Fill in the PR Form

### Title:
```
Add Multi-Tier Translator Support (ISA + OS) for Cross-Platform Gaming
```

### Description:
Copy and paste the content from `PR_TEMPLATE.md` (the file I created for you)

Or use this shorter version:

```markdown
<!-- Note: Only PRs where the automated tests pass will be reviewed, so make sure they pass -->
## Description

This PR adds comprehensive support for multi-tier translation layers (ISA + OS translators), enabling Minigalaxy to run Windows games on non-x86 architectures like ARM64 and RISC-V.

### What Changed

**Core Features:**
- Added two-tier translator system: ISA translator (FEX, QEMU) + OS translator (Wine, Proton-GE)
- Both translators are optional and can be used independently or together
- Consolidated "Wine executable" field into generic "OS Translator" field
- Added "ISA Translator" field for architecture translation
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
- Native Linux games: No translators → `./game`

**Documentation:**
- Added `TRANSLATOR_COMBINATIONS.md` with complete compatibility matrix

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
- ✅ All translator combinations tested
- ✅ Backward compatibility verified

## Checklist
 
 - [x] _CHANGELOG.md_ was updated (**format**: - Change made (thanks to mateusbentes))
```

## Step 4: Review and Submit

1. **Review the changes**: Click on "Files changed" tab to review all your changes
2. **Check the commits**: Make sure all your commits are included
3. **Verify the base branch**: Should be `sharkwouter:master` ← `mateusbentes:master`
4. **Click "Create pull request"**

## Step 5: Wait for CI/CD

The automated tests will run. You should see:
- ✅ Build tests
- ✅ Linting tests
- ✅ Any other automated checks

If any fail, you can push fixes to your fork and they'll automatically update the PR.

## Step 6: Respond to Review

The maintainers may:
- Ask questions
- Request changes
- Suggest improvements

Be responsive and collaborative!

## Tips

1. **Be patient**: Open source maintainers are volunteers
2. **Be respectful**: They're reviewing your code for free
3. **Be responsive**: Answer questions promptly
4. **Be flexible**: Be open to suggestions and changes

## What Happens Next?

If accepted:
- Your code will be merged into the main repository
- You'll be credited in the CHANGELOG
- Your changes will be in the next release
- You'll be a Minigalaxy contributor! 🎉

## Need Help?

If you have questions:
1. Check the project's CONTRIBUTING.md (if it exists)
2. Ask in the PR comments
3. Check the project's issue tracker

---

**Good luck with your PR!** 🚀
