import json
import os
from typing import List, Dict, Optional
from openai import OpenAI

class QuestionGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("OpenAI API KEY not available.")
            print("Using Backup question templates.")
        
        # Default profile 
        self.default_profile = {
            "job_role": "Software Engineer",
            "degree": "Computer Science",
            "experience_level": "Entry Level",
            "company_type": "Tech Startup"
        }
        
        # Default number of questions
        self.default_question_count = 5
    
    def generate_questions(
        self, 
        profile: Optional[Dict] = None,
        num_questions: int = 5
    ) -> List[Dict]:
        if profile is None:
            profile = self.default_profile
        
        # Try GPT-4 first
        if self.client:
            try:
                questions = self._generate_with_gpt4(profile, num_questions)
                if questions:
                    print(f"✅ Generated {len(questions)} questions using GPT-4")
                    return questions
            except Exception as e:
                print(f"GPT-4 generation failed: {e}")
                print(" Falling back to template questions...")
        
        # Fallback to template questions
        return self._get_fallback_questions(profile, num_questions)
    
    def _generate_with_gpt4(
        self, 
        profile: Dict, 
        num_questions: int
    ) -> Optional[List[Dict]]:

        job_role = profile.get("job_role", "Software Engineer")
        degree = profile.get("degree", "Computer Science")
        experience = profile.get("experience_level", "Entry Level")
        
        prompt = f"""You are an expert interviewer. Generate {num_questions} interview questions for a candidate with the following profile:

- Job Role: {job_role}
- Degree: {degree}
- Experience Level: {experience}

Requirements:
1. Mix of behavioral (2-3) and technical/role-specific (2-3) questions
2. Progress from easier to harder questions
3. Questions should be realistic and commonly asked in actual interviews
4. Each question should be clear and specific
5. Avoid overly complex or trick questions

Return ONLY a JSON array in this exact format:
[
  {{
    "id": 1,
    "question": "Tell me about yourself and your background.",
    "type": "behavioral",
    "difficulty": "easy"
  }},
  ...
]

Important: Return ONLY the JSON array, no other text or explanation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert interview question generator. Always return valid JSON arrays only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            questions = json.loads(content)

            if isinstance(questions, list) and len(questions) > 0:
                for i, q in enumerate(questions):
                    if "question" not in q:
                        raise ValueError(f"Question {i} missing 'question' field")
                    if "id" not in q:
                        q["id"] = i + 1
                    if "type" not in q:
                        q["type"] = "general"
                    if "difficulty" not in q:
                        q["difficulty"] = "medium"
                
                return questions[:num_questions] 
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse GPT-4 JSON response: {e}")
            return None
        except Exception as e:
            print(f"GPT-4 API error: {e}")
            return None
    
    def _get_fallback_questions(
        self, 
        profile: Dict, 
        num_questions: int
    ) -> List[Dict]:

        job_role = profile.get("job_role", "Software Engineer").lower()
        templates = self._load_question_templates()
        role_questions = templates.get(job_role, templates.get("default", []))
        questions = role_questions[:num_questions]
        if len(questions) < num_questions:
            default_qs = templates.get("default", [])
            remaining = num_questions - len(questions)
            questions.extend(default_qs[:remaining])
        
        print(f"📦 Using {len(questions)} fallback questions for: {job_role}")
        return questions
    
    def _load_question_templates(self) -> Dict[str, List[Dict]]:

        template_path = "data/question_templates/questions.json"

        if os.path.exists(template_path):
            try:
                with open(template_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading templates from file: {e}")
        
        # Hardcoded fallback templates
        return {
            "software engineer": [
                {
                    "id": 1,
                    "question": "Tell me about yourself and your background in software development.",
                    "type": "behavioral",
                    "difficulty": "easy"
                },
                {
                    "id": 2,
                    "question": "Describe a challenging project you worked on. What was your role and how did you overcome the challenges?",
                    "type": "behavioral",
                    "difficulty": "medium"
                },
                {
                    "id": 3,
                    "question": "Explain the difference between object-oriented programming and functional programming. When would you use each?",
                    "type": "technical",
                    "difficulty": "medium"
                },
                {
                    "id": 4,
                    "question": "How do you approach debugging a complex issue in production? Walk me through your process.",
                    "type": "technical",
                    "difficulty": "medium"
                },
                {
                    "id": 5,
                    "question": "Describe a time when you had to work with a difficult team member. How did you handle the situation?",
                    "type": "behavioral",
                    "difficulty": "medium"
                },
                {
                    "id": 6,
                    "question": "What's your experience with version control systems like Git? Can you explain branching strategies?",
                    "type": "technical",
                    "difficulty": "easy"
                },
                {
                    "id": 7,
                    "question": "How do you stay updated with the latest technologies and programming trends?",
                    "type": "behavioral",
                    "difficulty": "easy"
                }
            ],
            "data analyst": [
                {
                    "id": 1,
                    "question": "Tell me about yourself and your experience with data analysis.",
                    "type": "behavioral",
                    "difficulty": "easy"
                },
                {
                    "id": 2,
                    "question": "Describe a time when you used data to solve a business problem. What was your approach?",
                    "type": "behavioral",
                    "difficulty": "medium"
                },
                {
                    "id": 3,
                    "question": "What tools and programming languages are you proficient in for data analysis?",
                    "type": "technical",
                    "difficulty": "easy"
                },
                {
                    "id": 4,
                    "question": "Explain the difference between supervised and unsupervised learning. Give examples.",
                    "type": "technical",
                    "difficulty": "medium"
                },
                {
                    "id": 5,
                    "question": "How do you handle missing or inconsistent data in a dataset?",
                    "type": "technical",
                    "difficulty": "medium"
                }
            ],
            "default": [
                {
                    "id": 1,
                    "question": "Tell me about yourself and why you're interested in this position.",
                    "type": "behavioral",
                    "difficulty": "easy"
                },
                {
                    "id": 2,
                    "question": "What are your greatest strengths and how do they relate to this role?",
                    "type": "behavioral",
                    "difficulty": "easy"
                },
                {
                    "id": 3,
                    "question": "Describe a challenging situation you faced and how you resolved it.",
                    "type": "behavioral",
                    "difficulty": "medium"
                },
                {
                    "id": 4,
                    "question": "Where do you see yourself in 5 years?",
                    "type": "behavioral",
                    "difficulty": "easy"
                },
                {
                    "id": 5,
                    "question": "Why should we hire you for this position?",
                    "type": "behavioral",
                    "difficulty": "medium"
                }
            ]
        }
    
    def save_questions_to_file(
        self, 
        questions: List[Dict], 
        filename: str = "interview_questions.json"
    ):
        """
        Save generated questions to file
        
        Args:
            questions: List of question dictionaries
            filename: Output filename
        """
        output_dir = "data/Questions"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(questions, f, indent=2)
        
        print(f"✅ Questions saved to: {filepath}")


# Example usage
if __name__ == "__main__":
    # Initialize generator
    generator = QuestionGenerator()
    
    # Generate questions with default profile
    print("🎯 Generating interview questions...\n")
    questions = generator.generate_questions()
    
    # Display questions
    print("\n📋 Generated Questions:\n")
    for q in questions:
        print(f"Q{q['id']}: {q['question']}")
        print(f"   Type: {q['type']} | Difficulty: {q['difficulty']}\n")
    
    # Save to file
    generator.save_questions_to_file(questions)