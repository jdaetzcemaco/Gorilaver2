from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
import time
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict
# Add this near the top of app.py after imports
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file
# Add this import at the top
from processing_reviewer import ProcessingReviewer

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
class SafeEnhancedTitleGenerator:
    """Wrapper to make EnhancedTitleGenerator safe for web interface"""
    
    def __init__(self, original_generator):
        self.original_generator = original_generator
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """Safe wrapper for title generation with comprehensive error handling"""
        try:
            # Try the enhanced generation
            title = self.original_generator.generate_ecommerce_title(product_data, category_info)
            if title and isinstance(title, str) and len(title.strip()) > 0:
                return title.strip()
            else:
                raise ValueError("Empty or invalid title returned")
        except Exception as e:
            print(f"   ⚠️  Enhanced generation failed ({e}), using fallback")
            # Create a safe fallback title
            return self._create_safe_fallback_title(product_data, category_info)

    def _create_safe_fallback_title(self, product_data: Dict, category_info: Dict) -> str:
        """Create a safe fallback title when enhanced generation fails"""
        parts = []

        # Add brand if available
        brand = product_data.get('brand', '')
        if brand:
            parts.append(str(brand).strip())

        # Add category (safe for None)
        categoria = category_info.get('categoria', 'Product') if category_info else 'Product'
        if categoria:
            parts.append(str(categoria).strip().title())

        # Add description or original title
        description = (product_data.get('description', '') or 
                      product_data.get('original_title', '') or 
                      'Item')

        # Take first few words from description
        desc_words = str(description).split()[:4]
        if desc_words:
            parts.extend(desc_words)

        # Add specs if available
        for key in ['color', 'size', 'dimensions', 'model']:
            value = product_data.get(key, '')
            if value:
                parts.append(str(value).strip())

        # Join and clean up
        title = ' '.join(str(part) for part in parts if part)

        # Ensure we have something
        if not title:
            title = "Product Item"

        # Limit length
        if len(title) > 150:
            title = title[:147] + "..."

        return title

try:
    from agents.tile_fixed_classifier import TileFixedCategoryClassifier
    from agents.enhanced_title_generator import EnhancedTitleGenerator
    from agents.label_formatter import LabelFormatter
    
    class SimpleTilePipeline:
        def __init__(self):
            self.classifier = TileFixedCategoryClassifier()
            
            # Wrap the enhanced generator with safety
            try:
                original_generator = EnhancedTitleGenerator(os.getenv('OPENAI_API_KEY'))
                self.generator = SafeEnhancedTitleGenerator(original_generator)
                print("✓ Using Enhanced TitleGenerator with safety wrapper")
            except Exception as e:
                print(f"⚠️  Enhanced generator failed to load: {e}")
                # Fallback to basic generator
                from agents.title_generator import TitleGenerator
                self.generator = TitleGenerator()
                print("✓ Using basic TitleGenerator as fallback")
            
            self.formatter = LabelFormatter()
        
        def process_raw_title(self, title):
            try:
                product_data = {'description': title, 'original_title': title}
                
                category_match = self.classifier.find_category_match(product_data)
                if not category_match:
                    return {'success': False, 'errors': ['No category found'], 'input_title': title}
                
                # This will now use the safe wrapper
                optimized_title = self.generator.generate_ecommerce_title(product_data, category_match)
                
                if not optimized_title:
                    return {'success': False, 'errors': ['Title generation failed'], 'input_title': title}
                
                store_label = self.formatter.format_store_label(optimized_title)
                
                return {
                    'success': True,
                    'input_title': title,
                    'optimized_title': optimized_title,
                    'store_label': store_label,
                    'category_match': category_match
                }
            except Exception as e:
                print(f"   ⚠️  Processing error for '{title}': {e}")
                return {'success': False, 'errors': [str(e)], 'input_title': title}
    
    CompletePipeline = SimpleTilePipeline
    print("✓ Tile-aware pipeline loaded successfully")
    
except ImportError as e:
    print(f"Error importing tile pipeline: {e}")
    CompletePipeline = None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Read the HTML content
try:
    with open('frontend.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
except FileNotFoundError:
    html_content = """
    <html>
    <body>
    <h1>Error: frontend.html not found</h1>
    <p>Please make sure frontend.html exists in the same directory as app.py</p>
    </body>
    </html>
    """

@app.route('/')
def index():
    return html_content

@app.route('/process', methods=['POST'])
def process_file():
    try:
        # Check if CompletePipeline is available
        if CompletePipeline is None:
            return jsonify({
                'success': False,
                'error': 'Pipeline not available. Check imports and dependencies.'
            }), 500

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        processing_type = request.form.get('type', 'messy')
        print(f"Processing file: {file.filename}, Type: {processing_type}")

        # Read file content based on extension
        try:
            if file.filename.lower().endswith('.csv'):
                content = file.read().decode('utf-8')
                lines = content.strip().split('\n')
                if processing_type == 'messy':
                    try:
                        from agents.smart_messy_parser import SmartMessyParser
                        messy_parser = SmartMessyParser()
                        products = []
                        for line in lines:
                            if line.strip():
                                parsed = messy_parser.parse_messy_title(line.strip())
                                products.append(parsed)
                        titles = [p['original_title'] for p in products]
                        structured_products = products
                    except ImportError:
                        print("SmartMessyParser not available, falling back to simple parsing")
                        titles = [line.strip() for line in lines if line.strip()]
                        structured_products = None
                else:
                    titles = [line.strip() for line in lines if line.strip()]
                    structured_products = None
            elif file.filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
                if not df.empty:
                    first_col = df.columns[0]
                    titles = df[first_col].dropna().astype(str).tolist()
                    structured_products = None
                else:
                    titles = []
                    structured_products = None
            elif file.filename.lower().endswith('.txt'):
                content = file.read().decode('utf-8')
                titles = [line.strip() for line in content.split('\n') if line.strip()]
                structured_products = None
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported file format. Please use CSV, Excel, or TXT files. Please use UTF-8 encoded files.'
                }), 400
        except UnicodeDecodeError:
            return jsonify({
                'success': False,
                'error': 'File encoding error. Please use UTF-8 encoded files.'
            }), 400
        except Exception as e:
            print(f"Error parsing file: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'File parsing error: {str(e)}'
            }), 400
        print(f"Found {len(titles)} titles to process")

        # Initialize pipeline
        try:
            pipeline = CompletePipeline()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error initializing pipeline: {str(e)}'
            }), 500

        # Process titles
        results = []
        successful = 0
        for i, title in enumerate(titles):
            print(f"Processing title {i+1}/{len(titles)}: {title}")
            try:
                if processing_type == 'messy':
                    result = pipeline.process_raw_title(title)
                else:
                    if 'structured_products' in locals() and structured_products and i < len(structured_products):
                        product_data = structured_products[i]
                        print(f"   Using structured data: Dept={product_data.get('departamento', 'N/A')}, Cat={product_data.get('categoria', 'N/A')}")
                    else:
                        product_data = {
                            'description': title,
                            'original_title': title
                        }
                    category_match = pipeline.classifier.find_category_match(product_data)
                    if category_match:
                        optimized_title = pipeline.generator.generate_ecommerce_title(product_data, category_match)
                        store_label = pipeline.formatter.format_store_label(optimized_title) if optimized_title else None
                        result = {
                            'input_title': title,
                            'success': bool(optimized_title and store_label),
                            'category_match': category_match,
                            'optimized_title': optimized_title,
                            'store_label': store_label,
                            'errors': [] if optimized_title and store_label else ['Failed to generate title or label']
                        }
                    else:
                        result = {
                            'input_title': title,
                            'success': False,
                            'category_match': None,
                            'optimized_title': None,
                            'store_label': None,
                            'errors': ['No category match found']
                        }
                results.append(result)
                if result.get('success', False):
                    successful += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing title '{title}': {str(e)}")
                results.append({
                    'input_title': title,
                    'success': False,
                    'category_match': None,
                    'optimized_title': None,
                    'store_label': None,
                    'errors': [f'Processing error: {str(e)}']
                })
# Add processing review and quality analysis
        print(f"\n📊 ANALYZING PROCESSING QUALITY...")
        reviewer = ProcessingReviewer()
        
        # Generate quality report
        quality_report = reviewer.generate_quality_report(results)
        print(quality_report)
        
        # Export detailed results with quality metrics
        try:
            detailed_df = reviewer.export_detailed_csv(results, 'detailed_results_with_quality.csv')
            print(f"✅ Detailed results exported to: detailed_results_with_quality.csv")
        except Exception as e:
            print(f"⚠️  Could not export detailed CSV: {e}")
        
        # Get processing statistics from the generator
        if hasattr(pipeline.generator, 'get_processing_stats'):
            stats = pipeline.generator.get_processing_stats()
            print(f"\n📈 API STATISTICS:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'successful': successful,
            'errors': len(results) - successful
        })

    except Exception as e:
        print(f"Unexpected error in /process: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'pipeline_available': CompletePipeline is not None,
            'frontend_available': os.path.exists('frontend.html')
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Cemaco Title Processor...")
    print(f"Frontend available: {os.path.exists('frontend.html')}")
    print(f"Pipeline available: {CompletePipeline is not None}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)