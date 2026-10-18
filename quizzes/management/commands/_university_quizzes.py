"""Extra University-level quizzes.

Same format as QUIZZES in seed_quizzes.py:
each question is (text, [choices], index of correct choice, explanation).
"""

UNIVERSITY_QUIZZES = [
    {
        "title": "Databases and SQL",
        "level": "University",
        "category": "Computer Science",
        "minutes": 10,
        "description": "Relational design, keys, joins and transactions.",
        "questions": [
            ("Which SQL statement is used to read data from a table?", ["INSERT", "SELECT", "UPDATE", "GRANT"], 1, "SELECT retrieves rows; INSERT and UPDATE change data."),
            ("A primary key…", ["Can contain duplicate values", "Uniquely identifies each row", "Must be a text column", "Links to another database"], 1, "Primary keys are unique and not null."),
            ("Which join returns only rows with a match in both tables?", ["LEFT JOIN", "FULL OUTER JOIN", "INNER JOIN", "CROSS JOIN"], 2, "INNER JOIN keeps only matching rows."),
            ("A foreign key is a column that…", ["Stores encrypted data", "References the primary key of another table", "Is always indexed twice", "Cannot be NULL"], 1, "Foreign keys enforce relationships between tables."),
            ("The main goal of normalization is to…", ["Speed up every query", "Reduce redundancy and update anomalies", "Encrypt the database", "Add more tables for fun"], 1, "Normal forms remove duplicated data that can fall out of sync."),
            ("In ACID, the 'A' stands for…", ["Availability", "Atomicity", "Authentication", "Accuracy"], 1, "Atomicity: a transaction happens completely or not at all."),
            ("Which clause filters groups after aggregation?", ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1, "WHERE filters rows before grouping; HAVING filters groups after."),
        ],
    },
    {
        "title": "Operating Systems",
        "level": "University",
        "category": "Computer Science",
        "minutes": 10,
        "description": "Processes, threads, memory and scheduling.",
        "questions": [
            ("Which is NOT one of the four necessary conditions for deadlock?", ["Mutual exclusion", "Hold and wait", "Circular wait", "Resources can be preempted"], 3, "The condition is NO preemption; if resources can be taken away, deadlock can be broken."),
            ("Threads of the same process share…", ["Nothing", "Their stack only", "The same address space", "Separate copies of all memory"], 2, "Threads share code, data and heap but each has its own stack and registers."),
            ("Saving one process's state and loading another's is called a…", ["System call", "Context switch", "Page fault", "Interrupt vector"], 1, "Context switches let the CPU be shared between processes."),
            ("Virtual memory allows a system to…", ["Run without RAM", "Use disk space to extend apparent memory", "Skip the CPU cache", "Run only one program"], 1, "Pages not in use can live on disk and be loaded on demand."),
            ("When a system spends most of its time swapping pages instead of doing work, it is…", ["Thrashing", "Caching", "Spooling", "Polling"], 0, "Thrashing happens when the working set doesn't fit in memory."),
            ("Round Robin scheduling gives each process…", ["Priority based on size", "A fixed time quantum in turn", "The CPU until it finishes", "A random time slot"], 1, "Each process runs for a time slice, then goes to the back of the queue."),
        ],
    },
    {
        "title": "Software Engineering Principles",
        "level": "University",
        "category": "Computer Science",
        "minutes": 8,
        "description": "SDLC, Agile, testing and object-oriented design.",
        "questions": [
            ("In Scrum, a short, fixed-length period of work is called a…", ["Milestone", "Sprint", "Phase gate", "Backlog"], 1, "Sprints are usually 1-4 weeks."),
            ("Testing the smallest piece of code (like one function) in isolation is…", ["Integration testing", "Unit testing", "System testing", "Acceptance testing"], 1, "Unit tests check individual functions or methods."),
            ("Hiding an object's internal data and exposing only methods is…", ["Inheritance", "Polymorphism", "Encapsulation", "Abstraction layers"], 2, "Encapsulation protects internal state."),
            ("In the Waterfall model, which phase comes first?", ["Testing", "Deployment", "Requirements gathering", "Coding"], 2, "Waterfall moves from requirements to design, build, test and deploy."),
            ("Git is an example of a…", ["Compiler", "Version control system", "Database", "Web server"], 1, "Git tracks changes to code over time."),
            ("Running tests automatically on every push is part of…", ["Continuous Integration", "Waterfall", "Code obfuscation", "Pair programming"], 0, "CI catches broken code early."),
        ],
    },
    {
        "title": "Cybersecurity Fundamentals",
        "level": "University",
        "category": "Cybersecurity",
        "minutes": 10,
        "description": "Cryptography, attacks and defenses at degree level.",
        "questions": [
            ("Symmetric encryption uses…", ["A public and private key pair", "The same key to encrypt and decrypt", "No key at all", "Only hashing"], 1, "AES is a common symmetric cipher."),
            ("To send a confidential message with public-key cryptography, encrypt it with the…", ["Sender's private key", "Recipient's public key", "Recipient's private key", "Sender's public key"], 1, "Only the recipient's private key can decrypt it."),
            ("Adding a random salt before hashing passwords mainly defends against…", ["Phishing", "Rainbow table attacks", "DDoS attacks", "Shoulder surfing"], 1, "Salts make precomputed hash tables useless."),
            ("A denial-of-service attack targets which part of the CIA triad?", ["Confidentiality", "Integrity", "Availability", "Authentication"], 2, "DoS stops legitimate users from reaching a service."),
            ("A digital signature provides…", ["Encryption of the whole message", "Integrity and non-repudiation", "Faster network speed", "Anonymity"], 1, "It proves who signed and that the message wasn't changed."),
            ("Which defense best stops SQL injection?", ["Longer passwords", "Parameterized queries", "Disabling HTTPS", "Bigger servers"], 1, "Parameters keep user input separate from SQL code."),
        ],
    },
    {
        "title": "Calculus I",
        "level": "University",
        "category": "Math",
        "minutes": 12,
        "description": "Limits, derivatives and basic integrals.",
        "questions": [
            ("What is the derivative of x³?", ["x²", "3x²", "3x³", "x⁴/4"], 1, "Power rule: d/dx xⁿ = n·xⁿ⁻¹."),
            ("What is the derivative of sin x?", ["cos x", "-cos x", "-sin x", "tan x"], 0, "d/dx sin x = cos x."),
            ("What is ∫ 2x dx?", ["2", "x²", "x² + C", "2x² + C"], 2, "Reverse the power rule and add the constant of integration."),
            ("What is the limit of (sin x)/x as x → 0?", ["0", "1", "∞", "Does not exist"], 1, "A standard limit, provable with the squeeze theorem."),
            ("What is the derivative of eˣ?", ["x·eˣ⁻¹", "eˣ", "ln x", "1/x"], 1, "eˣ is its own derivative."),
            ("Using the chain rule, d/dx (2x + 1)² equals…", ["2(2x + 1)", "4(2x + 1)", "(2x + 1)", "4x"], 1, "2(2x + 1) × 2 = 4(2x + 1)."),
        ],
    },
    {
        "title": "Introductory Statistics",
        "level": "University",
        "category": "Math",
        "minutes": 10,
        "description": "Averages, spread, distributions and hypothesis tests.",
        "questions": [
            ("What is the mean of 2, 4, 6, 8, 10?", ["5", "6", "7", "30"], 1, "Sum 30 ÷ 5 values = 6."),
            ("What is the median of 3, 7, 9, 1, 5?", ["3", "5", "7", "25"], 1, "Sorted: 1, 3, 5, 7, 9; the middle value is 5."),
            ("Standard deviation measures…", ["The most common value", "How spread out the data is", "The middle value", "Sample size"], 1, "A larger SD means values are further from the mean."),
            ("In a normal distribution, about what share of data falls within 1 standard deviation of the mean?", ["50%", "68%", "95%", "99.7%"], 1, "The 68-95-99.7 rule."),
            ("With a significance level of 0.05, a p-value of 0.01 means you should…", ["Accept the null hypothesis", "Reject the null hypothesis", "Collect no more data", "Double the sample"], 1, "p < α, so the result is statistically significant."),
            ("A correlation coefficient of r = -0.9 shows…", ["No relationship", "A weak positive relationship", "A strong negative relationship", "Causation"], 2, "Close to -1 means strong negative; correlation never proves causation."),
        ],
    },
    {
        "title": "Principles of Economics",
        "level": "University",
        "category": "Business",
        "minutes": 8,
        "description": "Supply, demand and the Caribbean economy.",
        "questions": [
            ("According to the law of demand, when price rises, quantity demanded…", ["Rises", "Falls", "Stays the same", "Doubles"], 1, "Other things equal, higher prices reduce quantity demanded."),
            ("Opportunity cost is…", ["The price on the receipt", "The value of the next best alternative given up", "A sunk cost", "Tax paid on a purchase"], 1, "Every choice gives up something else."),
            ("GDP measures…", ["Government debt", "The total value of final goods and services produced in a country", "Only exports", "Household savings"], 1, "Gross Domestic Product."),
            ("A general rise in the price level over time is called…", ["Deflation", "Recession", "Inflation", "Devaluation"], 2, "Inflation reduces purchasing power."),
            ("Which institution is the central bank for St. Vincent and the Grenadines?", ["Bank of Jamaica", "Eastern Caribbean Central Bank", "Central Bank of Barbados", "Federal Reserve"], 1, "The ECCB serves the eight members of the Eastern Caribbean Currency Union."),
            ("A market with only one seller is a…", ["Monopoly", "Oligopoly", "Perfect competition", "Monopsony"], 0, "A monopsony has one buyer; an oligopoly has a few sellers."),
        ],
    },
]
