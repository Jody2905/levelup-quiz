from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .models import Attempt, Category, Level, Quiz


def published_quizzes():
    return Quiz.objects.filter(is_published=True).select_related("level", "category")


def home(request):
    """Landing page: pick your education level."""
    levels = Level.objects.annotate(
        quiz_count=Count("quizzes", filter=Q(quizzes__is_published=True))
    ).order_by("order", "name")
    return render(request, "quizzes/home.html", {"levels": levels})


def level_detail(request, slug):
    """All quizzes for one level, optionally filtered by subject."""
    level = get_object_or_404(Level, slug=slug)
    quizzes = published_quizzes().filter(level=level).annotate(
        question_count=Count("questions")
    )
    categories = Category.objects.filter(quizzes__in=quizzes).distinct()

    selected = request.GET.get("category")
    if selected:
        quizzes = quizzes.filter(category__slug=selected)

    return render(
        request,
        "quizzes/level_detail.html",
        {
            "level": level,
            "levels": Level.objects.all(),
            "quizzes": quizzes,
            "categories": categories,
            "selected_category": selected,
        },
    )


def quiz_detail(request, slug):
    quiz = get_object_or_404(published_quizzes(), slug=slug)
    past_attempts = []
    if request.user.is_authenticated:
        past_attempts = Attempt.objects.filter(
            user=request.user, quiz=quiz, submitted_at__isnull=False
        )[:5]
    return render(
        request,
        "quizzes/quiz_detail.html",
        {
            "quiz": quiz,
            "question_count": quiz.questions.count(),
            "past_attempts": past_attempts,
        },
    )


@login_required
@require_POST
def start_quiz(request, slug):
    quiz = get_object_or_404(published_quizzes(), slug=slug)
    if not quiz.questions.exists():
        messages.error(request, "This quiz has no questions yet.")
        return redirect(quiz)
    attempt = services.start_attempt(request.user, quiz)
    return redirect("take_attempt", pk=attempt.pk)


def get_own_attempt(request, pk):
    """Users can only see their own attempts (404 instead of 403 so IDs can't be probed)."""
    attempt = get_object_or_404(
        Attempt.objects.select_related("quiz", "quiz__level"), pk=pk
    )
    if attempt.user_id != request.user.id:
        raise Http404
    return attempt


@login_required
def take_attempt(request, pk):
    attempt = get_own_attempt(request, pk)
    if attempt.is_submitted:
        return redirect(attempt)

    if request.method == "POST":
        submitted = {}
        for qid in attempt.question_order:
            raw = request.POST.get(f"q{qid}")
            submitted[qid] = int(raw) if raw and raw.isdigit() else None
        attempt = services.grade_attempt(attempt, submitted)
        if attempt.timed_out:
            messages.warning(request, "Time ran out before you submitted, so this attempt scored 0.")
        return redirect(attempt)

    return render(
        request,
        "quizzes/take.html",
        {
            "attempt": attempt,
            "quiz": attempt.quiz,
            "questions": services.questions_for_attempt(attempt),
            "seconds_remaining": attempt.seconds_remaining(),
        },
    )


@login_required
def attempt_result(request, pk):
    attempt = get_own_attempt(request, pk)
    if not attempt.is_submitted:
        return redirect("take_attempt", pk=attempt.pk)

    answers = {a.question_id: a for a in attempt.answers.select_related("selected_choice")}
    review = []
    for question, choices in services.questions_for_attempt(attempt):
        answer = answers.get(question.id)
        review.append(
            {
                "question": question,
                "choices": choices,
                "selected": answer.selected_choice if answer else None,
                "is_correct": answer.is_correct if answer else False,
            }
        )
    return render(request, "quizzes/result.html", {"attempt": attempt, "review": review})


@login_required
def history(request):
    attempts = Attempt.objects.filter(
        user=request.user, submitted_at__isnull=False
    ).select_related("quiz", "quiz__level")
    return render(request, "quizzes/history.html", {"attempts": attempts})


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Pick a level to get started.")
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})
