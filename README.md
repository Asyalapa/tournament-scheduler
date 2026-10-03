# tournament-scheduler

Веб-приложение для автоматической генерации расписания спортивных турниров.

## Демо

🔗 [tournament-scheduler-hagr.onrender.com](https://tournament-scheduler-hagr.onrender.com)

> Хостинг на бесплатном тарифе Render — первый запрос после 15 минут простоя может занять до минуты.

## Текущий статус: MVP

- Круговая система («каждый с каждым»)
- N команд, M параллельных полей
- Жёсткое правило: минимум 1 слот отдыха между играми одной команды
- Пустые слоты заполняются перерывом (rest)
- Экспорт в JSON

Усложнения:

- Олимпийская система, швейцарка, двойное выбывание
- Обеденный перерыв (в работе)
- Переход на следующий день
- Экспорт в CSV

## Стек

- Backend: Python 3.11+, Flask
- Frontend: HTML + CSS + чистый JS
- Без БД (stateless API)

## Запуск

Windows (Git Bash):

```bash
python -m venv backend/venv
source backend/venv/Scripts/activate
pip install -r backend/requirements.txt
npm install
npm start
```

Linux / macOS:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
npm install
npm start
```

## Структура

```text
tournament-scheduler/
├── backend/
│   ├── app.py
│   ├── logic/
│   │   ├── match_generator.py
│   │   ├── scheduler.py
│   │   └── validator.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```
