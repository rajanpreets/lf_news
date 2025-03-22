import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from serpapi import GoogleSearch
from openai import OpenAI

# --- Configuration ---
open_api_key = st.secrets["OPENAI_API"]
SERPAPI_API_KEY = "6c2d737aa68c281962070dc62054aa7e0ebba529957364ec07bdaa3f8c7e296b"

client = OpenAI(api_key=open_api_key)

# --- Functions ---
def get_visible_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"Error fetching text: {e}"

def summarize_news(url):
    news_text = get_visible_text(url)
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize this news in 3 bullet points focusing on drug development aspects. Ignore website-specific text."},
                {"role": "user", "content": news_text}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error summarizing news: {e}"

def categorize_news(summary):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Classify this news into ONLY ONE of these categories: Clinical, Regulatory, Commercial. Respond only with the category name."},
                {"role": "user", "content": summary}
            ],
            temperature=0.1
        )
        category = completion.choices[0].message.content.strip()
        return category if category in ['Clinical', 'Regulatory', 'Commercial'] else 'Other'
    except Exception as e:
        return f"Error: {e}"

def extract_moa(drug_name, summaries):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Identify the mechanism of action for {drug_name} from these news summaries. Respond concisely."},
                {"role": "user", "content": "\n".join(summaries)}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return "MoA not available"

# --- Streamlit App ---
st.title("Pharma News Analyzer")

# User input for drug molecules
drugs_input = st.text_input("Enter drug molecules (comma-separated)", "Jardiance, Ozempic")
drug_list = [d.strip() for d in drugs_input.split(',')]

if st.button("Analyze News"):
    all_data = []
    
    for drug in drug_list:
        with st.spinner(f'Processing {drug}...'):
            # Get news results
            params = {
                "api_key": SERPAPI_API_KEY,
                "engine": "google",
                "q": f"{drug} pharmaceutical news",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en",
                "tbm": "nws",
                "tbs": "qdr:w",
                "num": 5
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            news_results = results.get('news_results', [])
            
            # Process news articles
            clinical, regulatory, commercial = [], [], []
            summaries = []
            
            for item in news_results[:5]:  # Process top 5 results
                link = item.get('link')
                summary = summarize_news(link)
                if "Error" not in summary:
                    category = categorize_news(summary)
                    summaries.append(summary)
                    
                    if category == 'Clinical':
                        clinical.append(summary)
                    elif category == 'Regulatory':
                        regulatory.append(summary)
                    elif category == 'Commercial':
                        commercial.append(summary)
            
            # Extract MoA
            moa = extract_moa(drug, summaries) if summaries else "MoA not available"
            
            # Prepare data for table
            all_data.append({
                "Molecule (Company)": drug,
                "Mechanism of Action": moa,
                "Regulatory News": "\n\n".join(regulatory) if regulatory else "No regulatory news",
                "Clinical News": "\n\n".join(clinical) if clinical else "No clinical news",
                "Commercial News": "\n\n".join(commercial) if commercial else "No commercial news"
            })
    
    # Display results
    df = pd.DataFrame(all_data)
    st.dataframe(df, height=800, use_container_width=True)
    st.success("Analysis complete!")
