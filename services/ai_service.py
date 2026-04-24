import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
# Ensure your Pydantic model is imported so the config can use it!
from schemas.analysis import AIFeedback 
import time

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class SkillGapAnalyzer:
    @staticmethod
    def analyze_resume(resume_text: str, job_description: str) -> dict:
        model = genai.GenerativeModel('gemini-2.5-flash')

        config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=AIFeedback
        )

        prompt = f"""
        You are a Senior Technical Recruiter with 15+ years of experience evaluating candidates 
        for software engineering roles. Your assessments are honest, precise, and actionable.

        STEP 1 — VALIDATION (CRITICAL FIRST STEP):
        Carefully read the text provided as the "Job Description".
        Determine if it is actually a valid job posting.
        
        A valid job description typically contains: Job title, required skills/qualifications, and responsibilities.
        It is NOT valid if it is: A resume, a company "About Us" page, a news article, gibberish, or fewer than 3 sentences.

        - If it is VALID: set "is_valid_jd" to true, "validation_error" to null, and proceed with the full analysis.
        - If it is INVALID: set "is_valid_jd" to false, provide a friendly 1-sentence "validation_error" (e.g., "This looks like a company page, not a job posting. Please paste an actual job listing."), and fill the rest of the required fields with dummy data (e.g., match_percentage: 0, job_title: "N/A", company: "N/A", empty arrays).

        ---

        STEP 2 — ANALYSIS INSTRUCTIONS (If valid):

        1. **job_title**: Extract the exact job title from the Job Description. 
           If not clearly stated, infer it. Never return null — default to "Software Engineer".

        2. **company**: Extract the company name from the Job Description.
           If not found, return "Unknown Company".

        3. **match_percentage**: An integer from 0 to 100.
           - 80-100: Candidate meets almost all requirements including experience level
           - 60-79: Strong foundation, missing a few non-critical skills
           - 40-59: Partial match, missing some important requirements
           - 0-39: Significant gaps in experience, skills, or domain knowledge
           Be strict and realistic. A fresh graduate applying for a 5-year role should not exceed 40.

        4. **executive_summary**: A 3-4 sentence honest and professional paragraph.
           - Sentence 1: Overall impression and strongest qualities
           - Sentence 2: The most critical gap(s) holding them back
           - Sentence 3: Specific actionable advice on how to improve their fit
           - Tone: Like a mentor, not a rejection letter. Encouraging but truthful.

        5. **matched_skills**: A flat list of skill/technology/experience NAMES that the 
           candidate clearly demonstrates AND the job requires.
           - Only include skills relevant to the job description
           - Keep each item short: "Python", "PostgreSQL", "REST APIs", "Agile"
           - Maximum 10 items. Quality over quantity.

        6. **partial_skills**: A flat list of skill NAMES where the candidate has SOME 
           relevant experience but not at the level or depth the job requires.
           - Example: Job requires Django expertise, candidate only used Flask/FastAPI
           - Example: Job needs 5 years experience, candidate has 1 year
           - Keep each item short. Maximum 5 items.

        7. **missing_skills**: The top 3 most critical skills or experiences that are 
           required by the job but completely absent from the candidate's profile.
           - Prioritize by importance to the role
           - Each item needs both a "skill" name and an honest "reason" explaining the gap
           - "reason" should be 1-2 sentences max, specific to THIS candidate and THIS job

        ---

        EXAMPLE OUTPUT (use this only as a guide for structure, tone, and formatting — never copy these example values):

        {{
            "is_valid_jd": true,
            "validation_error": null,
            "job_title": "Python Engineer",
            "company": "Acme Fintech",
            "match_percentage": 30,
            "executive_summary": "Muhammad demonstrates a solid foundation in Python and backend development through his academic projects and internship experience. However, he is a fresh graduate and falls significantly short of the required 4-5 years of professional experience, which is the primary barrier for this role. To strengthen his candidacy, Muhammad should focus on gaining practical cloud infrastructure experience with AWS and Docker, and seek out fintech-adjacent projects or certifications to build domain credibility.",
            "matched_skills": ["Python", "SQL", "PostgreSQL", "REST APIs", "FastAPI", "Git"],
            "partial_skills": ["Backend Development", "Database Management"],
            "missing_skills": [
                {{
                    "skill": "Professional Experience (4-5 years)",
                    "reason": "The role explicitly requires at least 4-5 years as a Software Developer. Muhammad is a fresh graduate with only a 3-month internship, which does not meet this threshold."
                }},
                {{
                    "skill": "Fintech Domain Knowledge",
                    "reason": "The job emphasizes fintech processes and cards issuing/processing knowledge. There is no evidence of fintech exposure in the candidate's background."
                }},
                {{
                    "skill": "Cloud & DevOps (AWS, Docker, Kubernetes, Terraform)",
                    "reason": "The tech stack requires hands-on experience with modern cloud and deployment tools. The candidate's resume shows no experience with any of these technologies."
                }}
            ]
        }}

        ---

        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}
        """

        # --- NEW RETRY LOGIC STARTS HERE ---
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt, generation_config=config)
                
                # Safely load the text
                result = json.loads(response.text)
                # # --- ENHANCED SAFETY NET ---
                # # 1. Ensure the core arrays always exist even if the AI drops them
                # if "matched_skills" not in result or result["matched_skills"] is None:
                #     result["matched_skills"] = []
                # if "partial_skills" not in result or result["partial_skills"] is None:
                #     result["partial_skills"] = []
                # if "missing_skills" not in result or result["missing_skills"] is None:
                #     result["missing_skills"] = []
                    
                # # 2. Ensure every missing skill has a 'reason' field
                # if isinstance(result["missing_skills"], list):
                #     for skill_obj in result["missing_skills"]:
                #         if "reason" not in skill_obj:
                #             skill_obj["reason"] = "This skill was requested but not clearly demonstrated in the resume."
                # # ------------------------------------------
                return result
                
            except ResourceExhausted as e:
                # If we've tried 3 times and still hit the limit, throw a specific error
                if attempt == max_retries - 1:
                    print(f"Gemini API Error (Rate Limit Final): {e}")
                    raise ValueError("RATE_LIMIT_EXCEEDED")
                
                # Otherwise, pause for 15 seconds and try again
                print(f"⚠️ Quota hit! Waiting 15 seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(15) 
                
            except Exception as e:
                # This catches API timeouts, quota limits, or major generation failures
                print(f"Gemini API Error: {e}")
                raise ValueError(f"Failed to generate AI analysis: {str(e)}")




# class SkillGapAnalyzer:
#     @staticmethod
#     def analyze_resume(resume_text: str, job_description: str) -> dict:
        
#         # --- MOCK DATA FOR UI TESTING ---
#         time.sleep(4.5) # Lets you watch the UI loading animation
        
#         return {
#             "is_valid_jd": True,
#             "validation_error": None,
#             "job_title": "Backend Python Developer",
#             "company": "Fintech Corp",
#             "match_percentage": 78,
#             "executive_summary": "This is a perfect, clean test response to verify your frontend UI is rendering correctly!",
#             "matched_skills": ["Python", "FastAPI", "SQL"],
#             "partial_skills": ["Docker"],
#             "missing_skills": [
#                 {"skill": "Django", "reason": "The JD specifically asks for Django, but the resume only lists FastAPI."},
#                 {"skill": "Fintech Experience", "reason": "Requires 4-5 years in financial systems processing."}
#             ]
#         }