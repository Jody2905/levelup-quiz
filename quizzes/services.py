"""Quiz logic kept out of the views so it is easy to test."""

import random
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Attempt, AttemptAnswer, Choice


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
