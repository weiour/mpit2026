# Otmech.AI Frontend Light

Светлая версия фронта на React + Vite + Tailwind CSS.

## Страницы
- `/` — главная
- `/auth` — вход / регистрация
- `/create-event` — пошаговая анкета
- `/event/:eventId/chat` — чат
- `/event/:eventId/variants` — варианты
- `/event/:eventId/refine` — уточнение

## Запуск

```bash
npm install
npm run dev
```

Создай `.env` рядом с `package.json`:

```env
VITE_API_URL=http://127.0.0.1:8000
```
