"""Load sample levels, subjects, and quizzes.

Usage:  python manage.py seed_quizzes
Safe to run more than once: existing quizzes (matched by slug) are replaced.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from quizzes.models import Category, Choice, Level, Question, Quiz

from ._school_quizzes import SCHOOL_QUIZZES
from ._university_quizzes import UNIVERSITY_QUIZZES

LEVELS = [
    ("Elementary School", "Grades 1-6: building the basics."),
    ("Middle School", "Grades 7-9: stepping it up."),
    ("High School", "Grades 10-12 / CSEC level."),
    ("University", "College and degree-level topics."),
    ("Professional", "Certification prep and workplace skills."),
]

# Each question: (text, [choices], index of correct choice, explanation)
QUIZZES = [
    {
        "title": "Adding and Subtracting",
        "level": "Elementary School",
        "category": "Math",
        "minutes": 5,
        "description": "Quick practice with addition and subtraction.",
        "questions": [
            ("What is 7 + 5?", ["11", "12", "13", "14"], 1, "7 + 5 = 12."),
            ("What is 15 - 8?", ["6", "7", "8", "9"], 1, "15 - 8 = 7."),
            ("What is 9 + 9?", ["16", "17", "18", "19"], 2, "9 + 9 = 18."),
            ("What is 20 - 13?", ["7", "8", "6", "5"], 0, "20 - 13 = 7."),
            ("Sam has 4 apples and gets 6 more. How many does he have?", ["8", "9", "10", "11"], 2, "4 + 6 = 10."),
        ],
    },
    {
        "title": "Animals and Plants",
        "level": "Elementary School",
        "category": "Science",
        "minutes": 5,
        "description": "Living things around us.",
        "questions": [
            ("What do plants need to make their food?", ["Sunlight", "Sand", "Plastic", "Moonlight"], 0, "Plants use sunlight, water and air to make food (photosynthesis)."),
            ("Which animal is a mammal?", ["Shark", "Frog", "Dolphin", "Parrot"], 2, "Dolphins breathe air and feed their babies milk."),
            ("Which part of a plant is usually under the ground?", ["Leaf", "Root", "Flower", "Fruit"], 1, "Roots hold the plant and take in water."),
            ("A caterpillar turns into a…", ["Bee", "Butterfly", "Spider", "Beetle"], 1, "Caterpillars become butterflies (or moths)."),
        ],
    },
    {
        "title": "Fractions and Decimals",
        "level": "Middle School",
        "category": "Math",
        "minutes": 8,
        "description": "Convert, compare and calculate with fractions and decimals.",
        "questions": [
            ("What is 3/4 as a decimal?", ["0.34", "0.75", "0.7", "0.43"], 1, "3 ÷ 4 = 0.75."),
            ("Which is the largest?", ["2/3", "0.6", "5/8", "0.65"], 0, "2/3 ≈ 0.667, larger than 0.65, 0.625 and 0.6."),
            ("What is 1/2 + 1/3?", ["2/5", "5/6", "1/6", "2/3"], 1, "3/6 + 2/6 = 5/6."),
            ("What is 0.2 × 0.3?", ["0.6", "0.06", "0.5", "0.006"], 1, "2 × 3 = 6, with two decimal places: 0.06."),
            ("Simplify 12/18.", ["2/3", "3/4", "6/9", "4/6"], 0, "Divide top and bottom by 6."),
        ],
    },
    {
        "title": "Caribbean Geography",
        "level": "Middle School",
        "category": "Social Studies",
        "minutes": 6,
        "description": "Islands, capitals and landmarks of the Caribbean.",
        "questions": [
            ("What is the capital of St. Vincent and the Grenadines?", ["Castries", "Kingstown", "Bridgetown", "St. George's"], 1, "Kingstown is the capital of SVG."),
            ("La Soufrière volcano is found on which island?", ["St. Vincent", "Jamaica", "Antigua", "Bahamas"], 0, "La Soufrière is on St. Vincent (Guadeloupe and Montserrat have Soufrière volcanoes too)."),
            ("What is the capital of Barbados?", ["Bridgetown", "Roseau", "Basseterre", "Nassau"], 0, "Bridgetown is the capital of Barbados."),
            ("Which sea surrounds most of the Caribbean islands?", ["Red Sea", "Caribbean Sea", "Coral Sea", "Arabian Sea"], 1, "The Caribbean Sea, part of the Atlantic Ocean."),
        ],
    },
    {
        "title": "Cell Biology Basics",
        "level": "High School",
        "category": "Science",
        "minutes": 8,
        "description": "Organelles and what they do.",
        "questions": [
            ("Which organelle is known as the powerhouse of the cell?", ["Nucleus", "Ribosome", "Mitochondrion", "Golgi body"], 2, "Mitochondria release energy through respiration."),
            ("Where is genetic material stored in a eukaryotic cell?", ["Cell membrane", "Nucleus", "Vacuole", "Cytoplasm"], 1, "DNA is kept in the nucleus."),
            ("Which structure is found in plant cells but not animal cells?", ["Cell wall", "Mitochondria", "Ribosomes", "Cell membrane"], 0, "Plant cells have a cellulose cell wall."),
            ("What is the function of ribosomes?", ["Make proteins", "Store water", "Photosynthesis", "Cell division"], 0, "Ribosomes are the site of protein synthesis."),
            ("Diffusion is the movement of particles from…", ["Low to high concentration", "High to low concentration", "Only through water", "Only in plants"], 1, "Particles spread from high to low concentration."),
        ],
    },
    {
        "title": "Algebra Essentials",
        "level": "High School",
        "category": "Math",
        "minutes": 10,
        "description": "Solve equations and work with expressions.",
        "questions": [
            ("Solve: 2x + 5 = 17", ["x = 5", "x = 6", "x = 7", "x = 11"], 1, "2x = 12, so x = 6."),
            ("Expand: 3(x - 4)", ["3x - 4", "3x - 12", "x - 12", "3x + 12"], 1, "Multiply both terms by 3."),
            ("Factor: x² - 9", ["(x - 3)(x - 3)", "(x + 9)(x - 1)", "(x + 3)(x - 3)", "Cannot be factored"], 2, "Difference of two squares."),
            ("What is the gradient of y = 4x - 2?", ["-2", "2", "4", "-4"], 2, "In y = mx + c, m is the gradient."),
        ],
    },
    {
        "title": "Computer Networking Fundamentals",
        "level": "University",
        "category": "Computer Science",
        "minutes": 10,
        "description": "OSI model, IP addressing and core protocols.",
        "questions": [
            ("Which OSI layer is responsible for routing between networks?", ["Data Link", "Network", "Transport", "Session"], 1, "Layer 3 (Network) handles logical addressing and routing."),
            ("How many usable host addresses are in a /24 IPv4 subnet?", ["256", "255", "254", "252"], 2, "256 addresses minus network and broadcast = 254."),
            ("Which protocol resolves IP addresses to MAC addresses?", ["DNS", "ARP", "DHCP", "ICMP"], 1, "ARP maps IPv4 addresses to MAC addresses on a LAN."),
            ("TCP differs from UDP because TCP is…", ["Connectionless", "Faster with no overhead", "Connection-oriented and reliable", "Only used for video"], 2, "TCP uses a handshake, acknowledgments and retransmission."),
            ("Which port does HTTPS use by default?", ["80", "21", "443", "25"], 2, "HTTPS runs on TCP 443."),
        ],
    },
    {
        "title": "Data Structures",
        "level": "University",
        "category": "Computer Science",
        "minutes": 10,
        "description": "Stacks, queues, trees and Big-O.",
        "questions": [
            ("Which structure works Last In, First Out?", ["Queue", "Stack", "Linked list", "Heap"], 1, "Stacks are LIFO."),
            ("Average lookup time in a hash table is…", ["O(1)", "O(log n)", "O(n)", "O(n²)"], 0, "With a good hash function, lookups are constant time on average."),
            ("Binary search requires the data to be…", ["Sorted", "Unique", "In a linked list", "Numeric only"], 0, "It halves a sorted range each step."),
            ("Which traversal visits a binary search tree in sorted order?", ["Pre-order", "In-order", "Post-order", "Level-order"], 1, "In-order visits left, node, right."),
        ],
    },
    {
        "title": "Security+ Practice: Threats and Controls",
        "level": "Professional",
        "category": "Cybersecurity",
        "minutes": 12,
        "description": "CompTIA Security+ style questions on attacks and defenses.",
        "questions": [
            ("An email pretending to be from a bank asks you to verify your password. This is…", ["Vishing", "Phishing", "Tailgating", "Smishing"], 1, "Phishing uses email; vishing is voice and smishing is SMS."),
            ("Which control best protects against a stolen password being used?", ["Firewall", "Multifactor authentication", "Antivirus", "Encryption at rest"], 1, "MFA requires something beyond the password."),
            ("The principle of giving users only the access they need is…", ["Defense in depth", "Least privilege", "Separation of duties", "Zero day"], 1, "Least privilege limits damage from compromised accounts."),
            ("Which of these is a hashing algorithm?", ["AES", "RSA", "SHA-256", "Diffie-Hellman"], 2, "SHA-256 is a hash; AES and RSA are encryption; DH is key exchange."),
            ("What does the 'A' in the CIA triad stand for?", ["Authentication", "Authorization", "Availability", "Accounting"], 2, "Confidentiality, Integrity, Availability."),
            ("An attacker inserts ' OR 1=1 -- into a login form. This is…", ["XSS", "SQL injection", "CSRF", "Buffer overflow"], 1, "Untrusted input changes the SQL query; prevent it with parameterized queries."),
        ],
    },
    {
        "title": "IT Help Desk Essentials",
        "level": "Professional",
        "category": "IT Support",
        "minutes": 8,
        "description": "Troubleshooting and support fundamentals for help desk roles.",
        "questions": [
            ("What is the first step in the CompTIA troubleshooting methodology?", ["Implement the solution", "Identify the problem", "Document findings", "Test the theory"], 1, "Start by identifying the problem and gathering information."),
            ("A user gets a 169.254.x.x address. The most likely cause is…", ["DNS failure", "The DHCP server couldn't be reached", "Expired password", "Full hard drive"], 1, "That's an APIPA address, assigned when DHCP fails."),
            ("Which command shows the IP configuration on Windows?", ["ifconfig", "ipconfig", "netstat -r", "tracert"], 1, "ipconfig (ipconfig /all for details)."),
            ("A ticket should be escalated when…", ["The user is impatient", "It's outside your access or skill level", "It's Friday", "Never"], 1, "Escalate when the issue needs higher access or expertise."),
        ],
    },
]


class Command(BaseCommand):
    help = "Load sample levels, categories and quizzes."

    @transaction.atomic
    def handle(self, *args, **options):
        levels = {}
        for order, (name, desc) in enumerate(LEVELS, start=1):
            level, _ = Level.objects.update_or_create(
                slug=slugify(name), defaults={"name": name, "description": desc, "order": order}
            )
            levels[name] = level

        all_quizzes = QUIZZES + SCHOOL_QUIZZES + UNIVERSITY_QUIZZES
        for data in all_quizzes:
            category, _ = Category.objects.get_or_create(
                slug=slugify(data["category"]), defaults={"name": data["category"]}
            )
            slug = slugify(data["title"])
            Quiz.objects.filter(slug=slug).delete()
            quiz = Quiz.objects.create(
                title=data["title"],
                slug=slug,
                description=data["description"],
                level=levels[data["level"]],
                category=category,
                time_limit_minutes=data["minutes"],
            )
            for i, (text, choices, correct, explanation) in enumerate(data["questions"]):
                question = Question.objects.create(
                    quiz=quiz, text=text, explanation=explanation, order=i
                )
                Choice.objects.bulk_create(
                    Choice(question=question, text=c, is_correct=(j == correct))
                    for j, c in enumerate(choices)
                )

        self.stdout.write(
            self.style.SUCCESS(f"Loaded {len(LEVELS)} levels and {len(all_quizzes)} quizzes.")
        )
