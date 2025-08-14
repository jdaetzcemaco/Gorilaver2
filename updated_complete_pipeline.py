from agents.improved_title_parser import ImprovedTitleParser
from agents.improved_category_classifier import ImprovedCategoryClassifier
from agents.title_generator import TitleGenerator  
from agents.label_formatter import LabelFormatter
from typing import Dict, List
import json
import pandas as pd

class UpdatedCompletePipeline:
    def __init__(self, openai_api_key: str = None):
        """Initialize the improved 4-agent pipeline"""
        self.parser = ImprovedTitleParser(openai_api_key)        # NEW: Improved parser
        self.classifier = ImprovedCategoryClassifier()           # NEW: Improved classifier
        self.generator = TitleGenerator(openai_api_key)          # Agent 2: Generate titles
        self.formatter = LabelFormatter()                        # Agent 3: Create labels
        
        print("✓ Updated pipeline initialized with improved construction vocabulary")
    
    def process_raw_title(self, raw_title: str) -> Dict:
        """
        Process a raw title through the improved pipeline
        """
        
        result = {
            'input_title': raw_title,
            'parsed_data': None,
            'category_match': None,
            'optimized_title': None,
            'store_label': None,
            'success': False,
            'errors': [],
            'processing_details': {}
        }
        
        try:
            # Step 1: Parse with improved construction vocabulary
            print(f"🔍 Parsing: {raw_title}")
            parsed_data = self.parser.parse_title_to_product_data(raw_title)
            result['parsed_data'] = parsed_data
            
            detected_type = parsed_data.get('producto_tipo', 'Unknown')
            print(f"   ✓ Detected: {detected_type}")
            
            # Store parsing details
            result['processing_details']['detected_construction_terms'] = parsed_data.get('construction_analysis', {}).get('detected_terms', {})
            result['processing_details']['likely_category'] = parsed_data.get('categoria_especifica', 'Unknown')
            
            # Step 2: Find category with improved matching
            print("📂 Finding category with construction context...")
            category_match = self.classifier.find_category_match(parsed_data)
            
            if not category_match:
                result['errors'].append("No category match found even with improved parsing")
                return result
            
            result['category_match'] = category_match
            result['category_match'] = category_match
            confidence = category_match.get('confidence', 0.5)
            print(f"   ✓ Category: {category_match['categoria']} (confidence: {confidence:.2f})")
            
            # Step 3: Generate optimized title with better context
            print("📝 Generating optimized title...")
            
            # Enhanced product data for title generation
            enhanced_product_data = parsed_data.copy()
            enhanced_product_data.update({
                'category_info': category_match,
                'construction_context': parsed_data.get('construction_analysis', {})
            })
            
            optimized_title = self.generator.generate_ecommerce_title(enhanced_product_data, category_match)
            
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
            
            # Store additional processing details
            result['processing_details'].update({
                'match_type': category_match.get('match_type', 'unknown'),
                'parsing_method': 'improved_construction_aware',
                'construction_vocabulary_used': bool(parsed_data.get('construction_analysis', {}).get('detected_terms'))
            })
            
        except Exception as e:
            result['errors'].append(f"Pipeline error: {str(e)}")
            print(f"   ✗ Error: {e}")
        
        return result
    
    def process_title_list(self, titles: List[str]) -> List[Dict]:
        """Process multiple raw titles with detailed reporting"""
        
        results = []
        print(f"\n🚀 Processing {len(titles)} titles with improved construction vocabulary...\n")
        
        processing_stats = {
            'construction_vocab_detected': 0,
            'high_confidence_matches': 0,
            'improved_categorization': 0
        }
        
        for i, title in enumerate(titles, 1):
            print(f"--- Title {i}/{len(titles)} ---")
            result = self.process_raw_title(title)
            results.append(result)
            
            # Track improvement statistics
            if result['success']:
                details = result['processing_details']
                if details.get('construction_vocabulary_used'):
                    processing_stats['construction_vocab_detected'] += 1
                
                confidence = result['category_match'].get('confidence', 0)
                if confidence > 0.7:
                    processing_stats['high_confidence_matches'] += 1
                
                if details.get('match_type') in ['construction_aware', 'enhanced_keyword']:
                    processing_stats['improved_categorization'] += 1
                
                print("✅ Success!\n")
            else:
                print(f"❌ Failed: {', '.join(result['errors'])}\n")
        
        # Print improvement statistics
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        
        print(f"\n📊 PROCESSING IMPROVEMENT STATISTICS:")
        print(f"   Total processed: {total}")
        print(f"   Successful: {successful}")
        print(f"   Construction vocabulary detected: {processing_stats['construction_vocab_detected']}")
        print(f"   High confidence matches (>70%): {processing_stats['high_confidence_matches']}")
        print(f"   Improved categorization methods: {processing_stats['improved_categorization']}")
        print(f"   Overall success rate: {(successful/total)*100:.1f}%")
        
        return results
    
    def analyze_problematic_cases(self, titles: List[str]) -> Dict:
        """Special analysis for problematic cases"""
        
        print("🔬 ANALYZING PROBLEMATIC CASES WITH IMPROVED LOGIC:")
        print("=" * 70)
        
        analysis_results = {
            'cases': [],
            'improvements': [],
            'remaining_issues': []
        }
        
        for title in titles:
            print(f"\n🔍 ANALYZING: {title}")
            
            # Process with improved pipeline
            result = self.process_raw_title(title)
            
            # Detailed analysis
            case_analysis = {
                'original_title': title,
                'result': result,
                'analysis': {}
            }
            
            if result['success']:
                parsed = result['parsed_data']
                category = result['category_match']
                
                print(f"✅ IMPROVED RESULT:")
                print(f"   Original: {title}")
                print(f"   Detected Type: {parsed.get('producto_tipo', 'Unknown')}")
                print(f"   Category: {category['categoria']}")
                print(f"   Confidence: {category.get('confidence', 0):.2f}")
                print(f"   Match Method: {category.get('match_type', 'unknown')}")
                print(f"   Optimized: {result['optimized_title']}")
                print(f"   Label: {result['store_label']}")
                
                # Check for improvements
                construction_terms = parsed.get('construction_analysis', {}).get('detected_terms', {})
                if construction_terms:
                    print(f"   🎯 Construction vocabulary detected: {list(construction_terms.keys())}")
                    analysis_results['improvements'].append({
                        'title': title,
                        'improvement': f"Used construction vocabulary: {list(construction_terms.keys())}"
                    })
                
                case_analysis['analysis'] = {
                    'construction_vocabulary_used': bool(construction_terms),
                    'confidence_level': category.get('confidence', 0),
                    'categorization_method': category.get('match_type'),
                    'detected_product_type': parsed.get('producto_tipo')
                }
                
            else:
                print(f"❌ STILL PROBLEMATIC:")
                print(f"   Errors: {', '.join(result['errors'])}")
                analysis_results['remaining_issues'].append({
                    'title': title,
                    'errors': result['errors']
                })
            
            analysis_results['cases'].append(case_analysis)
            print("-" * 50)
        
        return analysis_results
    
    def save_detailed_results(self, results: List[Dict], output_path: str = "improved_results.csv"):
        """Save results with detailed improvement information"""
        
        output_data = []
        
        for result in results:
            row = {
                'original_title': result['input_title'],
                'success': result['success'],
                'optimized_title': result['optimized_title'] or 'FAILED',
                'store_label_36char': result['store_label'] or 'FAILED',
                'category_found': result['category_match']['categoria'] if result['category_match'] else 'NOT FOUND',
                'category_confidence': result['category_match'].get('confidence', 0) if result['category_match'] else 0,
                'match_type': result['category_match'].get('match_type', '') if result['category_match'] else '',
                'errors': '; '.join(result['errors']) if result['errors'] else ''
            }
            
            # Add improvement details
            if result['parsed_data']:
                parsed = result['parsed_data']
                row.update({
                    'detected_product_type': parsed.get('producto_tipo', ''),
                    'construction_vocab_detected': str(parsed.get('construction_analysis', {}).get('detected_terms', {})),
                    'specifications_extracted': parsed.get('especificaciones_tecnicas', ''),
                    'application_identified': parsed.get('aplicacion_construccion', '')
                })
            
            output_data.append(row)
        
        df = pd.DataFrame(output_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n💾 Detailed results saved to: {output_path}")
        return df

def test_improved_pipeline():
    """Test the improved pipeline with problematic cases"""
    
    pipeline = UpdatedCompletePipeline()
    
    # Test the specific problematic cases
    problematic_cases = [
        "CHAPA BARI DE BAÑO CROMO COBRE ANTIGUO",
        "TOR. PUNTA DE BROCA AR. 1/4 X 1 1/2",
        "GRIFO COCINA CROMADO MODERNO",
        "BROCA PARA CONCRETO 8MM HSS",
        "CERRADURA BAÑO CROMADA CILINDRICA"
    ]
    
    # Analyze improvements
    analysis = pipeline.analyze_problematic_cases(problematic_cases)
    
    # Process normally
    results = pipeline.process_title_list(problematic_cases)
    
    # Save detailed results
    pipeline.save_detailed_results(results)
    
    return results, analysis

if __name__ == "__main__":
    results, analysis = test_improved_pipeline()
