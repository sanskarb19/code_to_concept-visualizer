---
name: Replit Python package setup
description: Recover when an imported project has an immutable Python runtime without pip.
---

For imported projects whose base Nix Python has no pip, direct pip installation can fail with the externally-managed-environment error. Installing a supported Replit Python tools module provides a managed interpreter and package installer.

**Why:** Replit's base Python may be a wrapper around an immutable Nix store runtime; the project package installer can then use the managed Python environment.

**How to apply:** Check available Python modules, install a suitable tools module, then install project dependencies through the Replit language-package manager. Keep the app's chosen run command consistent with that interpreter.