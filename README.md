# AI Interview Preparation System

A beginner-friendly Python project that helps students practice interview questions, get instant feedback on answers, and track improvement for placement preparation.

## Features

- Practice common interview questions by category
- Analyze answers with instant scoring
- Get feedback on relevance, structure, clarity, and confidence
- Track past attempts and average scores
- View progress by category over time
- Store data locally in JSON format

## Project Structure

```text
AI Interview Preparation System/
|
|-- app.py
|-- feedback_engine.py
|-- question_bank.py
|-- storage.py
|-- requirements.txt
|-- README.md
|-- .gitignore
`-- data/
    `-- interview_sessions.json
```

## Tech Stack

- Python
- Streamlit
- Pandas
- Local JSON storage

## How to Run

1. Open terminal in this folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

## How It Works

- `question_bank.py` stores interview questions and guidance points
- `feedback_engine.py` scores answers and generates suggestions
- `storage.py` saves attempts locally
- `app.py` provides the interface and progress dashboard

## Future Improvements

- Add voice input and speech analysis
- Add resume-based personalized questions
- Connect an LLM API for deeper feedback
- Add admin panel for trainers or placement cells
- Export reports to PDF
