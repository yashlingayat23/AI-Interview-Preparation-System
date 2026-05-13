from datetime import datetime
import time

import pandas as pd
import streamlit as st

from feedback_engine import evaluate_answer
from question_bank import QUESTION_BANK, get_questions
from storage import initialize_storage, load_sessions, save_session


st.set_page_config(page_title="AI Interview Preparation System", layout="wide")

# Initialize session state variables
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "answered_questions" not in st.session_state:
    st.session_state.answered_questions = []
if "current_streak" not in st.session_state:
    st.session_state.current_streak = 0
if "answer_start_time" not in st.session_state:
    st.session_state.answer_start_time = None
if "session_scores" not in st.session_state:
    st.session_state.session_scores = []


def get_score_badge(score: int) -> str:
    """Return a badge/emoji based on score."""
    if score >= 85:
        return "🌟 Excellent"
    elif score >= 70:
        return "👍 Good"
    elif score >= 55:
        return "📈 Decent"
    else:
        return "💪 Keep practicing"


def render_feedback(result: dict, time_taken: int = None) -> None:
    # Main scores row
    score_col, relevance_col, structure_col, clarity_col = st.columns(4)

    overall_badge = get_score_badge(result['overall_score'])
    score_col.metric("Overall Score", f"{result['overall_score']}/100", overall_badge)
    relevance_col.metric("Relevance", f"{result['relevance_score']}/100")
    structure_col.metric("Structure", f"{result['structure_score']}/100")
    clarity_col.metric("Clarity", f"{result['clarity_score']}/100")

    # Additional scores row
    confidence_col, accuracy_col, completeness_col, specificity_col = st.columns(4)
    confidence_col.metric("Confidence", f"{result['confidence_score']}/100")
    accuracy_col.metric("Technical Accuracy", f"{result.get('technical_accuracy_score', 0)}/100")
    completeness_col.metric("Completeness", f"{result.get('completeness_score', 0)}/100")
    specificity_col.metric("Specificity", f"{result.get('specificity_score', 0)}/100")

    # Bottom row with keyword coverage and time
    filler_col, time_col = st.columns(2)
    filler_col.metric("Keyword Coverage", result["keyword_coverage_text"])
    if time_taken:
        time_col.metric("Time Taken", f"{time_taken}s")

    st.subheader("✅ Strengths")
    for item in result["strengths"]:
        st.write(f"• {item}")

    st.subheader("🎯 Areas for Improvement")
    for item in result["improvements"]:
        st.write(f"• {item}")

    st.subheader("💡 Suggested Answer Flow")
    st.write(result["suggested_flow"])

    # New section: Category-Specific Suggestions
    if result.get("category_suggestions"):
        st.subheader("🎯 Category-Specific Tips")
        for suggestion in result["category_suggestions"]:
            st.write(f"• {suggestion}")



def render_progress() -> None:
    sessions = load_sessions()
    st.subheader("📊 Progress Dashboard")

    if not sessions:
        st.info("Answer a few interview questions to start seeing progress insights.")
        return

    frame = pd.DataFrame(sessions)
    frame["created_at"] = pd.to_datetime(frame["created_at"])
    frame = frame.sort_values("created_at")

    total_attempts = len(frame)
    average_score = round(frame["overall_score"].mean(), 1)
    best_score = int(frame["overall_score"].max())
    recent_score = int(frame.iloc[-1]["overall_score"])
    
    # Calculate category-wise statistics
    category_attempts = frame.groupby("category").size()
    best_category = frame.groupby("category")["overall_score"].mean().idxmax()

    metric_a, metric_b, metric_c, metric_d, metric_e = st.columns(5)
    metric_a.metric("📝 Total Attempts", total_attempts)
    metric_b.metric("📈 Average Score", average_score)
    metric_c.metric("⭐ Best Score", best_score)
    metric_d.metric("🎯 Latest Score", recent_score)
    metric_e.metric("💪 Strong Category", best_category)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score Trend")
        score_chart = frame[["created_at", "overall_score"]].set_index("created_at")
        st.line_chart(score_chart, use_container_width=True)
    
    with col2:
        st.subheader("Performance by Category")
        category_scores = frame.groupby("category")["overall_score"].mean().sort_values(ascending=False)
        st.bar_chart(category_scores, use_container_width=True)

    st.subheader("📋 Recent Attempts")
    recent_columns = ["created_at", "role", "target_role", "category", "question", "overall_score"]
    # Only include columns that exist in the frame
    available_columns = [col for col in recent_columns if col in frame.columns]
    display_frame = frame[available_columns].sort_values("created_at", ascending=False).head(20)
    # Fill missing target_role values for backward compatibility
    if "target_role" in display_frame.columns:
        display_frame["target_role"] = display_frame["target_role"].fillna("N/A")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)
    
    # Summary statistics
    st.subheader("📌 Summary Statistics")
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    stat_col1.metric("Attempts per Category", len(category_attempts))
    stat_col2.metric("Score Improvement", f"{recent_score - average_score:+.1f}", "vs Average")
    
    # Calculate streak
    recent_high_scores = len(frame[frame["overall_score"] >= 70].tail(5))
    stat_col3.metric("Recent Wins (70+)", f"{recent_high_scores}/5")



def main() -> None:
    initialize_storage()
    st.title("🎤 AI Interview Preparation System")
    st.caption("🚀 Practice common interview questions, get instant AI feedback, and track your improvement for placements.")

    categories = list(QUESTION_BANK.keys())

    with st.sidebar:
        st.header("⚙️ Practice Setup")
        candidate_name = st.text_input("👤 Your name", "Student")
        role = st.text_input("💼 Target Role", "Software Engineer")
        category = st.selectbox("📚 Select Category", categories)
        questions = get_questions(category)
        
        # Display difficulty filter
        difficulties = list(set([q.get("difficulty", "Medium") for q in questions]))
        selected_difficulty = st.selectbox("🎯 Difficulty Level", ["All"] + sorted(difficulties))
        
        # Display target role filter
        target_roles = list(set([q.get("target_role", "General") for q in questions]))
        selected_target_role = st.selectbox("👔 Filter by Role", ["All"] + sorted(target_roles))
        
        # Filter questions by difficulty and target role
        filtered_questions = questions
        if selected_difficulty != "All":
            filtered_questions = [q for q in filtered_questions if q.get("difficulty", "Medium") == selected_difficulty]
        if selected_target_role != "All":
            filtered_questions = [q for q in filtered_questions if q.get("target_role", "General") == selected_target_role]
        
        selected_question = st.selectbox(
            "❓ Select Question",
            filtered_questions,
            index=st.session_state.current_question_index % len(filtered_questions) if len(filtered_questions) > 0 else 0,
            format_func=lambda item: f"{item['question'][:50]}... [{item.get('difficulty', 'Medium')}] - {item.get('target_role', 'General')}",
        )
        
        # Add category to selected_question for feedback engine
        selected_question = dict(selected_question)  # Create a copy
        selected_question["category"] = category
        
        # Session stats in sidebar
        st.divider()
        st.subheader("📊 Session Stats")
        col1, col2 = st.columns(2)
        col1.metric("Questions Answered", len(st.session_state.answered_questions))
        col2.metric("Current Streak 🔥", st.session_state.current_streak)
        
        if st.session_state.session_scores:
            avg_session_score = sum(st.session_state.session_scores) / len(st.session_state.session_scores)
            col1.metric("Session Avg", f"{avg_session_score:.1f}")

    practice_tab, progress_tab, tips_tab = st.tabs(["🎯 Practice", "📈 Progress", "💡 Tips"])

    with practice_tab:
        st.subheader("📝 Interview Question")
        
        # Display question with difficulty badge and target role
        difficulty = selected_question.get("difficulty", "Medium")
        target_role = selected_question.get("target_role", "General")
        difficulty_colors = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
        difficulty_badge = difficulty_colors.get(difficulty, "🟡")
        
        st.markdown(f"## {difficulty_badge} {selected_question['question']}")
        
        col_info1, col_info2 = st.columns(2)
        col_info1.info(f"Difficulty: **{difficulty}**")
        col_info2.info(f"Target Role: **{target_role}**")

        with st.expander("💬 What a strong answer should include", expanded=True):
            st.write(f"**Guidance:** {selected_question['hint']}")
            st.write("**Key Points to Cover:**")
            for keyword in selected_question["keywords"]:
                st.write(f"  ✓ {keyword}")

        answer = st.text_area(
            "✍️ Write your answer",
            height=240,
            placeholder="Type your answer here. Try using a clear structure with examples or results.",
        )

        col_analyze, col_skip, col_random = st.columns(3)
        
        with col_analyze:
            if st.button("🚀 Analyze Answer", type="primary", use_container_width=True):
                if not answer.strip():
                    st.error("❌ Please write an answer before analyzing it.")
                else:
                    # Calculate time taken
                    time_taken = None
                    if st.session_state.answer_start_time:
                        time_taken = int(time.time() - st.session_state.answer_start_time)
                    
                    result = evaluate_answer(selected_question, answer)
                    record = {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "candidate_name": candidate_name,
                        "role": role,
                        "target_role": target_role,
                        "category": category,
                        "question": selected_question["question"],
                        "answer": answer,
                        "overall_score": result["overall_score"],
                        "relevance_score": result["relevance_score"],
                        "structure_score": result["structure_score"],
                        "clarity_score": result["clarity_score"],
                        "confidence_score": result["confidence_score"],
                    }
                    save_session(record)
                    st.session_state["last_result"] = result
                    st.session_state["last_result"]["time_taken"] = time_taken
                    
                    # Update session stats
                    st.session_state.answered_questions.append(selected_question["question"])
                    st.session_state.session_scores.append(result["overall_score"])
                    
                    # Update streak
                    if result["overall_score"] >= 70:
                        st.session_state.current_streak += 1
                    else:
                        st.session_state.current_streak = 0
                    
                    st.session_state.answer_start_time = None
                    st.success("✅ Answer analyzed and saved!")
        
        with col_skip:
            if st.button("⏭️ Skip", use_container_width=True):
                st.session_state.current_question_index += 1
                st.rerun()
        
        with col_random:
            if st.button("🎲 Random", use_container_width=True):
                import random
                st.session_state.current_question_index = random.randint(0, len(questions) - 1)
                st.rerun()

        # Set start time when page loads (if not already set)
        if st.session_state.answer_start_time is None and "last_result" not in st.session_state:
            st.session_state.answer_start_time = time.time()

        if "last_result" in st.session_state and st.session_state["last_result"] is not None:
            st.divider()
            render_feedback(st.session_state["last_result"], st.session_state["last_result"].get("time_taken"))
            
            st.info("🎉 Great job! Click the button below to load the next question and continue practicing.")
            if st.button("➡️ Next Question", type="primary", use_container_width=True, key="next_button"):
                st.session_state["last_result"] = None
                st.session_state.current_question_index += 1
                st.session_state.answer_start_time = time.time()
                st.rerun()

    with progress_tab:
        render_progress()
    
    with tips_tab:
        st.subheader("🎯 Interview Tips & Best Practices")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📌 General Tips")
            st.write("""
            - **Pause and think:** Take 10-15 seconds to structure your answer
            - **STAR Method:** Use Situation, Task, Action, Result for behavioral questions
            - **Give examples:** Back up your points with real examples from your experience
            - **Ask clarifying questions:** Show you understand the problem deeply
            - **Be concise:** Aim for 1-2 minute answers
            - **Show enthusiasm:** Let your passion for the role shine through
            """)
        
        with col2:
            st.markdown("### 💡 Technical Tips")
            st.write("""
            - **Explain your approach:** Walk through your thinking process
            - **Consider tradeoffs:** Discuss pros and cons of your solution
            - **Use examples:** Provide concrete code or architecture diagrams mentally
            - **Mention edge cases:** Show comprehensive thinking
            - **Optimize:** Discuss time and space complexity
            - **Practice coding:** Actually write code, don't just talk about it
            """)
        
        st.divider()
        st.markdown("### 🚀 Do's and Don'ts")
        
        col_do, col_dont = st.columns(2)
        
        with col_do:
            st.success("""**DO:**
            - Make eye contact (or look at camera)
            - Speak clearly and confidently
            - Ask questions about the role
            - Follow up with a thank you
            - Research the company beforehand
            """)
        
        with col_dont:
            st.error("""**DON'T:**
            - Interrupt the interviewer
            - Speak too fast or too slowly
            - Use filler words (um, uh, like)
            - Criticize previous employers
            - Lie about your experience
            """)


if __name__ == "__main__":
    main()
