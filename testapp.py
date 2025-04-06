from flask import Flask, render_template, request
import os
import sqlite3
from werkzeug.utils import secure_filename
from testsm import summarize_job_description
from parser import parse_resume  # Using your updated parser
from matcher import match_resume_to_job  # Using your updated matcher

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        
        def format_to_bullets(text):
            if isinstance(text, str) and "\n" in text:
                return text.split("\n")
            return [text] if text else ["Not Available"]
        
        formatted_result = {
            "job_summary": result.get("Job Summary", "Not Available"),
            "responsibilities": format_to_bullets(result.get("Responsibilities", "Not Available")),
            "eligibility": format_to_bullets(result.get("Eligibility", "Not Available")),
            "skills": format_to_bullets(result.get("Skills and Technologies", "Not Available")),
            "preferred_qualifications": format_to_bullets(result.get("Preferred Qualifications", "Not Available")),
            "match_score": "N/A"
        }
        return render_template('outy.html', result=formatted_result)
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/process_resume', methods=['POST'])
def process_resume():
    job_description = request.form.get('job_description')
    if not job_description:
        return "❌ Error: Job Description is required."
    
    if 'resume' not in request.files:
        return "❌ Error: No file uploaded."
    
    file = request.files['resume']
    if file.filename == '':
        return "❌ Error: No selected file."
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process job description
            job_summary_data = summarize_job_description(job_description)
            
            # Parse resume and get basic match score
            parsed_result = parse_resume(filepath, job_summary_data)
            resume_data = parsed_result.get("resume_summary", None)
            job_summary = parsed_result.get("job_summary", {})
            basic_match_score = parsed_result.get("match_score", "0%")
            
            # Use the matcher for detailed scoring
            if resume_data:
                match_result = match_resume_to_job(resume_data, job_summary)
                detailed_match_score = f"{match_result['final_match_score']}%"
                individual_scores = match_result['individual_scores']
            else:
                detailed_match_score = basic_match_score
                individual_scores = {}
            
            def format_to_bullets(text):
                if isinstance(text, str) and "\n" in text:
                    return text.split("\n")
                return [text] if text else ["Not Available"]
                
            formatted_result = {
                "job_summary": job_summary.get("Job Summary", "Not Available"),
                "responsibilities": format_to_bullets(job_summary.get("Responsibilities", "Not Available")),
                "eligibility": format_to_bullets(job_summary.get("Eligibility", "Not Available")),
                "skills": format_to_bullets(job_summary.get("Skills and Technologies", "Not Available")),
                "preferred_qualifications": format_to_bullets(job_summary.get("Preferred Qualifications", "Not Available")),
                "resume_summary": resume_data,
                "match_score": detailed_match_score,
                "individual_scores": individual_scores
            }
            
            return render_template('outy.html', result=formatted_result)
        
        except Exception as e:
            import traceback
            return f"❌ Error: {str(e)}<br><pre>{traceback.format_exc()}</pre>"
    
    return "❌ Error: Invalid file type. Only PDF and DOCX files are allowed."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx'}

if __name__ == '__main__':
    app.run(debug=True)