# AI Agent for Information Extraction

This project is an AI-powered agent that allows users to upload data, perform web searches, and extract specific information using an LLM.

## Setup Instructions
1. **Clone the Repository**: `git clone <repo-url>`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Google Sheets API Setup**:
   - Enable the Sheets API on Google Cloud.
   - Download `credentials.json` and place it in the project directory.
4. **API Keys**:
   - Enter your SerpAPI and OpenAI API keys directly in the app UI.
   
## Usage Guide
1. Run the app with `streamlit run app.py`.
2. Upload a CSV file or link a Google Sheet, define a query, and start extraction.
3. Download results as CSV or update Google Sheets directly.

