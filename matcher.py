import re
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Define weights for different criteria
WEIGHTS = {
    "education": 0.2,
    "experience": 0.2,
    "skills": 0.5,
    "certifications": 0.1
}

# Improved experience extraction function
def extract_years_of_experience(experience_text):
    # Try to find years of experience directly
    years_pattern = r'(\d+)(?:\.\d+)?\+?\s*years?'
    years_match = re.search(years_pattern, experience_text, re.IGNORECASE)
    
    if years_match:
        return int(years_match.group(1))
    
    # If no direct years mentioned, try to calculate from date ranges
    date_pattern = r'(\d{4})\s*[–-]\s*(Present|\d{4})'
    dates = re.findall(date_pattern, experience_text, re.IGNORECASE)
    
    if dates:
        total_years = 0
        for start, end in dates:
            start_year = int(start)
            end_year = 2025 if end.lower() == 'present' else int(end)
            total_years += (end_year - start_year)
        return total_years
    
    # If we have internship or other experience without years, return a default value
    if 'intern' in experience_text.lower():
        return 1
    
    return 0

# Cosine Similarity for text comparison
def calculate_cosine_similarity(text1, text2):
    if not text1 or not text2 or text1 == "Not Found" or text2 == "Not Found":
        return 0  # No similarity if either is empty or not found
    
    # Convert lists to strings if needed
    if isinstance(text1, list):
        text1 = ' '.join(text1)
    if isinstance(text2, list):
        text2 = ' '.join(text2)
        
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])
        return similarity[0][0] * 100  # Convert to percentage
    except:
        return 0  # Return 0 if there's an error in processing

# Match Resume to Job Description & Calculate Score
def match_resume_to_job(resume_data, job_data):
    scores = {}
    
    # Match Education
    education_score = calculate_cosine_similarity(
        resume_data.get("education", "Not Found"),
        job_data.get("eligibility", "Not Found")
    )
    scores["education"] = min(100, education_score)
    
    # Match Experience
    # Extract years from resume
    resume_exp_text = resume_data.get("experience", "0")
    resume_years = extract_years_of_experience(resume_exp_text)
    
    # Extract required years from job
    job_exp_text = ' '.join([str(item) for item in job_data.get("eligibility", [])])
    job_years = extract_years_of_experience(job_exp_text)
    
    # Calculate experience score
    if job_years > 0:
        exp_ratio = min(resume_years / job_years, 1.5)  # Cap at 150%
        scores["experience"] = min(100, exp_ratio * 100)
    else:
        scores["experience"] = 50  # Default value if job years can't be determined
    
    # Match Skills using Cosine Similarity
    skills_score = calculate_cosine_similarity(
        resume_data.get("skills", "Not Found"),
        ' '.join([str(item) for item in job_data.get("skills", [])])
    )
    scores["skills"] = min(100, skills_score)
    
    # Match Certifications using Cosine Similarity
    cert_score = calculate_cosine_similarity(
        resume_data.get("certifications", "Not Found"),
        ' '.join([str(item) for item in job_data.get("preferred_qualifications", [])])
    )
    scores["certifications"] = min(100, cert_score)
    
    # Calculate Final Match Score
    final_score = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
    
    return {
        "individual_scores": scores,
        "final_match_score": round(final_score, 2)
    }

# Example Usage
if __name__ == "__main__":
    sample_resume = {
        "education": "B.Tech in Computer Science",
        "experience": "5 years",
        "skills": ["Python", "Machine Learning", "Deep Learning", "SQL"],
        "certifications": ["AWS Certified ML", "TensorFlow Developer"]
    }
    
    sample_job = {
        "eligibility": ["B.Tech", "5+ years of experience"],
        "skills": ["Python", "TensorFlow", "NLP", "Deep Learning"],
        "preferred_qualifications": ["AWS Certified ML"]
    }
    
    result = match_resume_to_job(sample_resume, sample_job)
    print("🎯 Match Score:", result["final_match_score"], "%")
    print("📊 Breakdown:", result["individual_scores"])

