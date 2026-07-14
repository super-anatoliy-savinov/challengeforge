from django.contrib import admin

from .models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'game', 'difficulty', 'players', 'challenge_type', 'generated_by_ai', 'created_at')
    list_filter = ('game', 'difficulty', 'players', 'challenge_type', 'generated_by_ai', 'created_at')
    search_fields = ('title', 'game', 'story', 'main_goal')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Параметры', {
            'fields': ('game', 'difficulty', 'players', 'challenge_type', 'wishes')
        }),
        ('Результат генерации', {
            'fields': (
                'title', 'short_description', 'story', 'main_goal',
                'rules', 'forbidden', 'win_condition',
                'difficulty_rating', 'estimated_time', 'generated_by_ai',
            )
        }),
        ('Служебное', {
            'fields': ('created_at',)
        }),
    )
