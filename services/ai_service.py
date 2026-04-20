import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class SkillGapAnalyzer:
    @staticmethod
    def analyze_resume(resume_text: str, job_description: str) -> dict:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        prompt = f"""
        You are an expert Technical Recruiter. 
        Compare the following Candidate Resume to the Job Description.
        
        1. Provide a rough "match_percentage" from 0 to 100 based on how well they fit the core requirements.
        2. Write a friendly, professional, but honest 2-3 sentence "executive_summary" explaining their overall fit.
        3. Identify the top 3 missing skills or experiences the candidate needs.
        
        You must strictly follow this JSON format:
        {{
            "match_percentage": 75,
            "executive_summary": "Muhammad has a strong foundation in Python and backend development, but lacks the 4-5 years of required Fintech experience. To become a strong fit, he needs to focus on cloud deployment tools and industry-specific knowledge.",
            "missing_skills": [
                {{
                    "skill": "Name of skill",
                    "reason": "Brief reason why it's missing or falls short"
                }}
            ]
        }}
        
        RESUME:
        {resume_text}
        
        JOB DESCRIPTION:
        {job_description}
        """
        
        response = model.generate_content(prompt, generation_config=config)
        return json.loads(response.text)