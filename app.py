import streamlit as st
import pandas as pd
from agent.planner import route_query
from agent.reporting import generate_pdf_report

# --- Page Configuration ---
st.set_page_config(
    page_title="CFO Copilot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Styling ---
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 12px;
        background-color: #f8f9fa;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    /* More specific selector to ensure text inside the chat message is dark */
    div[data-testid="stChatMessageContent"] {
        color: #333 !important;
    }
    .st-emotion-cache-1c7y2kd {
        border-radius: 12px;
    }
    .st-emotion-cache-janbn0 {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# --- Application ---

st.title("🤖 CFO Copilot")
st.caption("Your AI-powered assistant for financial analysis. Ask me anything about your monthly financials.")

# --- Sample Questions ---
sample_questions = [
    "What was June 2025 revenue vs budget in USD?",
    "Show Gross Margin % trend for the last 6 months.",
    "Break down Opex by category for May 2025.",
    "What is our cash runway right now?",
]

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "content": "How can I help you analyze the latest financials?"}
    )

# --- Display chat messages from history ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "chart" in message and message["chart"] is not None:
            st.markdown(message["content"])
            st.plotly_chart(
                message["chart"], use_container_width=True, key=f"history_chart_{i}"
            )
        else:
            st.markdown(message["content"])


# --- Handle Sidebar Clicks and Chat Input ---

# Use session state to hold the prompt from a sidebar click. Initialize if not present.
if "prompt_from_sidebar" not in st.session_state:
    st.session_state.prompt_from_sidebar = None

# The user-facing chat input box at the bottom of the screen
chat_prompt = st.chat_input("Ask a finance question...")

# Sidebar with Sample Questions
with st.sidebar:
    st.header("Sample Questions")
    for q in sample_questions:
        if st.button(q, use_container_width=True, key=q):
            # When a button is clicked, store the question in session state and rerun the script
            st.session_state.prompt_from_sidebar = q
            st.rerun()
    
    st.markdown("---")

    if st.button("Export PDF Report", use_container_width=True):
        with st.spinner("Generating PDF report..."):
            st.session_state.pdf_report = generate_pdf_report()

    if "pdf_report" in st.session_state and st.session_state.pdf_report is not None:
        st.download_button(
            label="Download PDF Report",
            data=st.session_state.pdf_report,
            file_name="financial_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("---")
    st.info("This is a demo application. The data is from the provided `data.xlsx` file in the `fixtures` directory.")


# --- Main Chat Logic ---

# Determine the prompt to use. Prioritize the one from the sidebar click.
prompt = st.session_state.prompt_from_sidebar or chat_prompt

# Clear the sidebar prompt from state after using it so it doesn't re-trigger
if st.session_state.prompt_from_sidebar:
    st.session_state.prompt_from_sidebar = None

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                response = route_query(prompt)
                
                # Check if the response contains a chart
                if response.get("chart"):
                    st.markdown(response["text"])
                    st.plotly_chart(
                        response["chart"],
                        use_container_width=True,
                        key=f"live_chart_{len(st.session_state.messages)}",
                    )
                else:
                    st.markdown(response["text"])
                
                # Add assistant response to chat history
                assistant_message = {
                    "role": "assistant", 
                    "content": response["text"],
                    "chart": response.get("chart")
                }
                st.session_state.messages.append(assistant_message)

            except Exception as e:
                error_message = f"Sorry, I encountered an error: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

