# LevelUp Quiz

An online quiz application built with Django. Learners pick their education level — **Elementary School, Middle School, High School, University, or Professional** — and take timed, auto-graded multiple-choice quizzes made for that level.

## Features

- **Level picker**: browse quizzes by education level, then filter by subject
- **User accounts**: sign up, log in, and see your full result history
- **Timed quizzes**: live countdown that auto-submits when time runs out
- **Shuffled questions and answers** on every attempt
- **Instant results** with the correct answer and an explanation for each question
- **Admin panel** for creating levels, subjects, quizzes, questions, and reviewing attempts
- **Sample content** across all five levels (math, science, Caribbean geography, networking, Security+, IT help desk)

## Security design

The quiz engine is built so a user can't cheat by inspecting or tampering with the page:

| Risk | How it's handled |
|---|---|
| Reading answers from page source | Correct answers are never sent to the browser while a quiz is being taken; grading happens only on the server |
| Submitting a forged answer ID | Each submitted choice is checked to belong to that exact question; anything else counts as blank |
| Beating the timer | The browser timer is display-only; the server checks the deadline (with a 30-second grace period) and scores late submissions as 0 |
| Resubmitting for a better score | An attempt can be graded only once (row lock + submitted check) |
| Restarting to reshuffle | An unfinished attempt within its time limit is resumed, not replaced |
| Viewing other users' results | Attempts are scoped to their owner; others get a 404, so attempt IDs can't be probed |
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

## Running tests

```bash
python manage.py test
```

Tests cover grading, tampered answers, late submissions, double submits, access control, and level ordering.

## Project structure

```
config/                 Django settings and root URLs
quizzes/
  models.py             Level, Category, Quiz, Question, Choice, Attempt, AttemptAnswer
  services.py           Quiz engine: start, shuffle, grade, deadline checks
  views.py              Pages
  admin.py              Admin panel setup
  management/commands/seed_quizzes.py   Sample data
  tests.py
templates/              HTML templates
static/css/style.css    Styling
```

## Roadmap

- [ ] Leaderboards per quiz and per level
- [ ] Stats dashboard (average score by subject, progress over time)
- [ ] Rate limiting on login and quiz starts
- [ ] Question types beyond multiple choice (true/false, multi-select)
- [ ] Import quizzes from CSV
- [ ] PostgreSQL + deployment
- [ ] GitHub Actions CI
