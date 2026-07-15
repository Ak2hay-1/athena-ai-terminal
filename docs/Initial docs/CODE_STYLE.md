# Athena Code Style Guide

---

# Python Version

Python 3.12+

---

# Formatting

Black

Line length

88

---

# Imports

Use absolute imports.

Correct

from app.services.analysis_service import AnalysisService

Incorrect

from ..services import *

---

# Type Hints

Required.

Every public function must include type hints.

---

# Docstrings

Every public class

Every public method

Every service

Every repository

Google style.

Example

"""
Analyze market conditions.

Args:
    dataframe: Candle dataframe.

Returns:
    Analysis result.
"""

---

# Naming

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

---

# Logging

Never use print().

Always use the project logger.

Good

logger.info("Analysis completed")

Bad

print("Done")

---

# Exceptions

Never swallow exceptions.

Always log them.

Raise meaningful exceptions.

---

# Configuration

Never hardcode

Passwords

API Keys

Broker Credentials

Database URLs

Everything comes from configuration.

---

# SQLAlchemy

Repositories only.

No raw SQL unless necessary.

Transactions managed by services.

---

# Pydantic

Use BaseModel

Validation required

Use ConfigDict

---

# Comments

Explain WHY.

Do not explain WHAT.

Bad

# Increment x

x += 1

Good

# MT5 occasionally returns duplicate ticks.
# Ignore duplicates to prevent double processing.
