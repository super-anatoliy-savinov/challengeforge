"""
ai_generator.py
================

Здесь находится ЕДИНСТВЕННАЯ функция, которая отвечает за придумывание
челленджа — generate_challenge().

Как это устроено:
-----------------
1. Функция по очереди пробует несколько бесплатных моделей на OpenRouter
   (settings.OPENROUTER_MODELS — список, а не одна модель). Если первая
   модель перегружена/недоступна — сразу пробуем следующую. Это заметно
   повышает шанс получить настоящий ИИ-ответ, а не шаблон.
2. У каждой попытки есть таймаут (settings.OPENROUTER_TIMEOUT секунд).
   Если ни одна из моделей не ответила вовремя, вернула не-JSON или
   произошла любая другая ошибка — используется встроенный офлайн-генератор
   _fallback_generate(), который собирает правдоподобный челлендж из
   шаблонов и случайных элементов. Так сайт никогда не "зависает" и всегда
   быстро отдаёт результат, даже если весь OpenRouter недоступен.

Чтобы подключить другой ИИ-провайдер позже — правьте только эту функцию,
остальной код (views.py) её не касается.

Возвращаемый словарь ВСЕГДА содержит ключи:
    title, short_description, story, main_goal,
    rules (list[str]), forbidden (list[str]),
    win_condition, difficulty_rating, estimated_time,
    generated_by_ai (bool)
"""

import json
import logging
import random

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)




DIFFICULTY_LABELS = {
    'easy': 'Лёгкая',
    'medium': 'Средняя',
    'hard': 'Сложная',
    'extreme': 'Экстремальная',
    'insane': 'Безумная',
}

PLAYERS_LABELS = {
    'solo': '1 игрок',
    'duo': '2 игрока',
    'team': 'Команда',
}

TYPE_LABELS = {
    'survival': 'Выживание',
    'exploration': 'Исследование',
    'building': 'Строительство',
    'boss': 'Босс',
    'speedrun': 'Скоростное прохождение',
    'random': 'Случайный',
}


def generate_challenge(game, difficulty, players, challenge_type, wishes):
    """Пытается сгенерировать челлендж через ИИ, перебирая несколько бесплатных
    моделей по очереди (на случай, если одна из них перегружена/не отвечает),
    а при полном провале — мгновенно откатывается на офлайн-генератор, чтобы
    пользователь никогда не ждал долго и не видел ошибку."""
    if not settings.OPENROUTER_API_KEY:
        logger.warning(
            "OPENROUTER_API_KEY не задан — генерация сразу идёт в офлайн-режим."
        )
    else:
        for model in settings.OPENROUTER_MODELS:
            try:
                return _generate_with_openrouter(
                    game,
                    difficulty,
                    players,
                    challenge_type,
                    wishes,
                    model=model,
                )
            except Exception as exc:
                # Эта модель не ответила вовремя / вернула не-JSON / упала —
                # логируем причину (видно в логах Render) и пробуем следующую
                # модель из списка, не показывая ошибку пользователю.
                logger.warning("OpenRouter модель %s не сработала: %r", model, exc)
                continue

    return _fallback_generate(game, difficulty, players, challenge_type, wishes)



def _generate_with_openrouter(game, difficulty, players, challenge_type, wishes, model):
    difficulty_ru = DIFFICULTY_LABELS.get(difficulty, difficulty)
    players_ru = PLAYERS_LABELS.get(players, players)
    type_ru = TYPE_LABELS.get(challenge_type, challenge_type)

    prompt = f"""
Ты — профессиональный геймдизайнер и автор игровых испытаний.

Твоя задача — создать максимально интересный и уникальный челлендж.

========================

ИГРА

{game}

========================

СЛОЖНОСТЬ

{difficulty_ru}

Очень внимательно соблюдай уровень сложности.

Если Легкая —
не делай жестких ограничений.

Если Средняя —
добавь несколько интересных условий.

Если Сложная —
используй реальные игровые механики.

Если Экстремальная —
комбинируй сложные правила.

Если Безумная —
создай действительно очень сложное испытание,
но оно ОБЯЗАТЕЛЬНО должно быть выполнимым.

========================

КОЛИЧЕСТВО ИГРОКОВ

{players_ru}

Если игроков несколько —
используй кооперативные механики.

========================

ТИП

{type_ru}

Очень внимательно соблюдай выбранный тип.

Если это строительство —
челлендж должен быть именно про строительство.

Если это выживание —
делай упор на выживание.

Если это босс —
главная цель должна быть победить сильного противника.

========================

ПОЖЕЛАНИЯ

{wishes if wishes else "Нет"}

Обязательно учитывай пожелания.

========================

ВАЖНО

Сначала мысленно проанализируй игру.

Используй ТОЛЬКО реальные механики игры.

Не придумывай предметы, которых нет.

Не придумывай боссов которых нет.

Не придумывай блоков которых нет.

Не придумывай режимов которых нет.

Челлендж должен выглядеть так,
словно его придумал профессиональный игрок именно этой игры.

Добавь атмосферную историю.

Название должно быть коротким и запоминающимся.

Ответ ТОЛЬКО JSON.

{{
"title":"",
"short_description":"",
"story":"",
"main_goal":"",
"rules":[],
"forbidden":[],
"win_condition":"",
"difficulty_rating":"",
"estimated_time":""
}}
"""

    client = OpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        timeout=settings.OPENROUTER_TIMEOUT,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты профессиональный геймдизайнер. "
                    "Создавай только интересные, реальные и выполнимые игровые челленджи. "
                    "Отвечай строго JSON без пояснений."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.0,
        max_tokens=900,
    )

    content = response.choices[0].message.content.strip()

    # Иногда модель оборачивает JSON в ```json ... ```
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    parsed = json.loads(content)

    parsed["generated_by_ai"] = True

    return parsed


# ==========================================================================
# Офлайн-генератор (запасной вариант, работает без интернета и мгновенно)
# ==========================================================================

_STORY_INTROS = [
    "Легенды {game} до сих пор помнят игрока, который принял этот вызов.",
    "Никто не верил, что это возможно — пока кто-то не попробовал в {game}.",
    "Это испытание родилось из спора: можно ли пройти {game} вот так?",
    "Сообщество {game} придумало этот челлендж как проверку настоящего мастерства.",
]

_GOAL_TEMPLATES = {
    'survival': "Продержаться как можно дольше, не нарушив ни одного правила ниже.",
    'exploration': "Исследовать как можно больше игрового мира, следуя условиям испытания.",
    'building': "Построить впечатляющее сооружение, соблюдая все ограничения.",
    'boss': "Победить сильнейшего противника, доступного в игре, на заданных условиях.",
    'speedrun': "Пройти ключевую цель как можно быстрее, не нарушая правил.",
    'random': "Выполнить случайный набор условий и довести испытание до конца.",
}

_DIFFICULTY_EXTRA_RULES = {
    'easy': ["Разрешено использовать любые подсказки и гайды."],
    'medium': ["Нельзя использовать гайды во время самого испытания."],
    'hard': ["Нельзя сохраняться чаще одного раза в час.", "Запрещена помощь других игроков."],
    'extreme': ["Смерть или провал условия — начинаешь испытание заново.",
                "Запрещены любые внешние подсказки."],
    'insane': ["Одна ошибка — полный рестарт всего челленджа.",
               "Запрещены паузы дольше 5 минут.",
               "Никаких гайдов, подсказок и повторных попыток внутри отдельных этапов."],
}

_FORBIDDEN_BASE = [
    "Читы и сторонние программы",
    "Дублирование багов игры",
    "Помощь других игроков без их официального участия",
]


def _fallback_generate(game, difficulty, players, challenge_type, wishes):
    """Собирает челлендж из шаблонов локально, без обращения к интернету.

    Используется, когда ИИ недоступен, отвечает слишком долго или вернул
    некорректный результат. Работает мгновенно и без ключей API.
    """
    difficulty_ru = DIFFICULTY_LABELS.get(difficulty, difficulty)
    players_ru = PLAYERS_LABELS.get(players, players)
    type_ru = TYPE_LABELS.get(challenge_type, challenge_type)

    title = f"{game}: {type_ru} на уровне «{difficulty_ru}»"
    short_description = (
        f"Испытание для игры {game} — {type_ru.lower()}, "
        f"рассчитанное на {players_ru.lower()} и сложность «{difficulty_ru}»."
    )
    story = random.choice(_STORY_INTROS).format(game=game)

    main_goal = _GOAL_TEMPLATES.get(challenge_type, _GOAL_TEMPLATES['random'])

    rules = [
        f"Играть строго в {game}, без модов, дающих преимущество.",
        f"Формат игроков: {players_ru}.",
    ]
    if players in ('duo', 'team'):
        rules.append("Все участники должны следовать одним и тем же правилам.")
    rules.extend(_DIFFICULTY_EXTRA_RULES.get(difficulty, []))
    if wishes:
        rules.append(f"Учтено пожелание: {wishes}")

    forbidden = list(_FORBIDDEN_BASE)

    win_condition = "Испытание засчитано пройденным, если цель выше достигнута без нарушения правил."

    estimated_time_map = {
        'easy': '30–60 минут',
        'medium': '1–2 часа',
        'hard': '2–4 часа',
        'extreme': '4–8 часов',
        'insane': '8+ часов (возможно, несколько сессий)',
    }

    return {
        "title": title,
        "short_description": short_description,
        "story": story,
        "main_goal": main_goal,
        "rules": rules,
        "forbidden": forbidden,
        "win_condition": win_condition,
        "difficulty_rating": difficulty_ru,
        "estimated_time": estimated_time_map.get(difficulty, '1–2 часа'),
        "generated_by_ai": False,
    }