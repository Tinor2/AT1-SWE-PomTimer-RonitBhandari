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
    task_hierarchy_html = ""
    if active_list:
        tasks = get_tasks_with_hierarchy(active_list['id'], current_user.id)
        task_hierarchy_html = render_task_hierarchy(tasks)
    
    return render_template('home/index.html', active_list=active_list, task_hierarchy_html=task_hierarchy_html)

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

@bp.route('/update-tags-ajax/<int:id>', methods=['POST'])
@login_required
def update_tags_ajax(id):
    """AJAX endpoint for real-time tag updates."""
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
        return jsonify({'success': False, 'error': 'Task not found or access denied'})
    
    return jsonify({'success': True, 'tags': tags_value})

@bp.route('/api/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    """API endpoint for tag CRUD operations."""
    db = get_db()
    
    if request.method == 'GET':
        # Get all user tags
        tags = db.execute(
            'SELECT * FROM user_tags WHERE user_id = ? ORDER BY position ASC, color_name ASC',
            (current_user.id,)
        ).fetchall()
        
        return jsonify({
            'success': True,
            'tags': [dict(tag) for tag in tags]
        })
    
    elif request.method == 'POST':
        # Add new tag
        color_hex = request.form.get('color_hex', '').strip()
        color_name = request.form.get('color_name', '').strip()
        
        if not color_hex:
            return jsonify({'success': False, 'error': 'Color is required'})
        
        try:
            # Get next position
            max_position = db.execute(
                'SELECT MAX(position) FROM user_tags WHERE user_id = ?',
                (current_user.id,)
            ).fetchone()[0] or 0
            
            # Insert new tag
            db.execute(
                'INSERT INTO user_tags (user_id, color_hex, color_name, position) VALUES (?, ?, ?, ?)',
                (current_user.id, color_hex, color_name or None, max_position + 1)
            )
            db.commit()
            
            return jsonify({'success': True, 'message': 'Tag added successfully'})
            
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                return jsonify({'success': False, 'error': 'Tag color already exists'})
            return jsonify({'success': False, 'error': 'Failed to add tag'})

@bp.route('/api/tags/<int:tag_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_single_tag(tag_id):
    """API endpoint for individual tag operations."""
    db = get_db()
    
    # Verify tag belongs to current user
    tag = db.execute(
        'SELECT * FROM user_tags WHERE id = ? AND user_id = ?',
        (tag_id, current_user.id)
    ).fetchone()
    
    if not tag:
        return jsonify({'success': False, 'error': 'Tag not found'})
    
    if request.method == 'PUT':
        # Update tag
        color_hex = request.form.get('color_hex', '').strip()
        color_name = request.form.get('color_name', '').strip()
        
        if not color_hex:
            return jsonify({'success': False, 'error': 'Color is required'})
        
        try:
            db.execute(
                'UPDATE user_tags SET color_hex = ?, color_name = ? WHERE id = ?',
                (color_hex, color_name or None, tag_id)
            )
            db.commit()
            
            return jsonify({'success': True, 'message': 'Tag updated successfully'})
            
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                return jsonify({'success': False, 'error': 'Tag color already exists'})
            return jsonify({'success': False, 'error': 'Failed to update tag'})
    
    elif request.method == 'DELETE':
        # Delete tag
        try:
            db.execute('DELETE FROM user_tags WHERE id = ?', (tag_id,))
            db.commit()
            
            return jsonify({'success': True, 'message': 'Tag deleted successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': 'Failed to delete tag'})

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

@bp.route('/task/update_hierarchy', methods=['POST'])
@login_required
def update_task_hierarchy():
    """Update task hierarchy (parent_id and position)."""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    data = request.get_json()
    task_id = data.get('task_id')
    new_parent_id = data.get('parent_id')  # null for main tasks
    position_after_id = data.get('position_after_id')  # optional
    list_id = data.get('list_id')
    
    if not task_id or list_id is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    # Verify the task belongs to the current user
    task_check = db.execute(
        'SELECT id FROM tasks WHERE id = ? AND user_id = ?',
        (task_id, current_user.id)
    ).fetchone()
    
    if not task_check:
        return jsonify({'error': 'Task not found or unauthorized'}), 404
    
    # Verify the list belongs to the current user
    list_check = db.execute(
        'SELECT id FROM lists WHERE id = ? AND user_id = ?',
        (list_id, current_user.id)
    ).fetchone()
    
    if not list_check:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Update the task hierarchy with proper level and path
        if new_parent_id is None:
            # Moving to root level
            new_level = 0
            new_path = str(task_id)
            db.execute(
                'UPDATE tasks SET parent_id = ?, level = ?, path = ? WHERE id = ? AND user_id = ?',
                (new_parent_id, new_level, new_path, task_id, current_user.id)
            )
            # Update all descendants
            update_descendants_paths(task_id, new_path, new_level, db)
        else:
            # Moving to a parent
            # Verify new parent ownership and get its hierarchy info
            new_parent = db.execute(
                'SELECT level, path FROM tasks WHERE id = ? AND user_id = ?',
                (new_parent_id, current_user.id)
            ).fetchone()
            
            if not new_parent:
                return jsonify({'error': 'Parent task not found or access denied'}), 403
            
            # Prevent circular references
            if is_descendant(new_parent_id, task_id, db):
                return jsonify({'error': 'Cannot create circular reference'}), 400
            
            new_level = new_parent['level'] + 1
            new_path = f"{new_parent['path']}/{task_id}"
            
            db.execute(
                'UPDATE tasks SET parent_id = ?, level = ?, path = ? WHERE id = ? AND user_id = ?',
                (new_parent_id, new_level, new_path, task_id, current_user.id)
            )
            # Update all descendants
            update_descendants_paths(task_id, new_path, new_level, db)
        
        # Update position
        if position_after_id:
            # Get the position of the task we're inserting after
            after_task = db.execute(
                'SELECT position FROM tasks WHERE id = ? AND user_id = ? AND list_id = ?',
                (position_after_id, current_user.id, list_id)
            ).fetchone()
            
            if after_task:
                new_position = after_task['position'] + 1
                # Update positions of tasks that come after
                db.execute(
                    'UPDATE tasks SET position = position + 1 WHERE position > ? AND user_id = ? AND list_id = ?',
                    (after_task['position'], current_user.id, list_id)
                )
                
                db.execute(
                    'UPDATE tasks SET position = ? WHERE id = ? AND user_id = ?',
                    (new_position, task_id, current_user.id)
                )
        else:
            # Moving to top of list - position 0
            # Shift all existing tasks down by 1
            db.execute(
                'UPDATE tasks SET position = position + 1 WHERE user_id = ? AND list_id = ?',
                (current_user.id, list_id)
            )
            
            # Set this task to position 0
            db.execute(
                'UPDATE tasks SET position = 0 WHERE id = ? AND user_id = ?',
                (task_id, current_user.id)
            )
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        print(f"Database error in update_task_hierarchy: {e}")
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
        return jsonify({'success': True})
        
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

# Phase 1: DOM Structure Migration Functions
def render_task_hierarchy(tasks):
    """Render tasks as nested HTML structure for Phase 1."""
    html = ""
    
    # Group tasks by parent_id
    root_tasks = [task for task in tasks if task['parent_id'] is None]
    
    for task in root_tasks:
        html += render_parent_task(task, tasks)
    
    return html

def render_parent_task(task, all_tasks):
    """Render a parent task with nested subtasks."""
    from flask import url_for
    
    # Find subtasks of this task
    subtasks = [t for t in all_tasks if t['parent_id'] == task['id']]
    
    # Determine CSS classes
    css_classes = ['task-item']
    if task['is_done']:
        css_classes.append('completed')
    if subtasks:
        css_classes.append('parent')
    
    # Process tags - use original color mapping
    tags_str = task['tags'] or ''
    tags_list = tags_str.split(',') if tags_str else []
    color_to_class = {
        '#ff5252':'red',
        '#ff9800':'orange',
        '#ffeb3b':'yellow',
        '#4caf50':'green',
        '#00bcd4':'cyan',
        '#3f51b5':'indigo',
        '#9c27b0':'purple',
        '#795548':'brown'
    }
    
    html = f'''<li class="{' '.join(css_classes)}" data-task-id="{task['id']}" draggable="true">
        <div class="task-header">
            <div class="drag-handle">⋮⋮</div>
            <form method="post" action="{url_for('home.toggle_task', id=task['id'])}" style="display: inline;">
                <input type="checkbox" {"checked" if task['is_done'] else ""} onchange="this.form.submit()">
            </form>
            <span class="task-content">{task['content']}</span>'''
    
    # Add tags display using original structure
    if tags_list and any(color.strip() for color in tags_list):
        html += '<div class="task-tags-display">'
        for color in tags_list:
            if color.strip():
                cc = color_to_class.get(color.strip())
                if cc:
                    html += f'<span class="tag-dot tag-{cc}" title="{color.strip()}"></span>'
        html += '</div>'
    
    # Add tag button and popup using original structure
    html += f'''
            <form method="post" action="{url_for('home.update_tags', id=task['id'])}" class="tag-form" data-task-id="{task['id']}">
                <input type="hidden" name="tags" value="{tags_str}">
                <button type="button" class="tag-btn" aria-label="Edit tags">
                    <img src="{url_for('static', filename='assets/tag.png')}" alt="Tags" class="tag-icon">
                </button>
                <div class="tag-menu" role="menu" aria-hidden="true">
                    <div class="tag-menu-header">
                        <span class="tag-menu-title">Tags</span>
                        <button type="button" class="tag-settings-btn" aria-label="Tag settings" title="Manage tags">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <path d="m12 1 0 6m0 6 0 6m11-7-6 0m-6 0-6 0"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="tag-menu-grid">
                        <button type="button" class="color-choice tag-red" data-color="#ff5252" title="#ff5252"></button>
                        <button type="button" class="color-choice tag-orange" data-color="#ff9800" title="#ff9800"></button>
                        <button type="button" class="color-choice tag-yellow" data-color="#ffeb3b" title="#ffeb3b"></button>
                        <button type="button" class="color-choice tag-green" data-color="#4caf50" title="#4caf50"></button>
                        <button type="button" class="color-choice tag-cyan" data-color="#00bcd4" title="#00bcd4"></button>
                        <button type="button" class="color-choice tag-indigo" data-color="#3f51b5" title="#3f51b5"></button>
                        <button type="button" class="color-choice tag-purple" data-color="#9c27b0" title="#9c27b0"></button>
                        <button type="button" class="color-choice tag-brown" data-color="#795548" title="#795548"></button>
                    </div>
                    <div class="tag-menu-actions">
                        <button type="button" class="btn btn-secondary tag-clear">Clear</button>
                        <button type="submit" class="btn btn-primary tag-apply">Apply</button>
                    </div>
                </div>
            </form>
            
            <button type="button" class="delete-btn" data-task-id="{task['id']}" data-task-content="{task['content']}" aria-label="Delete task">
                <img src="{url_for('static', filename='assets/delete.png')}" alt="Delete" class="delete-icon">
            </button>
        </div>'''
    
    # Add subtasks if any
    if subtasks:
        html += '<ul class="task-children">'
        for subtask in subtasks:
            html += render_subtask(subtask)
        html += '</ul>'
    
    html += '</li>'
    return html

def render_subtask(task):
    """Render a single subtask."""
    from flask import url_for
    
    # Process tags - use original color mapping
    tags_str = task['tags'] or ''
    tags_list = tags_str.split(',') if tags_str else []
    color_to_class = {
        '#ff5252':'red',
        '#ff9800':'orange',
        '#ffeb3b':'yellow',
        '#4caf50':'green',
        '#00bcd4':'cyan',
        '#3f51b5':'indigo',
        '#9c27b0':'purple',
        '#795548':'brown'
    }
    
    # Determine CSS classes
    css_classes = ['task-item', 'subtask']
    if task['is_done']:
        css_classes.append('completed')
    
    html = f'''<li class="{' '.join(css_classes)}" data-task-id="{task['id']}" draggable="true">
        <div class="task-header">
            <div class="drag-handle">⋮⋮</div>
            <form method="post" action="{url_for('home.toggle_task', id=task['id'])}" style="display: inline;">
                <input type="checkbox" {"checked" if task['is_done'] else ""} onchange="this.form.submit()">
            </form>
            <span class="task-content">{task['content']}</span>'''
    
    # Add tags display using original structure
    if tags_list and any(color.strip() for color in tags_list):
        html += '<div class="task-tags-display">'
        for color in tags_list:
            if color.strip():
                cc = color_to_class.get(color.strip())
                if cc:
                    html += f'<span class="tag-dot tag-{cc}" title="{color.strip()}"></span>'
        html += '</div>'
    
    # Add tag button and popup using original structure
    html += f'''
            <form method="post" action="{url_for('home.update_tags', id=task['id'])}" class="tag-form" data-task-id="{task['id']}">
                <input type="hidden" name="tags" value="{tags_str}">
                <button type="button" class="tag-btn" aria-label="Edit tags">
                    <img src="{url_for('static', filename='assets/tag.png')}" alt="Tags" class="tag-icon">
                </button>
                <div class="tag-menu" role="menu" aria-hidden="true">
                    <div class="tag-menu-header">
                        <span class="tag-menu-title">Tags</span>
                        <button type="button" class="tag-settings-btn" aria-label="Tag settings" title="Manage tags">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <path d="m12 1 0 6m0 6 0 6m11-7-6 0m-6 0-6 0"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="tag-menu-grid">
                        <button type="button" class="color-choice tag-red" data-color="#ff5252" title="#ff5252"></button>
                        <button type="button" class="color-choice tag-orange" data-color="#ff9800" title="#ff9800"></button>
                        <button type="button" class="color-choice tag-yellow" data-color="#ffeb3b" title="#ffeb3b"></button>
                        <button type="button" class="color-choice tag-green" data-color="#4caf50" title="#4caf50"></button>
                        <button type="button" class="color-choice tag-cyan" data-color="#00bcd4" title="#00bcd4"></button>
                        <button type="button" class="color-choice tag-indigo" data-color="#3f51b5" title="#3f51b5"></button>
                        <button type="button" class="color-choice tag-purple" data-color="#9c27b0" title="#9c27b0"></button>
                        <button type="button" class="color-choice tag-brown" data-color="#795548" title="#795548"></button>
                    </div>
                    <div class="tag-menu-actions">
                        <button type="button" class="btn btn-secondary tag-clear">Clear</button>
                        <button type="submit" class="btn btn-primary tag-apply">Apply</button>
                    </div>
                </div>
            </form>
            
            <button type="button" class="delete-btn" data-task-id="{task['id']}" data-task-content="{task['content']}" aria-label="Delete task">
                <img src="{url_for('static', filename='assets/delete.png')}" alt="Delete" class="delete-icon">
            </button>
        </div>
    </li>'''
    
    return html