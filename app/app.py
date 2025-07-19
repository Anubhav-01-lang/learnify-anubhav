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

messages = [
    SystemMessage(content="You are a helpful assistant and an expert course designer.")
]

st.title("AI Personalized Learning Roadmap Generator")
st.write("Generate a *personalized learning roadmap* based on topic, weeks, and time availability.")

topic = st.text_input("Enter the topic you want to learn", "AI Agents")
weeks = st.number_input("How many weeks do you want to study?", min_value=1, max_value=52, value=4)
hours_per_week = st.number_input("How many hours per week can you dedicate?", min_value=1, max_value=40, value=5)

if st.button("Generate Course Plan"):
    user_prompt = f"""
    You are an expert course designer.
    Create a well structured {weeks}-week learning course for "{topic}".

    The user can dedicate {hours_per_week} hours per week.
    It should contain real content and be suitable for a beginner.
    For each week, give:
    - Key topics
    - Type of resources (videos/articles)
    - Estimated time per topic
    - Total expected hours for the week

    Don't hallucinate or provide vague suggestions.
    Provide the course in a structured format with clear headings and bullet points.
    """
    messages.append(HumanMessage(content=user_prompt))
    response = llm.invoke(messages)
    messages.append(AIMessage(content=response.content))

    st.subheader("📖 Your Personalized Learning Roadmap")
    st.write(response.content)
