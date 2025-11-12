from flask import Blueprint, render_template, g, redirect, url_for

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    db = get_db()
    
    # Get the active list
    active_list = db.execute(
        'SELECT * FROM lists WHERE is_active = 1'
    ).fetchone()
    
    # Get tasks for the active list
    tasks = []
    if active_list:
        tasks = db.execute(
            'SELECT * FROM tasks WHERE list_id = ? ORDER BY created_at',
            (active_list['id'],)
        ).fetchall()
    
    return render_template('home/index.html', active_list=active_list, tasks=tasks)

def get_db():
    from .. import db
    return db.get_db()
