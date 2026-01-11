# AI Crime Scene Investigator - Web UI

This is a Streamlit-based web interface for the CSI Agent.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **API Key**:
    You need a Google Gemini API Key for the "Executive Summary" feature.
    -   Get one from [Google AI Studio](https://aistudio.google.com/).
    -   You can enter it in the Sidebar when the app runs, or set it as an environment variable: `GOOGLE_API_KEY`.

## Running the App

Run the following command in your terminal:

```bash
streamlit run app.py
```

## Features

-   **Dashboard**: Overview of cases, risk scores, and recent activity.
-   **New Investigation**: Enter scene descriptions and upload photos to run the AI agents.
-   **Case History**: View past case reports, evidence tables, and download PDF/JSON reports.
-   **Ask Memory**: Chat with the agent to recall details from specific cases ("What was the weapon in Case X?").

## Note on "Stubs"
The current version uses "Vision Stubs" (filename keyword matching) for image analysis as per the original project design. Real image analysis would require a vision model integration.
