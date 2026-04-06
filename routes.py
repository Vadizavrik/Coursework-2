# Маршруты Flask-приложения для анализа татарских текстов
from flask import render_template, request, redirect, url_for, flash
from text import Text

# Ключи базовой статистики (не сохраняются как отдельные метрики)
STATS_KEYS = ['word_count', 'sentence_count', 'unique_word_count', 
              'avg_word_length', 'long_word_count', 'avg_sentence_length', 
              'total_syllables']

def register_routes(app, db) -> None:
    """Регистрация всех маршрутов Flask с объектами app и db"""
    from models import init_models
    TextRecord, Metric = init_models(db)

    # Главная страница, отображает все тексты и сводную статистику по категориям
    @app.route('/')
    def index() -> None:
        texts = TextRecord.query.order_by(TextRecord.category, TextRecord.file_name).all()
        
        # Словарь метрик для каждого текста
        for text in texts:
            text.metrics_dict = {m.metric_name: m.metric_value for m in text.metrics}
        
        # Сводка по категориям
        summary = {}
        categories = set(t.category for t in texts)
        for cat in categories:
            cat_texts = [t for t in texts if t.category == cat]
            n = len(cat_texts)
            
            if n == 0:
                continue
            
            # 6 метрик для сводки
            metrics_to_summarize = [
                'lix', 'flesch_kincaid', 'coleman_liau',
                'ttr', 'guiraud', 'mmw'
            ]
            
            summary[cat] = {'count': n}
            
            for metric in metrics_to_summarize:
                values = []
                for t in cat_texts:
                    val = t.metrics_dict.get(metric)
                    if val is not None:
                        values.append(val)
                
                if values:
                    avg_val = sum(values) / len(values)
                    # Точность округления по метрике
                    if metric == 'ttr':
                        summary[cat][metric] = round(avg_val, 3)
                    else:
                        summary[cat][metric] = round(avg_val, 2)
                else:
                    summary[cat][metric] = 0.0
        
        return render_template('index.html', texts=texts, summary=summary)
    
    # Загрузка нового текста - валидация файла, расчёт метрик, сохранение в БД
    @app.route('/add', methods=['POST'])
    def add_text() -> None:
        file = request.files.get('file')
        category = request.form.get('category')

        # Только .txt файлы
        if not file or not file.filename.endswith('.txt'):
            flash('Ошибка: загрузите файл с расширением .txt', 'error')
            return redirect(url_for('index'))

        # Только категории simple/medium/complex
        if not category or category not in ['simple', 'medium', 'complex']:
            flash('Ошибка: выберите корректную категорию', 'error')
            return redirect(url_for('index'))

        # При ошибке - откат изменений
        try:
            content = file.read().decode('utf-8')
            filename = file.filename

            # Анализ через Text-объект
            text_obj = Text(content=content, category=category, title=filename)
            metrics = text_obj.calculate_all_metrics()

            # Сохранение текста в БД
            text_record = TextRecord(
                file_name=filename,
                category=category,
                full_text=content,
                char_count=len(content),
                word_count=metrics['word_count'],
                sentence_count=metrics['sentence_count']
            )
            db.session.add(text_record)
            db.session.flush()  # Получаем ID для метрик

            # Сохранение 6 метрик (исключая базовую статистику)
            stats_keys = STATS_KEYS
            
            for name, value in metrics.items():
                if isinstance(value, (int, float)) and name not in stats_keys:
                    metric = Metric(text_id=text_record.id, metric_name=name, metric_value=float(value))
                    db.session.add(metric)

            db.session.commit()
            flash(f'Текст "{filename}" успешно добавлен', 'message')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при анализе: {str(e)}', 'error')

        return redirect(url_for('index'))
    
    # Пересчёт метрик для одного текста по id, удаляет старые метрики перед записью новых
    @app.route('/reanalyze/<int:text_id>')
    def reanalyze_text(text_id: int) -> None:
        text_record = TextRecord.query.get_or_404(text_id)
        try:
            # Пересоздание Text-объекта из сохранённого текста
            text_obj = Text(content=text_record.full_text, category=text_record.category, title=text_record.file_name)
            metrics = text_obj.calculate_all_metrics()

            # Обновление базовой статистики
            text_record.char_count = len(text_record.full_text)
            text_record.word_count = metrics['word_count']
            text_record.sentence_count = metrics['sentence_count']

            # Удаление старых метрик
            Metric.query.filter_by(text_id=text_id).delete()

            # Добавление новых метрик (без базовой статистики)
            stats_keys = STATS_KEYS
            
            for name, value in metrics.items():
                if isinstance(value, (int, float)) and name not in stats_keys:
                    metric = Metric(text_id=text_id, metric_name=name, metric_value=float(value))
                    db.session.add(metric)

            db.session.commit()
            flash(f'Метрики пересчитаны для "{text_record.file_name}"', 'message')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при пересчёте: {str(e)}', 'error')

        return redirect(url_for('index'))
    
    # Пересчёт всех текстов в базе для обновления при изменении алгоритма
    @app.route('/reanalyze_all')
    def reanalyze_all_texts() -> None:
        try:
            texts = TextRecord.query.all()
            count = 0
            
            for text_record in texts:
                # Пересоздание Text-объекта из сохранённого текста
                text_obj = Text(
                    content=text_record.full_text,
                    category=text_record.category,
                    title=text_record.file_name
                )
                metrics = text_obj.calculate_all_metrics()

                # Обновление базовой статистики
                text_record.char_count = len(text_record.full_text)
                text_record.word_count = metrics['word_count']
                text_record.sentence_count = metrics['sentence_count']

                # Удаление старых метрик
                Metric.query.filter_by(text_id=text_record.id).delete()

                # Добавление новых метрик (без базовой статистики)
                stats_keys = STATS_KEYS
                
                for name, value in metrics.items():
                    if isinstance(value, (int, float)) and name not in stats_keys:
                        metric = Metric(
                            text_id=text_record.id,
                            metric_name=name,
                            metric_value=float(value)
                        )
                        db.session.add(metric)
                
                count += 1

            db.session.commit()
            flash(f'Метрики пересчитаны для {count} текстов', 'message')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при пересчёте: {str(e)}', 'error')

        return redirect(url_for('index'))
    
    # Удаление текста и всех связанных метрик
    @app.route('/delete/<int:text_id>')
    def delete_text(text_id: int) -> None:
        text_record = TextRecord.query.get_or_404(text_id)
        db.session.delete(text_record)
        db.session.commit()
        flash('Текст удалён', 'message')
        return redirect(url_for('index'))
