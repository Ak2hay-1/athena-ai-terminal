# Contributing to Athena

Welcome to Athena.

Thank you for contributing.

---

# Development Philosophy

Athena follows a startup-first approach.

We prioritize:

- Shipping working software
- Clean architecture
- Readability
- Stability
- Maintainability

Enterprise features are intentionally postponed until after the MVP release.

---

# Development Workflow

Every feature follows the same lifecycle.

Planning

↓

Architecture

↓

Implementation

↓

Testing

↓

Documentation

↓

Pull Request

↓

Merge

---

# Branch Strategy

main

Production

develop

Active Development

feature/<feature-name>

Bug Fixes

bugfix/<bug-name>

Hotfixes

hotfix/<issue-name>

---

# Commit Convention

feat(module): add feature

fix(module): fix issue

refactor(module): improve implementation

docs: documentation updates

test(module): add tests

chore: maintenance

Examples

feat(ai): implement recommendation persistence

fix(mt5): reconnect after disconnect

docs: update roadmap

---

# Pull Requests

Every pull request must include

- Description
- Related Sprint
- Related Issue
- Testing Summary
- Breaking Changes

---

# Definition of Done

A feature is complete only if

- Code implemented
- Tests pass
- Logging added
- Documentation updated
- No linting issues
- No TODO placeholders

---

# Code Reviews

Review checklist

- Readability
- Performance
- Security
- Error Handling
- Logging
- Tests
- Documentation
- API Compatibility

---

# Development Principles

Prefer composition over inheritance.

Avoid unnecessary abstractions.

Keep business logic inside services.

Repositories only access the database.

API never contains business logic.

MT5 SDK is accessed only through the MT5 module.
