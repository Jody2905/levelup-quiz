# LevelUp Quiz

![Tests](https://github.com/Jody2905/levelup-quiz/actions/workflows/tests.yml/badge.svg)

An online quiz application built with Django. Learners pick their education level — **Elementary School, Middle School, High School, University, or Professional** — and take timed, auto-graded multiple-choice quizzes made for that level.

## Features

- **Level picker**: browse quizzes by education level, then filter by subject
- **User accounts**: sign up, log in, and see your full result history
- **Timed quizzes**: live countdown that auto-submits when time runs out
- **Shuffled questions and answers** on every attempt
- **Instant results** with the correct answer and an explanation for each question
- **Leaderboards** per level and per quiz, ranked by best score with time as the tie-breaker
- **Personal stats dashboard**: average by subject and level, score-over-time chart, and a practice suggestion for your weakest subject
- **Admin panel** for creating levels, subjects, quizzes, questions, and reviewing attempts
- **CSV import** so teachers can write quizzes in Excel or Google Sheets and load them in one command
- **Rate limiting** on login, sign-up and quiz starts
- **34 sample quizzes** across all five levels: math, English, science, Caribbean history and geography, computer basics, CSEC IT, databases, operating systems, calculus, statistics, economics, Security+, IT help desk

## Security design

The quiz engine is built so a user can't cheat by inspecting or tampering with the page:

| Risk | How it's handled |
|---|---|
| Reading answers from page source | Correct answers are never sent to the browser while a quiz is being taken; grading happens only on the server |
| Submitting a forged answer ID | Each submitted choice is checked to belong to that exact question; anything else counts as blank |
| Beating the timer | The browser timer is display-only; the server checks the deadline (with a 30-second grace period) and scores late submissions as 0 |
| Resubmitting for a better score | An attempt can be graded only once (row lock + submitted check) |
| Restarting to reshuffle | An unfinished attempt within its time limit is resumed, not replaced |
| Gaming the leaderboard | Only on-time attempts count, and only each player's best attempt per quiz |
| Viewing other users' results | Attempts are scoped to their owner; others get a 404, so attempt IDs can't be probed |
| Password guessing | An account locks for 15 minutes after 5 failed logins; one IP address is blocked after 20 failures across any accounts |
| Mass account creation / spam | Sign-ups are limited to 5 per hour per IP address; quiz starts to 10 per minute per user |
| Password storage, CSRF | Django's built-in password hashing and CSRF protection; logout is POST-only |

## Tech stack

Python 3, Django 6, SQLite (works with PostgreSQL by changing `DATABASES`), plain HTML/CSS/JS.

## Getting started

```bash
git clone https://github.com/Jody2905/levelup-quiz.git
cd levelup-quiz
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_quizzes    # loads levels and sample quizzes
python manage.py createsuperuser # for the admin panel
python manage.py runserver
```

Open http://127.0.0.1:8000 for the app and http://127.0.0.1:8000/admin for the admin panel.

## Importing quizzes from CSV

Write one row per question in a spreadsheet, save it as CSV, then run:

```bash
python manage.py import_quizzes my_quizzes.csv --dry-run   # check for mistakes, save nothing
python manage.py import_quizzes my_quizzes.csv             # import
python manage.py import_quizzes my_quizzes.csv --replace   # overwrite quizzes with the same title
```

| Column | What to put |
|---|---|
| `quiz_title` | Rows with the same title become one quiz |
| `level` | An existing level, e.g. `High School` or `high-school` |
| `category` | Subject; created if it doesn't exist |
| `time_limit_minutes` | 1 to 180 |
| `quiz_description` | Short description |
| `question` | The question text |
| `choice_1` … `choice_4` | At least two choices; 3 and 4 can be blank (true/false questions) |
| `correct` | Number of the right choice (1-4) |
| `explanation` | Shown on the results page |

The whole file is checked first, with line numbers for every problem, and nothing is saved unless every row is valid. See [`sample_data/quizzes_example.csv`](sample_data/quizzes_example.csv).

## Running tests

```bash
python manage.py test
```

Tests cover grading, tampered answers, late submissions, double submits, access control, level ordering, leaderboard ranking, dashboard stats, rate limiting and CSV import.

GitHub Actions runs the full test suite on Python 3.12 and 3.13 on every push, along with migration and system checks.

## Project structure

```
config/                 Django settings and root URLs
quizzes/
  models.py             Level, Category, Quiz, Question, Choice, Attempt, AttemptAnswer
  services.py           Quiz engine: start, shuffle, grade, deadline checks, leaderboards, stats
  ratelimit.py          Cache-based rate limiter
  auth_views.py         Login view with lockout
  views.py              Pages
  templatetags/         Template helpers (m:ss time format)
  admin.py              Admin panel setup
  management/commands/  seed_quizzes (sample data), import_quizzes (CSV import)
  tests.py
templates/              HTML templates
static/css/style.css    Styling
sample_data/            Example CSV for import_quizzes
.github/workflows/      CI: tests on every push
```

## Roadmap

- [x] Leaderboards per quiz and per level
- [x] Stats dashboard (average score by subject, progress over time)
- [x] Rate limiting on login, sign-up and quiz starts
- [x] Import quizzes from CSV
- [x] GitHub Actions CI
- [ ] Multi-select questions
- [ ] Password reset by email
- [ ] PostgreSQL + deployment
