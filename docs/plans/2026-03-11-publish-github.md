# Publish GitHub Repository Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish the `liver_rfa` project to a new public GitHub repository while excluding only virtual environments and cache files.

**Architecture:** Add a root `.gitignore` to keep local Python environments and cache artifacts out of version control while preserving code, outputs, and manuscript figures. Then initialize Git in the project root, create an initial commit, create a matching public GitHub repository with `gh`, and push the default branch.

**Tech Stack:** Git, GitHub CLI, Python project files

---

### Task 1: Add repository ignore rules

**Files:**
- Create: `.gitignore`
- Modify: `docs/plans/2026-03-11-publish-github.md`

**Step 1: Create the ignore file**

Add a root `.gitignore` that excludes:
- `**/.venv/`
- `__pycache__/`
- `*.py[cod]`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `.ipynb_checkpoints/`
- `.DS_Store`

**Step 2: Verify tracked scope**

Run: `git status --short`
Expected: Project files are visible for staging, but `.venv` and cache paths are absent.

### Task 2: Initialize local Git history

**Files:**
- Create: `.git/` (repository metadata)
- Modify: `.gitignore`

**Step 1: Initialize Git**

Run: `git init`
Expected: Git repository created in project root.

**Step 2: Stage project files**

Run: `git add .`
Expected: All desired files staged, with `.venv` and caches omitted.

**Step 3: Create initial commit**

Run: `git commit -m "Initial commit"`
Expected: Initial repository history created successfully.

### Task 3: Create GitHub repository and push

**Files:**
- Modify: `.git/config`

**Step 1: Create the remote repository**

Run: `gh repo create liver_rfa --public --source . --remote origin --push`
Expected: Public GitHub repository created and current branch pushed.

**Step 2: Verify remote state**

Run: `git remote -v` and `git status`
Expected: `origin` points to the new GitHub repo and the working tree is clean.
