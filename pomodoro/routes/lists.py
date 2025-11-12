from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint('lists', __name__, url_prefix='/lists')

def get_db():
    """Helper function to get database connection."""
    from .. import db
    return db.get_db()

@bp.route('/')
def index():
    db = get_db()
    lists = db.execute('SELECT * FROM lists ORDER BY name').fetchall()
    return render_template('lists/index.html', lists=lists)

@bp.route('/<int:id>/select', methods=('POST',))
def select_list(id):
    db = get_db()
    
    # Set all lists to inactive
    db.execute('UPDATE lists SET is_active = 0')
    
    # Set the selected list to active
    db.execute('UPDATE lists SET is_active = 1 WHERE id = ?', (id,))
    db.commit()
    
    return redirect(url_for('lists.index'))

@bp.route('/create', methods=('GET', 'POST'))
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
                    'INSERT INTO lists (name, description) VALUES (?, ?)',
                    (name, description)
                )
                db.commit()
                return redirect(url_for('lists.index'))
            except db.IntegrityError:
                error = f"List '{name}' already exists."
        
        flash(error)
    
    return render_template('lists/create.html')

@bp.route('/<int:id>/delete', methods=('POST',))
def delete_list(id):
    db = get_db()
    
    # Check if this is the active list
    list_to_delete = db.execute('SELECT is_active FROM lists WHERE id = ?', (id,)).fetchone()
    
    if list_to_delete:
        was_active = list_to_delete['is_active']
        
        # Delete the list (CASCADE will delete associated tasks)
        db.execute('DELETE FROM lists WHERE id = ?', (id,))
        
        # If we deleted the active list, make another list active
        if was_active:
            new_active = db.execute('SELECT id FROM lists LIMIT 1').fetchone()
            if new_active:
                db.execute('UPDATE lists SET is_active = 1 WHERE id = ?', (new_active['id'],))
        
        db.commit()
        flash('List deleted successfully.')
    
    return redirect(url_for('lists.index'))