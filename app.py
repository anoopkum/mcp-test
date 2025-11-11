import streamlit as st
from openai import AzureOpenAI
import pandas as pd
import json

# Azure OpenAI configuration
endpoint = "https://azureai-rxt.cognitiveservices.azure.com/"
model_name = "gpt-4o"
deployment = "gpt-4o"
subscription_key = "2csrPYOUz5XLOeTArCS8OPcSOIDgdWOpoov0bYvSYSeiKtuol2AmJQQJ99BDACHYHv6XJ3w3AAAAACOG8eg9"
api_version = "2024-12-01-preview"

# Page config
st.set_page_config(page_title="Azure OpenAI Chat", page_icon="💬", layout="wide")

# Sidebar for file uploads
with st.sidebar:
    st.header("📁 Data Sources")
    uploaded_files = st.file_uploader(
        "Upload your files",
        accept_multiple_files=True,
        type=["txt", "pdf", "csv", "json", "xlsx", "xls", "md"]
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded")
        for file in uploaded_files:
            st.write(f"- {file.name}")

st.title("💬 Azure OpenAI Chat")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_contents" not in st.session_state:
    st.session_state.file_contents = []

# Process uploaded files
if uploaded_files:
    st.session_state.file_contents = []
    for uploaded_file in uploaded_files:
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'csv':
                df = pd.read_csv(uploaded_file)
                content = f"File: {uploaded_file.name}\n\n{df.to_string()}"
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
                content = f"File: {uploaded_file.name}\n\n{df.to_string()}"
            elif file_type == 'json':
                data = json.load(uploaded_file)
                content = f"File: {uploaded_file.name}\n\n{json.dumps(data, indent=2)}"
            elif file_type == 'txt' or file_type == 'md':
                content = f"File: {uploaded_file.name}\n\n{uploaded_file.read().decode('utf-8')}"
            elif file_type == 'pdf':
                content = f"File: {uploaded_file.name}\n\n[PDF content - requires PyPDF2 library]"
            else:
                content = f"File: {uploaded_file.name}\n\n{uploaded_file.read().decode('utf-8')}"
            
            st.session_state.file_contents.append(content)
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {str(e)}")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )
        
        # Create messages for API with file context
        system_content = "You are a helpful assistant."
        if st.session_state.file_contents:
            system_content += "\n\nYou have access to the following uploaded files:\n\n"
            system_content += "\n\n---\n\n".join(st.session_state.file_contents)
        
        messages = [{"role": "system", "content": system_content}]
        messages.extend(st.session_state.messages)
        
        # Stream response
        response = client.chat.completions.create(
            stream=True,
            messages=messages,
            max_tokens=4096,
            temperature=1.0,
            top_p=1.0,
            model=deployment,
        )
        
        for update in response:
            if update.choices:
                chunk = update.choices[0].delta.content or ""
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        client.close()
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
