import os
from dotenv import load_dotenv

load_dotenv()
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    user = os.getenv('DB_USER', 'advuser')
    password = os.getenv('DB_PASSWORD', 'probe365')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    db = os.getenv('DB_NAME', 'advdb')
    return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = create_engine(get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
