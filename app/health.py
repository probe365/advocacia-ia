from flask import Blueprint, jsonify
import time

health_bp = Blueprint('health', __name__)

start_time = time.time()

@health_bp.route('/healthz')
def healthz():
    # Lightweight health check
    uptime = time.time() - start_time
    return jsonify(status='ok', uptime_seconds=int(uptime))
