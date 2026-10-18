"""Quiz logic kept out of the views so it is easy to test."""

import random
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Attempt, AttemptAnswer, Choice, Quiz


def start_attempt(user, quiz):
    """Create a new attempt with a randomized question order.

    If the user already has an unfinished attempt that is still within its
    time limit, reuse it instead of creating a new one (stops "restart until
    you get easy questions").
    """
    open_attempt = (
        Attempt.objects.filter(user=user, quiz=quiz, submitted_at__isnull=True)
        .order_by("-started_at")
        .first()
    )
    if open_attempt and open_attempt.seconds_remaining() > 0:
        return open_attempt

    question_ids = list(quiz.questions.values_list("id", flat=True))
    random.shuffle(question_ids)
    return Attempt.objects.create(
        user=user, quiz=quiz, question_order=question_ids, total=len(question_ids)
    )


def questions_for_attempt(attempt):
    """Return the attempt's questions in its stored order, each with shuffled choices.

    Seeds the shuffle with the attempt ID so a page refresh shows the same order.
    """
    questions = {q.id: q for q in attempt.quiz.questions.prefetch_related("choices")}
    rng = random.Random(attempt.pk)
    ordered = []
    for qid in attempt.question_order:
        question = questions.get(qid)
        if question is None:  # question deleted after the attempt started
            continue
        choices = list(question.choices.all())
        rng.shuffle(choices)
        ordered.append((question, choices))
    return ordered


def is_past_deadline(attempt, now=None):
    now = now or timezone.now()
    grace = timedelta(seconds=getattr(settings, "QUIZ_SUBMIT_GRACE_SECONDS", 30))
    return now > attempt.deadline + grace


@transaction.atomic
def grade_attempt(attempt, submitted_answers):
    """Grade an attempt on the server.

    submitted_answers: dict mapping question_id (int) -> choice_id (int or None).
    Choices that don't belong to the question are ignored (treated as blank),
    so a tampered form can't score points. Late submissions score zero.
    """
    attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)
    if attempt.is_submitted:
        return attempt  # already graded; ignore double submits

    now = timezone.now()
    timed_out = is_past_deadline(attempt, now)

    valid_choices = {
        c.id: c
        for c in Choice.objects.filter(question_id__in=attempt.question_order)
    }

    # Skip any question deleted after the attempt started
    live_ids = set(attempt.quiz.questions.values_list("id", flat=True))
    question_ids = [qid for qid in attempt.question_order if qid in live_ids]

    score = 0
    for qid in question_ids:
        choice = valid_choices.get(submitted_answers.get(qid))
        if choice is not None and choice.question_id != qid:
            choice = None
        correct = bool(choice and choice.is_correct and not timed_out)
        score += correct
        AttemptAnswer.objects.create(
            attempt=attempt, question_id=qid, selected_choice=choice, is_correct=correct
        )

    attempt.score = score
    attempt.total = len(question_ids)
    attempt.submitted_at = now
    attempt.timed_out = timed_out
    attempt.save()
    return attempt


# ----------------------------------------------------------------------
# Leaderboards
# ----------------------------------------------------------------------

def _graded_attempts():
    """Submitted, on-time attempts: the only ones that count for rankings."""
    return Attempt.objects.filter(submitted_at__isnull=False, timed_out=False)


def _duration_seconds(attempt):
    return int((attempt.submitted_at - attempt.started_at).total_seconds())


def best_attempts(attempts):
    """Keep each user's best attempt per quiz: highest score, then fastest."""
    best = {}
    for a in attempts:
        key = (a.user_id, a.quiz_id)
        rank_key = (-a.score, _duration_seconds(a))
        if key not in best or rank_key < best[key][0]:
            best[key] = (rank_key, a)
    return [a for _, a in best.values()]


def quiz_leaderboard(quiz, limit=10):
    attempts = best_attempts(_graded_attempts().filter(quiz=quiz).select_related("user"))
    attempts.sort(key=lambda a: (-a.score, _duration_seconds(a), a.submitted_at))
    return [
        {
            "rank": i,
            "user": a.user,
            "score": a.score,
            "total": a.total,
            "percent": a.percent,
            "seconds": _duration_seconds(a),
        }
        for i, a in enumerate(attempts[:limit], start=1)
    ]


def level_leaderboard(level, limit=20):
    """Rank users across all quizzes in a level by total points from their best attempts."""
    attempts = best_attempts(
        _graded_attempts()
        .filter(quiz__level=level, quiz__is_published=True)
        .select_related("user")
    )
    totals = {}
    for a in attempts:
        row = totals.setdefault(
            a.user_id, {"user": a.user, "points": 0, "possible": 0, "quizzes": 0, "seconds": 0}
        )
        row["points"] += a.score
        row["possible"] += a.total
        row["quizzes"] += 1
        row["seconds"] += _duration_seconds(a)

    rows = list(totals.values())
    for row in rows:
        row["percent"] = round(100 * row["points"] / row["possible"]) if row["possible"] else 0
    rows.sort(key=lambda r: (-r["points"], -r["percent"], r["seconds"]))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows[:limit]


# ----------------------------------------------------------------------
# Personal stats dashboard
# ----------------------------------------------------------------------

def _average(values):
    return round(sum(values) / len(values)) if values else 0


def user_stats(user):
    attempts = list(
        Attempt.objects.filter(user=user, submitted_at__isnull=False)
        .select_related("quiz", "quiz__level", "quiz__category")
        .order_by("submitted_at")
    )
    percents = [a.percent for a in attempts]

    def group_average(key_fn, order_fn=None):
        groups = {}
        for a in attempts:
            groups.setdefault(key_fn(a), []).append(a.percent)
        rows = [
            {"name": str(k), "key": k, "average": _average(v), "attempts": len(v)}
            for k, v in groups.items()
        ]
        rows.sort(key=order_fn or (lambda r: -r["average"]))
        return rows

    by_subject = group_average(lambda a: a.quiz.category)
    by_level = group_average(lambda a: a.quiz.level, order_fn=lambda r: r["key"].order)

    weakest = min(by_subject, key=lambda r: r["average"]) if len(by_subject) > 1 else None
    suggestion = None
    if weakest:
        tried = {a.quiz_id for a in attempts}
        candidates = Quiz.objects.filter(
            is_published=True, category=weakest["key"]
        ).exclude(id__in=tried).select_related("level")
        favourite_level = max(by_level, key=lambda r: r["attempts"])["key"]
        suggestion = (
            candidates.filter(level=favourite_level).first() or candidates.first()
        )

    return {
        "attempt_count": len(attempts),
        "quiz_count": len({a.quiz_id for a in attempts}),
        "average": _average(percents),
        "best": max(percents) if percents else 0,
        "by_subject": by_subject,
        "by_level": by_level,
        "recent": attempts[-15:],
        "weakest": weakest,
        "suggestion": suggestion,
    }


def progress_chart(attempts, width=640, height=200, pad=24, left=48):
    """Pre-compute SVG coordinates for a simple score-over-time line chart."""
    if not attempts:
        return None
    inner_w, inner_h = width - left - pad, height - pad * 2
    step = inner_w / max(1, len(attempts) - 1)
    points = []
    for i, a in enumerate(attempts):
        x = left + (i * step if len(attempts) > 1 else inner_w / 2)
        y = pad + inner_h * (1 - a.percent / 100)
        points.append({"x": round(x, 1), "y": round(y, 1), "attempt": a})
    gridlines = [
        {"y": round(pad + inner_h * (1 - v / 100), 1), "label": v} for v in (0, 50, 100)
    ]
    return {
        "width": width,
        "height": height,
        "left": left,
        "label_x": left - 8,
        "right": width - pad,
        "points": points,
        "polyline": " ".join(f"{p['x']},{p['y']}" for p in points),
        "gridlines": gridlines,
    }
