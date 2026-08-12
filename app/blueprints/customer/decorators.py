from functools import wraps
from flask import session, abort, g
from app.models.table import Table


def table_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        table_id = session.get("table_id")
        qr_token = session.get("qr_token")

        if not table_id or not qr_token:
            abort(403)

        table = Table.query.filter_by(id=table_id, qr_token=qr_token, is_active=True).first()
        if not table:
            session.clear()
            abort(403)

        g.current_table = table
        return f(*args, **kwargs)
    return decorated_function
