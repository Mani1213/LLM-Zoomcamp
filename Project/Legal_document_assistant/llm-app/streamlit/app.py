import streamlit as st
from src.elasticSearch import getEsClient, elasticSearch
from src.llm import query, captureUserInput, generate_document_id, captureUserFeedback
from src.evaluation import evaluate
import time

def initialize_session_state():
    """Initializes session state variables."""
    session_vars = {
        'result': None,
        'docId': None,
        'userInput': "",
        'feedbackSubmitted': False
    }
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

def ask_question(esClient, userInput, indexName):
    """Handles question querying and processing."""
    ragOutputs = elasticSearch(esClient, userInput, indexName)
    context = ''.join([output['answer'] for output in ragOutputs])
    evaluateResult = evaluate(lambda q: elasticSearch(esClient, userInput, indexName))

    
    output, responseTime = query({"inputs": {"question": userInput, "context": context}})
    result = output['answer']
    docId = generate_document_id(userInput, result)


    captureUserInput(
        docId, userInput, result, output['score'], responseTime, 
        evaluateResult['hit_rate'], evaluateResult['mrr']
    )
    
    return result, docId

def display_feedback_buttons():
    """Displays feedback buttons."""
    feedback_col1, feedback_col2 = st.columns(2)
    if not st.session_state.feedbackSubmitted:
        with feedback_col1:
            if st.button('Satisfied'):
                captureUserFeedback(st.session_state.docId, st.session_state.userInput, st.session_state.result, True)
                st.session_state.feedbackSubmitted = True
        with feedback_col2:
            if st.button('Unsatisfied'):
                captureUserFeedback(st.session_state.docId, st.session_state.userInput, st.session_state.result, False)
                st.session_state.feedbackSubmitted = True

def main():
    st.set_page_config(page_title="Legal Assistant")
    st.title("Legal Document Assistant")
    
    
    initialize_session_state()

    userInput = st.text_input("Enter your question:")

    indexName = "legal-documents"
    try:
        esClient = getEsClient()
    except Exception as e:
        st.error("Elastic Search seems to be running, please refresh.")
        return

    if st.button("Ask"):
        if userInput:
            with st.spinner("Preparing the answer..."):
                try:
                    result, docId = ask_question(esClient, userInput, indexName)
                    st.session_state.result = result
                    st.session_state.docId = docId
                    st.session_state.userInput = userInput
                    st.session_state.feedbackSubmitted = False
                except Exception as e:
                    st.error("There was an issue retrieving the answer. Please try again.")
        else:
            st.warning("Please enter a question before clicking Ask.")

    
    if st.session_state.result:
        st.write(st.session_state.result)
        display_feedback_buttons()

if __name__ == "__main__":
    main()
