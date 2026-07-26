# database/db_manager.py
from database.models import db, User, WorkerProfile, EmployerProfile, JobPosting, Match, Review, Message, Notification
import json
from datetime import datetime

class DatabaseManager:
    @staticmethod
    def get_user_stats():
        return {
            'total_users': User.query.count(),
            'total_workers': User.query.filter_by(role='worker').count(),
            'total_employers': User.query.filter_by(role='employer').count(),
        }
    
    @staticmethod
    def get_recent_users(limit=10):
        return User.query.order_by(User.created_at.desc()).limit(limit).all()