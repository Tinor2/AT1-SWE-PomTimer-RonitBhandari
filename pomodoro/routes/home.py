from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

bp = Blueprint('home', __name__)

def get_db():
    """Helper function to get database connection."""
    from .. import db
    return db.get_db()

@bp.route('/')
@login_required
def index():
    db = get_db()
    
    # Get the active list for the current user
    active_list = db.execute(
        'SELECT * FROM lists WHERE is_active = 1 AND user_id = ?',
        (current_user.id,)
    ).fetchone()
    
    # Get tasks for the active list
    tasks = []
    if active_list:
        tasks = db.execute(
            'SELECT * FROM tasks WHERE list_id = ? AND user_id = ? ORDER BY created_at',
            (active_list['id'], current_user.id)
        ).fetchall()
    
    return render_template('home/index.html', active_list=active_list, tasks=tasks)

@bp.route('/task/add', methods=['POST'])
@login_required
def add_task():
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Task content cannot be empty.')
        return redirect(url_for('home.index'))
    
    db = get_db()
    
    # Get the active list for the current user
    active_list = db.execute(
        'SELECT id FROM lists WHERE is_active = 1 AND user_id = ?',
        (current_user.id,)
    ).fetchone()
    
    if not active_list:
        flash('No active list selected.')
        return redirect(url_for('home.index'))
    
    # Insert the new task for the current user
    db.execute(
        'INSERT INTO tasks (list_id, user_id, content) VALUES (?, ?, ?)',
        (active_list['id'], current_user.id, content)
    )
    db.commit()
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    db = get_db()
    
    # Get current status and verify ownership
    task = db.execute(
        'SELECT is_done FROM tasks WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()
    
    if task:
        # Toggle the status
        new_status = 0 if task['is_done'] else 1
        db.execute('UPDATE tasks SET is_done = ? WHERE id = ? AND user_id = ?', (new_status, id, current_user.id))
        db.commit()
    else:
        flash('Task not found or access denied.', 'error')
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/delete', methods=['POST'])
@login_required
def delete_task(id):
    db = get_db()
    result = db.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (id, current_user.id))
    db.commit()
    
    if result.rowcount == 0:
        flash('Task not found or access denied.', 'error')
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/tags', methods=['POST'])
@login_required
def update_tags(id):
    """Update tags for a task. Accepts comma-separated colors in 'tags' field."""
    tags = request.form.get('tags', '').strip()
    # Normalize: remove spaces, deduplicate and keep order
    colors = [c.strip() for c in tags.split(',') if c.strip()]
    seen = set()
    normalized = []
    for c in colors:
        if c not in seen:
            normalized.append(c)
            seen.add(c)
    tags_value = ','.join(normalized)

    db = get_db()
    result = db.execute('UPDATE tasks SET tags = ? WHERE id = ? AND user_id = ?', (tags_value, id, current_user.id))
    db.commit()
    
    if result.rowcount == 0:
        flash('Task not found or access denied.', 'error')
    
    return redirect(url_for('home.index'))