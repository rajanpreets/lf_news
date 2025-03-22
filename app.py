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
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"Error fetching text: {e}"

def summarize_content(text, prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error summarizing content: {e}"

def get_latest_summary(drug):
    try:
        # Get top Google result
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "q": f"{drug} latest drug developments 2024",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "num": 1
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get('organic_results', [])
        
        if not organic_results:
            return "No recent information found"
            
        top_result = organic_results[0]
        link = top_result.get('link')
        text = get_visible_text(link)
        
        if "Error" in text:
            return "Information unavailable - could not fetch source"
            
        return summarize_content(
            text, 
            "Extract the most recent and important information about this drug in 3 bullet points. Focus on updates from the last 12 months."
        )
        
    except Exception as e:
        return f"Error retrieving summary: {str(e)}"

def categorize_news(summary):
    return summarize_content(
        summary,
        "Classify this news into ONLY ONE of these categories: Clinical, Regulatory, Commercial. Respond only with the category name."
    )

def extract_moa(drug_name, summaries):
    return summarize_content(
        "\n".join(summaries),
        f"Identify the mechanism of action for {drug_name} from these news summaries. Respond concisely in one sentence."
    )

# --- Streamlit App ---
st.title("Pharma News Analyzer")

# User input for drug molecules
drugs_input = st.text_input("Enter drug molecules (comma-separated)", "Jardiance, Ozempic")
drug_list = [d.strip() for d in drugs_input.split(',')]

if st.button("Analyze News"):
    all_data = []
    
    for drug in drug_list:
        with st.spinner(f'Processing {drug}...'):
            # Get latest summary
            latest_summary = get_latest_summary(drug)
            
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
            
            for item in news_results[:5]:
                link = item.get('link')
                news_text = get_visible_text(link)
                
                if "Error" not in news_text:
                    news_summary = summarize_content(
                        news_text,
                        "Summarize this pharmaceutical news in 3 bullet points focusing on drug development aspects."
                    )
                    summaries.append(news_summary)
                    
                    category = categorize_news(news_summary)
                    if category == 'Clinical':
                        clinical.append(news_summary)
                    elif category == 'Regulatory':
                        regulatory.append(news_summary)
                    elif category == 'Commercial':
                        commercial.append(news_summary)

            # Extract MoA
            moa = extract_moa(drug, summaries) if summaries else "MoA not available"
            
            # Prepare data for table
            all_data.append({
                "Molecule (Company)": drug,
                "Latest Summary": latest_summary,
                "Mechanism of Action": moa,
                "Regulatory News": "\n\n".join(regulatory) or "No regulatory news",
                "Clinical News": "\n\n".join(clinical) or "No clinical news",
                "Commercial News": "\n\n".join(commercial) or "No commercial news"
            })
    
    # Display results
    df = pd.DataFrame(all_data)
    column_order = ["Molecule (Company)", "Latest Summary", "Mechanism of Action", 
                    "Regulatory News", "Clinical News", "Commercial News"]
    st.dataframe(df[column_order], height=1000, use_container_width=True)
    st.success("Analysis complete!")
