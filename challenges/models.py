from django.db import models


class Challenge(models.Model):
    """Один сгенерированный челлендж, сохранённый в базе данных.

    Все текстовые поля результата (история, цель, правила и т.д.) хранятся
    отдельно, чтобы их было удобно выводить на странице результата, в истории
    и в админке, а также независимо редактировать.
    """

    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкая'),
        ('medium', 'Средняя'),
        ('hard', 'Сложная'),
        ('extreme', 'Экстремальная'),
        ('insane', 'Безумная'),
    ]

    PLAYERS_CHOICES = [
        ('solo', '1 игрок'),
        ('duo', '2 игрока'),
        ('team', 'Команда'),
    ]

    TYPE_CHOICES = [
        ('survival', 'Выживание'),
        ('exploration', 'Исследование'),
        ('building', 'Строительство'),
        ('boss', 'Босс'),
        ('speedrun', 'Скоростное прохождение'),
        ('random', 'Случайный'),
    ]

    # --- исходные параметры, выбранные пользователем ---
    game = models.CharField('Игра', max_length=100)
    difficulty = models.CharField('Сложность', max_length=20, choices=DIFFICULTY_CHOICES)
    players = models.CharField('Игроки', max_length=20, choices=PLAYERS_CHOICES)
    challenge_type = models.CharField('Тип челленджа', max_length=20, choices=TYPE_CHOICES)
    wishes = models.TextField('Дополнительные пожелания', blank=True)

    # --- результат генерации (то, что вернула generate_challenge) ---
    title = models.CharField('Название', max_length=255)
    short_description = models.TextField('Краткое описание', blank=True)
    story = models.TextField('История', blank=True)
    main_goal = models.TextField('Главная цель', blank=True)
    rules = models.TextField('Правила (каждое с новой строки)', blank=True)
    forbidden = models.TextField('Запреты (каждый с новой строки)', blank=True)
    win_condition = models.TextField('Условие победы', blank=True)
    difficulty_rating = models.CharField('Оценка сложности', max_length=100, blank=True)
    estimated_time = models.CharField('Примерное время прохождения', max_length=100, blank=True)

    generated_by_ai = models.BooleanField('Сгенерировано настоящим ИИ', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    # Ключ сессии браузера, создавшего челлендж. Нужен, чтобы у каждого
    # посетителя в истории была видна только своя история, а не чужая.
    # Пустое значение — на случай старых записей, созданных до этого поля.
    session_key = models.CharField(
        'Ключ сессии создателя',
        max_length=40,
        blank=True,
        default='',
        db_index=True,
    )

    class Meta:
        verbose_name = 'Челлендж'
        verbose_name_plural = 'Челленджи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.game})'

    def rules_list(self):
        return [line.strip() for line in self.rules.splitlines() if line.strip()]

    def forbidden_list(self):
        return [line.strip() for line in self.forbidden.splitlines() if line.strip()]
