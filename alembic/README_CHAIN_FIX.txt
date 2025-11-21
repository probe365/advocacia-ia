To fix your Alembic migration chain:

1. Ensure 0001_create_processos_table.py is the first migration (down_revision = None).
2. For every migration that alters the 'processos' table, set its down_revision to '0001_create_processos_table' (or to the previous migration in the correct order).
3. For merge migrations, ensure their down_revision includes all previous heads.
4. If you want exact changes, list the filenames and the 'revision' and 'down_revision' headers of all migration files in alembic/versions/.

After fixing the chain, run:
alembic downgrade base
alembic upgrade head

This will apply migrations in the correct order and resolve the missing table error.