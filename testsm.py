import os
from dotenv import load_dotenv
import sqlite3
from langchain_core.prompts import PromptTemplate
from openai import OpenAI

# ✅ Load API key from .env
load_dotenv()
kluster_api_key = os.getenv("KLUSTER_API_KEY")
if not kluster_api_key:
    raise ValueError("❌ Error: KLUSTER_API_KEY is missing. Check your .env file.")

# ✅ Initialize Kluster AI client
kluster_client = OpenAI(
    api_key=kluster_api_key,
    base_url="https://api.kluster.ai/v1"
)

# ✅ Truncate JD if too long
def truncate_text(text, max_length=3000):
    if len(text) > max_length:
        print("⚠️ JD is too long, truncating...")
        return text[:max_length] + "..."
    return text

# ✅ Combined Prompt Generator
def generate_combined_prompt(jd_text):
    return f"""
    You are an AI assistant skilled in extracting information from job descriptions.
    Analyze the following JD and extract structured data. If any information is unavailable, say "Not Available."
    
    Job Description: {jd_text}

    Provide a response strictly in this format:
    Job Summary: <One-line summary>
    Responsibilities: - <Responsibility 1>\n- <Responsibility 2>\n...
    Eligibility: - <Qualification 1>\n- <Qualification 2>\n...
    Skills and Technologies: - <Skill 1>\n- <Skill 2>\n...
    Preferred Qualifications: - <Qualification 1>\n- <Qualification 2>\n...
    """

# ✅ Run API Call (Optimized for Single Call)
def run_combined_agent(jd_text):
    jd_text = truncate_text(jd_text)
    try:
        messages = [
            {"role": "system", "content": "You are an AI specialized in job description analysis."},
            {"role": "user", "content": generate_combined_prompt(jd_text)}
        ]

        print("🔎 Sending request to Kluster AI...")
        completion = kluster_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=messages,
            max_tokens=4000,
            temperature=0.3,
            top_p=1,
            timeout=30
        )

        print("✅ Raw API Response:", completion.choices[0].message.content)
        return parse_response(completion.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

# ✅ Parse the Response
def parse_response(response_content):
    result = {}
    try:
        lines = response_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("Job Summary:"):
                result["Job Summary"] = line.replace("Job Summary:", "").strip()
            elif line.startswith("Responsibilities:"):
                current_section = "Responsibilities"
                result[current_section] = []
            elif line.startswith("Eligibility:"):
                current_section = "Eligibility"
                result[current_section] = []
            elif line.startswith("Skills and Technologies:"):
                current_section = "Skills and Technologies"
                result[current_section] = []
            elif line.startswith("Preferred Qualifications:"):
                current_section = "Preferred Qualifications"
                result[current_section] = []
            elif current_section and line.startswith("-"):
                result[current_section].append(line[1:].strip())
        
        # Convert list to text where applicable
        for key in result:
            if isinstance(result[key], list):
                result[key] = '\n'.join(result[key])
        
    except Exception as e:
        print(f"❌ Error in parse_response: {e}")
        result['error'] = str(e)

    return result

# ✅ Store in SQLite Database
def store_in_database(result):
    try:
        conn = sqlite3.connect('jobscreening.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_summary TEXT,
            responsibilities TEXT,
            eligibility TEXT,
            technologies TEXT,
            preferred_qualifications TEXT
        )
        ''')

        cursor.execute('''
        INSERT INTO job_descriptions 
        (job_summary, responsibilities, eligibility, technologies, preferred_qualifications) 
        VALUES (?, ?, ?, ?, ?)
        ''', (
            result.get("Job Summary", "N/A"),
            result.get("Responsibilities", "N/A"),
            result.get("Eligibility", "N/A"),
            result.get("Skills and Technologies", "N/A"),
            result.get("Preferred Qualifications", "N/A")
        ))

        conn.commit()
        conn.close()
        print("✅ Result stored successfully.")
    except Exception as e:
        print(f"❌ Error storing result in database: {e}")

# ✅ Display Results in Clean Format
def print_result(result):
    print("\n--- 📄 Summarization Result ---\n")
    
    for key, value in result.items():
        if isinstance(value, str):
            print(f"**{key}**:")
            if '\n' in value:
                for item in value.split('\n'):
                    print(f"  • {item.strip()}")
            else:
                print(f"  {value.strip()}")
        else:
            print(f"{key}: {value}")
        print("\n" + "-" * 50)

# ✅ Summarize Job Description Function
def summarize_job_description(jd_text):
    print("🔎 Starting Job Description Summarization...")
    
    # Step 1: Extract Initial Data
    result = run_combined_agent(jd_text)

    # Step 2: Store Result in Database
    store_in_database(result)
    
    print("✅ Job Description Summarized Successfully!")
    
    # Step 3: Display Formatted Result
    print_result(result)
    return result

# ✅ Example Usage
if __name__ == "__main__":
    jd_text = """As a Data Scientist at XYZ, you will be responsible for designing, developing, and implementing AI/ML models..."""
    result = summarize_job_description(jd_text)
