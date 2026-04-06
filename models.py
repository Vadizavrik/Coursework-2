# Модели базы данных для хранения татарских текстов и их метрик
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey


def init_models(db) -> None:
    """Инициализация моделей с объектом db (избегает циклических импортов)"""
    
    class TextRecord(db.Model):
        """Модель текста, хранит исходный текст, категорию сложности и базовую статистику"""
        __tablename__ = "texts"

        id: Mapped[int] = mapped_column(primary_key=True)
        file_name: Mapped[str] = mapped_column(String(255), nullable=False)
        category: Mapped[str] = mapped_column(String(50), nullable=False)
        full_text: Mapped[str] = mapped_column(Text, nullable=False)
        
        # Базовая статистика
        char_count: Mapped[int] = mapped_column(Integer, default=0)
        word_count: Mapped[int] = mapped_column(Integer, default=0)
        sentence_count: Mapped[int] = mapped_column(Integer, default=0)
        creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

        # Один текст - много метрик, удаление текста удаляет связанные с ним метрики
        metrics = db.relationship("Metric", back_populates="text_record", cascade="all, delete-orphan")

    class Metric(db.Model):
        """Модель метрики, хранит название и значение каждой метрики отдельно"""
        __tablename__ = "metrics"

        id: Mapped[int] = mapped_column(primary_key=True)
        text_id: Mapped[int] = mapped_column(ForeignKey("texts.id"), nullable=False)
        metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
        metric_value: Mapped[float] = mapped_column(Float, nullable=False)
        calculation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

        text_record = db.relationship("TextRecord", back_populates="metrics")

        # Один текст не может иметь две метрики с одинаковым именем
        __table_args__ = (db.UniqueConstraint('text_id', 'metric_name', name='uq_text_metric'),)
    
    return TextRecord, Metric
