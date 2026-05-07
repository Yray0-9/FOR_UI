# Service layer package for backend business logic.

from .auth_service import login_user, login_user_or_admin, register_user
from .client_service import (
	create_client_for_bookkeeper,
	delete_client_for_bookkeeper,
	list_clients_for_bookkeeper,
	update_client_for_bookkeeper,
)
from .financial_record_service import (
	create_record_for_client_period,
	delete_record_for_client,
	list_financial_clients_for_bookkeeper,
	list_records_for_client_period,
	list_transactions_for_client_range,
	update_record_for_client_period,
)
from .dashboard_service import get_dashboard_summary_for_bookkeeper
from .analytics_service import get_analytics_summary_for_bookkeeper

__all__ = [
	"login_user",
	"login_user_or_admin",
	"register_user",
	"list_clients_for_bookkeeper",
	"create_client_for_bookkeeper",
	"update_client_for_bookkeeper",
	"delete_client_for_bookkeeper",
	"list_financial_clients_for_bookkeeper",
	"list_records_for_client_period",
	"list_transactions_for_client_range",
	"create_record_for_client_period",
	"update_record_for_client_period",
	"delete_record_for_client",
	"get_dashboard_summary_for_bookkeeper",
	"get_analytics_summary_for_bookkeeper",
]
