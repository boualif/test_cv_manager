# Fix the script_location in alembic.ini
alembic_ini_path = "app/database/alembic.ini"

with open(alembic_ini_path, 'r') as f:
    content = f.read()

# Replace the script_location line
new_content = content.replace(
    "script_location = migrations",
    "script_location = app/database/migrations"
)

with open(alembic_ini_path, 'w') as f:
    f.write(new_content)

print(f"Updated {alembic_ini_path} with the correct script_location")
