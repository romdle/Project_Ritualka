from __future__ import annotations

import os

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "1")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "xaWXw3NcJ9TEjhbrXN2Cmcm43fVLYqcVMNMehcz7EQZvY3ycLdrgzXH")
