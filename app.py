import streamlit as st
from agent import planner, tools
from dotenv import load_dotenv

# Load environment variables (for OpenAI API key)
load_dotenv()

st.set_page_config(page_title="CFO Copilot", layout="wide")
st.title("🤖 Mini CFO Copilot")
st.markdown("Ask me a question about your monthly financials.")

@st.cache_data
def load_data():
    """Load and cache the financial data."""
    return tools.load_and_prepare_data()

# Load the data
data = load_data()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "figure" in message and message["figure"] is not None:
            st.plotly_chart(message["figure"], use_container_width=True, key=message["figure"])


# Accept user input
if prompt := st.chat_input("What was June 2025 revenue vs budget?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call the agent to get the response
            result = planner.run_query(prompt, data)
            response_text = result.get("response")
            response_figure = result.get("figure")
            
            st.markdown(response_text)
            if response_figure:
                st.plotly_chart(response_figure, use_container_width=True)
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",

                "content": response_text,
                "figure": response_figure
            })