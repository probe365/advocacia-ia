import logging
import json
import sys
from datetime import datetime, timezone


class ContextFilter(logging.Filter):
    """Inject context attributes if present on log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'tenant_id'):
            record.tenant_id = None
        if not hasattr(record, 'request_id'):
            record.request_id = None
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            'ts': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'msg': record.getMessage(),
            'module': record.module,
            'func': record.funcName,
            'line': record.lineno,
            'tenant_id': getattr(record, 'tenant_id', None),
            'request_id': getattr(record, 'request_id', None),
        }
        if record.exc_info:
            base['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


def init_logging(level: str = 'INFO'):
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(ContextFilter())
    root.addHandler(handler)
