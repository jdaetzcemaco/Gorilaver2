from agents.category_classifier import CategoryClassifier
from agents.title_generator import TitleGenerator  
from agents.label_formatter import LabelFormatter
from typing import Dict, Tuple
import json

class ProductTitlePipeline:
    def __init__(self, openai_api_key: str = None):
        """Initialize the 3-agent pipeline"""
        self.agent1 = CategoryClassifier()
        self.agent2 = TitleGenerator(openai_api_key)
        self.agent3 = LabelFormatter()
        
        print("✓ Pipeline initialized with 3 agents")
    
    def process_product(self, product_data: Dict) -> Dict:
        """
        Process a single product through all 3 agents
        
        Args:
            product_data: Product information dict
            
        Returns:
            Dict with original data, category match, full title, and store label
        """
        
        result = {
            'input': product_data,
            'category_match': None,
            'full_title': None,
            'store_label': None,
            'success': False,
            'errors': []
        }
        
        try:
            # Agent 1: Classify category
            print("🔍 Agent 1: Finding category match...")
            category_match = self.agent1.find_category_match(product_data)
            
            if not category_match:
                result['errors'].append("No category match found")
                return result
            
            result['category_match'] = category_match
            print(f"   ✓ Found: {category_match['categoria']}")
            
            # Agent 2: Generate ecommerce title
            print("📝 Agent 2: Generating ecommerce title...")
            full_title = self.agent2.generate_ecommerce_title(product_data, category_match)
            
            if not full_title:
                result['errors'].append("Failed to generate title")
                return result
                
            result['full_title'] = full_title
            print(f"   ✓ Generated ({len(full_title)} chars): {full_title}")
            
            # Agent 3: Create store label
            print("🏷️  Agent 3: Creating store label...")
            store_label = self.agent3.format_store_label(full_title)
            
            result['store_label'] = store_label
            result['success'] = True
            print(f"   ✓ Label ({len(store_label)} chars): {store_label}")
            
        except Exception as e:
            result['errors'].append(f"Pipeline error: {str(e)}")
            print(f"   ✗ Error: {e}")
        
        return result
    
    def process_batch(self, products: list) -> list:
        """Process multiple products"""
        results = []
        
        print(f"\n🚀 Processing {len(products)} products...\n")
        
        for i, product in enumerate(products, 1):
            print(f"--- Product {i}/{len(products)} ---")
            result = self.process_product(product)
            results.append(result)
            
            if result['success']:
                print("✅ Success!\n")
            else:
                print(f"❌ Failed: {', '.join(result['errors'])}\n")
        
        return results
    
    def print_summary(self, results: list):
        """Print processing summary"""
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Processed: {total} products")
        print(f"   Successful: {successful}")
        print(f"   Failed: {total - successful}")
        print(f"   Success rate: {(successful/total)*100:.1f}%")
        
        if successful > 0:
            print(f"\n✅ SUCCESSFUL RESULTS:")
            for i, result in enumerate([r for r in results if r['success']], 1):
                print(f"   {i}. {result['store_label']}")

def main():
    """Test the complete pipeline"""
    
    # Initialize pipeline
    pipeline = ProductTitlePipeline()
    
    # Test products
    test_products = [
        {
            'departamento': 'MATERIALES DE CONSTRUCCION',
            'familia': 'AISLANTE S',
            'categoria': 'FIBRA DE VIDRIO',
            'brand': 'Owens Corning',
            'r_value': 'R-13',
            'dimensions': '15"x93"x3.5"',
            'color': 'Gris',
            'description': 'Aislamiento térmico para construcción'
        },
        {
            'departamento': 'MATERIALES DE CONSTRUCCION', 
            'familia': 'AISLANTE S',
            'categoria': 'CASETON DE POLIESTIRENO',
            'brand': 'Technopor',
            'dimensions': '60x60x2cm',
            'color': 'Blanco',
            'description': 'Caseton para techo decorativo'
        },
        {
            'description': 'Grapas para aislante térmico 1000 piezas color azul'
        }
    ]
    
    # Process all products
    results = pipeline.process_batch(test_products)
    
    # Show summary
    pipeline.print_summary(results)
    
    # Save results to file
    with open('processing_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to processing_results.json")

if __name__ == "__main__":
    main()