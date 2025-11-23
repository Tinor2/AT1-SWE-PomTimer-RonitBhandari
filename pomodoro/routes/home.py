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
    
    # Get tasks for the active list using hierarchical query
    tasks = []
    if active_list:
        tasks = get_tasks_with_hierarchy(active_list['id'], current_user.id)
    
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
    
    # Insert the new task for the current user with hierarchical fields
    cursor = db.execute(
        'INSERT INTO tasks (list_id, user_id, content, position, parent_id, level, path) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (active_list['id'], current_user.id, content, max_position + 1, None, 0, None)
    )
    new_task_id = cursor.lastrowid
    
    # Update the path for the new root-level task
    db.execute('UPDATE tasks SET path = ? WHERE id = ?', (str(new_task_id), new_task_id))
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
        return jsonify({'error': 'Missing required data'}), 400
    
    # Convert task IDs to integers if they're strings
    try:
        task_order = [int(task_id) for task_id in task_order]
        list_id = int(list_id)
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data format'}), 400
    
    db = get_db()
    
    # Verify the list belongs to the current user
    list_check = db.execute(
        'SELECT id FROM lists WHERE id = ? AND user_id = ?',
        (list_id, current_user.id)
    ).fetchone()
    
    if not list_check:
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

@bp.route('/task/<int:parent_id>/subtask', methods=['POST'])
@login_required
def create_subtask(parent_id):
    """Create a new subtask under the specified parent task."""
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Subtask content cannot be empty.')
        return redirect(url_for('home.index'))
    
    db = get_db()
    
    # Verify parent task ownership and get its details
    parent_task = db.execute(
        'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
        (parent_id, current_user.id)
    ).fetchone()
    
    if not parent_task:
        flash('Parent task not found or access denied.', 'error')
        return redirect(url_for('home.index'))
    
    # Get the highest position among siblings (tasks with same parent)
    max_position = db.execute(
        'SELECT COALESCE(MAX(position), -1) FROM tasks WHERE list_id = ? AND user_id = ? AND parent_id = ?',
        (parent_task['list_id'], current_user.id, parent_id)
    ).fetchone()[0]
    
    # Insert the new subtask
    cursor = db.execute(
        'INSERT INTO tasks (list_id, user_id, content, position, parent_id, level, path) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (parent_task['list_id'], current_user.id, content, max_position + 1, parent_id, parent_task['level'] + 1, None)
    )
    new_task_id = cursor.lastrowid
    
    # Update the path for the new subtask
    new_path = f"{parent_task['path']}/{new_task_id}"
    db.execute('UPDATE tasks SET path = ? WHERE id = ?', (new_path, new_task_id))
    db.commit()
    
    return redirect(url_for('home.index'))

@bp.route('/task/<int:id>/move', methods=['POST'])
@login_required
def move_task(id):
    """Move a task to a new parent or reorder within the same level."""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    data = request.get_json()
    new_parent_id = data.get('new_parent_id')
    operation = data.get('operation', 'move')
    
    db = get_db()
    
    # Verify task ownership
    task = db.execute(
        'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()
    
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 403
    
    try:
        if operation == 'make_subtask' and new_parent_id:
            # Verify new parent ownership
            new_parent = db.execute(
                'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
                (new_parent_id, current_user.id)
            ).fetchone()
            
            if not new_parent:
                return jsonify({'error': 'Parent task not found or access denied'}), 403
            
            # Prevent circular references
            if is_descendant(new_parent_id, id, db):
                return jsonify({'error': 'Cannot create circular reference'}), 400
            
            # Update task to become a subtask
            new_level = new_parent['level'] + 1
            new_path = f"{new_parent['path']}/{id}"
            
            db.execute(
                'UPDATE tasks SET parent_id = ?, level = ?, path = ? WHERE id = ?',
                (new_parent_id, new_level, new_path, id)
            )
            
            # Recursively update all descendants
            update_descendants_paths(id, new_path, new_level, db)
            
        elif operation == 'move_to_root':
            # Move task to root level
            db.execute(
                'UPDATE tasks SET parent_id = NULL, level = 0, path = ? WHERE id = ?',
                (str(id), id)
            )
            
            # Recursively update all descendants
            update_descendants_paths(id, str(id), 0, db)
        
        db.commit()
        return jsonify({'success': True, 'updated_tasks': get_tasks_with_hierarchy(task['list_id'], current_user.id)})
        
    except Exception as e:
        db.rollback()
        print(f"Database error in move_task: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@bp.route('/tasks/tree', methods=['GET'])
@login_required
def get_task_tree():
    """Get the hierarchical task structure for the active list."""
    db = get_db()
    
    # Get the active list
    active_list = db.execute(
        'SELECT id FROM lists WHERE is_active = 1 AND user_id = ?',
        (current_user.id,)
    ).fetchone()
    
    if not active_list:
        return jsonify({'error': 'No active list'}), 404
    
    tasks = get_tasks_with_hierarchy(active_list['id'], current_user.id)
    return jsonify({'tasks': tasks})

# Helper functions for hierarchical operations

def get_tasks_with_hierarchy(list_id, user_id):
    """Get tasks ordered hierarchically with proper nesting."""
    db = get_db()
    query = '''
    WITH RECURSIVE task_tree AS (
        SELECT id, content, is_done, tags, position, parent_id, level, path, created_at
        FROM tasks 
        WHERE list_id = ? AND user_id = ? AND parent_id IS NULL
        
        UNION ALL
        
        SELECT t.id, t.content, t.is_done, t.tags, t.position, 
               t.parent_id, t.level, t.path, t.created_at
        FROM tasks t
        JOIN task_tree tt ON t.parent_id = tt.id
        WHERE t.list_id = ? AND t.user_id = ?
    )
    SELECT * FROM task_tree ORDER BY 
        CASE WHEN parent_id IS NULL THEN position ELSE 999999 END,
        path,
        CASE WHEN parent_id IS NOT NULL THEN position ELSE 999999 END;
    '''
    return db.execute(query, (list_id, user_id, list_id, user_id)).fetchall()

def is_descendant(potential_ancestor_id, potential_descendant_id, db):
    """Check if potential_ancestor_id is a descendant of potential_descendant_id."""
    descendant = db.execute(
        'SELECT path FROM tasks WHERE id = ?',
        (potential_descendant_id,)
    ).fetchone()
    
    if not descendant:
        return False
    
    ancestor_path = str(potential_ancestor_id)
    descendant_path = descendant['path']
    
    # Check if ancestor's ID appears in descendant's path
    return ancestor_path in descendant_path.split('/')

def update_descendants_paths(parent_id, new_parent_path, new_parent_level, db):
    """Recursively update paths and levels of all descendants."""
    descendants = db.execute(
        'SELECT id, level FROM tasks WHERE parent_id = ?',
        (parent_id,)
    ).fetchall()
    
    for descendant in descendants:
        new_path = f"{new_parent_path}/{descendant['id']}"
        new_level = new_parent_level + 1
        
        db.execute(
            'UPDATE tasks SET path = ?, level = ? WHERE id = ?',
            (new_path, new_level, descendant['id'])
        )
        
        # Recursively update this descendant's children
        update_descendants_paths(descendant['id'], new_path, new_level, db)