from django import forms

from .models import Challenge

POPULAR_GAMES = [
    'Minecraft',
    'Terraria',
    'Stardew Valley',
    'Project Zomboid',
    'Factorio',
    'Geometry Dash',
    'GTA V',
    'Roblox',
    'Brawl Stars',
    'FIFA',
    'Plants vs. Zombies',
    'Fortnite',
    'Among Us',
    'The Sims 4',
]

GAME_CHOICES = [(g, g) for g in POPULAR_GAMES] + [('other', 'Другая игра')]


class ChallengeCreateForm(forms.Form):
    game_select = forms.ChoiceField(
        label='Игра',
        choices=GAME_CHOICES,
        widget=forms.Select(attrs={'class': 'field-select', 'id': 'id_game_select'}),
    )
    game_other = forms.CharField(
        label='Другая игра',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'field-input',
            'placeholder': 'Впишите название игры...',
            'id': 'id_game_other',
        }),
    )
    difficulty = forms.ChoiceField(
        label='Сложность',
        choices=Challenge.DIFFICULTY_CHOICES,
        widget=forms.RadioSelect,
    )
    players = forms.ChoiceField(
        label='Количество игроков',
        choices=Challenge.PLAYERS_CHOICES,
        widget=forms.RadioSelect,
    )
    challenge_type = forms.ChoiceField(
        label='Тип челленджа',
        choices=Challenge.TYPE_CHOICES,
        widget=forms.RadioSelect,
    )
    wishes = forms.CharField(
        label='Дополнительные пожелания',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'field-textarea',
            'rows': 4,
            'placeholder': 'Например: хочу больше юмора, добавь редкий предмет, играю ночью...',
        }),
    )

    def get_game_name(self):
        """Возвращает финальное название игры с учётом поля 'Другая игра'."""
        selected = self.cleaned_data.get('game_select')
        if selected == 'other':
            return self.cleaned_data.get('game_other') or 'Неизвестная игра'
        return selected

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('game_select') == 'other' and not cleaned.get('game_other'):
            self.add_error('game_other', 'Укажите название игры.')
        return cleaned
