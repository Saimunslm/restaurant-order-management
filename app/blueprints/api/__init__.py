from app.blueprints.api.routes import api_bp
from app.extensions import csrf

csrf.exempt(api_bp)
