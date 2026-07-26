# utils/helpers.py
from datetime import datetime

def format_date(date):
    return date.strftime('%B %d, %Y') if date else 'N/A'

def format_datetime(dt):
    return dt.strftime('%B %d, %Y at %H:%M') if dt else 'N/A'

def time_ago(dt):
    if not dt: return 'Never'
    diff = datetime.utcnow() - dt
    if diff.days > 365: return f"{diff.days // 365} year(s) ago"
    if diff.days > 30: return f"{diff.days // 30} month(s) ago"
    if diff.days > 0: return f"{diff.days} day(s) ago"
    if diff.seconds > 3600: return f"{diff.seconds // 3600} hour(s) ago"
    if diff.seconds > 60: return f"{diff.seconds // 60} minute(s) ago"
    return 'Just now'

def generate_star_rating(rating):
    stars = ''
    for i in range(5):
        stars += '<i class="fa fa-star"></i>' if i < int(rating) else '<i class="fa fa-star-o"></i>'
    return stars