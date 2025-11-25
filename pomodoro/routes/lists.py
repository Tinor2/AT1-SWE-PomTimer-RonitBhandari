from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

bp = Blueprint('lists', __name__, url_prefix='/lists')

def get_db():
    """Helper function to get database connection."""
    from .. import db
    return db.get_db()

@bp.route('/')
@login_required
def index():
    db = get_db()
    lists = db.execute(
        'SELECT * FROM lists WHERE user_id = ? ORDER BY name',
        (current_user.id,)
    ).fetchall()
    return render_template('lists/index.html', lists=lists)

@bp.route('/<int:id>/select', methods=('POST',))
@login_required
def select_list(id):
    db = get_db()
    
    # Verify the list belongs to the current user
    list_to_select = db.execute(
        'SELECT id FROM lists WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()
    
    if not list_to_select:
        flash('List not found or access denied.', 'error')
        return redirect(url_for('lists.index'))
    
    # Set all of user's lists to inactive
    db.execute('UPDATE lists SET is_active = 0 WHERE user_id = ?', (current_user.id,))
    
    # Set the selected list to active
    db.execute('UPDATE lists SET is_active = 1 WHERE id = ? AND user_id = ?', (id, current_user.id))
    db.commit()
    
    return redirect(url_for('home.index'))

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        error = None
        
        if not name:
            error = 'List name is required.'
            
        if error is None:
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO lists (user_id, name, description) VALUES (?, ?, ?)',
                    (current_user.id, name, description)
                )
                db.commit()
                return redirect(url_for('lists.index'))
            except db.IntegrityError:
                error = f"List '{name}' already exists."
        
        flash(error)
    
    return render_template('lists/create.html')

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete_list(id):
    db = get_db()
    
    # Check if this is the active list and verify ownership
    list_to_delete = db.execute(
        'SELECT is_active FROM lists WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()
    
    if not list_to_delete:
        flash('List not found or access denied.', 'error')
        return redirect(url_for('lists.index'))
    
    was_active = list_to_delete['is_active']
    
    # Delete the list (CASCADE will delete associated tasks)
    db.execute('DELETE FROM lists WHERE id = ? AND user_id = ?', (id, current_user.id))
    
    # If we deleted the active list, make another list active for this user
    if was_active:
        new_active = db.execute(
            'SELECT id FROM lists WHERE user_id = ? LIMIT 1',
            (current_user.id,)
        ).fetchone()
        if new_active:
            db.execute('UPDATE lists SET is_active = 1 WHERE id = ? AND user_id = ?', (new_active['id'], current_user.id))
    
    db.commit()
    flash('List deleted successfully.')
    
    return redirect(url_for('lists.index'))