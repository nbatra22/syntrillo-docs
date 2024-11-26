from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()

class Messages(db.Model):
    __tablename__ = 'Messages'
    
    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    content = db.Column(db.Text, nullable=False)
    sender_role = db.Column(Enum('user', 'assistant', name='sender_roles'), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {
            'role': self.sender_role,
            'content': [{"type": "text", "text": self.content}]
        }

    def __repr__(self):
        return f'<Messages {self.message_id}>'