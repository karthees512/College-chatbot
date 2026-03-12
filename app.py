from flask import Flask, request, jsonify, render_template
from rapidfuzz import process
from dotenv import load_dotenv
from openai import OpenAI
import json
import os

# ------------------- CONFIG -------------------
load_dotenv()
app = Flask(__name__)

# Optional: OpenAI client
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# ------------------- LOAD FAQ FILES -------------------
faq_dir = "faqs"
faqs = []

for file_name in os.listdir(faq_dir):
    if file_name.endswith(".json"):
        file_path = os.path.join(faq_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # ✅ Ensure it’s a list of dicts
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "question" in item and "answer" in item:
                            faqs.append(item)
                        else:
                            print(f"⚠️ Skipped malformed item in {file_name}: {item}")
                else:
                    print(f"⚠️ Skipped {file_name}: not a list")
        except Exception as e:
            print(f"❌ Error reading {file_name}: {e}")

# Now prepare list of questions
faq_questions = [faq["question"] for faq in faqs]
print(f"✅ Loaded {len(faqs)} FAQs from {faq_dir}")
for i, q in enumerate(faq_questions[:5]):
    print(f"  {i+1}. {q}")

# ------------------- ROUTES -------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_response():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"response": "Please type something 😅"})

    # ------------------- FAQ Matching -------------------
    if faq_questions:
        match = process.extractOne(user_input, faq_questions, score_cutoff=70)
        print("🟣 User input:", user_input)
        print("🟢 Match result:", match)

        if match:
            best_question = match[0]
            best_index = faq_questions.index(best_question)
            best_answer = faqs[best_index]["answer"]
            print(f"✅ Matched '{best_question}' ({match[1]}%) → {best_answer}")
            return jsonify({"response": best_answer})

    # ------------------- AI Fallback -------------------
    if client:
        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a official chatbot assistant for P.K.N arts & science college."},
                    {"role": "user", "content": user_input},
                ]
            )
            answer = completion.choices[0].message.content
            return jsonify({"response": answer})
        except Exception as e:
            print(f"⚠️ OpenAI Error: {e}")
            return jsonify({"response": "⚠️ AI service unavailable. Try later."})

    # ------------------- Default -------------------
    return jsonify({"response": "Sorry, I couldn’t find any answer for that 😅"})

# ------------------- MAIN -------------------
if __name__ == "__main__":
    app.run(debug=True)
