from backend.extensions import db

# models are imported here to expose them via `from backend.models import ...`
from .trip import Trip
from .user import User
from .registry import EmployeeRegistry
