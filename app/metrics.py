from flask import Blueprint, jsonify
from .middleware import REQUEST_METRICS

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics')
def metrics():
    output = {
        'requests_total': REQUEST_METRICS['total'],
        'paths': {
            path: {
                'count': data['count'],
                'avg_time': (data['accumulated_time']/data['count']) if data['count'] else 0
            } for path, data in REQUEST_METRICS['by_path'].items()
        }
    }
    return jsonify(output)
