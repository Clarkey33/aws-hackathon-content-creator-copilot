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

# --- The UI Elements ---
st.title("🤖 Creator's Co-Pilot")
st.markdown("Your autonomous AI partner for content creation. Provide a topic, and the agent will handle the rest, from research to a final, downloadable script and social media posts.")

# Get the API Gateway endpoint from an environment variable for security
# For local testing, you can paste the URL directly.
API_ENDPOINT = os.getenv("BEDROCK_AGENT_API_URL", "") 

# --- User Inputs ---
with st.form("agent_form"):
    topic = st.text_input(
        "Enter your video topic:", 
        placeholder="e.g., The career of Dwight Yorke"
    )
    
    # We will need the API endpoint to call the agent.
    # For the demo, it's okay to have the user paste it in.
    api_url = st.text_input(
        "Enter your deployed API Gateway Endpoint URL:",
        value=API_ENDPOINT,
        placeholder="https://[...].execute-api.us-east-1.amazonaws.com/Prod/..."
    )

    generate_button = st.form_submit_button("🚀 Generate Content Package")

# --- The Logic Block ---
if generate_button:
    # --- Input Validation ---
    if not topic:
        st.error("Please enter a video topic.")
    elif not api_url:
        st.error("Please enter the API Gateway Endpoint URL.")
    else:
        # --- API Call to the Bedrock Agent ---
        # Show a spinner while the agent is working (this can take minutes)
        with st.spinner("🤖 Agent is thinking... This can take a few minutes. Please wait."):
            try:
                # The payload for the Bedrock Agent endpoint
                payload = {
                    "inputText": topic,
                    "sessionId": "streamlit-session-123" # A unique ID for the session
                }
                
                # Make the POST request
                response = requests.post(
                    api_url, 
                    headers={'Content-Type': 'application/json'},
                    json=payload,
                    timeout=900 # Set a long timeout (15 minutes)
                )

                response.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)

                # --- Parsing the Response ---
                # The response from a Bedrock Agent API Gateway is a bit complex.
                # The final output is streamed and needs to be decoded.
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        # Each line might be a JSON object containing a chunk of data
                        try:
                            # This part might need adjustment based on the exact streaming format
                            # We are looking for the final chunk that contains the agent's output
                            chunk = json.loads(decoded_line)
                            if 'bytes' in chunk:
                                response_text += chunk['bytes'].decode('utf-8')
                        except json.JSONDecodeError:
                            # If a line is not JSON, it might be part of the raw response
                            response_text += decoded_line
                
                # The agent's final response should be the JSON from our 'save_package_to_file' tool
                final_output_json = json.loads(response_text)
                download_url = final_output_json.get("download_url")

                if download_url:
                    st.success("✅ Success! Your content package is ready.")
                    st.markdown(f"### [Click here to download your file]({download_url})")
                    st.balloons()
                else:
                    st.error(f"Agent finished but did not provide a download link. Final response: {response_text}")

            except requests.exceptions.RequestException as e:
                st.error(f"A network error occurred: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.info(f"Raw response content: {response.text if 'response' in locals() else 'No response'}")