# tournament-scheduler

Веб-приложение для автоматической генерации расписания спортивных турниров.

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

## Структура

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