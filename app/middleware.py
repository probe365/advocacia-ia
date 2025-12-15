import time
import uuid
import logging
from flask import g, request, current_app, session
from flask_login import current_user

REQUEST_METRICS = {
    'total': 0,
    'by_path': {}
}

def before_request():
    g.start_time = time.time()

    tenant = session.get('tenant_id')
    if not tenant and getattr(current_user, 'is_authenticated', False):
        tenant = getattr(current_user, 'tenant_id', None)
    if not tenant:
        tenant = request.headers.get('X-Tenant-ID')
    if not tenant:
        tenant = current_app.config.get('DEFAULT_TENANT_ID')

    g.tenant_id = tenant
    session['tenant_id'] = tenant
    # Correlation / request ID
    g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    # Attach adapter for contextual logging
    g.log = logging.LoggerAdapter(logging.getLogger('request'), {
        'tenant_id': g.tenant_id,
        'request_id': g.request_id
    })
    user_id = current_user.get_id() if getattr(current_user, 'is_authenticated', False) else None
    session_id = session.get('_id') or session.get('session_id')
    g.log.info(
        "request.start path=%s method=%s tenant=%s user=%s session_id=%s session_keys=%s",
        request.path,
        request.method,
        g.tenant_id,
        user_id,
        session_id,
        list(session.keys())
    )


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
        g.log.info(
            "request.end path=%s status=%s duration_ms=%s tenant=%s user=%s",
            request.path,
            response.status_code,
            int(duration * 1000),
            getattr(g, 'tenant_id', None),
            current_user.get_id() if getattr(current_user, 'is_authenticated', False) else None
        )
    return response
