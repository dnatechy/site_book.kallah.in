"""KALLAH Book: Flask application factory."""
from flask import Flask
from .config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    from .web.routes import web_bp
    from .api.routes import api_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    from .content import get_site, get_theme, get_locations, theme_css

    @app.context_processor
    def shared_layout():
        return {"site": get_site(), "locations": get_locations(),
                "theme_css": theme_css(get_theme())}
    return app
