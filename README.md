# EduGenie - Gemini Learning Assistant

EduGenie is a Node.js web version of the uploaded Streamlit Gemini Learning Assistant.

## Features

- AI Chat & Doubt Solver
- Notes Summarizer
- Exam Question Generator
- AI Quiz Hub
- Study Planner
- Progress Tracking
- Beginner / Intermediate / Advanced difficulty
- Gemini API integration
- Responsive mobile-friendly interface

## Project structure

```text
edugenie_nodejs/
├── package.json
├── .env
├── index.js
├── server.js
├── index.html
├── app.js
├── style.css
└── README.md
```

## Requirements

- Node.js 18+
- A Gemini API key

## Setup

1. Open a terminal in this project folder.
2. Install packages:

```bash
npm install
```

3. Open `.env` and replace:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

with your own Gemini API key.

Do not upload `.env` or your API key to GitHub.

4. Start the app:

```bash
npm start
```

5. Open:

```text
http://localhost:3000
```

## API routes

- `POST /api/chat`
- `POST /api/summarize`
- `POST /api/questions`
- `POST /api/quiz`
- `POST /api/study-plan`
- `GET /api/health`

## GitHub

Recommended `.gitignore`:

```text
node_modules/
.env
```

Then upload the project files to GitHub.

## Notes

The original Python version uses Streamlit and the Google GenAI Python SDK. This version replaces the Streamlit UI with HTML/CSS/JavaScript and keeps Gemini calls on the Node.js server so the API key is not exposed in browser JavaScript.
