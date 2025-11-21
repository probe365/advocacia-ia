import os
import sys
from flask import current_app
from app import create_app
from alembic import command
from alembic.config import Config

app = create_app()

def alembic_config():
    cfg = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    cfg.set_main_option('script_location', 'alembic')
    return cfg

@app.cli.command('db-upgrade')
def db_upgrade():
    """Apply latest database migrations."""
    command.upgrade(alembic_config(), 'head')

@app.cli.command('db-revision')
def db_revision():
    """Create new autogenerate revision (manual editing recommended)."""
    message = input('Revision message: ')
    command.revision(alembic_config(), message=message, autogenerate=True)

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', '5001')))
