import time
import uuid
import logging
from flask import g, request, current_app

REQUEST_METRICS = {
    'total': 0,
    'by_path': {}
}

def before_request():
    g.start_time = time.time()
    # Tenant resolution (stub)
    tenant = request.headers.get('X-Tenant-ID') or current_app.config.get('DEFAULT_TENANT_ID')
    g.tenant_id = tenant
    # Correlation / request ID
    g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    # Attach adapter for contextual logging
    g.log = logging.LoggerAdapter(logging.getLogger('request'), {
        'tenant_id': g.tenant_id,
        'request_id': g.request_id
    })
    g.log.info('request.start', extra={'path': request.path, 'method': request.method})


def after_request(response):
    duration = time.time() - getattr(g, 'start_time', time.time())
    REQUEST_METRICS['total'] += 1
    path_key = request.path.split('?')[0]
    data = REQUEST_METRICS['by_path'].setdefault(path_key, {'count':0, 'accumulated_time':0.0})
    data['count'] += 1
    data['accumulated_time'] += duration
    response.headers['X-Process-Time'] = f"{duration:.4f}s"
    response.headers['X-Tenant'] = getattr(g, 'tenant_id', 'unknown')
    response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
    if hasattr(g, 'log'):
        g.log.info('request.end', extra={'status_code': response.status_code, 'duration_ms': int(duration*1000)})
    return response
