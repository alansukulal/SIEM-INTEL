
from app.config import settings

print("Database URL configured:", bool(settings.database_url))
print("Environment:", settings.environment)
