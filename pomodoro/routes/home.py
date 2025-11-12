from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint('home', __name__)

def get_db():
    """Helper function to get database connection."""
    from .. import db
    return db.get_db()

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

@bp.route('/task/add', methods=['POST'])
def add_task():
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Task content cannot be empty.')
        return redirect(url_for('home.index'))
    
    db = get_db()
    
    # Get the active list
    active_list = db.execute(
        'SELECT id FROM lists WHERE is_active = 1'
    ).fetchone()
    
    if not active_list:
        flash('No active list selected.')
        return redirect(url_for('home.index'))
    
    # Insert the new task
    db.execute(
        'INSERT INTO tasks (list_id, content) VALUES (?, ?)',
        (active_list['id'], content)
    )
    db.commit()
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/toggle', methods=['POST'])
def toggle_task(id):
    db = get_db()
    
    # Get current status
    task = db.execute('SELECT is_done FROM tasks WHERE id = ?', (id,)).fetchone()
    
    if task:
        # Toggle the status
        new_status = 0 if task['is_done'] else 1
        db.execute('UPDATE tasks SET is_done = ? WHERE id = ?', (new_status, id))
        db.commit()
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/delete', methods=['POST'])
def delete_task(id):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id = ?', (id,))
    db.commit()
    
    return redirect(url_for('home.index'))