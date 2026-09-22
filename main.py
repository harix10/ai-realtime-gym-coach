import streamlit as st
import os
import time
import base64
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
from twilio.rest import Client
import os


def main():
    load_dotenv()

    st.set_page_config(
        page_icon="🏋️",
        page_title="FormAI",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    st.markdown("<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>", unsafe_allow_html=True)
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
                <svg width="28" height="28" viewBox="0 0 640 512" fill="#00d2ff"><path d="M96 64c0-17.7 14.3-32 32-32l32 0c17.7 0 32 14.3 32 32l0 160 0 64 0 160c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-64-32 0c-17.7 0-32-14.3-32-32l0-64c-17.7 0-32-14.3-32-32s14.3-32 32-32l0-64c0-17.7 14.3-32 32-32l32 0 0-64zm448 0l0 64 32 0c17.7 0 32 14.3 32 32l0 64c17.7 0 32 14.3 32 32s-14.3 32-32 32l0 64c0 17.7-14.3 32-32 32l-32 0 0 64c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-160 0-64 0-160c0-17.7 14.3-32 32-32l32 0c17.7 0 32 14.3 32 32zM416 224l0 64-192 0 0-64 192 0z"/></svg>
                <h1 style="margin: 0; padding: 0; font-size: 1.75rem; font-weight: 700;">FormAI</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

        if st.session_state.username:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 0.95rem; margin-bottom: 0.5rem;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                    <span>Logged in as {st.session_state.username}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Logout", key="logout_btn", help="Click to log out of your session"):
                st.session_state.clear()
                st.rerun()

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

    username = st.session_state.username if st.session_state.username else "User"
    st.markdown(f"<h1 style='margin-bottom: 0.2rem; font-size: 2.2rem;'>Welcome, {username}! Prepare your session with FormAI.</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #94a3b8; font-weight: 400; margin-top: 0; font-size: 1.2rem;'>Set Your Workout Plan in the Sidebar</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
 
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
        try:
            with open(os.path.join(os.getcwd(), "static", "squat_wireframe.jpg"), "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode()
            img_src = f"data:image/jpeg;base64,{img_b64}"
        except FileNotFoundError:
            img_src = ""

        st.markdown(
            f"""
            <div class="premium-placeholder" style="display: flex; flex-direction: row; align-items: center; gap: 32px; padding: 24px; background: rgba(15, 23, 42, 0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; text-align: left;">
                <img src="{img_src}" style="width: 180px; height: 180px; border-radius: 12px; object-fit: contain; background: transparent;" />
                <div>
                    <h2 style="margin: 0 0 12px 0; font-size: 1.8rem; color: #e2e8f0; font-weight: 600;">Ready to Train?</h2>
                    <p style="margin: 0; color: #94a3b8; font-size: 1.05rem; line-height: 1.6;">
                        Choose your exercise and set details on the left. Click <strong>Start</strong> when<br>
                        you are ready to receive real-time FormAI coaching.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Get ICE servers (STUN/TURN)
        def get_ice_servers():
            try:
                account_sid = os.environ.get("TWILIO_ACCOUNT_SID") or st.secrets.get("TWILIO_ACCOUNT_SID")
                auth_token = os.environ.get("TWILIO_AUTH_TOKEN") or st.secrets.get("TWILIO_AUTH_TOKEN")
                if account_sid and auth_token:
                    client = Client(account_sid, auth_token)
                    token = client.tokens.create()
                    return token.ice_servers
            except Exception:
                pass
            return [{"urls": ["stun:stun.l.google.com:19302"]}]

        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": get_ice_servers()},
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
    
