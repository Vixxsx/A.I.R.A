import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class QuestionGenerator:
    def __init__(self):

        self.api_key = os.getenv('GROK_API_KEY')
        
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.x.ai/v1"
                )
                print("✅ Question Generator initialized (Grok API)")
                self.use_ai = True
            except Exception as e:
                print(f"⚠️  Grok API unavailable: {e}")
                print("   Using template questions instead")
                self.client = None
                self.use_ai = False
        else:
            print("⚠️  GROK_API_KEY not found in environment")
            print("   Using template questions")
            self.client = None
            self.use_ai = False
        
        # Template questions as fallback
        self.template_questions = self._load_templates()
    
    
    def generate_questions(
        self,
        profile: Optional[Dict] = None,
        num_questions: int = 5
    ) -> List[Dict]:
        """
        Generate interview questions
        
        Args:
            profile: {
                'job_role': str,
                'degree': str,
                'experience_level': str,
                'company_type': str
            }
            num_questions: Number of questions to generate
        
        Returns:
            List of question dictionaries
        """
        # Default profile
        if profile is None:
            profile = {
                'job_role': 'Software Engineer',
                'degree': 'Computer Science',
                'experience_level': 'Entry Level',
                'company_type': 'Tech Startup'
            }
        
        if self.use_ai and self.client:
            try:
                return self._generate_with_grok(profile, num_questions)
            except Exception as e:
                print(f"⚠️  Grok generation failed: {e}")
                print("   Falling back to templates")
                return self._generate_from_templates(profile, num_questions)
        else:
            return self._generate_from_templates(profile, num_questions)
    
    
    def _generate_with_grok(
        self,
        profile: Dict,
        num_questions: int
    ) -> List[Dict]:
        """Generate questions using Grok API"""
        
        print(f"🤖 Generating {num_questions} questions with Grok...")
        
        prompt = f"""Generate {num_questions} interview questions for:
- Job Role: {profile.get('job_role', 'Software Engineer')}
- Degree: {profile.get('degree', 'Computer Science')}
- Experience Level: {profile.get('experience_level', 'Entry Level')}
- Company Type: {profile.get('company_type', 'Tech Startup')}

Requirements:
1. Mix of technical, behavioral, and situational questions
2. Appropriate difficulty for {profile.get('experience_level', 'Entry Level')}
3. Relevant to {profile.get('job_role', 'Software Engineer')} role

Return ONLY a JSON array of objects with this structure:
[
  {{
    "id": 1,
    "question": "question text here",
    "category": "technical/behavioral/situational",
    "difficulty": "easy/medium/hard",
    "time_limit": 120
  }}
]

Do not include any markdown formatting or code blocks. Return only the raw JSON array."""

        try:
            response = self.client.chat.completions.create(
                model="Grok-2-1212",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer. Generate clear, relevant interview questions. Return only valid JSON, no markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            content = content.strip()
            
            # Parse JSON
            questions = json.loads(content)
            
            print(f"✅ Generated {len(questions)} questions with Grok")
            return questions
        
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Grok response: {e}")
            print(f"   Response: {content[:200]}...")
            raise
        
        except Exception as e:
            print(f"❌ Grok API error: {e}")
            raise
    
    
    def _generate_from_templates(
        self,
        profile: Dict,
        num_questions: int
    ) -> List[Dict]:
        """Generate questions from templates"""
        
        print(f"📝 Generating {num_questions} questions from templates...")
        
        job_role = profile.get('job_role', 'Software Engineer')
        experience = profile.get('experience_level', 'Entry Level')
        
        # Get relevant templates
        all_questions = []
        
        if job_role.lower() in ['software engineer', 'developer', 'programmer']:
            all_questions.extend(self.template_questions['technical'])
        
        all_questions.extend(self.template_questions['behavioral'])
        all_questions.extend(self.template_questions['situational'])
        
        # Adjust difficulty based on experience
        if experience.lower() in ['entry level', 'junior']:
            all_questions = [q for q in all_questions if q['difficulty'] in ['easy', 'medium']]
        elif experience.lower() in ['senior', 'lead']:
            all_questions = [q for q in all_questions if q['difficulty'] in ['medium', 'hard']]
        
        # Select questions
        import random
        selected = random.sample(
            all_questions,
            min(num_questions, len(all_questions))
        )
        
        # Add IDs
        for i, q in enumerate(selected, 1):
            q['id'] = i
        
        print(f"✅ Selected {len(selected)} template questions")
        return selected
    
    
    def _load_templates(self) -> Dict:
        """Load template questions"""
        return {
            "technical": [
                {
                    "question": "Explain the difference between a stack and a queue. When would you use each?",
                    "category": "technical",
                    "difficulty": "easy",
                    "time_limit": 120
                },
                {
                    "question": "What is object-oriented programming? Explain with examples.",
                    "category": "technical",
                    "difficulty": "easy",
                    "time_limit": 120
                },
                {
                    "question": "How would you optimize a slow database query?",
                    "category": "technical",
                    "difficulty": "medium",
                    "time_limit": 180
                },
                {
                    "question": "Design a URL shortener like bit.ly. What components would you need?",
                    "category": "technical",
                    "difficulty": "hard",
                    "time_limit": 240
                },
                {
                    "question": "Explain REST APIs and how they differ from GraphQL.",
                    "category": "technical",
                    "difficulty": "medium",
                    "time_limit": 120
                }
            ],
            "behavioral": [
                {
                    "question": "Tell me about a time you faced a challenging deadline. How did you handle it?",
                    "category": "behavioral",
                    "difficulty": "easy",
                    "time_limit": 120
                },
                {
                    "question": "Describe a situation where you had to work with a difficult team member.",
                    "category": "behavioral",
                    "difficulty": "medium",
                    "time_limit": 120
                },
                {
                    "question": "What's your greatest professional achievement and why?",
                    "category": "behavioral",
                    "difficulty": "easy",
                    "time_limit": 120
                },
                {
                    "question": "Tell me about a time you failed. What did you learn?",
                    "category": "behavioral",
                    "difficulty": "medium",
                    "time_limit": 120
                },
                {
                    "question": "How do you stay updated with new technologies in your field?",
                    "category": "behavioral",
                    "difficulty": "easy",
                    "time_limit": 90
                }
            ],
            "situational": [
                {
                    "question": "If you discovered a critical bug in production, what steps would you take?",
                    "category": "situational",
                    "difficulty": "medium",
                    "time_limit": 120
                },
                {
                    "question": "Your manager assigns you a task you disagree with. How do you respond?",
                    "category": "situational",
                    "difficulty": "medium",
                    "time_limit": 120
                },
                {
                    "question": "Two team members have conflicting ideas on implementation. How would you mediate?",
                    "category": "situational",
                    "difficulty": "hard",
                    "time_limit": 150
                },
                {
                    "question": "You're running behind on a project deadline. What do you do?",
                    "category": "situational",
                    "difficulty": "easy",
                    "time_limit": 90
                }
            ]
        }


# ========== CONVENIENCE FUNCTION ==========

def quick_generate(num_questions: int = 5) -> List[Dict]:
    """Quick question generation"""
    generator = QuestionGenerator()
    return generator.generate_questions(num_questions=num_questions)


# ========== TEST ==========

if __name__ == "__main__":
    print("\n🎯 Testing Question Generator\n")
    
    generator = QuestionGenerator()
    
    profile = {
        "job_role": "Software Engineer",
        "degree": "Computer Science",
        "experience_level": "Entry Level",
        "company_type": "Tech Startup"
    }
    
    questions = generator.generate_questions(profile=profile, num_questions=5)
    
    print(f"\n📋 Generated {len(questions)} questions:\n")
    for q in questions:
        print(f"{q['id']}. [{q['category'].upper()}] {q['question']}")
        print(f"   Difficulty: {q['difficulty']} | Time: {q['time_limit']}s\n")