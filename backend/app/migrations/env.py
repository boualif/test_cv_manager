import os
import sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the 'app' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from models.candidate import Base
from config.settings import settings

# The key part - make sure this uses the environment variable via settings
config = context.config
postgres_url = os.getenv("POSTGRES_URI")  # <-- Change this to match
if postgres_url:
    config.set_main_option('sqlalchemy.url', postgres_url)
else:
    config.set_main_option('sqlalchemy.url', settings.POSTGRES_URI)

connectable = engine_from_config(
    config.get_section(config.config_ini_section),
    prefix='sqlalchemy.',
    poolclass=pool.NullPool)

with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata
    )

    with context.begin_transaction():
        context.run_migrations()
