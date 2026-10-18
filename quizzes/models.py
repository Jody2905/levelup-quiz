from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Level(models.Model):
    """An education level, e.g. Elementary School, High School, University."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Lower numbers are listed first."
    )

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("level_detail", args=[self.slug])


class Category(models.Model):
    """A subject area, e.g. Math, Science, Networking."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name="quizzes")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="quizzes"
    )
    time_limit_minutes = models.PositiveSmallIntegerField(default=10)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["level__order", "title"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return f"{self.title} ({self.level})"

    def get_absolute_url(self):
        return reverse("quiz_detail", args=[self.slug])

    @property
    def time_limit(self):
        return timedelta(minutes=self.time_limit_minutes)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(
        blank=True, help_text="Shown on the results page after submitting."
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]

    def correct_choice(self):
        return self.choices.filter(is_correct=True).first()


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Attempt(models.Model):
    """One user's run through one quiz. Graded on the server only."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    # Randomized question order for this attempt, stored as a list of question IDs
    question_order = models.JSONField(default=list)
    score = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    timed_out = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} - {self.quiz.title} - {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def is_submitted(self):
        return self.submitted_at is not None

    @property
    def deadline(self):
        return self.started_at + self.quiz.time_limit

    def seconds_remaining(self):
        return max(0, int((self.deadline - timezone.now()).total_seconds()))

    @property
    def percent(self):
        return round(100 * self.score / self.total) if self.total else 0

    def get_absolute_url(self):
        return reverse("attempt_result", args=[self.pk])


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        Attempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"], name="one_answer_per_question"
            )
        ]
