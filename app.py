from flask import Flask, request, render_template, redirect, url_for
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


# Configure the Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash-lite')

self_prompt = "You are a helpful assistant that provides detailed advice."

def get_response(prompt):
    # The Gemini API has a simpler prompt structure
    full_prompt = self_prompt + "\n\n" + prompt
    response = model.generate_content(full_prompt)
    return response

def get_journal_prompt() -> str:
    """Generates a single, reflective journal prompt from the AI."""
    import time
    prompt = f"Generate a unique, gentle, open-ended question to help someone reflect on their day. Make it different each time. Current time: {time.time()}. Return only the question, nothing else."
    try:
        response = get_response(prompt)
        result = response.text.strip()
        print(f"Generated prompt: {result}")
        return result
    except Exception as e:
        print(f"Error generating prompt: {e}")
        raise  # Re-raise to show error instead of blank page

def analyze_sentiment(text: str) -> int:
    """Analyzes the sentiment of a text using Gemini AI."""
    prompt = f"Sentiment analysis: Is this text positive, negative, or neutral? Return only: 1 for positive, 0 for neutral, -1 for negative. Text: {text}"
    try:
        response = get_response(prompt)
        raw_text = response.text.strip()
        print(f"Sentiment analysis for '{text}': raw response = '{raw_text}'")
        # Extract the first integer found
        match = re.search(r'-?\d+', raw_text)
        if match:
            sentiment = int(match.group())
            print(f"Extracted sentiment: {sentiment}")
            return sentiment
        else:
            print("No valid sentiment number found in response")
            return 0
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        raise  # Re-raise to show error instead of blank page

# In-memory data store for the hackathon prototype
journal_entries = []

def update_sentiment_graph():
    """Generates and saves a plot of sentiment trends."""
    if not journal_entries:
        # Create a blank plot if there are no entries
        plt.figure(figsize=(8, 4))
        plt.plot([], [], label='Sentiment', color='blue', marker='o')
    else:
        sentiments = [entry['sentiment'] for entry in journal_entries]
        days = range(1, len(sentiments) + 1)
        plt.figure(figsize=(8, 4))
        plt.plot(days, sentiments, label='Sentiment', color='blue', marker='o')

    plt.xlabel('Journal Entry')
    plt.ylabel('Sentiment Score')
    plt.title('Your Emotional Trends')
    plt.yticks([-1, 0, 1], ['Negative', 'Neutral', 'Positive'])
    plt.grid(True)
    plt.legend()

    if not os.path.exists('static'):
        os.makedirs('static')
    plt.savefig('static/plot.png')
    plt.close()

@app.route("/")
def home():
    prompt = get_journal_prompt()
    score = len(journal_entries) * 10  # Simple score based on entries
    update_sentiment_graph()
    return render_template("home.html", prompt=prompt, score=score)

@app.route("/submit", methods=["POST"])
def submit_entry():
    entry_text = request.form.get("entry")
    if entry_text:
        sentiment = analyze_sentiment(entry_text)
        journal_entries.append({"text": entry_text, "sentiment": sentiment})
    return redirect(url_for('home'))
