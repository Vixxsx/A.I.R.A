import os
import json
import random
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class QuestionGenerator:
    def __init__(self):

        self.api_key = os.getenv('OPENAI_API_KEY')

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ Question Generator initialized (GPT-4o-mini)")
                self.use_ai = True
            except Exception as e:
                print(f"⚠️  OpenAI API unavailable: {e}")
                self.client = None
                self.use_ai = False
        else:
            print("⚠️  OPENAI_API_KEY not found in environment")
            print("   Using template questions")
            self.client = None
            self.use_ai = False

        self.template_questions = self._load_templates()
        self.history_file = "Data/question_history.json"
        os.makedirs("Data", exist_ok=True)


    def generate_questions(self, profile: Optional[Dict] = None, num_questions: int = 5) -> List[Dict]:
        if profile is None:
            profile = {
                'job_role':       'Software Engineer',
                'degree':         'Computer Science',
                'difficulty':     'intermediate',
                'company_type':   'Tech Company',
                'interview_type': 'mixed'
            }

        if self.use_ai and self.client:
            try:
                questions = self._generate_with_openai(profile, num_questions)
                # Save to history to avoid future repeats
                self._save_to_history([q['question'] for q in questions])
                return questions
            except Exception as e:
                print(f"⚠️  OpenAI generation failed: {e}")
                print("   Falling back to templates")
                return self._generate_from_templates(profile, num_questions)
        else:
            return self._generate_from_templates(profile, num_questions)


    def _load_question_history(self) -> List[str]:
        """Load recently asked questions to avoid repeats"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load question history: {e}")
        return []


    def _save_to_history(self, questions: List[str]):
        """Save questions to history (keep last 100)"""
        try:
            history = self._load_question_history()
            history.extend(questions)
            # Keep only last 100 questions
            history = history[-100:]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Could not save question history: {e}")


    def _generate_with_openai(self, profile: Dict, num_questions: int) -> List[Dict]:

        interview_type = profile.get('interview_type', 'mixed').lower()
        job_role       = profile.get('job_role',       'Software Engineer')
        difficulty     = profile.get('difficulty',     'intermediate')
        degree         = profile.get('degree',         'Computer Science')
        company_type   = profile.get('company_type',   'Tech Company')

        # Load recently asked questions
        recent_questions = self._load_question_history()[-30:]  # Last 30 questions
       
        # Random seed for variety
        random_seed = random.randint(1, 1000000)

        # Dynamic system prompt
        system_prompt = (
            f"You are a creative and experienced interviewer for {job_role} positions. "
            f"Generate UNIQUE, VARIED, and THOUGHTFUL questions. "
            f"Avoid cliché or generic interview questions. "
            f"Return only valid raw JSON — no markdown, no code fences, no explanation."
        )

        # Type instructions
        type_instructions = {
            'behavioral': (
                "Generate ONLY behavioral questions answerable in STAR format. "
                "Focus on: past experiences, teamwork, conflict resolution, leadership, "
                "handling failure, communication, adaptability, decision-making. "
                "Make each question UNIQUE — no repetitive themes. "
                "Do NOT include technical questions."
            ),
            'technical': (
                f"Generate ONLY technical questions specific to a {job_role} role. "
                f"Cover diverse topics: algorithms, design patterns, system design, "
                f"tools, frameworks, best practices, debugging, optimization. "
                f"Make each question UNIQUE and SPECIFIC — avoid generic questions. "
                f"Do NOT include soft-skill or behavioral questions."
            ),
            'mixed': (
                f"Generate EXACTLY {num_questions // 2} technical questions AND "
                f"EXACTLY {num_questions - num_questions // 2} behavioral questions. "
                f"Technical: diverse topics, {job_role}-specific, tests real knowledge. "
                f"Behavioral: STAR-format, varied scenarios, past experiences. "
                f"Make EVERY question unique and interesting. "
                f"Alternate them: technical, behavioral, technical, behavioral..."
            )
        }

        type_instruction = type_instructions.get(interview_type, type_instructions['mixed'])

        # Build exclusion list
        exclusion_text = ""
        if recent_questions:
            exclusion_text = f"""
DO NOT generate questions similar to these recently asked questions:
{chr(10).join(f"  ❌ {q}" for q in recent_questions)}

Make sure your questions are COMPLETELY DIFFERENT in topic, structure, and focus.
"""

        print(f"🤖 Generating {num_questions} UNIQUE [{interview_type}] questions...")

        prompt = f"""Generate exactly {num_questions} UNIQUE and CREATIVE interview questions.

Profile:
- Job Role:       {job_role}
- Degree:         {degree}
- Difficulty:     {difficulty}
- Company Type:   {company_type}
- Interview Type: {interview_type.upper()}

Type rule (STRICTLY follow):
{type_instruction}

Difficulty guide:
- beginner:     simple, common scenarios, foundational knowledge
- intermediate: requires real experience or solid understanding
- advanced:     deep expertise, complex scenarios, leadership thinking

{exclusion_text}

CRITICAL REQUIREMENTS:
1. Each question must be UNIQUE — no overlapping topics or themes
2. Avoid cliché questions like "tight deadlines" or "learning new technology fast"
3. Be SPECIFIC and CREATIVE — use real scenarios and concrete examples
4. Test different aspects of {job_role} work
5. Random seed for variety: {random_seed}

Return ONLY a raw JSON array. No markdown. No explanation. No code fences:
[
  {{
    "id": 1,
    "question": "specific and unique question text here",
    "category": "technical | behavioral | situational",
    "difficulty": "easy | medium | hard",
    "time_limit": 120
  }}
]"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1.1,  # ← INCREASED from 0.7 for more creativity!
            max_tokens=1500,
            presence_penalty=0.6,  # ← Encourages diverse topics
            frequency_penalty=0.3   # ← Reduces repetition
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        questions = json.loads(content)
        print(f"✅ Generated {len(questions)} unique questions")
        return questions


    def _generate_from_templates(self, profile: Dict, num_questions: int) -> List[Dict]:
        """
        Generate questions from templates with proper type enforcement
        - mixed: EXACTLY 50/50 split between technical and behavioral
        - technical: 80% technical, 20% behavioral
        - behavioral: 80% behavioral, 20% technical
        """
        print(f"📝 Generating {num_questions} questions from templates...")

        job_role       = profile.get('job_role',       'Software Engineer')
        difficulty     = profile.get('difficulty',     'intermediate')
        interview_type = profile.get('interview_type', 'mixed').lower()

        difficulty_map = {
            'beginner':     ['easy'],
            'intermediate': ['easy', 'medium'],
            'advanced':     ['medium', 'hard'],
        }
        allowed = difficulty_map.get(difficulty.lower(), ['easy', 'medium'])

        if interview_type == 'mixed':
            # ENFORCE 50/50 SPLIT
            tech_pool = [q for q in self.template_questions['technical']
                         if q['difficulty'] in allowed]
            behav_pool = [q for q in (self.template_questions['behavioral'] +
                                      self.template_questions['situational'])
                          if q['difficulty'] in allowed]
           
            # Calculate split
            tech_count = num_questions // 2
            behav_count = num_questions - tech_count
           
            # Sample from each pool
            tech_selected = random.sample(tech_pool, min(tech_count, len(tech_pool)))
            behav_selected = random.sample(behav_pool, min(behav_count, len(behav_pool)))
           
            # Combine and shuffle
            selected = tech_selected + behav_selected
            random.shuffle(selected)
           
            # Add IDs
            for i, q in enumerate(selected, 1):
                q['id'] = i
           
            print(f"✅ Selected {len(tech_selected)} technical + {len(behav_selected)} behavioral = {len(selected)} total")
            return selected
           
        elif interview_type == 'technical':
            # 80% technical, 20% behavioral
            tech_pool = [q for q in self.template_questions['technical']
                         if q['difficulty'] in allowed]
            behav_pool = [q for q in self.template_questions['behavioral']
                          if q['difficulty'] in allowed]
           
            tech_count = int(num_questions * 0.8)
            behav_count = num_questions - tech_count
           
            tech_selected = random.sample(tech_pool, min(tech_count, len(tech_pool)))
            behav_selected = random.sample(behav_pool, min(behav_count, len(behav_pool)))
           
            selected = tech_selected + behav_selected
            random.shuffle(selected)
           
        elif interview_type == 'behavioral':
            # 80% behavioral, 20% technical
            behav_pool = [q for q in (self.template_questions['behavioral'] +
                                      self.template_questions['situational'])
                          if q['difficulty'] in allowed]
            tech_pool = [q for q in self.template_questions['technical']
                         if q['difficulty'] in allowed]
           
            behav_count = int(num_questions * 0.8)
            tech_count = num_questions - behav_count
           
            behav_selected = random.sample(behav_pool, min(behav_count, len(behav_pool)))
            tech_selected = random.sample(tech_pool, min(tech_count, len(tech_pool)))
           
            selected = behav_selected + tech_selected
            random.shuffle(selected)
           
        else:
            # Fallback
            all_questions = (self.template_questions['technical'] +
                           self.template_questions['behavioral'] +
                           self.template_questions['situational'])
            filtered = [q for q in all_questions if q['difficulty'] in allowed]
            selected = random.sample(filtered, min(num_questions, len(filtered)))

        # Add IDs
        for i, q in enumerate(selected, 1):
            q['id'] = i

        print(f"✅ Selected {len(selected)} {interview_type} questions")
        return selected


    def _load_templates(self) -> Dict:
        return {
            "technical": [
                {"question": "Explain the difference between a stack and a queue. When would you use each?",          "category": "technical",   "difficulty": "easy",   "time_limit": 120},
                {"question": "What is object-oriented programming? Explain the four pillars with examples.",           "category": "technical",   "difficulty": "easy",   "time_limit": 120},
                {"question": "How would you optimize a slow database query?",                                          "category": "technical",   "difficulty": "medium", "time_limit": 180},
                {"question": "Design a URL shortener like bit.ly. What components would you need?",                    "category": "technical",   "difficulty": "hard",   "time_limit": 240},
                {"question": "Explain REST APIs and how they differ from GraphQL.",                                    "category": "technical",   "difficulty": "medium", "time_limit": 120},
                {"question": "What is the time complexity of binary search and why?",                                  "category": "technical",   "difficulty": "easy",   "time_limit": 90},
                {"question": "Explain database indexing and when you would avoid using it.",                           "category": "technical",   "difficulty": "medium", "time_limit": 150},
                {"question": "How does garbage collection work in Python or Java?",                                    "category": "technical",   "difficulty": "medium", "time_limit": 120},
                {"question": "Design a system to handle 1 million concurrent users. Walk through your architecture.", "category": "technical",   "difficulty": "hard",   "time_limit": 300},
                {"question": "What is the difference between concurrency and parallelism?",                           "category": "technical",   "difficulty": "medium", "time_limit": 120},
            ],
            "behavioral": [
                {"question": "Tell me about a time you faced a challenging deadline. How did you handle it?",              "category": "behavioral", "difficulty": "easy",   "time_limit": 120},
                {"question": "Describe a situation where you had to work with a difficult team member.",                   "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "What's your greatest professional achievement and why?",                                     "category": "behavioral", "difficulty": "easy",   "time_limit": 120},
                {"question": "Tell me about a time you failed. What did you learn from it?",                               "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "How do you stay updated with new technologies in your field?",                               "category": "behavioral", "difficulty": "easy",   "time_limit": 90},
                {"question": "Describe a time you led a project without formal authority. How did you manage it?",         "category": "behavioral", "difficulty": "hard",   "time_limit": 150},
                {"question": "Tell me about a time you disagreed with your manager. What did you do?",                    "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "Give an example of when you had to learn something quickly under pressure.",                 "category": "behavioral", "difficulty": "medium", "time_limit": 120},
            ],
            "situational": [
                {"question": "If you discovered a critical bug in production, what steps would you take?",          "category": "situational", "difficulty": "medium", "time_limit": 120},
                {"question": "Your manager assigns you a task you strongly disagree with. How do you respond?",     "category": "situational", "difficulty": "medium", "time_limit": 120},
                {"question": "Two team members have conflicting implementation ideas. How would you mediate?",      "category": "situational", "difficulty": "hard",   "time_limit": 150},
                {"question": "You're running behind on a project deadline. What do you do?",                        "category": "situational", "difficulty": "easy",   "time_limit": 90},
                {"question": "You inherit a legacy codebase with no documentation. How do you approach it?",       "category": "situational", "difficulty": "medium", "time_limit": 120},
            ]
        }


# ========== CONVENIENCE FUNCTION ==========

def quick_generate(num_questions: int = 5) -> List[Dict]:
    generator = QuestionGenerator()
    return generator.generate_questions(num_questions=num_questions)


# ========== TEST ==========

if __name__ == "__main__":
    print("\n🎯 Testing Question Generator\n")
    generator = QuestionGenerator()

    for itype in ['behavioral', 'technical', 'mixed']:
        print(f"\n{'='*60}")
        print(f"Testing type: {itype.upper()}")
        print('='*60)
        profile = {
            "job_role":       "Software Engineer",
            "degree":         "Computer Science",
            "difficulty":     "intermediate",
            "company_type":   "Tech Company",
            "interview_type": itype
        }
        questions = generator.generate_questions(profile=profile, num_questions=6)
        for q in questions:
            print(f"{q['id']}. [{q['category'].upper()}] {q['question']}")
            print(f"   Difficulty: {q['difficulty']} | Time: {q['time_limit']}s\n")