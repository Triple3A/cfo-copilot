# CFO Copilot

Chat with your financial data. Ask questions in plain English and get instant answers with charts.

CFO Copilot is a mini AI-powered assistant that lets you chat directly with your financial data. Instead of spending hours digging through CSVs and building charts manually, you can just ask questions in plain English and get back clean, board-ready answers in seconds.✨ 

## Features
- Chat with your data: Ask simple, natural language questions.
- Instant Answers: Get key financial metrics without the manual work.
- Board-Ready Charts: Visualizations are generated on the fly with Plotly.
- Powered by Gemini: Uses Google's Gemini API to understand your questions and route them to the right data function.

You can ask things like:
* "What was June 2025 revenue vs budget in USD?"
* "Show me the gross margin % trend for the last few months."
* "What is our cash runway right now?"
  
## 🛠️ How to Get it Running
Want to try it out on your own machine? It's pretty straightforward.

1. Clone the repository:
First, grab the code from GitHub.
```
git clone https://github.com/triple3a/cfo-copilot.git
cd cfo-copilot
```

2. Set up your environment:
I recommend using a virtual environment to keep all the project packages tidy.
```
# Create the environment
python -m venv venv
# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

3. Install the good stuff:
This project relies on a few Python libraries, all listed in requirements.txt.
```
pip install -r requirements.txt
```

4. Add your API Key:
The app needs a Google Gemini API key to work its magic.
- Create a new file in the root of the project called .env.
- Inside this file, add your API key like this:
```
GOOGLE_API_KEY="your-super-secret-api-key"
```
You can get a key from the [Google AI Studio](http://aistudio.google.com/app/apikey). The `.gitignore` file is already set up to make sure you don't accidentally commit this key!

5. Fire it up!
You're all set. Run the Streamlit command from your terminal:
```
streamlit run app.py
```
Your web browser should open with the app running. Go ahead and ask it a question!✅ 

## Running Tests
I've included a simple test to make sure the data functions are working as expected. You can run it yourself with `pytest`.
```
pytest
```
If everything is set up correctly, you should see it pass. ✅

Hope you enjoy checking it out! Let me know if you have any ideas or feedback.
