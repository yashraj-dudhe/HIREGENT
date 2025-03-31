from flask import Flask, render_template, request
from testsm import summarize_job_description

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])   
def index():
    if request.method == 'POST':
        try:
            jd_text = request.form['job_description']
            print("Job Description Input:", jd_text)  # Debug input
            result = summarize_job_description(jd_text)
            print("Summarization Result:", result)  # Debug output
            return render_template('output.html', result=result)
        except Exception as e:
            print("Error in POST request:", e)  # Debug errors
            return render_template('output.html', result={"error": "An error occurred while processing the job description."})
    print("Rendering input.html")  # Debug rendering
    return render_template('input.html')

if __name__ == "__main__":
    app.run(debug=True)
