import os
import sys



backend_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.Question_Generator import QuestionGenerator

def test_basic_generation():
    """Test basic question generation with default profile"""
    print("="*60)
    print("TEST 1: Basic Question Generation (Default Profile)")
    print("="*60)
    
    generator = QuestionGenerator()
    questions = generator.generate_questions()
    
    print(f"\n✅ Generated {len(questions)} questions\n")
    
    for q in questions:
        print(f"Q{q['id']}: {q['question']}")
        print(f"   Type: {q['type']} | Difficulty: {q['difficulty']}\n")
    
    return questions


def test_custom_profile():
    """Test with custom profile"""
    print("\n" + "="*60)
    print("TEST 2: Custom Profile (Data Analyst)")
    print("="*60)
    
    generator = QuestionGenerator()
    
    default_profile = {
        "job_role": "Data Analyst",
        "degree": "Statistics",
        "experience_level": "Mid Level",
        "company_type": "Finance"
    }
    
    questions = generator.generate_questions(profile=default_profile, num_questions=5)
    
    print(f"\n✅ Generated {len(questions)} questions for Data Analyst\n")
    
    for q in questions:
        print(f"Q{q['id']}: {q['question']}")
        print(f"   Type: {q['type']} | Difficulty: {q['difficulty']}\n")


def test_different_counts():
    """Test generating different numbers of questions"""
    print("\n" + "="*60)
    print("TEST 3: Different Question Counts")
    print("="*60)
    
    generator = QuestionGenerator()
    
    for count in [3, 5, 7]:
        questions = generator.generate_questions(num_questions=count)
        print(f"\n✅ Requested {count} questions, got {len(questions)} questions")


def test_save_to_file():
    """Test saving questions to file"""
    print("\n" + "="*60)
    print("TEST 4: Save Questions to File")
    print("="*60)
    
    generator = QuestionGenerator()
    questions = generator.generate_questions()
    
    generator.save_questions_to_file(questions, "test_questions.json")
    print("\n✅ Check data/Report/test_questions.json")


def test_api_key_status():
    """Check if OpenAI API key is available"""
    print("\n" + "="*60)
    print("API Key Status Check")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        print(f"\n✅ OpenAI API key found (length: {len(api_key)})")
        print("   Questions will be generated using GPT-4")
    else:
        print("\n⚠️  No OpenAI API key found")
        print("   Questions will use fallback templates")
        print("\n   To use GPT-4:")
        print("   1. Get API key from: https://platform.openai.com/api-keys")
        print("   2. Create a .env file with: OPENAI_API_KEY=your_key_here")
        print("   3. Or set environment variable: export OPENAI_API_KEY=your_key")


if __name__ == "__main__":
    print("\n" + "🎯 AIRA - Question Generator Test Suite" + "\n")
    
    # Check API key status first
    test_api_key_status()
    
    try:
        # Run tests
        test_basic_generation()
        test_custom_profile()
        test_different_counts()
        test_save_to_file()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()