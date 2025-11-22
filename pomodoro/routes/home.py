from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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
            'SELECT * FROM tasks WHERE list_id = ? AND user_id = ? ORDER BY position',
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
    
    # Get the highest position in the list
    max_position = db.execute(
        'SELECT COALESCE(MAX(position), -1) FROM tasks WHERE list_id = ? AND user_id = ?',
        (active_list['id'], current_user.id)
    ).fetchone()[0]
    
    # Insert the new task for the current user
    db.execute(
        'INSERT INTO tasks (list_id, user_id, content, position) VALUES (?, ?, ?, ?)',
        (active_list['id'], current_user.id, content, max_position + 1)
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

@bp.route('/task/reorder', methods=['POST'])
@login_required
def reorder_tasks():
    """Update task positions based on drag-and-drop."""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    data = request.get_json()
    task_order = data.get('task_order', [])
    list_id = data.get('list_id')
    
    if not task_order or not list_id:
        print(f"Missing data: task_order={task_order}, list_id={list_id}")
        return jsonify({'error': 'Missing required data'}), 400
    
    # Convert task IDs to integers if they're strings
    try:
        task_order = [int(task_id) for task_id in task_order]
        list_id = int(list_id)
    except (ValueError, TypeError) as e:
        print(f"Invalid data types: {e}")
        return jsonify({'error': 'Invalid data format'}), 400
    
    db = get_db()
    
    # Verify the list belongs to the current user
    list_check = db.execute(
        'SELECT id FROM lists WHERE id = ? AND user_id = ?',
        (list_id, current_user.id)
    ).fetchone()
    
    if not list_check:
        print(f"Unauthorized access: list_id={list_id}, user_id={current_user.id}")
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Update positions for all tasks in the order
        for index, task_id in enumerate(task_order):
            result = db.execute(
                'UPDATE tasks SET position = ? WHERE id = ? AND user_id = ? AND list_id = ?',
                (index, task_id, current_user.id, list_id)
            )
            if result.rowcount == 0:
                print(f"No rows updated for task_id={task_id}, index={index}")
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        print(f"Database error in reorder_tasks: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500