from agents.title_parser import TitleParser
from agents.category_classifier import CategoryClassifier
from agents.enhanced_title_generator import EnhancedTitleGenerator 
from agents.label_formatter import LabelFormatter
from typing import Dict, List
import json
import pandas as pd

class CompletePipeline:
    def __init__(self, openai_api_key: str = None):
        """Initialize the complete 4-agent pipeline"""
        self.parser = TitleParser(openai_api_key)                   # NEW: Extract info from raw titles
        self.classifier = CategoryClassifier()                      # Agent 1: Find category
        self.generator = EnhancedTitleGenerator(openai_api_key)     # Agent 2: Generate titles
        self.formatter = LabelFormatter()                           # Agent 3: Create labels
        
        print("✓ Complete pipeline initialized with 4 agents (Enhanced Title Generator)")
    
    def process_raw_title(self, raw_title: str) -> Dict:
        """
        Process a raw title through the complete pipeline
        
        Args:
            raw_title: Raw product title from user
            
        Returns:
            Dict with all processing results
        """
        
        result = {
            'input_title': raw_title,
            'parsed_data': None,
            'category_match': None,
            'optimized_title': None,
            'store_label': None,
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Parse raw title into structured data
            print(f"🔍 Parsing: {raw_title}")
            parsed_data = self.parser.parse_title_to_product_data(raw_title)
            result['parsed_data'] = parsed_data
            
            print(f"   ✓ Extracted: {parsed_data.get('producto_tipo', 'Unknown type')}")
            
            # Step 2: Find category match
            print("📂 Finding category...")
            category_match = self.classifier.find_category_match(parsed_data)
            
            if not category_match:
                # Try fuzzy matching with keywords
                category_match = self._fuzzy_category_search(parsed_data)
            
            if not category_match:
                result['errors'].append("No category match found")
                return result
            
            result['category_match'] = category_match
            print(f"   ✓ Category: {category_match['categoria']}")
            
            # Step 3: Generate optimized ecommerce title
            print("📝 Generating optimized title...")
            optimized_title = self.generator.generate_ecommerce_title(parsed_data, category_match)
            
            if not optimized_title:
                result['errors'].append("Failed to generate optimized title")
                return result
                
            result['optimized_title'] = optimized_title
            print(f"   ✓ Title ({len(optimized_title)} chars): {optimized_title}")
            
            # Step 4: Create store label
            print("🏷️  Creating store label...")
            store_label = self.formatter.format_store_label(optimized_title)
            
            result['store_label'] = store_label
            result['success'] = True
            print(f"   ✓ Label ({len(store_label)} chars): {store_label}")
            
        except Exception as e:
            result['errors'].append(f"Pipeline error: {str(e)}")
            print(f"   ✗ Error: {e}")
        
        return result
    
    def _fuzzy_category_search(self, parsed_data: Dict) -> Dict:
        """Try to find category match using keywords"""
        
        keywords = parsed_data.get('categoria_keywords', [])
        if not keywords:
            # Generate keywords from product type and description
            keywords = []
            if 'producto_tipo' in parsed_data:
                keywords.extend(parsed_data['producto_tipo'].split())
            if 'description' in parsed_data:
                keywords.extend(parsed_data['description'].split()[:5])  # First 5 words
        
        # Search categories that contain these keywords
        df = self.classifier.get_all_categories()
        
        best_match = None
        best_score = 0
        
        for _, row in df.iterrows():
            score = 0
            categoria = row['Categoria'].upper()
            
            for keyword in keywords:
                if keyword.upper() in categoria:
                    score += len(keyword)
            
            if score > best_score:
                best_score = score
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'fuzzy_keyword',
                    'score': score
                }
        
        return best_match if best_score > 0 else None
    
    def process_title_list(self, titles: List[str]) -> List[Dict]:
        """Process multiple raw titles"""
        
        results = []
        print(f"\n🚀 Processing {len(titles)} raw titles through complete pipeline...\n")
        
        for i, title in enumerate(titles, 1):
            print(f"--- Title {i}/{len(titles)} ---")
            result = self.process_raw_title(title)
            results.append(result)
            
            if result['success']:
                print("✅ Success!\n")
            else:
                print(f"❌ Failed: {', '.join(result['errors'])}\n")
        
        return results
    
    def save_results_to_csv(self, results: List[Dict], output_path: str = "processed_titles.csv"):
        """Save results to CSV format"""
        
        output_data = []
        
        for result in results:
            row = {
                'original_title': result['input_title'],
                'success': result['success'],
                'extracted_type': result['parsed_data'].get('producto_tipo') if result['parsed_data'] else '',
                'found_category': result['category_match']['categoria'] if result['category_match'] else 'NOT FOUND',
                'category_rule': result['category_match']['nomenclatura_sugerida'] if result['category_match'] else '',
                'optimized_title': result['optimized_title'] or 'FAILED',
                'store_label_36char': result['store_label'] or 'FAILED',
                'errors': '; '.join(result['errors']) if result['errors'] else ''
            }
            
            # Add parsed data fields
            if result['parsed_data']:
                row.update({
                    'extracted_brand': result['parsed_data'].get('brand'),
                    'extracted_color': result['parsed_data'].get('color'),
                    'extracted_specs': result['parsed_data'].get('specifications'),
                })
            
            output_data.append(row)
        
        df = pd.DataFrame(output_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Show summary
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"   Total titles: {total}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {total - successful}")
        print(f"   Success rate: {(successful/total)*100:.1f}%")
        print(f"\n💾 Results saved to: {output_path}")
        
        return df

def main():
    """Test with sample raw titles"""
    
    pipeline = CompletePipeline()
    
    # Test with messy, real-world titles
    test_titles = [
        "fibra vidrio r13 gris owens corning 15x93",
        "grapas azules para aislante 1000 piezas",
        "caseton blanco 60x60 decorativo techo",
        "tornillos galvanizados 1/4 x 2 pulgadas 100pz",
        "foam board xps r10 2 inch silver",
        "alambre galvanizado calibre 14 rollo 50m"
    ]
    
    # Process all titles
    results = pipeline.process_title_list(test_titles)
    
    # Save to CSV
    pipeline.save_results_to_csv(results)

if __name__ == "__main__":
    main()