from flask import Flask, request, jsonify, render_template, send_from_directory
import mysql.connector
import fitz
import os
import re

app = Flask(__name__)
UPLOAD_FOLDER = r'D:\rahul1\internship(cuvasol)\Cooked\Cooked\HellaCooked\resumes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Asqw123$",
        database="skills",
    )
    return conn

def extract_keywords_from_text(text):
    text = text.upper()
    keywords = re.findall(r'\b\w+\b', text)
    stopwords = set(['AND', 'OR', 'THE', 'A', 'AN', 'OF', 'TO', 'IN', 'FOR', 'WITH', 'ON', 'AT', 'BY', 'FROM', 'AS', 'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN', 'BEING'])
    keywords = [kw for kw in keywords if kw not in stopwords and len(kw) > 1]
    return keywords

def extract_skills(resume_path):
    skills = []
    languages = []

    with fitz.open(resume_path) as doc:
        for page in doc:
            text = page.get_text().upper()

            # Extract skills
            skills_match = re.search(r'SKILLS(.*?)(?:\n\n|\nEDUCATION|\nEXPERIENCE|\nLANGUAGES|\nHOBBIES|\nCERTIFICATIONS|\nSUMMARY|\nCERTIFICATES|\nINTERESTS|\nPROFILES|\nPROJECTS|$)', text, re.DOTALL)
            if skills_match:
                skills_section = skills_match.group(1)
                extracted_skills = re.findall(r'\b[A-Z0-9+\-][A-Z0-9+\- ]*[A-Z0-9+\-]\b', skills_section)
                skills.extend(skill.strip() for skill in extracted_skills if len(skill) < 30)

            # Extract languages
            languages_match = re.search(r'LANGUAGES(.*?)(?:\n\n|\nEDUCATION|\nEXPERIENCE|\nHOBBIES|\nCERTIFICATIONS|\nSUMMARY|\nCERTIFICATES|\nINTERESTS|\nPROFILES|\nPROJECTS|$)', text, re.DOTALL)
            if languages_match:
                languages_section = languages_match.group(1)
                extracted_languages = re.findall(r'\b[A-Z]+\b', languages_section)
                languages.extend(lang.strip() for lang in extracted_languages if len(lang) < 30)

    return skills + languages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'name' not in request.form:
        return jsonify({'error': 'No file or name part'})
    file = request.files['file']
    
    name = request.form['name']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = f"{name}_resume.pdf"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        skills = extract_skills(file_path)
        save_skills(name, skills)
        return jsonify({'skills': skills})
    else:
        return jsonify({'error': 'Invalid file format'})


@app.route('/view_table', methods=['GET'])
def view_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ApplicantName, skills FROM skills')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    table_data = {
        "columns": ["Applicant Name", "Skills"],
        "data": []
    }
    
    for row in rows:
        name = row[0]
        skills = row[1].split(', ')
        #rating = request.args.get('rating', 0)
        table_data["data"].append({"Applicant Name": name, "Skills": ', '.join(skills)})

    #table_data["data"].sort(key=lambda x: x["Rating"], reverse=True)

    return jsonify(table_data)

@app.route('/match_job_description', methods=['POST'])
def match_job_description():
    job_description = request.form.get('description', '')
    if not job_description:
        return jsonify({'error': 'No job description provided'})

    job_keywords = extract_keywords_from_text(job_description)

    

    if not job_keywords:
        return jsonify({'error': 'No keywords extracted from job description'})

    conn = get_db_connection()
    cursor = conn.cursor()

    like_clauses = " OR ".join(["skills LIKE %s"] * len(job_keywords))
    query = f"SELECT ApplicantName, skills FROM skills WHERE {like_clauses}"
    params = tuple(f"%{kw}%" for kw in job_keywords)

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        cursor.close()
        conn.close()
    
    matching_resumes = []
    for row in rows:
        name = row[0]
        skills = row[1].split(', ')
        matched_skills = set(job_keywords) & set(skills)
        rating = len(matched_skills)/len(job_keywords) * 100
        matching_resumes.append({"name": name, "skills": ', '.join(skills), "rating": rating})

    matching_resumes.sort(key=lambda x: x["rating"], reverse=True)

    return jsonify({'matching_resumes': matching_resumes})

@app.route('/view_resume/<name>', methods=['GET'])
def view_resume(name):
    resume_filename = f"{name}_resume.pdf"
    return send_from_directory(app.config['UPLOAD_FOLDER'], resume_filename)

def save_skills(name, skills):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO skills (ApplicantName, skills) VALUES (%s, %s)', (name, ', '.join(skills)))
    conn.commit()
    cursor.close()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

if __name__ == '__main__':
    app.run(debug=True)
