import uuid

import pandas as pd
import streamlit as st

from app import GeminiLearningEngine, MissingAPIKeyError

st.set_page_config(page_title="Gemini Learning Assistant", page_icon="🎓", layout="wide")


@st.cache_resource
def get_engine(api_key=None):
    return GeminiLearningEngine(api_key=api_key)


# ---------- Sidebar ----------
st.sidebar.title("🎓 Study Dashboard")
module = st.sidebar.selectbox(
    "Choose Module",
    [
        "AI Chat & Doubt Solver",
        "Notes Summarizer",
        "Question Generator",
        "AI Quiz Hub",
        "Study Planner",
        "Progress Tracking",
    ],
)
student_level = st.sidebar.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
key_input = st.sidebar.text_input("Gemini API key (optional if set in .env)", type="password")

try:
    engine = get_engine(key_input or None)
except MissingAPIKeyError as e:
    st.error(str(e))
    st.stop()

# ---------- Session state ----------
defaults = {
    "chat_history": [],
    "completed_topics": [],
    "quiz_score": 0,
    "quiz_results": [],  # [{"topic":..., "score":..., "total":...}]
    "quiz": None,
    "quiz_topic": "",
    "quiz_id": None,
    "quiz_submitted": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def log_topic(name):
    if name not in st.session_state.completed_topics:
        st.session_state.completed_topics.append(name)


def run(fn, *args, **kwargs):
    """Call the engine and show errors nicely."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        st.error(str(e))
        return None


# ---------- Chat ----------
if module == "AI Chat & Doubt Solver":
    st.header("💬 AI Tutor & Doubt Solver")
    if st.sidebar.button("Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_input = st.chat_input("Ask a question or paste a difficult concept...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = run(
                    engine.chat_assistant,
                    st.session_state.chat_history,
                    user_input,
                    level=student_level,
                )
            if reply:
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ---------- Notes ----------
elif module == "Notes Summarizer":
    st.header("📝 Notes Summarizer")
    notes = st.text_area("Paste study material:", height=220)
    if st.button("Generate Notes"):
        if notes.strip():
            with st.spinner("Summarizing..."):
                summary = run(engine.summarize_notes, notes)
            if summary:
                st.subheader("📌 Summary")
                st.markdown(summary)
                log_topic("Notes summarized")
        else:
            st.warning("Please paste some text first.")

# ---------- Questions ----------
elif module == "Question Generator":
    st.header("❓ Exam Question Generator")
    c1, c2 = st.columns(2)
    topic = c1.text_input("Subject / Topic:")
    marks = c2.selectbox(
        "Mark weight",
        ["2-Mark (Short Answer)", "5-Mark (Analytical)", "10-Mark (Essay)"],
    )
    if st.button("Generate Questions"):
        if topic.strip():
            with st.spinner("Drafting questions..."):
                out = run(engine.generate_questions, topic, marks)
            if out:
                st.markdown(out)
                log_topic(f"Questions: {topic}")
        else:
            st.warning("Please enter a topic.")

# ---------- Quiz ----------
elif module == "AI Quiz Hub":
    st.header("🎯 AI Quiz")
    topic = st.text_input("Quiz topic:")
    if st.button("Build Quiz"):
        if topic.strip():
            with st.spinner("Building quiz..."):
                quiz = run(engine.generate_quiz, topic, student_level)
            if quiz:
                st.session_state.quiz = quiz
                st.session_state.quiz_topic = topic
                st.session_state.quiz_id = uuid.uuid4().hex
                st.session_state.quiz_submitted = False
        else:
            st.warning("Enter a topic first.")

    quiz = st.session_state.quiz
    if quiz:
        st.divider()
        st.subheader(f"Quiz: {st.session_state.quiz_topic}")
        with st.form(f"quiz_form_{st.session_state.quiz_id}"):
            answers = []
            for i, q in enumerate(quiz):
                answers.append(
                    st.radio(
                        f"Q{i + 1}. {q['question']}",
                        q["options"],
                        index=None,
                        key=f"{st.session_state.quiz_id}_{i}",
                    )
                )
            submitted = st.form_submit_button("Submit Answers")

        if submitted and not st.session_state.quiz_submitted:
            if any(a is None for a in answers):
                st.warning("Please answer every question.")
            else:
                score = sum(
                    1 for a, q in zip(answers, quiz) if q["options"].index(a) == q["answer_index"]
                )
                st.session_state.quiz_submitted = True
                st.session_state.quiz_score += score * 10
                st.session_state.quiz_results.append(
                    {"topic": st.session_state.quiz_topic, "score": score, "total": len(quiz)}
                )
                log_topic(f"Quiz: {st.session_state.quiz_topic}")
                st.session_state.last_answers = answers

        if st.session_state.quiz_submitted:
            answers = st.session_state.get("last_answers", [])
            last = st.session_state.quiz_results[-1]
            st.success(f"Score: {last['score']}/{last['total']} (+{last['score'] * 10} XP)")
            for i, (a, q) in enumerate(zip(answers, quiz)):
                correct = q["options"][q["answer_index"]]
                icon = "✅" if a == correct else "❌"
                st.markdown(f"{icon} **Q{i + 1}.** Correct answer: **{correct}**")
                if q["explanation"]:
                    st.caption(q["explanation"])

# ---------- Planner ----------
elif module == "Study Planner":
    st.header("📅 Study Schedule Builder")
    c1, c2, c3 = st.columns(3)
    subjects = c1.text_input("Subjects (comma separated):", "Math, Physics, Computer Science")
    hours = c2.number_input("Hours per day:", min_value=1, max_value=14, value=4)
    days = c3.number_input("Days until exam:", min_value=1, max_value=90, value=7)
    if st.button("Create Schedule"):
        with st.spinner("Building your plan..."):
            plan = run(engine.generate_study_plan, subjects, hours, days)
        if plan:
            st.markdown(plan)
            log_topic("Study plan created")

# ---------- Progress ----------
else:
    st.header("📈 Progress Tracking")
    c1, c2 = st.columns(2)
    c1.metric("Quiz XP", f"{st.session_state.quiz_score} XP")
    c2.metric("Activities completed", len(st.session_state.completed_topics))

    if st.session_state.quiz_results:
        st.subheader("Quiz scores")
        df = pd.DataFrame(st.session_state.quiz_results)
        df["label"] = [f"{i + 1}. {t}" for i, t in enumerate(df["topic"])]
        df["percent"] = (df["score"] / df["total"] * 100).round()
        st.bar_chart(df.set_index("label")["percent"])

    st.subheader("Milestones")
    if st.session_state.completed_topics:
        for item in st.session_state.completed_topics:
            st.markdown(f"- ✅ {item}")
    else:
        st.info("Nothing yet. Try a quiz or summarize some notes!")
