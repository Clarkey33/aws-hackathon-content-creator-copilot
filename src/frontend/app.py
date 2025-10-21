import streamlit as st
import requests
import json
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Creator's Co-Pilot",
    page_icon="🤖",
    layout="centered"
)

# --- App State Management ---
# This helps keep track of the download link if the user interacts with the page.
if 'download_url' not in st.session_state:
    st.session_state.download_url = None

# --- Get the API Gateway endpoint from an environment variable ---
# App Runner will inject this value for us during deployment.
API_ENDPOINT = os.getenv("BEDROCK_AGENT_API_URL")

# --- The UI Elements ---
st.title("🤖 Creator's Co-Pilot")
st.markdown("Your autonomous AI partner for content creation. Provide a topic, and the agent will handle the rest, from research to a final, downloadable script and social media posts.")

# --- User Input Form ---
with st.form("agent_form"):
    topic = st.text_input(
        "Enter your video topic:",
        placeholder="e.g., The career of Dwight Yorke"
    )
    generate_button = st.form_submit_button("🚀 Generate Content Package")

# --- Logic Block to Call the Agent ---
if generate_button:
    # --- Input Validation ---
    if not topic:
        st.error("Please enter a video topic.")
    elif not API_ENDPOINT:
        st.error("API endpoint is not configured. This app may not be deployed correctly.")
    else:
        # Clear any previous results
        st.session_state.download_url = None
        
        # Show a spinner while the agent works
        with st.spinner("🤖 Agent is thinking... This can take several minutes. Please wait."):
            try:
                # The payload for the Bedrock Agent endpoint
                payload = {
                    "inputText": topic,
                    "sessionId": "streamlit-session-123" # A unique ID for the session
                }
                
                # Make the POST request to our deployed API
                response = requests.post(
                    API_ENDPOINT,
                    headers={'Content-Type': 'application/json'},
                    json=payload,
                    timeout=900 # 15 minute timeout for the long-running agent
                )
                response.raise_for_status()

                # The response from our api_handler is a clean JSON string
                final_output_json = response.json()
                download_url = final_output_json.get("download_url")

                if download_url:
                    st.session_state.download_url = download_url
                    st.success("✅ Success! Your content package is ready.")
                    st.balloons()
                else:
                    st.error("Agent finished but did not provide a download link.")
                    st.json(final_output_json) # Display the raw output for debugging

            except requests.exceptions.RequestException as e:
                st.error(f"A network error occurred: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# --- Display the Download Link ---
# This part is outside the 'if generate_button' block, so the link persists.
if st.session_state.download_url:
    st.markdown("---")
    st.markdown(f"### 🔗 [Click here to download your content package]({st.session_state.download_url})")