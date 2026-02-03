import os
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.dje_imap_service import DjeImapService

logging.basicConfig(level=logging.INFO)


def main():
    tenant_id = os.getenv("TENANT_ID") or os.getenv("DEFAULT_TENANT_ID", "public")
    service = DjeImapService(tenant_id)
    result = service.sync()
    print(result)


if __name__ == "__main__":
    main()
