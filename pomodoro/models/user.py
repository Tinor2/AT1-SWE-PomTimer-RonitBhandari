from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, created_at=None, last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.last_login = last_login
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        database = db.get_db()
        user_data = database.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        database = db.get_db()
        user_data = database.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        database = db.get_db()
        user_data = database.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    def create(username, email, password):
        """Create a new user."""
        password_hash = generate_password_hash(password)
        database = db.get_db()
        cursor = database.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        database.commit()
        return User.get_by_id(cursor.lastrowid)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp."""
        database = db.get_db()
        database.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (self.id,)
        )
        database.commit()
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
