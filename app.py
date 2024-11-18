import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from serpapi import GoogleSearch
import openai
import time

# Google Sheets Authentication
def authenticate_google_sheets(credentials_file):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    return build('sheets', 'v4', credentials=credentials)

# Google Sheets Fetch Function
def fetch_google_sheet(sheet_url, sheet_service):
    sheet_id = sheet_url.split("/")[5]
    sheet = sheet_service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Sheet1").execute()
    values = sheet.get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# Streamlit App UI
st.title("AI Agent ")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
google_sheet_url = st.text_input("Enter Google Sheets URL")

# Load Data
data = None
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.write("CSV Data Preview:", data.head())
elif google_sheet_url:
    try:
        sheet_service = authenticate_google_sheets("path/to/credentials.json")
        data = fetch_google_sheet(google_sheet_url, sheet_service)
        st.write("Google Sheets Data Preview:", data.head())
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")

# Column Selection
if data is not None:
    selected_column = st.selectbox("Select the primary column for entities", data.columns)

# Dynamic Query Input
if data is not None:
    st.subheader("Dynamic Query Input")
    query_template = st.text_input(
        "Enter your query template. Use {entity} as a placeholder for the selected column.",
        value="Find the email address of {entity}"
    )

    if st.button("Start Search"):
        if selected_column:
            entities = data[selected_column].dropna().tolist()
            st.write(f"Performing searches for {len(entities)} entities...")

            serpapi_api_key = st.text_input("Enter your SerpAPI key", type="password")
            search_results = []

            if serpapi_api_key:
                progress_bar = st.progress(0)
                for i, entity in enumerate(entities):
                    query = query_template.replace("{entity}", entity)
                    search = GoogleSearch({"q": query, "api_key": serpapi_api_key})
                    result = search.get_dict()

                    if "organic_results" in result:
                        results = result["organic_results"]
                        extracted = {
                            "entity": entity,
                            "query": query,
                            "results": [
                                {"title": r["title"], "link": r["link"], "snippet": r.get("snippet", "")}
                                for r in results
                            ]
                        }
                        search_results.append(extracted)
                    else:
                        st.warning(f"No results found for {entity}")

                    progress_bar.progress((i + 1) / len(entities))
                    time.sleep(1)

                st.success("Search completed!")
                st.write("Search Results Preview", search_results)
                st.session_state["search_results"] = search_results
            else:
                st.error("Please provide a valid SerpAPI key.")

# LLM Extraction
if "search_results" in st.session_state:
    st.subheader("Extract Information with LLM")
    llm_prompt_template = st.text_area(
        "Enter the LLM prompt template. Use {entity} and {results} as placeholders.",
        value="Extract the email address of {entity} from the following web results: {results}."
    )
    openai_api_key = st.text_input("Enter your OpenAI API key", type="password")

    if st.button("Run LLM Extraction"):
        if openai_api_key:
            openai.api_key = openai_api_key

            search_results = st.session_state["search_results"]
            extracted_data = []

            progress_bar = st.progress(0)
            for i, result in enumerate(search_results):
                entity = result["entity"]
                results_text = "\n".join(
                    f"Title: {r['title']}\nSnippet: {r['snippet']}\nLink: {r['link']}"
                    for r in result["results"]
                )
                llm_prompt = llm_prompt_template.replace("{entity}", entity).replace("{results}", results_text)

                try:
                    response = openai.Completion.create(
                        engine="text-davinci-003",
                        prompt=llm_prompt,
                        max_tokens=200,
                        temperature=0.7
                    )
                    extracted_info = response["choices"][0]["text"].strip()
                    extracted_data.append({"entity": entity, "extracted_info": extracted_info})
                except Exception as e:
                    st.error(f"Error processing {entity}: {e}")
                    extracted_data.append({"entity": entity, "extracted_info": "Error"})

                progress_bar.progress((i + 1) / len(search_results))

            st.success("LLM extraction completed!")
            st.write("Extracted Data", pd.DataFrame(extracted_data))
            st.session_state["extracted_data"] = extracted_data
        else:
            st.error("Please provide a valid OpenAI API key.")

# Display and Download Results
if "extracted_data" in st.session_state:
    st.subheader("Extracted Information")
    extracted_df = pd.DataFrame(st.session_state["extracted_data"])
    st.write(extracted_df)

    st.download_button(
        label="Download CSV",
        data=extracted_df.to_csv(index=False),
        file_name="extracted_data.csv",
        mime="text/csv"
    )

    if google_sheet_url and "sheet_service" in locals():
        if st.button("Update Google Sheet"):
            try:
                sheet_service.spreadsheets().values().update(
                    spreadsheetId=google_sheet_url.split("/")[5],
                    range="Sheet1",
                    valueInputOption="RAW",
                    body={"values": [extracted_df.columns.tolist()] + extracted_df.values.tolist()}
                ).execute()
                st.success("Google Sheet updated successfully!")
            except Exception as e:
                st.error(f"Error updating Google Sheet: {e}")
