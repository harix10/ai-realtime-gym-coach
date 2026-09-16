import streamlit as st
import os
import time
from dotenv import load_dotenv
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_default import initial_session_defaults 
from services.config.workout_config import EXERCISE_OPTIONS, METRICS_FIELDS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from services.coaching.voice_pipeline import VoicePipeline


def main():
    load_dotenv()

    st.set_page_config(
        page_icon="⚡",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        st.session_state.voice_pipeline = VoicePipeline()

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14.4 14.4 9.6 9.6"/>
                    <path d="M18.65 21.35a2 2 0 0 1-2.83 0l-7.17-7.18a2 2 0 0 1 0-2.83l.53-.53"/>
                    <path d="M21.5 18.5a2 2 0 0 1-2.83 0l-3.54-3.54a2 2 0 0 1 0-2.83l.54-.53"/>
                    <path d="M5.35 2.65a2 2 0 0 1 2.83 0l7.17 7.18a2 2 0 0 1 0 2.83l-.53.53"/>
                    <path d="M2.5 5.5a2 2 0 0 1 2.83 0l3.54 3.54a2 2 0 0 1 0 2.83l-.54.53"/>
                </svg>
                <h1 style="margin: 0; padding: 0; font-size: 1.75rem; font-weight: 700;">FormAI</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

        if st.session_state.username:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 0.95rem; margin-bottom: 1rem;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                    <span>Logged in as {st.session_state.username}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise in METRICS_FIELDS:
                st.subheader(f"{exercise} Metrics")
                for key in METRICS_FIELDS[exercise]:
                    label = key.replace('_', ' ').title()
                    value = st.session_state.get(key, "N/A")
                    unit = "°" if "angle" in key else ""
                    st.metric(label, f"{value}{unit}")

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")
 
    if st.session_state.get("audio_to_play"):
        st.session_state.audio_to_play = None

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; background: rgba(0, 210, 255, 0.1); border: 1px solid rgba(0, 210, 255, 0.3); padding: 1rem 1.5rem; border-radius: 12px; color: #e2e8f0; margin-bottom: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>
                </svg>
                <span><strong>Coach:</strong> {st.session_state.coach_feedback}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not workout_started:
        st.markdown(
            """
            <div class="premium-placeholder">
                <div style="display: flex; justify-content: center; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2"/>
                    </svg>
                    <h2 style="margin: 0;">Set your workout plan</h2>
                </div>
                <p>
                    Choose your exercise, sets, and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()

            agg_df = agg_df.sort_values(by="Date", ascending=False)

            agg_df.index += 1

            st.dataframe(agg_df, use_container_width=True, hide_index=True)

        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()
    
