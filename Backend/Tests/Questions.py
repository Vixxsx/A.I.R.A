import os
import sys
backend_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
from Models.Question_Generator import QuestionGenerator
print("\n" + "="*70)
print("🎯 AIRA - Question Generator Display Test")
print("="*70 + "\n")
# Create generator
generator = QuestionGenerator()

# Generate questions
print("Generating questions...\n")
questions = generator.generate_questions()

# Display questions nicely
print("="*70)
print(f"📋 GENERATED {len(questions)} INTERVIEW QUESTIONS")
print("="*70 + "\n")

for i, q in enumerate(questions, 1):
    print(f"QUESTION {i}")
    print(f"\n{q['question']}\n")
    print(f"Type: {q.get('category', q.get('type', 'N/A')).upper()}")
    print(f"Difficulty: {q['difficulty'].upper()}")
    print(f"\n")

print("="*70)
print("✅ TEST COMPLETE - Questions displayed above")
print("="*70 + "\n")