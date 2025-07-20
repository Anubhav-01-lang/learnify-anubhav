import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

# load API keys from environment
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# initialize API clients
youtube = build("youtube", "v3", developerKey=youtube_api_key)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=openai_api_key,
    temperature=0.3
)

# session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="You are an AI educator who creates detailed, structured lessons with exercises and sensible video suggestions.")
    ]
if "weekly_plan" not in st.session_state:
    st.session_state.weekly_plan = None
if "shown_videos" not in st.session_state:
    st.session_state.shown_videos = set()

# streamlit UI
st.title("📚 AI Course Builder with Text + Sensible YouTube Videos")
st.write("Creates a **structured course** with detailed text, exercises, and only relevant embedded videos.")

topic = st.text_input("📌 Enter the topic you want to learn", "AI Agents")
weeks = st.number_input("📆 How many weeks do you want to study?", min_value=1, max_value=12, value=4)
hours_per_week = st.number_input("⏳ How many hours per week?", min_value=1, max_value=40, value=5)

# fetch relevant Medium articles
def scrape_medium_articles(query, max_articles=5):
    search_url = f"https://medium.com/search?q={query.replace(' ', '%20')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True) if "/p/" in a["href"]][:max_articles]

        content = ""
        for link in links:
            if link.startswith("/"):
                link = "https://medium.com" + link
            try:
                article = requests.get(link, headers=headers, timeout=8)
                article_soup = BeautifulSoup(article.text, "html.parser")
                paragraphs = [p.text for p in article_soup.find_all("p")]
                content += "\n\n".join(paragraphs[:5])  # take first few paragraphs
            except:
                continue
        return content if content else "No relevant Medium articles found."
    except:
        return "Error fetching Medium articles."

# fetch YouTube video only if needed
def fetch_best_youtube_video(query):
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=3,
        type="video",
        videoDuration="medium"
    ).execute()
    
    if search_response["items"]:
        for item in search_response["items"]:
            vid_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            if vid_url not in st.session_state.shown_videos:
                vid_title = item["snippet"]["title"]
                st.session_state.shown_videos.add(vid_url)
                return vid_title, vid_url
    return None, None

# generate deep structured plan with forced video suggestions
def generate_in_depth_plan(topic, weeks, hours_per_week):
    medium_content = scrape_medium_articles(topic, max_articles=8)
    total_hours = weeks * hours_per_week
    words_per_week = hours_per_week * 800  # ~800 words per study hour

    prompt = f"""
You are an expert educator creating a **mini-textbook style course** on "{topic}".
The learner will study for {weeks} weeks, {hours_per_week} hours/week ({total_hours} total hours).

I have collected Medium articles on this topic:
\"\"\" 
{medium_content} 
\"\"\"

✅ Your task:
- Give a **course title + overview**.
- Create a **WEEK-BY-WEEK course**.
- For EACH week:
  - Write a **well-structured lesson (~{words_per_week} words)** filling the time.
  - Use clear sections:
    ## Week X: Title
    1. Concept → Detailed explanation
    ✅ Example
    ✅ Exercise
  - Include **examples, analogies, exercises, and key takeaways**.
  - **MANDATORY:** Suggest **at least 1 but max 2 video recommendations per week** using this exact format:
    🎥 Video Needed: <short descriptive title>

📌 IMPORTANT:
- There MUST be at least **one video suggestion per week**, even if the text is detailed.
- Videos should be for **visually complex or practical concepts**.
- Do NOT suggest more than 2 videos/week.

Now write the full course.
"""

    st.session_state.messages.append(HumanMessage(content=prompt))
    response = llm.invoke(st.session_state.messages)
    st.session_state.messages.append(AIMessage(content=response.content))
    st.session_state.weekly_plan = response.content
    st.session_state.shown_videos.clear()

# button to build course
if st.button("🚀 Build Full Course"):
    generate_in_depth_plan(topic, weeks, hours_per_week)

# display generated course
if st.session_state.weekly_plan:
    st.subheader("📖 Full Course with Structured Lessons & Sensible Videos")
    weekly_lines = st.session_state.weekly_plan.split("\n")

    i = 0
    while i < len(weekly_lines):
        line = weekly_lines[i].rstrip()

        # “undefined” delimited code block
        if line == "undefined":
            i += 1
            code_block = []
            # collect until next “undefined”
            while i < len(weekly_lines) and weekly_lines[i].strip() != "undefined":
                code_block.append(weekly_lines[i])
                i += 1
            # skip closing “undefined”
            i += 1
            st.code("\n".join(code_block))
            continue

        # generic ''' code fence
        if line.startswith("```"):
            i += 1
            code_block = []
            while i < len(weekly_lines) and not weekly_lines[i].startswith("```"):
                code_block.append(weekly_lines[i])
                i += 1
            i += 1  # skip closing ```
            st.code("\n".join(code_block))
            continue

        # week headers
        if line.lower().startswith("## week"):
            st.markdown(f"## 📅 {line.replace('##', '').strip()}")

        # subsections
        elif line.startswith("###"):
            st.markdown(f"### {line.replace('###', '').strip()}")

        # video suggestions
        elif line.startswith("🎥 Video Needed:"):
            video_topic = line.replace("🎥 Video Needed:", "").strip()
            vid_title, vid_url = fetch_best_youtube_video(f"{topic} {video_topic}")
            if vid_url:
                st.write(f"🎥 **{vid_title}**")
                st.video(vid_url)

        # normal markdown
        else:
            st.markdown(line)

        i += 1

    # Refinement UI
    st.subheader("✏️ Refine the Course")
    refine_input = st.text_area("What would you like to change? (e.g., 'make it beginner-friendly', 'add more coding examples')")
    
    if st.button("🔄 Refine Plan"):
        if refine_input.strip():
            st.session_state.messages.append(
                HumanMessage(content=f"Refine the previous course. {refine_input}")
            )
            refined_response = llm.invoke(st.session_state.messages)
            st.session_state.messages.append(AIMessage(content=refined_response.content))
            st.session_state.weekly_plan = refined_response.content
            st.session_state.shown_videos.clear()

