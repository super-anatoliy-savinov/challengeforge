from django.shortcuts import render, redirect, get_object_or_404

from .ai_generator import generate_challenge
from .forms import ChallengeCreateForm
from .models import Challenge


def home(request):
    """Главная страница сайта."""
    return render(request, 'challenges/home.html')


def _get_session_key(request):
    """Возвращает ключ текущей сессии браузера, создавая сессию при
    необходимости (у анонимного посетителя без cookie её сначала нет)."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def create_challenge(request):
    """Страница выбора параметров и создания челленджа.

    При GET — просто показывает форму.
    При POST — вызывает generate_challenge(), сохраняет результат в БД
    и перенаправляет на страницу результата (redirect, чтобы обновление
    страницы не создавало челлендж повторно).
    """
    if request.method == 'POST':
        form = ChallengeCreateForm(request.POST)
        if form.is_valid():
            game = form.get_game_name()
            difficulty = form.cleaned_data['difficulty']
            players = form.cleaned_data['players']
            challenge_type = form.cleaned_data['challenge_type']
            wishes = form.cleaned_data['wishes']

            # Единственное место, где вызывается генерация — легко заменить
            # на реальный/другой ИИ-провайдер внутри ai_generator.py
            result = generate_challenge(
                game=game,
                difficulty=difficulty,
                players=players,
                challenge_type=challenge_type,
                wishes=wishes,
            )

            challenge = Challenge.objects.create(
                game=game,
                difficulty=difficulty,
                players=players,
                challenge_type=challenge_type,
                wishes=wishes,
                title=result['title'],
                short_description=result['short_description'],
                story=result['story'],
                main_goal=result['main_goal'],
                rules='\n'.join(result['rules']),
                forbidden='\n'.join(result['forbidden']),
                win_condition=result['win_condition'],
                difficulty_rating=result['difficulty_rating'],
                estimated_time=result['estimated_time'],
                generated_by_ai=result['generated_by_ai'],
                session_key=_get_session_key(request),
            )

            return redirect('challenge_result', pk=challenge.pk)
    else:
        form = ChallengeCreateForm()

    return render(request, 'challenges/create.html', {
        'form': form,
        'popular_games': [c[0] for c in form.fields['game_select'].choices if c[0] != 'other'],
    })


def challenge_result(request, pk):
    """Страница результата — красивая карточка со сгенерированным челленджем."""
    challenge = get_object_or_404(Challenge, pk=pk)
    return render(request, 'challenges/result.html', {'challenge': challenge})


def challenge_history(request):
    """Список ранее созданных челленджей.

    Обычный посетитель видит только челленджи, созданные в его собственной
    браузерной сессии. Создатель сайта, вошедший в /admin под staff-аккаунтом,
    видит историю всех посетителей.
    """
    is_owner_view = request.user.is_authenticated and request.user.is_staff

    if is_owner_view:
        challenges = Challenge.objects.all()
    else:
        challenges = Challenge.objects.filter(session_key=_get_session_key(request))

    return render(request, 'challenges/history.html', {
        'challenges': challenges,
        'is_owner_view': is_owner_view,
    })


def challenge_detail(request, pk):
    """Полный просмотр одного челленджа из истории (та же карточка результата)."""
    challenge = get_object_or_404(Challenge, pk=pk)
    return render(request, 'challenges/result.html', {'challenge': challenge, 'from_history': True})
