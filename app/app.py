import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# Load the API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI(   
    model="gpt-4o-mini",
    api_key=api_key,
    temperature=0
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="You are a helpful assistant and an expert course designer.")
    ]

if "last_course" not in st.session_state:
    st.session_state.last_course = None

st.title(" AI Course Generator")
st.write("Generate a personalized learning roadmap and refine it as needed.")

topic = st.text_input("Enter the topic you want to learn", "AI Agents")
weeks = st.number_input("How many weeks do you want to study?", min_value=1, max_value=52, value=4)
hours_per_week = st.number_input("How many hours per week can you dedicate?", min_value=1, max_value=40, value=5)

if st.button("Generate Course Plan"):
    prompt = f"""
    You are an expert course designer.
    Create a structured {weeks}-week learning roadmap for "{topic}".
    The user can dedicate {hours_per_week} hours per week.
    For each week, give:
    - Key topics
    - Type of resources (videos/articles)
    - Estimated time per topic
    - Total expected hours for the week
    At the end, give a short motivational note.
    """
    st.session_state.messages.append(HumanMessage(content=prompt))
    response = llm.invoke(st.session_state.messages)
    st.session_state.messages.append(AIMessage(content=response.content))
    st.session_state.last_course = response.content

if st.session_state.last_course:
    st.subheader(" Current Course Plan")
    st.write(st.session_state.last_course)

    refinement_input = st.text_area("Want to refine? Describe changes you want.")
    if st.button("Refine This Course"):
        refine_prompt = f"""
        Here is the previously generated course:
        {st.session_state.last_course}

        Now refine it with these changes:
        {refinement_input}

        Keep the same {weeks}-week structure and hours/week constraint.
        """
        st.session_state.messages.append(HumanMessage(content=refine_prompt))
        refine_response = llm.invoke(st.session_state.messages)
        st.session_state.messages.append(AIMessage(content=refine_response.content))
        words = refinement_input.split()
        for word in words:
            if word.isdigit():
                if words[words.index(word)-1] == "weeks":
                    weeks = int(word)
                elif words[words.index(word)-1] == "hours":
                    hours_per_week = int(word)
        st.session_state.last_course = refine_response.content
        st.rerun()

