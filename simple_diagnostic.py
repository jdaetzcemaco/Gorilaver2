# simple_diagnostic.py - Quick project check
import os
import sys

def main():
    print("🔍 QUICK PROJECT CHECK")
    print("=" * 40)
    
    # Check core files
    print("\n📁 CHECKING FILES:")
    files_to_check = [
        'app.py',
        'frontend.html', 
        'agents/enhanced_title_generator.py',
        'agents/label_formatter.py',
        'nomenclatura_gorila2.csv'
    ]
    
    for file in files_to_check:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
    
    # Check Python imports
    print("\n📦 CHECKING IMPORTS:")
    try:
        import pandas
        print("✅ pandas")
    except ImportError:
        print("❌ pandas - run: pip install pandas")
    
    try:
        import flask
        print("✅ flask")
    except ImportError:
        print("❌ flask - run: pip install flask flask-cors")
    
    try:
        from openai import OpenAI
        print("✅ openai")
    except ImportError:
        print("❌ openai - run: pip install openai")
    
    # Check project imports
    print("\n🔧 CHECKING PROJECT MODULES:")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from agents.enhanced_title_generator import EnhancedTitleGenerator
        print("✅ Enhanced Title Generator")
    except Exception as e:
        print(f"❌ Enhanced Title Generator: {e}")
    
    try:
        from agents.label_formatter import LabelFormatter
        print("✅ Label Formatter")
    except Exception as e:
        print(f"❌ Label Formatter: {e}")
    
    # Check environment
    print("\n🔑 ENVIRONMENT:")
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY set")
    else:
        print("⚠️  OPENAI_API_KEY not set (web search disabled)")
    
    print("\n" + "=" * 40)
    print("🚀 TO FIX ISSUES:")
    print("1. Install packages: pip install pandas flask flask-cors openai")
    print("2. Add .env file with: OPENAI_API_KEY=your_key_here")
    print("3. Run: python app.py")

if __name__ == "__main__":
    main()