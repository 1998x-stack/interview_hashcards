# hashcards Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Clone or download the project
git clone https://github.com/1998x-stack/hashcards.git
cd hashcards

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install hashcards
pip install -e .
```

## Create Your First Deck (2 minutes)

```bash
# 1. Create a directory for your cards
mkdir MyCards
cd MyCards

# 2. Create your first deck file
cat > Python.md << 'EOF'
Q: What is a list comprehension in Python?
A: A concise way to create lists: [x**2 for x in range(10)]

Q: What does the 'with' statement do?
A: It provides context management, automatically handling resource cleanup

C: Python uses [indentation] to define code blocks.

C: The [GIL] (Global Interpreter Lock) prevents true parallelism in CPython.
EOF
```

## Start Studying (30 seconds)

```bash
# From the directory containing your .md files
hashcards drill .
```

Open your browser to `http://localhost:8000` and start learning!

## Keyboard Shortcuts

While studying:
- **Space** - Reveal the answer
- **1** - Again (forgot it)
- **2** - Hard (difficult recall)
- **3** - Good (normal recall)
- **4** - Easy (perfect recall)

## Typical Workflow

### Daily Study Session

```bash
# 1. Navigate to your cards directory
cd ~/MyCards

# 2. (Optional) Pull latest changes if using Git
git pull

# 3. Start studying
hashcards drill .

# 4. (Optional) Commit your progress
git add .hashcards.db
git commit -m "Study session $(date +%Y-%m-%d)"
```

### Adding New Cards

```bash
# Edit any .md file with your favorite editor
vim Chemistry.md
# or
code Biology.md
# or
nano Physics.md

# The next time you run 'hashcards drill', new cards are automatically loaded
```

### Checking Progress

```bash
hashcards stats .
```

Output:
```
📊 hashcards Statistics
========================================
Total cards:      150
Due for review:   23
Reviewed today:   47

Cards by state:
  NEW         : 15
  REVIEW      : 120
  RELEARNING  : 15
```

## Directory Structure

Your cards directory will look like this:

```
MyCards/
├── .hashcards.db          # SQLite database (scheduling data)
├── Python.md              # Your card decks
├── Chemistry.md
├── Biology.md
└── Math.md
```

**Important**: 
- `.md` files = your cards (commit to Git)
- `.hashcards.db` = scheduling state (optional to commit)

## Using Git

### Initial Setup

```bash
cd MyCards
git init
git add *.md
git commit -m "Initial card collection"
```

### Share on GitHub

```bash
# Create a repo on GitHub, then:
git remote add origin https://github.com/1998x-stack/my-cards.git
git push -u origin main
```

### Sync Across Devices

```bash
# On device A: make changes and push
git add .
git commit -m "Added more chemistry cards"
git push

# On device B: pull changes
git pull
hashcards drill .  # New cards automatically loaded
```

## Card Syntax Reference

### Question-Answer

```markdown
Q: Your question here?
A: Your answer here.
```

- Can be multi-line
- Supports any text
- One Q-A pair = one card

### Cloze Deletion

```markdown
C: The [answer] is hidden in brackets.
```

- Each `[...]` creates a separate review
- Can have multiple deletions per line
- Great for definitions and fill-in-the-blanks

### Best Practices

✅ **Do:**
- Keep questions atomic (one concept per card)
- Use cloze for related facts
- Group related cards in the same deck file
- Edit cards to improve them over time

❌ **Don't:**
- Make cards too complex
- Include multiple unrelated facts in one card
- Forget to use specific, testable questions

## Troubleshooting

### "No cards due"
- You've reviewed all cards! Come back later.
- Or add new cards to your `.md` files.

### Cards not showing up
```bash
# Validate your card syntax
hashcards validate .
```

### Want to reset a card's schedule
Delete it from the database:
```bash
sqlite3 .hashcards.db "DELETE FROM schedules WHERE card_hash='<hash>';"
```

Or delete the entire database to start fresh:
```bash
rm .hashcards.db
hashcards drill .  # Will recreate
```

## Advanced: Scripted Card Generation

Create cards from a CSV file:

```python
# generate_vocab.py
import csv

with open('french_vocab.csv') as f:
    reader = csv.DictReader(f)
    with open('French.md', 'w') as out:
        for row in reader:
            out.write(f"Q: What is '{row['english']}' in French?\n")
            out.write(f"A: {row['french']}\n\n")
            
            out.write(f"Q: What is '{row['french']}' in English?\n")
            out.write(f"A: {row['english']}\n\n")
```

Run:
```bash
python generate_vocab.py
hashcards drill .
```

## Next Steps

1. **Read the full README** - Learn about design philosophy
2. **Customize FSRS parameters** - Edit scheduler.py for your learning style
3. **Build card generation scripts** - Automate repetitive card creation
4. **Share your decks** - Push to GitHub for others to learn from
5. **Integrate with your workflow** - Use Make, cron, or other tools

## Getting Help

- Check the README.md for detailed documentation
- Validate card syntax: `hashcards validate <directory>`
- Use standard Unix tools: `grep`, `wc`, `find` work on your cards
- Cards are just Markdown - debug by opening the files!

Happy learning! 🎓