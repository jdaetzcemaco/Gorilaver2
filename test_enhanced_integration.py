#!/usr/bin/env python3
"""
Integration test script for Enhanced TitleGenerator
Run this after updating your pipeline files to verify everything works
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test if we can import the enhanced generator"""
    try:
        from agents.enhanced_title_generator import EnhancedTitleGenerator
        print("✅ EnhancedTitleGenerator imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import EnhancedTitleGenerator: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without API calls"""
    try:
        from agents.enhanced_title_generator import EnhancedTitleGenerator
        
        # Test initialization
        generator = EnhancedTitleGenerator()
        print("✅ EnhancedTitleGenerator initialized successfully")
        
        # Test fallback title creation (doesn't require API)
        product_data = {
            'verified_brand': 'TestBrand',
            'verified_product_type': 'Test Product',
            'color': 'Blue',
            'size': '10mm'
        }
        
        category_info = {
            'categoria': 'TEST CATEGORY',
            'nomenclatura_sugerida': 'Brand + Type + Specs'
        }
        
        fallback_title = generator._create_enhanced_fallback_title(product_data, category_info)
        print(f"✅ Fallback title generation works: {fallback_title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_pipeline_integration():
    """Test integration with existing pipelines"""
    
    # Test main.py pipeline
    try:
        from main import ProductTitlePipeline
        
        # Check if it imports EnhancedTitleGenerator
        pipeline = ProductTitlePipeline()
        
        if hasattr(pipeline, 'agent2'):
            generator_class = pipeline.agent2.__class__.__name__
            if generator_class == 'EnhancedTitleGenerator':
                print("✅ main.py pipeline using EnhancedTitleGenerator")
            else:
                print(f"⚠️  main.py pipeline using {generator_class} (update needed)")
        
    except Exception as e:
        print(f"⚠️  main.py pipeline test failed: {e}")
    
    # Test complete_pipeline.py
    try:
        from complete_pipeline import CompletePipeline
        
        pipeline = CompletePipeline()
        if hasattr(pipeline, 'generator'):
            generator_class = pipeline.generator.__class__.__name__
            if generator_class == 'EnhancedTitleGenerator':
                print("✅ complete_pipeline.py using EnhancedTitleGenerator")
            else:
                print(f"⚠️  complete_pipeline.py using {generator_class} (update needed)")
        
    except Exception as e:
        print(f"⚠️  complete_pipeline.py test failed: {e}")
    
    # Test updated_complete_pipeline.py
    try:
        from updated_complete_pipeline import UpdatedCompletePipeline
        
        pipeline = UpdatedCompletePipeline()
        if hasattr(pipeline, 'generator'):
            generator_class = pipeline.generator.__class__.__name__
            if generator_class == 'EnhancedTitleGenerator':
                print("✅ updated_complete_pipeline.py using EnhancedTitleGenerator")
            else:
                print(f"⚠️  updated_complete_pipeline.py using {generator_class} (update needed)")
        
    except Exception as e:
        print(f"⚠️  updated_complete_pipeline.py test failed: {e}")

def test_with_real_openai_api():
    """Test with real OpenAI API if available"""
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  No OpenAI API key found in environment, skipping API test")
        return
    
    try:
        from agents.enhanced_title_generator import EnhancedTitleGenerator
        
        generator = EnhancedTitleGenerator()
        
        # Test with a simple product that should trigger category correction
        test_product = {
            'original_title': 'CHAPA BARI DE BAÑO CROMO',
            'description': 'Chapa para baño'
        }
        
        wrong_category = {
            'categoria': 'TUBERIA PVC',
            'nomenclatura_sugerida': 'Diámetro + Longitud',
            'ejemplo_aplicado': 'Tubo PVC 4" x 6m'
        }
        
        print("🔄 Testing with OpenAI API...")
        title = generator.generate_ecommerce_title(test_product, wrong_category)
        
        print(f"✅ API test successful!")
        print(f"   Generated title: {title}")
        
        # Check if research data was stored
        if hasattr(generator, '_last_research_data'):
            research = generator._last_research_data
            if 'error' not in research:
                print(f"   Research found: {research.get('verified_product_type', 'N/A')}")
            else:
                print(f"   Research had error: {research.get('error', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_app_integration():
    """Test Flask app integration"""
    try:
        # Import app to see if it loads with enhanced generator
        import app
        
        if hasattr(app, 'CompletePipeline'):
            print("✅ Flask app imports successfully")
            
            # Try to create a pipeline instance
            pipeline = app.CompletePipeline()
            if hasattr(pipeline, 'generator'):
                generator_class = pipeline.generator.__class__.__name__
                if generator_class == 'EnhancedTitleGenerator':
                    print("✅ Flask app using EnhancedTitleGenerator")
                else:
                    print(f"⚠️  Flask app using {generator_class} (update needed)")
            
        return True
        
    except Exception as e:
        print(f"⚠️  Flask app test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 Enhanced TitleGenerator Integration Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_import),
        ("Basic Functionality", test_basic_functionality),
        ("Pipeline Integration", test_pipeline_integration),
        ("Flask App Integration", test_app_integration),
        ("OpenAI API Test", test_with_real_openai_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Enhanced TitleGenerator is ready to use.")
    elif passed > 0:
        print(f"\n⚠️  {len(results) - passed} tests failed. Check the issues above.")
    else:
        print("\n🚨 All tests failed. Check your installation and configuration.")
    
    print("\n💡 Next steps:")
    print("1. Fix any failed tests")
    print("2. Update your pipeline imports if needed")
    print("3. Test with real product data")
    print("4. Monitor results and adjust settings")

if __name__ == "__main__":
    main()