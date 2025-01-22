
from evaluator import ChatbotEvaluator
from ecom_support import EcommerceSupport
import streamlit as st
from datetime import datetime
def create_streamlit_ui():
    st.title("E-commerce Customer Support")
    st.write("Welcome! How can I help you today?")
    
    # Initialize session state
    if 'support_agent' not in st.session_state:
        # Get both API keys from Streamlit secrets
        gemini_api_key = st.secrets.get("GEMINI_API_KEY", None)
        openai_api_key = st.secrets.get("OPENAI_API_KEY", None)
        
        if gemini_api_key:
            st.session_state.support_agent = EcommerceSupport(api_key=gemini_api_key, model_type="gemini")
            st.session_state.evaluator = ChatbotEvaluator() 

        elif openai_api_key:
            st.session_state.support_agent = EcommerceSupport(api_key=openai_api_key, model_type="openai")
            st.session_state.evaluator = ChatbotEvaluator() 
        else:
            st.error("Please set either GEMINI_API_KEY or OPENAI_API_KEY in your Streamlit secrets.")
            return
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Add sidebar for metrics
    with st.sidebar:
        st.header("Chatbot Performance Metrics")
        metrics = st.session_state.evaluator.get_summary_metrics()
        
        st.metric("Total Conversations", metrics['total_conversations'])
        st.metric("Average Accuracy", f"{metrics['average_accuracy']:.2%}")
        st.metric("Average Relevance", f"{metrics['average_relevance']:.2%}")
        st.metric("Avg Response Time", f"{metrics['average_response_time']:.2f}s")

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        start_time = datetime.now()
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response from support agent
        response = st.session_state.support_agent.process_message(prompt)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Evaluate response
        evaluation = st.session_state.evaluator.evaluate_response(prompt, response, response_time)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update chat display
        st.rerun()

if __name__ == "__main__":
    create_streamlit_ui()