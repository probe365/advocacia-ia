"""Minimal legacy shim. Use wsgi:app for production (Gunicorn)."""
from dotenv import load_dotenv
load_dotenv()
from app import create_app

app = create_app()

@app.get('/')
def root():
    return {'status': 'ok'}

if __name__ == '__main__':
    # Dev convenience run
    app.run(port=5001, debug=True)
