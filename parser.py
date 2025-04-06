
import os
import re
import docx2txt
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_resume(file_path, job_data):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file type"}
    
    original_text = text  # Keep original for reference
    cleaned_text = clean_text(text)
    
    # Extract name - improved pattern matching
    name_pattern = r'^([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)'
    name_match = re.search(name_pattern, cleaned_text)
    name = name_match.group(1) if name_match else "Not Found"
    
    # Extract email with common email pattern
    email_pattern = r'[\w.+-]+@[\w-]+\.[\w.-]+'
    email_match = re.search(email_pattern, original_text)
    email = email_match.group(0) if email_match else "Not Found"
    
    # Extract education - focus on degree programs and institutions
    education_section = re.search(r'(?:Education|EDUCATION)[\s\S]*?(?:Experience|EXPERIENCE|Projects|PROJECTS|Skills|SKILLS|\Z)', original_text, re.IGNORECASE)
    
    education = []
    if education_section:
        ed_text = education_section.group(0)
        # Look for university/college names
        uni_pattern = r'(?:University|College|Institute|School)[^.,;\n]*'
        unis = re.findall(uni_pattern, ed_text, re.IGNORECASE)
        education.extend(unis)
        
        # Look for degree programs
        degree_pattern = r'(?:B\.Tech|Bachelor|Master|M\.Tech|BSc|MSc|PhD|B\.E\.|M\.E\.|BE|ME|BTech)[^.,;\n]*'
        degrees = re.findall(degree_pattern, ed_text, re.IGNORECASE)
        education.extend(degrees)
    
    # Extract experience from dedicated section
    experience_section = re.search(r'(?:Experience|EXPERIENCE)[\s\S]*?(?:Projects|PROJECTS|Skills|SKILLS|Education|EDUCATION|\Z)', original_text, re.IGNORECASE)
    
    experience = []
    if experience_section:
        exp_text = experience_section.group(0)
        # Extract job titles with companies
        job_pattern = r'([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s\d–-]*(?:Present|Current|\d{4})'
        jobs = re.findall(job_pattern, exp_text)
        experience.extend(jobs)
        
        # Extract positions with dates
        position_pattern = r'((?:Intern|Engineer|Developer|Scientist|Analyst|Researcher|Consultant)[^\n]*)'
        positions = re.findall(position_pattern, exp_text, re.IGNORECASE)
        if positions:
            experience.extend(positions)
    
    # If no experience section found, look for jobs/internships in the whole document
    if not experience:
        # Look for jobs with date ranges
        job_date_pattern = r'([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[–-]\s*(?:Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec\s+\d{4})'
        jobs_dates = re.findall(job_date_pattern, original_text)
        experience.extend(jobs_dates)
        
        # Look for internship mentions
        internship_pattern = r'([^\n.]*Intern[^\n.]*)'
        internships = re.findall(internship_pattern, original_text, re.IGNORECASE)
        experience.extend(internships)
    
    # Extract skills
    skills_section = re.search(r'(?:Technical Skills|Skills|SKILLS)[\s\S]*?(?:Certifications|CERTIFICATIONS|Projects|PROJECTS|Experience|EXPERIENCE|\Z)', original_text, re.IGNORECASE)
    
    skills = []
    if skills_section:
        skills_text = skills_section.group(0)
        # Look for technical skills with better patterns
        tech_skills_pattern = r'(?:Python|Java|C\+\+|JavaScript|SQL|Excel|Machine Learning|Data Science|AWS|GCP|React|Node\.js|Pandas|NumPy|TensorFlow|PyTorch|Keras|Scikit-learn|NLTK|spaCy|Matplotlib|Seaborn|Power BI|Tableau|Streamlit|Azure|Hadoop|Spark|NLP|AI|Deep Learning|LLM|Transformer|Hugging Face)'
        tech_skills = re.findall(tech_skills_pattern, skills_text, re.IGNORECASE)
        skills.extend(tech_skills)
        
        # Additional pattern to find skill groups
        skill_groups = re.findall(r'(?:Languages|Tools|Technologies|Frameworks)\s*:\s*([^.\n]*)', skills_text, re.IGNORECASE)
        for group in skill_groups:
            group_skills = re.findall(r'\b([A-Za-z][\w\+\#\-\.]*)', group)
            skills.extend(group_skills)
    
    # If skills section wasn't found, look throughout the document
    if not skills:
        tech_skills_pattern = r'(?:Python|Java|C\+\+|JavaScript|SQL|Excel|Machine Learning|Data Science|AWS|GCP|React|Node\.js|Pandas|NumPy|TensorFlow|PyTorch|Keras|Scikit-learn|NLTK|spaCy|Matplotlib|Seaborn|Power BI|Tableau|Streamlit|Azure|Hadoop|Spark|NLP|AI|Deep Learning|LLM|Transformer|Hugging Face)'
        skills = re.findall(tech_skills_pattern, original_text, re.IGNORECASE)
    
    # Extract certifications
    cert_section = re.search(r'(?:Certifications|CERTIFICATIONS)[\s\S]*?(?:Projects|PROJECTS|Skills|SKILLS|Experience|EXPERIENCE|\Z)', original_text, re.IGNORECASE)
    
    certifications = []
    if cert_section:
        cert_text = cert_section.group(0)
        # Look for certification lines
        cert_lines = re.findall(r'([^\n•]*(?:Certificate|Certification|Course)[^\n•]*)', cert_text, re.IGNORECASE)
        certifications.extend(cert_lines)
        
        # Also try to extract bullet points that might be certifications
        bullet_certs = re.findall(r'[•-]\s*([^\n•-][^\n]*)', cert_text)
        certifications.extend(bullet_certs)
    
    # Clean up extracted data
    name = name.strip() if name else "Not Found"
    email = email.strip() if email else "Not Found"
    
    # Remove duplicates and clean up lists
    skills = list(set([s.strip() for s in skills if s.strip() and len(s.strip()) > 2]))
    education = list(set([e.strip() for e in education if e.strip()]))
    experience = list(set([e.strip() for e in experience if e.strip()]))
    certifications = list(set([c.strip() for c in certifications if c.strip()]))
    
    # Create resume summary with more accurate data
    resume_data = {
        "name": name,
        "email": email,
        "education": ', '.join(education[:3]) if education else "Not Found",
        "experience": ', '.join(experience[:3]) if experience else "Not Found",
        "skills": ', '.join(skills[:15]) if skills else "Not Found",
        "certifications": ', '.join(certifications[:3]) if certifications else "Not Found"
    }
    
    # Calculate match score between job summary and resume
    resume_text = f"{' '.join(education)} {' '.join(experience)} {' '.join(skills)} {' '.join(certifications)}"
    jd_text = ' '.join([v for k, v in job_data.items() if isinstance(v, str)])
    
    docs = [resume_text, jd_text]
    vectorizer = TfidfVectorizer().fit_transform(docs)
    vectors = vectorizer.toarray()
    sim_score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    match_score = round(sim_score * 100, 2)
    
    # Calculate individual scores for categories if needed
    # This is optional but provides more detailed matching information
    individual_scores = {}
    
    # Calculate education match
    if education and "education" in job_data:
        edu_docs = [' '.join(education), job_data["education"]]
        edu_vectorizer = TfidfVectorizer().fit_transform(edu_docs)
        edu_vectors = edu_vectorizer.toarray()
        edu_score = cosine_similarity([edu_vectors[0]], [edu_vectors[1]])[0][0]
        individual_scores["education"] = round(edu_score * 100, 2)
    
    # Calculate skills match
    if skills and "skills" in job_data:
        skill_docs = [' '.join(skills), job_data["skills"]]
        skill_vectorizer = TfidfVectorizer().fit_transform(skill_docs)
        skill_vectors = skill_vectorizer.toarray()
        skill_score = cosine_similarity([skill_vectors[0]], [skill_vectors[1]])[0][0]
        individual_scores["skills"] = round(skill_score * 100, 2)
    
    # Calculate experience match
    if experience and "experience" in job_data:
        exp_docs = [' '.join(experience), job_data["experience"]]
        exp_vectorizer = TfidfVectorizer().fit_transform(exp_docs)
        exp_vectors = exp_vectorizer.toarray()
        exp_score = cosine_similarity([exp_vectors[0]], [exp_vectors[1]])[0][0]
        individual_scores["experience"] = round(exp_score * 100, 2)
    
    return {
        "job_summary": job_data,
        "resume_summary": resume_data,
        "match_score": f"{match_score}%",
        "individual_scores": individual_scores
    }
