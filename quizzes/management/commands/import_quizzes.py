"""Import quizzes from a CSV file.

Usage:
    python manage.py import_quizzes sample_data/quizzes_example.csv
    python manage.py import_quizzes my_quizzes.csv --dry-run     # check only
    python manage.py import_quizzes my_quizzes.csv --replace     # overwrite quizzes with the same title

One row per question. Rows with the same quiz_title belong to the same quiz.

Columns:
    quiz_title, level, category, time_limit_minutes, quiz_description,
    question, choice_1, choice_2, choice_3, choice_4, correct, explanation

- level must match an existing level name or slug (e.g. "High School" or "high-school")
- category is created if it doesn't exist
- choice_3 and choice_4 are optional (at least 2 choices)
- correct is the number of the right choice (1-4)
- quiz-level columns (level, category, time, description) are read from each quiz's first row

The whole file is validated first and nothing is saved if any row has an error.
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from quizzes.models import Category, Choice, Level, Question, Quiz

REQUIRED_COLUMNS = [
    "quiz_title", "level", "category", "time_limit_minutes", "quiz_description",
    "question", "choice_1", "choice_2", "choice_3", "choice_4", "correct", "explanation",
]
MAX_CHOICE_LENGTH = Choice._meta.get_field("text").max_length
MAX_TITLE_LENGTH = Quiz._meta.get_field("title").max_length


def parse_csv(path):
    """Read and validate the file. Returns (quizzes, errors).

    quizzes: dict of title -> {"level", "category", "minutes", "description", "questions": [...]}
    errors: list of "line N: message" strings
    """
    errors = []
    quizzes = {}
    levels = list(Level.objects.all())

    def find_level(value):
        value = value.strip().lower()
        for level in levels:
            if value in (level.name.lower(), level.slug):
                return level
        return None

    with open(path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig handles Excel's BOM
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            return {}, [f"missing column(s): {', '.join(missing)}"]

        for line, row in enumerate(reader, start=2):  # line 1 is the header
            row = {k: (v or "").strip() for k, v in row.items() if k}
            if not any(row.values()):
                continue  # skip blank lines

            def err(msg):
                errors.append(f"line {line}: {msg}")

            title = row["quiz_title"]
            if not title:
                err("quiz_title is empty")
                continue
            if len(title) > MAX_TITLE_LENGTH:
                err(f"quiz_title is longer than {MAX_TITLE_LENGTH} characters")

            if title not in quizzes:
                level = find_level(row["level"])
                if level is None:
                    names = ", ".join(lv.name for lv in levels)
                    err(f"unknown level '{row['level']}' (use one of: {names})")
                if not row["category"]:
                    err("category is empty")
                try:
                    minutes = int(row["time_limit_minutes"])
                    if not 1 <= minutes <= 180:
                        raise ValueError
                except ValueError:
                    err("time_limit_minutes must be a whole number from 1 to 180")
                    minutes = 10
                quizzes[title] = {
                    "level": level,
                    "category": row["category"],
                    "minutes": minutes,
                    "description": row["quiz_description"],
                    "questions": [],
                }

            if not row["question"]:
                err("question is empty")
                continue

            choices = [row[f"choice_{i}"] for i in range(1, 5)]
            # Keep positions so 'correct' still points at the right one; drop trailing blanks
            while choices and not choices[-1]:
                choices.pop()
            if len(choices) < 2 or any(not c for c in choices):
                err("needs at least choice_1 and choice_2, with no gaps between choices")
                continue
            if len(set(c.lower() for c in choices)) != len(choices):
                err("two choices have the same text")
            for c in choices:
                if len(c) > MAX_CHOICE_LENGTH:
                    err(f"a choice is longer than {MAX_CHOICE_LENGTH} characters")

            try:
                correct = int(row["correct"])
                if not 1 <= correct <= len(choices):
                    raise ValueError
            except ValueError:
                err(f"correct must be a number from 1 to {len(choices)}")
                continue

            quizzes[title]["questions"].append(
                (row["question"], choices, correct - 1, row["explanation"])
            )

    return quizzes, errors


class Command(BaseCommand):
    help = "Import quizzes from a CSV file (one row per question)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to the CSV file")
        parser.add_argument("--dry-run", action="store_true", help="Validate only; save nothing")
        parser.add_argument(
            "--replace", action="store_true",
            help="Replace existing quizzes with the same title (deletes their past attempts)",
        )

    def handle(self, csv_path, dry_run=False, replace=False, **options):
        path = Path(csv_path)
        if not path.is_file():
            raise CommandError(f"File not found: {path}")

        quizzes, errors = parse_csv(path)

        # Duplicate check against the database
        for title in quizzes:
            slug = slugify(title)
            exists = Quiz.objects.filter(Q(slug=slug) | Q(title__iexact=title)).exists()
            if exists and not replace:
                errors.append(f"quiz '{title}' already exists (use --replace to overwrite it)")
            if not slug:
                errors.append(f"quiz title '{title}' can't be turned into a URL slug")

        if errors:
            for e in errors:
                self.stderr.write(self.style.ERROR(e))
            raise CommandError(f"{len(errors)} problem(s) found. Nothing was imported.")

        question_total = sum(len(q["questions"]) for q in quizzes.values())
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Dry run OK: {len(quizzes)} quiz(zes), {question_total} question(s). Nothing saved."
            ))
            return

        with transaction.atomic():
            for title, data in quizzes.items():
                slug = slugify(title)
                if replace:
                    Quiz.objects.filter(Q(slug=slug) | Q(title__iexact=title)).delete()
                category, _ = Category.objects.get_or_create(
                    slug=slugify(data["category"]), defaults={"name": data["category"]}
                )
                quiz = Quiz.objects.create(
                    title=title, slug=slug, description=data["description"],
                    level=data["level"], category=category, time_limit_minutes=data["minutes"],
                )
                for order, (text, choices, correct, explanation) in enumerate(data["questions"]):
                    question = Question.objects.create(
                        quiz=quiz, text=text, explanation=explanation, order=order
                    )
                    Choice.objects.bulk_create(
                        Choice(question=question, text=c, is_correct=(i == correct))
                        for i, c in enumerate(choices)
                    )
                self.stdout.write(f"  + {title} ({data['level']}, {len(data['questions'])} questions)")

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(quizzes)} quiz(zes) with {question_total} question(s)."
        ))
