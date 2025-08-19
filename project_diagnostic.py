# project_diagnostic.py - Verify project setup and fix issues
import os
import sys
import json
import pandas as pd
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and return status"""
    exists = os.path.exists(filepath)
    status = "✓ FOUND" if exists else "❌ MISSING"
    print(f"{status} {description}: {filepath}")
    return exists

def check_python_imports():
    """Test all required imports"""
    print("\n📦 CHECKING PYTHON IMPORTS:")
    
    imports_status = {}
    
    # Test basic imports
    try:
        import pandas as pd
        imports_status['pandas'] = True
        print("✓ pandas imported successfully")
    except ImportError as e:
        imports_status['pandas'] = False
        print(f"❌ pandas import failed: {e}")
    
    try:
        import flask
        imports_status['flask'] = True
        print("✓ flask imported successfully")
    except ImportError as e:
        imports_status['flask'] = False
        print(f"❌ flask import failed: {e}")
    
    try:
        from openai import OpenAI
        imports_status['openai'] = True
        print("✓ openai imported successfully")
    except ImportError as e:
        imports_status['openai'] = False
        print(f"❌ openai import failed: {e}")
    
    # Test project-specific imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from agents.enhanced_title_generator import EnhancedTitleGenerator
        imports_status['enhanced_title_generator'] = True
        print("✓ Enhanced Title Generator imported successfully")
    except ImportError as e:
        imports_status['enhanced_title_generator'] = False
        print(f"❌ Enhanced Title Generator import failed: {e}")
    
    try:
        from agents.label_formatter import LabelFormatter
        imports_status['label_formatter'] = True
        print("✓ Label Formatter imported successfully")
    except ImportError as e:
        imports_status['label_formatter'] = False
        print(f"❌ Label Formatter import failed: {e}")
    
    return imports_status

def check_nomenclatura_csv():
    """Check nomenclatura CSV file"""
    print("\n📋 CHECKING NOMENCLATURA CSV:")
    
    possible_paths = [
        'nomenclatura_gorila2.csv',
        'nomenclatura_gorila.csv', 
        'data/nomenclatura_gorila.csv',
        'data/nomenclatura_gorila2.csv'
    ]
    
    found_file = None
    for path in possible_paths:
        if os.path.exists(path):
            found_file = path
            print(f"✓ Found nomenclatura file: {path}")
            break
    
    if not found_file:
        print("❌ No nomenclatura CSV file found!")
        print("   Expected locations:")
        for path in possible_paths:
            print(f"   - {path}")
        return False, None
    
    # Check CSV structure
    try:
        df = pd.read_csv(found_file)
        print(f"✓ CSV loaded successfully: {len(df)} rows")
        
        required_columns = ['Departamento', 'Familia', 'Categoria']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            print(f"   Available columns: {list(df.columns)}")
            return False, found_file
        else:
            print(f"✓ All required columns present: {required_columns}")
            
        # Show sample data
        print("\n📊 Sample data:")
        print(df.head(3).to_string())
        
        return True, found_file
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False, found_file

def check_environment_variables():
    """Check environment variables"""
    print("\n🔑 CHECKING ENVIRONMENT:")
    
    # Check for .env file
    env_file_exists = os.path.exists('.env')
    print(f"{'✓' if env_file_exists else '❌'} .env file: {'FOUND' if env_file_exists else 'MISSING'}")
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✓ OPENAI_API_KEY: SET (***{openai_key[-4:]})")
    else:
        print("❌ OPENAI_API_KEY: NOT SET")
        print("   This will disable web search features")
    
    return {
        'env_file': env_file_exists,
        'openai_key': bool(openai_key)
    }

def test_json_parsing():
    """Test JSON parsing functionality"""
    print("\n🧪 TESTING JSON PARSING:")
    
    # Test sample JSON responses that might cause issues
    test_cases = [
        '```json\\n{"test": "value"}\\n```',  # Markdown formatted
        '{"test": "value"}',  # Clean JSON
        'Some text before\\n{"test": "value"}\\nSome text after',  # Embedded JSON
        '```\\n{"test": "value"}\\n```',  # Generic markdown
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case[:30]}...")
        
        try:
            # Apply the same cleaning logic as in the fixed generator
            cleaned = test_case.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            elif cleaned.startswith('```'):
                cleaned = cleaned.replace('```', '').strip()
            
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx + 1]
            
            # Try to parse
            result = json.loads(cleaned)
            print(f"✓ Parsed successfully: {result}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Parse failed: {e}")
        except Exception as e:
            print(f"❌ Other error: {e}")

def create_sample_env_file():
    """Create sample .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n📝 CREATING SAMPLE .env FILE:")
        
        env_content = """# Environment variables for Cemaco Title Processor
# Copy this file to .env and add your actual API key

# OpenAI API Key (required for enhanced features)
OPENAI_API_KEY=your_openai_api_key_here

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True
"""
        
        with open('.env.sample', 'w') as f:
            f.write(env_content)
        
        print("✓ Created .env.sample file")
        print("   Copy to .env and add your OpenAI API key")

def main():
    """Run complete project diagnostic"""
    print("🔍 CEMACO PROJECT DIAGNOSTIC")
    print("=" * 50)
    
    # Check core files
    print("\n📁 CHECKING CORE FILES:")
    core_files = [
        ('app.py', 'Main Flask application'),
        ('frontend.html', 'Web interface'),
        ('agents/enhanced_title_generator.py', 'Enhanced title generator'),
        ('agents/label_formatter.py', 'Label formatter'),
        ('agents/smart_messy_parser.py', 'Smart messy parser')
    ]
    
    files_ok = True
    for filepath, description in core_files:
        if not check_file_exists(filepath, description):
            files_ok = False
    
    # Check imports
    imports_status = check_python_imports()
    
    # Check nomenclatura CSV
    csv_ok, csv_path = check_nomenclatura_csv()
    
    # Check environment
    env_status = check_environment_variables()
    
    # Test JSON parsing
    test_json_parsing()
    
    # Create sample env file
    create_sample_env_file()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY:")
    
    issues = []
    
    if not files_ok:
        issues.append("Missing core project files")
    
    if not imports_status.get('pandas', False):
        issues.append("pandas not installed (pip install pandas)")
    
    if not imports_status.get('flask', False):
        issues.append("flask not installed (pip install flask flask-cors)")
    
    if not imports_status.get('openai', False):
        issues.append("openai not installed (pip install openai)")
    
    if not csv_ok:
        issues.append("nomenclatura CSV file missing or invalid")
    
    if not env_status['openai_key']:
        issues.append("OPENAI_API_KEY not set (enhanced features disabled)")
    
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        
        print("\n🛠️  RECOMMENDED FIXES:")
        print("1. Install missing Python packages:")
        print("   pip install pandas flask flask-cors openai")
        print("2. Add nomenclatura_gorila2.csv to project root")
        print("3. Copy .env.sample to .env and add your OpenAI API key")
        print("4. Run: python app.py")
    else:
        print("✅ All checks passed! Project should work correctly.")
    
    print("\n🚀 To start the application:")
    print("   python app.py")
    print("   Then open: http://localhost:5000")

if __name__ == "__main__":
    main()