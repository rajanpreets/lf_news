%%writefile app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from serpapi import GoogleSearch
from openai import OpenAI
from pydantic import BaseModel

# --- Configuration ---
open_api_key = st.secrets["OPENAI_API"]  # Replace with your OpenAI API key
SERPAPI_API_KEY = "6c2d737aa68c281962070dc62054aa7e0ebba529957364ec07bdaa3f8c7e296b"


client = OpenAI(api_key=open_api_key)


# --- Functions ---

def get_visible_text(url):
    """
    Extracts and returns the concatenated text from all <p> tags found in the webpage.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = []
        elements = soup.find_all('p')
        for element in elements:
            text_content = element.get_text(strip=True)
            if text_content:
                paragraphs.append(text_content)
        return "\n".join(paragraphs)
    except Exception as e:
        return f"Error fetching text: {e}"

def summarize_news(url):
    """
    Summarizes the news article found at the given URL.
    Uses OpenAI's chat completion with a prompt tailored for summarization.
    """
    news_text = get_visible_text(url)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a smart analyst whose job is to summarize the news provided in 3 bullet points for the leadership team. 
                                  The input will be from the text scrapped from the website so ignore website related text and focus only on news text.
                    """
                },

                {
                    'role': 'user',
                    'content': get_visible_text(url)
                }
            ],
          temperature=0.1  
        )

        return(completion.choices[0].message.content)
    except Exception as e:
        return f"Error summarizing news: {e}"

# Define Pydantic model for tags
class NewsTags(BaseModel):
    tags: list[str]

def get_news_tags(news_summary):
    """
    Uses OpenAI's beta function call (or equivalent) to extract up to 5 tags from the provided news summary.
    The response is validated against the NewsTags model.
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a lifesciences news analyzer. Extract the possible news tags from the provide news. Provide maximum 5 tags"},
                {"role": "user", "content": str(news_summary)},
            ],
            response_format=NewsTags,
        )
        # Extract tags from the parsed response.
        return completion.choices[0].message.parsed.tags
    except Exception as e:
        return f"Error extracting tags: {e}"

# --- Streamlit App ---

st.title("News Summarizer and Tag Extractor")

# User input for the news topic
topic = st.text_input("Enter a news topic", "bristol myers squibb bms")

if st.button("Get News"):
    with st.spinner('Fetching news, summarizing, and extracting tags...'):
        params = {
          "api_key": SERPAPI_API_KEY,
          "engine": "google",
          "q": topic,
          "google_domain": "google.com",
          "gl": "us",
          "hl": "en",
          "tbm": "nws",
          "tbs": "qdr:w"
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        news_results = results.get('news_results', [])
        news_data = []

        for item in news_results[:3]:
            link = item.get('link')
            title = item.get('title')
            snippet = item.get('snippet')

            summary = summarize_news(link)
            tags = get_news_tags(summary)

            news_data.append({
                "Title": title,
                "Link": link,
                "Snippet": snippet,
                "Summary": summary,
                "Tags": tags
            })

        df = pd.DataFrame(news_data)
        st.dataframe(df)
