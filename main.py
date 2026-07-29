import streamlit as st
from services.auth.login_wall import render_login_wall
from services.state.session_default import initial_session_defaults
import os
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font

def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered",
        )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    if not render_login_wall():
        return

    initial_session_defaults()

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("🏋️ AI Coach ")

        if st.session_state.username:
            st.caption(f"👤 Logged in as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            st.number_input("Sets", min_value=0, max_value=6, key="plan_sets", step=1)
            st.number_input("Reps per set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("") # space 

            start_session_button = st.button("Start Session", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state["workout_started"] = True
                st.rerun()
        else:
            exercise = st.session_state.get("plan_exercise")
            sets = st.session_state.get("plan_sets")
            reps = st.session_state.get("plan_reps")

            st.info(f"**{exercise}** — {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Session", key="end_session_button")

            if end_session_button:
                st.session_state["workout_started"] = False
                st.rerun()

        if workout_started:
            st.divider()

            exersice = st.session_state.get("plan_exercise")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("plan_reps")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("plan_sets")

            st.subheader("Workout Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                st.subheader("Squats Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                            st.subheader("Push-up Metrics")
                            st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                            st.metric("Body Alignment", st.session_state.body_alignment)
                            st.metric("Hip position", st.session_state.hip_status)

            elif exercise == "Biceps Curl (Dumbell)":
                            st.subheader("Curl Metrics")
                            st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                            st.metric("Shoulder Stability", st.session_state.shoulder_status)
                            st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                            st.subheader("Shoulder Press Metrics")
                            st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                            st.metric("Arm Extension", st.session_state.extension_status)
                            st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                            st.subheader("Lunge Metrics")
                            st.metric("Front Knee Angle", f"{st.session_state.elbow_angle}°")
                            st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                            st.metric("Balance Status", st.session_state.balance_status)

    st.write("Working..")

if __name__ == "__main__":
    main()