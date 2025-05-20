import pdfplumber
import io
import base64
from openai import OpenAI
from app.config.settings import settings
import json

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Define the comprehensive resume parsing prompt
resume_prompt = """
You are an HR assistant designed to extract structured candidate information from resumes and format it in JSON. 
Given a resume text, extract and classify the following fields:
1. Personal Information:
    - FullName
    - PhoneNumber:
        - Number
        - ISDCode (predict if missing)
        - OriginalNumber
        - FormattedNumber
        - Type (mobile, landline)
        - Location (predict from ISD if missing)
    - Email
    - Linkedin
    - Github
    - Other Links (excluding LinkedIn, GitHub, Email)
    - Country (of residence)
    - Nationalities (predict if missing)
    - Date of Birth or Age
    - Gender
    - Marital Status
    - Languages (leave blank if undetectable)
    - Current Job Title (as stated, not inferred)
2. Alternance Check:
    - If any variation or misspelling of 'Alternance' is found in the latest experience → override Job Title with "Alternance"
3. Jobs (suggest relevant roles based on resume)
    - Return a list of job titles matching the profile
4. Degrees:
    For each degree extract:
        - DegreeName
        - NormalizeDegree
        - Specialization
        - Date
        - CountryOrInstitute
5. Certifications:
    For each cert extract:
        - CertificationName
        - IssuingOrganization
        - IssueDate
6. Hard Skills:
    - Max 20 most relevant technical skills
7. Soft Skills:
    - Max 20 most relevant soft skills
8. Professional Experience:
    Include only relevant experiences based on:
        - Current role or career goal
        - Technical skills/industry
        - Not internships or non-professional roles
    For each:
        - Job Title
        - Company
        - Location
        - Start Date
        - End Date (handle "present", "en cours", etc. as "PRESENT")
        - Duration
        - Responsibilities (original text/bullets)
        - Achievements (with metrics)
        - Tools/Technologies used
        - Team Size
        - Relevance Score (High, Medium, Low, Skip)
9. Projects:
    For each:
        - ProjectName
        - Description
        - TechnologiesUsed (array)
        - Role
        - Period
        - URL (if available)
10. Awards and Publications (Prix et Publications):
    For each:
        - Type (Award/Publication)
        - Title
        - Description
        - Date
        - Publisher/Issuer
        - URL (if available)

For any field not found or undetectable, use empty strings or empty arrays.
Return the result in the following JSON structure:
{
    "CandidateInfo": {
        "FullName": "",
        "PhoneNumber": {
            "Number": "",
            "ISDCode": "",
            "OriginalNumber": "",
            "FormattedNumber": "",
            "Type": "",
            "Location": ""
        },
        "Email": "",
        "Linkedin": "",
        "Github": "",
        "OtherLinks": [],
        "Country": "",
        "Nationalities": [],
        "DateOfBirthOrAge": "",
        "Gender": "",
        "MaritalStatus": "",
        "Languages": [],
        "CurrentJobTitle": ""
    },
    "SuggestedJobs": [],
    "Degrees": [
        {
            "DegreeName": "",
            "NormalizeDegree": "",
            "Specialization": "",
            "Date": "",
            "CountryOrInstitute": ""
        }
    ],
    "Certifications": [
        {
            "CertificationName": "",
            "IssuingOrganization": "",
            "IssueDate": ""
        }
    ],
    "HardSkills": [],
    "SoftSkills": [],
    "ProfessionalExperience": [
        {
            "JobTitle": "",
            "Company": "",
            "Location": "",
            "StartDate": "",
            "EndDate": "",
            "Duration": "",
            "Responsibilities": [],
            "Achievements": [],
            "ToolsAndTechnologies": [],
            "TeamSize": "",
            "RelevanceScore": ""
        }
    ],
    "Projects": [
        {
            "ProjectName": "",
            "Description": "",
            "TechnologiesUsed": [],
            "Role": "",
            "Period": "",
            "URL": ""
        }
    ],
    "AwardsAndPublications": [
        {
            "Type": "",
            "Title": "",
            "Description": "",
            "Date": "",
            "PublisherOrIssuer": "",
            "URL": ""
        }
    ]
}
"""

def parse_cv(binary_data: bytes) -> dict:
    try:
        pdf_text = ""
        try:
            with pdfplumber.open(io.BytesIO(binary_data)) as pdf:
                for page in pdf.pages:
                    pdf_text += page.extract_text() + "\n"
            pdf_text = pdf_text.strip()
            print(f"Successfully extracted text from PDF: {len(pdf_text)} characters")
        except Exception as pdf_error:
            print(f"PDF extraction error: {str(pdf_error)}")
            return {
                "CandidateInfo": {
                    "FullName": "Not Provided",
                    "Email": "Not Provided",
                    "CurrentJobTitle": "Not Provided"
                }
            }

        try:
            if not settings.OPENAI_API_KEY:
                print("OpenAI API key is not set")
                return {
                    "CandidateInfo": {
                        "FullName": "Not Provided",
                        "Email": "Not Provided",
                        "CurrentJobTitle": "Not Provided"
                    }
                }
                
            # Using the comprehensive resume parsing prompt
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Consider using gpt-3.5-turbo for better extraction accuracy
                messages=[
                    {"role": "system", "content": resume_prompt},
                    {"role": "user", "content": pdf_text}
                ],
                temperature=0.1,
                max_tokens=4000  # Increased token limit for more comprehensive response
            )
            
            # Step 1: Parse the response and add debug statements
            result = json.loads(response.choices[0].message.content)
            print(f"Successfully parsed CV using OpenAI")
            print(f"Professional Experience count: {len(result.get('ProfessionalExperience', []))}")
            if result.get('ProfessionalExperience', []):
                print(f"First experience: {result.get('ProfessionalExperience', [])[0]}")
            else:
                print(f"No ProfessionalExperience data found in the parsed result")
            return result
        except Exception as openai_error:
            print(f"OpenAI API error: {str(openai_error)}")
            return {
                "CandidateInfo": {
                    "FullName": "Not Provided",
                    "Email": "Not Provided",
                    "CurrentJobTitle": "Not Provided"
                }
            }
    except Exception as e:
        print(f"Unexpected error in parse_cv: {str(e)}")
        return {
            "CandidateInfo": {
                "FullName": "Not Provided",
                "Email": "Not Provided",
                "CurrentJobTitle": "Not Provided"
            }
        }