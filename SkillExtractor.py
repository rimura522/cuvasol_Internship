import fitz
import re
import csv
import mysql.connector
import os

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="2711",
    database="skills",
    #auth_plugin='caching_sha2_password'  # Explicitly specify plugin
)

cursor = mydb.cursor()

def extract_name(file_path):
    """Extracts the name from a file path of the format resume/name_resume.pdf."""

    pattern = r"resumes/([^_]+)_resume\.pdf"

    # Search for the pattern in the file path
    match = re.search(pattern, file_path)
    if match:
        return match.group(1)  # Extract the captured name (group 1)
    else:
        return "No Name"  # Return None if no match is found

def extract_skills(resume_path):
    skills = []
    languages = []

    with fitz.open(resume_path) as doc:

        for page in enumerate(doc):
            text = page.get_text().upper() 

            match = re.search(fr"SKILLS(.?)(?=[\n]{{2,}}|EDUCATION|EXPERIENCE|LANGUAGES|HOBBIES|CERTIFICATIONS|SUMMARY|CERTIFICATES|INTERESTS|PROFILES|PROJECTS\Z)", text, re.DOTALL)
            if match:
                    skills_section = match.group(1)
                    extracted_skills = re.findall(r"([a-zA-Z0-9+\-][a-zA-Z0-9+\- ][a-zA-Z0-9+\-])", skills_section)

                    skills.extend(skill for skill in extracted_skills if len(skill) < 30)


            match = re.search(fr"LANGUAGES(.*?)(?=[\n]{{2,}}|EDUCATION|EXPERIENCE|HOBBIES|CERTIFICATIONS|CERTIFICATES|SUMMARY|INTERESTS|PROFILES|PROJECTS\Z)", text, re.DOTALL)
            if match:
                languages_section = match.group(1)
                languages = re.findall(r"([a-zA-Z]+)", languages_section)

    return skills + languages

def addtoDB(array):

    applicant_name = array[0]  # Extract name
    skills_list = array[1:]     # Extract skills
    skills_string = ','.join(skills_list)  # Create comma-separated string

    sql = "INSERT INTO skills (ApplicantName, skills) VALUES (%s, %s)"
    val = (applicant_name, skills_string)
    cursor.execute(sql, val)

    # Commit Changes and Close Connection
    mydb.commit()
    print(cursor.rowcount, "record(s) inserted.")
    mydb.close()



def main():  

    resume_path = "resumes/rahul_resume.pdf"
    DBfile="skillsfile.csv"
    extracted_skills = extract_skills(resume_path)
    name=extract_name(resume_path)
    name=name.upper()
    extracted_skills.insert(0,name)

    addtoDB(extracted_skills)

if __name__ == "__main__":
    main()
