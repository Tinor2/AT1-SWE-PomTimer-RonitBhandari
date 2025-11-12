from flask import Blueprint, render_template, request, redirect, url_for, flash, g

bp = Blueprint('lists', __name__, url_prefix='/lists')

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
    
    return redirect(url_for('home.index'))

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

def get_db():
    from .. import db
    return db.get_db()
