from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import services
from .models import Attempt, Category, Choice, Level, Question, Quiz


def make_quiz(level_name="High School", n_questions=3, minutes=5):
    level, _ = Level.objects.get_or_create(name=level_name, slug=level_name.lower().replace(" ", "-"))
    cat, _ = Category.objects.get_or_create(name="Math", slug="math")
    quiz = Quiz.objects.create(
        title=f"Quiz {Quiz.objects.count()}", slug=f"quiz-{Quiz.objects.count()}",
        level=level, category=cat, time_limit_minutes=minutes,
    )
    for i in range(n_questions):
        q = Question.objects.create(quiz=quiz, text=f"Q{i}", order=i)
        Choice.objects.create(question=q, text="right", is_correct=True)
        Choice.objects.create(question=q, text="wrong", is_correct=False)
    return quiz


def answers(quiz, correct=True):
    return {
        q.id: q.choices.get(is_correct=correct).id for q in quiz.questions.all()
    }


class GradingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jo", password="pass12345!")
        self.quiz = make_quiz()

    def test_all_correct(self):
        attempt = services.start_attempt(self.user, self.quiz)
        attempt = services.grade_attempt(attempt, answers(self.quiz))
        self.assertEqual((attempt.score, attempt.total), (3, 3))
        self.assertEqual(attempt.percent, 100)

    def test_all_wrong_and_blank(self):
        attempt = services.start_attempt(self.user, self.quiz)
        submitted = answers(self.quiz, correct=False)
        first = next(iter(submitted))
        submitted[first] = None
        attempt = services.grade_attempt(attempt, submitted)
        self.assertEqual(attempt.score, 0)

    def test_choice_from_another_question_is_ignored(self):
        """A tampered form can't use question B's correct choice to answer question A."""
        attempt = services.start_attempt(self.user, self.quiz)
        q1, q2, q3 = self.quiz.questions.all()
        tampered = {q1.id: q2.correct_choice().id, q2.id: None, q3.id: None}
        attempt = services.grade_attempt(attempt, tampered)
        self.assertEqual(attempt.score, 0)

    def test_choice_from_another_quiz_is_ignored(self):
        other = make_quiz()
        attempt = services.start_attempt(self.user, self.quiz)
        q1 = self.quiz.questions.first()
        attempt = services.grade_attempt(attempt, {q1.id: other.questions.first().correct_choice().id})
        self.assertEqual(attempt.score, 0)

    def test_double_submit_does_not_regrade(self):
        attempt = services.start_attempt(self.user, self.quiz)
        services.grade_attempt(attempt, answers(self.quiz, correct=False))
        attempt = services.grade_attempt(attempt, answers(self.quiz))
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.answers.count(), 3)

    def test_late_submission_scores_zero(self):
        attempt = services.start_attempt(self.user, self.quiz)
        attempt.started_at = timezone.now() - timedelta(minutes=10)
        attempt.save()
        attempt = services.grade_attempt(attempt, answers(self.quiz))
        self.assertTrue(attempt.timed_out)
        self.assertEqual(attempt.score, 0)

    def test_open_attempt_is_reused(self):
        a1 = services.start_attempt(self.user, self.quiz)
        a2 = services.start_attempt(self.user, self.quiz)
        self.assertEqual(a1.pk, a2.pk)

    def test_expired_open_attempt_is_not_reused(self):
        a1 = services.start_attempt(self.user, self.quiz)
        a1.started_at = timezone.now() - timedelta(minutes=10)
        a1.save()
        a2 = services.start_attempt(self.user, self.quiz)
        self.assertNotEqual(a1.pk, a2.pk)

    def test_question_order_is_stored(self):
        attempt = services.start_attempt(self.user, self.quiz)
        self.assertCountEqual(attempt.question_order, list(self.quiz.questions.values_list("id", flat=True)))


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jo", password="pass12345!")
        self.other = User.objects.create_user("sam", password="pass12345!")
        self.quiz = make_quiz("University")
        make_quiz("Elementary School")

    def test_home_lists_levels(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, "University")
        self.assertContains(r, "Elementary School")

    def test_level_page_only_shows_that_level(self):
        r = self.client.get(reverse("level_detail", args=["university"]))
        self.assertContains(r, self.quiz.title)
        self.assertEqual(len(r.context["quizzes"]), 1)

    def test_unpublished_quiz_hidden(self):
        self.quiz.is_published = False
        self.quiz.save()
        r = self.client.get(reverse("quiz_detail", args=[self.quiz.slug]))
        self.assertEqual(r.status_code, 404)

    def test_start_requires_login(self):
        r = self.client.post(reverse("start_quiz", args=[self.quiz.slug]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

    def test_take_page_does_not_leak_answers(self):
        self.client.login(username="jo", password="pass12345!")
        r = self.client.post(reverse("start_quiz", args=[self.quiz.slug]), follow=True)
        html = r.content.decode()
        self.assertNotIn("is_correct", html)
        self.assertNotIn("correct", html.lower().replace("incorrect", ""))

    def test_full_flow(self):
        self.client.login(username="jo", password="pass12345!")
        r = self.client.post(reverse("start_quiz", args=[self.quiz.slug]))
        attempt = Attempt.objects.get(user=self.user)
        self.assertRedirects(r, reverse("take_attempt", args=[attempt.pk]))
        form = {f"q{qid}": str(cid) for qid, cid in answers(self.quiz).items()}
        r = self.client.post(reverse("take_attempt", args=[attempt.pk]), form, follow=True)
        self.assertContains(r, "100%")

    def test_cannot_view_another_users_attempt(self):
        attempt = services.start_attempt(self.other, self.quiz)
        self.client.login(username="jo", password="pass12345!")
        self.assertEqual(self.client.get(reverse("take_attempt", args=[attempt.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("attempt_result", args=[attempt.pk])).status_code, 404)

    def test_signup_logs_in(self):
        r = self.client.post(reverse("signup"), {
            "username": "newbie", "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123",
        })
        self.assertRedirects(r, reverse("home"))
        self.assertTrue(User.objects.filter(username="newbie").exists())


class LevelOrderTests(TestCase):
    def test_home_lists_levels_in_learning_order(self):
        call_command("seed_quizzes", stdout=open("/dev/null", "w"))
        r = self.client.get(reverse("home"))
        names = [lvl.name for lvl in r.context["levels"]]
        self.assertEqual(names, ["Elementary School", "Middle School", "High School", "University", "Professional"])


class SeedTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_quizzes", stdout=open("/dev/null", "w"))
        call_command("seed_quizzes", stdout=open("/dev/null", "w"))
        self.assertEqual(Level.objects.count(), 5)
        for quiz in Quiz.objects.all():
            for q in quiz.questions.all():
                self.assertEqual(q.choices.filter(is_correct=True).count(), 1, q.text)
