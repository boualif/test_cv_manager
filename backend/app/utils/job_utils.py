import json
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI
from app.config.settings import settings
import logging
import re

logger = logging.getLogger(__name__)

def extract_job_fields(description: str) -> Tuple[str, Optional[str], str]:
    """
    Extract job title, competence_phare (key skill), and job type from a job description using OpenAI.
    IMPORTANT: This function maintains the original return type (tuple) for backward compatibility.
    For comprehensive data, use extract_comprehensive_job_data() instead.
    
    Args:
        description (str): The job description text
        
    Returns:
        Tuple[str, Optional[str], str]: A tuple containing the job title, competence_phare, and job_type_etiquette
    """
    try:
        # Get comprehensive data first (will be stored for later use)
        data = extract_comprehensive_job_data(description)
        
        # Extract the three required fields for backward compatibility
        title = data.get("title", "")
        if not title or len(title) > 255:
            title = get_fallback_title(description)
            
        competence_phare = data.get("competence_phare")
        
        job_type = data.get("job_type_etiquette", "technique")
        if job_type not in ["technique", "fonctionnel", "technicofonctionnel"]:
            job_type = "technique"  # Default fallback
        
        # Log the extraction
        logger.info(f"Extracted title: '{title}', competence_phare: '{competence_phare}', job_type: '{job_type}'")
        
        # Return just the tuple for backward compatibility
        return title, competence_phare, job_type
    
    except Exception as e:
        logger.error(f"Error extracting job fields with OpenAI: {str(e)}")
        # Fallback: Use basic extraction
        title = get_fallback_title(description)
        return title, None, "technique"  # Default job type as fallback


def extract_comprehensive_job_data(description: str) -> Dict[str, Any]:
    """
    Extract comprehensive job information including skills and contract details.
    
    Args:
        description (str): The job description text
        
    Returns:
        Dict[str, Any]: A dictionary containing all extracted job details
    """
    try:
        # Get the basic job fields (title, competence_phare, job_type)
        basic_data = extract_basic_job_fields(description)
        
        # Extract detailed skills
        skills_data = extract_job_skills(description)
        
        # Extract French contract details
        contract_data = extract_french_contract_details(description)
        
        # Combine all data into one comprehensive dictionary
        result = {
            **basic_data,
            **skills_data, 
            **contract_data
        }
        
        return result
    except Exception as e:
        logger.error(f"Error extracting comprehensive job data: {str(e)}")
        # Provide basic fallback
        title = get_fallback_title(description)
        return {
            "title": title,
            "competence_phare": None,
            "job_type_etiquette": "technique",
            "technical_skills": [],
            "soft_skills": [],
            "other_requirements": []
        }


def extract_basic_job_fields(description: str) -> Dict[str, Any]:
    """
    Extract basic job information (title, competence_phare, job type) from a job description.
    
    Args:
        description (str): The job description text
        
    Returns:
        Dict[str, Any]: A dictionary containing basic job fields
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Use a more detailed prompt to improve extraction accuracy
        prompt = (
            "Analyze the following job description and extract:\n"
            "1. The job title: A concise professional title for the position (e.g., 'Senior Python Developer', 'Marketing Manager').\n"
            "2. The primary skill (competence_phare): The most important technical or soft skill required for this position. "
            "This should be a single skill, not a list (e.g., 'Python', 'Leadership', 'Machine Learning').\n"
            "3. The job type (job_type_etiquette): Classify the job as one of these three categories:\n"
            "   - 'technique': Technical roles focused on implementation, coding, or technical operations\n"
            "   - 'fonctionnel': Functional roles focused on business analysis, processes, or operations\n"
            "   - 'technicofonctionnel': Hybrid roles requiring both technical and functional skills\n"
            "4. job_category: A general category (e.g., 'IT', 'Marketing', 'Finance')\n"
            "5. experience_level: Junior, Mid-level, Senior, or Executive\n\n"
            "If no clear primary skill can be identified, return null for competence_phare.\n"
            "Return the result as JSON with 'title', 'competence_phare', 'job_type_etiquette', 'job_category', and 'experience_level' fields.\n\n"
            f"Description:\n{description}"
        )

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Can be upgraded to "gpt-4" for better accuracy if needed
            messages=[
                {"role": "system", "content": "You are a specialized job description analyzer that extracts key information accurately."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower temperature for more consistent results
        )

        # Parse the result
        result = response.choices[0].message.content
        parsed = json.loads(result)
        
        # Extract and validate title
        title = parsed.get("title", "")
        if not title or len(title) > 255:
            # Fallback: Use first line or first sentence
            title = get_fallback_title(description)
            parsed["title"] = title
            
        return parsed
    
    except Exception as e:
        logger.error(f"Error extracting basic job fields with OpenAI: {str(e)}")
        # Fallback
        title = get_fallback_title(description)
        return {
            "title": title,
            "competence_phare": None,
            "job_type_etiquette": "technique",
            "job_category": "Other",
            "experience_level": "Mid-level"
        }


def get_fallback_title(description: str) -> str:
    """
    Generate a fallback title when OpenAI extraction fails
    
    Args:
        description (str): The job description
        
    Returns:
        str: A title extracted from the first line/sentence
    """
    # Try to get first line
    lines = description.split('\n')
    first_line = lines[0].strip() if lines else ""
    
    # If first line is empty or too long, try first sentence
    if not first_line or len(first_line) > 255:
        # Try to get first sentence
        sentences = re.split(r'[.!?]', description)
        first_sentence = sentences[0].strip() if sentences else ""
        
        if first_sentence and len(first_sentence) <= 255:
            return first_sentence
    
    # If first line is suitable, use it
    if first_line and len(first_line) <= 255:
        return first_line
    
    # Last resort: Just use "Offre d'emploi" with truncated description
    if description:
        return f"Offre d'emploi: {description[:50]}..." if len(description) > 50 else f"Offre d'emploi: {description}"
    else:
        return "Offre d'emploi"


def extract_job_skills(description: str) -> Dict[str, List[str]]:
    """
    Extract detailed technical and soft skills from a job description.
    
    Args:
        description (str): The job description text
        
    Returns:
        Dict[str, List[str]]: A dictionary containing lists of identified skills
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = (
            "You are given a job description (in any language). Extract and organize all relevant skills into the following categories:\n\n"
            "1. **Technical Skills (Hard Skills)** – Include all tools, technologies, programming languages, domain-specific methodologies, certifications, or systems mentioned.\n"
            "2. **Soft Skills (Behavioral/Interpersonal Skills)** – Include teamwork, communication, adaptability, leadership, problem-solving, etc.\n"
            "3. **Other Requirements** – Include education level, years of experience, language requirements, certifications, or specific domain knowledge.\n\n"
            "Return your output as a JSON object with three arrays: 'technical_skills', 'soft_skills', and 'other_requirements'.\n"
            "Keep tool or technology names in their original form. You may translate general category titles or descriptions into English for clarity.\n\n"
            f"Job Description:\n{description}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a specialized skill extractor for job descriptions in any language."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        result = response.choices[0].message.content
        parsed = json.loads(result)
        
        # Ensure the required lists exist
        if "technical_skills" not in parsed:
            parsed["technical_skills"] = []
        if "soft_skills" not in parsed:
            parsed["soft_skills"] = []
        if "other_requirements" not in parsed:
            parsed["other_requirements"] = []
            
        logger.info(f"Extracted {len(parsed['technical_skills'])} technical skills, {len(parsed['soft_skills'])} soft skills, {len(parsed['other_requirements'])} other requirements")
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error extracting job skills: {str(e)}")
        return {
            "technical_skills": [],
            "soft_skills": [],
            "other_requirements": []
        }


def extract_french_contract_details(description: str) -> Dict[str, Any]:
    """
    Extract French-specific contract details from job descriptions.
    
    Args:
        description (str): The job description text
        
    Returns:
        Dict[str, Any]: A dictionary of French contract details
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = (
            "From the following French job description, extract these specific contract details:\n\n"
            "1. contract_type: Type of contract (CDI, CDD, stage, alternance, etc.)\n"
            "2. salary_range: Any salary information (min-max or fixed amount)\n"
            "3. work_location: Work location information, including remote/hybrid options\n"
            "4. working_hours: Information about working hours or schedule\n"
            "5. start_date: When the position starts, if mentioned\n"
            "6. congés_payés: Information about paid leave\n"
            "7. transportation_benefits: Any benefits related to transportation\n"
            "8. meal_benefits: Tickets restaurant or food-related benefits\n"
            "9. benefits: A list of all benefits mentioned (as an array)\n\n"
            "Return the result as a JSON object with these fields. Set values to null if not mentioned.\n\n"
            f"Description:\n{description}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a specialized French job contract analyzer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        result = response.choices[0].message.content
        parsed = json.loads(result)
        
        logger.info(f"Extracted French contract details: contract_type: {parsed.get('contract_type')}")
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error extracting French contract details: {str(e)}")
        return {
            "contract_type": None,
            "salary_range": None,
            "work_location": None,
            "working_hours": None,
            "start_date": None,
            "congés_payés": None,
            "transportation_benefits": None,
            "meal_benefits": None,
            "benefits": []
        }


def extract_detailed_job_fields(description: str) -> Dict[str, Any]:
    """
    Extract more detailed job information beyond just title and competence_phare.
    This function provides comprehensive job data while maintaining backward compatibility.
    
    Args:
        description (str): The job description
        
    Returns:
        Dict: A dictionary containing extracted job details
    """
    # Simply call the comprehensive extraction function
    return extract_comprehensive_job_data(description)