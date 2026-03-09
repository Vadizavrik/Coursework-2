# Точка входа Flask-приложения
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
import os


class Base(DeclarativeBase):
    """Базовый класс для моделей (SQLAlchemy 2.0+)"""
    pass


def create_app():
    """Фабрика приложения — создаёт app, db, migrate"""
    app = Flask(__name__)
    app.secret_key = 'tatar_complexity_secret_key'
    
    # Путь к БД в папке instance/
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'language_complexity.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Инициализация расширений
    db = SQLAlchemy(app, model_class=Base)
    migrate = Migrate(app, db)
    
    # Регистрация маршрутов (app и db передаются явно)
    from routes import register_routes
    register_routes(app, db)
    
    return app, db, migrate


if __name__ == '__main__':
    app, db, migrate = create_app()
    
    # Создание таблиц при первом запуске
    with app.app_context():
        db.create_all()
    
    print("=" * 60)
    print("Запуск веб-приложения")
    print("=" * 60)
    print("Откройте в браузере: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)