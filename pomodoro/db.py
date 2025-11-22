import sqlite3
import click
import os
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """Get database connection."""
    if 'db' not in g:
        # Ensure the instance folder exists
        os.makedirs(current_app.instance_path, exist_ok=True)
        
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        _ensure_schema(g.db)

    return g.db

def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """Initialize the database with schema."""
    db = get_db()
    
    # Get the path to the schema file in the project root
    schema_path = os.path.join(current_app.root_path, '..', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        db.executescript(f.read())

@click.command('migrate-user-data')
@with_appcontext
def migrate_user_data_command():
    """Migrate existing lists and tasks to user accounts or clear if no users exist."""
    database = get_db()
    
    # Check if there are any users
    users = database.execute("SELECT id FROM users LIMIT 1").fetchall()
    
    if not users:
        # No users exist, clear all data
        click.echo('No users found. Clearing all lists and tasks...')
        database.execute("DELETE FROM tasks")
        database.execute("DELETE FROM lists")
        database.commit()
        click.echo('Cleared all lists and tasks.')
    else:
        # Get the first user ID
        first_user_id = users[0]['id']
        
        # Update existing lists to belong to the first user
        lists_updated = database.execute(
            "UPDATE lists SET user_id = ? WHERE user_id IS NULL",
            (first_user_id,)
        ).rowcount
        
        # Update existing tasks to belong to the first user
        tasks_updated = database.execute(
            "UPDATE tasks SET user_id = ? WHERE user_id IS NULL",
            (first_user_id,)
        ).rowcount
        
        database.commit()
        click.echo(f'Migrated {lists_updated} lists and {tasks_updated} tasks to user {first_user_id}.')
    
    # Update schema to add user_id columns if they don't exist
    _ensure_schema(database)
    database.commit()
    click.echo('Database migration completed.')

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(migrate_user_data_command)

def _ensure_schema(db: sqlite3.Connection):
    try:
        # Check if users table exists
        db.execute("SELECT 1 FROM users LIMIT 1")
    except sqlite3.Error:
        # Create users table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        db.commit()
    
    try:
        cols = db.execute("PRAGMA table_info(tasks)").fetchall()
        names = {c[1] for c in cols}
        if 'tags' not in names:
            db.execute("ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT ''")
        if 'user_id' not in names:
            db.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
            db.commit()
    except sqlite3.Error:
        pass
    
    try:
        cols = db.execute("PRAGMA table_info(lists)").fetchall()
        names = {c[1] for c in cols}
        if 'user_id' not in names:
            db.execute("ALTER TABLE lists ADD COLUMN user_id INTEGER")
            db.execute("ALTER TABLE lists ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            db.commit()
    except sqlite3.Error:
        pass