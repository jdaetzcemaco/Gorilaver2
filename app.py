from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
import time
import pandas as pd
from typing import Dict

class SafeEnhancedTitleGenerator:
    """Wrapper to make EnhancedTitleGenerator safe for web interface"""
    
    def __init__(self, original_generator):
        self.original_generator = original_generator
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """Safe wrapper for title generation with comprehensive error handling"""
        
        try:
            # Try the enhanced generation
            title = self.original_generator.generate_ecommerce_title(product_data, category_info)
            
            # Ensure we got a valid string
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
        
        # Add category
        categoria = category_info.get('categoria', 'Product')
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
        
        # Join and clean up
        title = ' '.join(str(part) for part in parts if part)
        
        # Ensure we have something
        if not title:
            title = "Product Item"
        
        # Limit length
        if len(title) > 150:
            title = title[:147] + "..."
        
        return title
# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.tile_fixed_classifier import TileFixedCategoryClassifier
    from agents.enhanced_title_generator import EnhancedTitleGenerator
    from agents.label_formatter import LabelFormatter
    
    class SimpleTilePipeline:
    def __init__(self): # Note: proper indentation and __init__
        self.classifier = TileFixedCategoryClassifier()

        # Wrap the enhanced generator with safety
        try:
            from agents.enhanced_title_generator import EnhancedTitleGenerator
            original_generator = EnhancedTitleGenerator()
            self.generator = SafeEnhancedTitleGenerator(original_generator)
            print("✓ Using Enhanced TitleGenerator with safety wrapper")
        except Exception as e:
            print(f"⚠️ Enhanced generator failed to load: {e}")
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
                
                # Use smart messy parser for "messy" processing type
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
                        
                elif len(lines) > 1 and ',' in lines[0]:
                    # Regular structured CSV processing
                    products = []
                    headers = [h.strip().strip('"') for h in lines[0].split(',')]
                    print(f"CSV Headers detected: {headers}")
                    
                    for line in lines[1:]:
                        if line.strip():
                            values = [v.strip().strip('"') for v in line.split(',')]
                            product = {}
                            
                            for i, header in enumerate(headers):
                                if i < len(values) and values[i]:
                                    header_lower = header.lower()
                                    if any(h in header_lower for h in ['titulo', 'title', 'nombre']):
                                        product['description'] = values[i]
                                        product['original_title'] = values[i]
                                    elif 'departamento' in header_lower:
                                        product['departamento'] = values[i]
                                    elif 'familia' in header_lower:
                                        product['familia'] = values[i]
                                    elif 'categoria' in header_lower:
                                        product['categoria'] = values[i]
                            
                            if 'description' not in product and values:
                                product['description'] = values[0]
                                product['original_title'] = values[0]
                            
                            products.append(product)
                    
                    titles = [p.get('description', p.get('original_title', '')) for p in products]
                    structured_products = products
                    
                else:
                    # No header or not CSV format, treat as plain text
                    titles = [line.strip() for line in lines if line.strip()]
                    structured_products = None
                            
            elif file.filename.lower().endswith(('.xlsx', '.xls')):
                # Read Excel file
                try:
                    df = pd.read_excel(file)
                    # Get first column
                    titles = df.iloc[:, 0].dropna().astype(str).tolist()
                    structured_products = None
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error reading Excel file: {str(e)}'
                    }), 400
                            
            else:
                # Plain text file
                content = file.read().decode('utf-8')
                titles = [line.strip() for line in content.strip().split('\n') if line.strip()]
                structured_products = None

        except UnicodeDecodeError:
            return jsonify({
                'success': False,
                'error': 'File encoding not supported. Please use UTF-8 encoded files.'
            }), 400

        if not titles:
            return jsonify({
                'success': False,
                'error': 'No valid titles found in file'
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
                    # Use the complete pipeline for raw titles
                    result = pipeline.process_raw_title(title)
                else:
                    # For structured data, use the structured product info
                    if 'structured_products' in locals() and structured_products and i < len(structured_products):
                        product_data = structured_products[i]
                        print(f"   Using structured data: Dept={product_data.get('departamento', 'N/A')}, Cat={product_data.get('categoria', 'N/A')}")
                    else:
                        # Fallback to simple product dict
                        product_data = {
                            'description': title,
                            'original_title': title
                        }
                    
                    # Find category
                    category_match = pipeline.classifier.find_category_match(product_data)
                    
                    if category_match:
                        # Generate title
                        optimized_title = pipeline.generator.generate_ecommerce_title(product_data, category_match)
                        
                        # Create label
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
                    
                # Add small delay to simulate processing
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
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Cemaco Title Processor...")
    print(f"Frontend available: {os.path.exists('frontend.html')}")
    print(f"Pipeline available: {CompletePipeline is not None}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)