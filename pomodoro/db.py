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

def _ensure_schema(db: sqlite3.Connection):
    try:
        cols = db.execute("PRAGMA table_info(tasks)").fetchall()
        names = {c[1] for c in cols}
        if 'tags' not in names:
            db.execute("ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT ''")
            db.commit()
    except sqlite3.Error:
        pass