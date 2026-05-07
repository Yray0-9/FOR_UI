"""
Central registry of all database table models used by SafeBooks.

Rule for future phases:
- Keep one table per model file (example: client_model.py, period_model.py)
- Register every new table model here for easy migration preparation and auditing.
"""

from .admin_model import AdminAccount
from .user_model import BookkeeperAccount
from .client_model import Client
from .period_model import Period
from .financial_record_model import FinancialRecord
from .financial_record_line_model import FinancialRecordLine

ALL_TABLE_MODELS = (
    AdminAccount,
    BookkeeperAccount,
    Client,
    Period,
    FinancialRecord,
    FinancialRecordLine,
)
