from flask import Flask, render_template, request, redirect, url_for
import os
from testsm import summarize_job_description

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dem.html')

@app.route('/process', methods=['POST'])
def process():
    job_description = request.form.get('job_description')

    if not job_description:
        return "❌ Error: Job Description is required."

    try:
        result = summarize_job_description(job_description)

        # Convert string results with \n into a bulleted list
        def format_to_bullets(text):
            if isinstance(text, str) and "\n" in text:
                return text.split("\n")
            return [text] if text else ["Not Available"]

        formatted_result = {
            "job_summary": result.get("Job Summary", "Not Available"),
            "responsibilities": format_to_bullets(result.get("Responsibilities", "Not Available")),
            "eligibility": format_to_bullets(result.get("Eligibility", "Not Available")),
            "skills": format_to_bullets(result.get("Skills and Technologies", "Not Available")),
            "preferred_qualifications": format_to_bullets(result.get("Preferred Qualifications", "Not Available"))
        }

        return render_template('outy.html', result=formatted_result)
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
