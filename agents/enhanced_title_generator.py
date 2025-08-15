import openai
import os
import json
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

class EnhancedTitleGenerator:
    def __init__(self, api_key: str = None):
        """Initialize OpenAI client with web search capabilities"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self._last_research_data = {}  # Store last research for debugging
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """
        Generate SEO-optimized ecommerce title with web research validation
        
        Args:
            product_data: Product information (brand, specs, color, etc.)
            category_info: Category rules from Agent 1
            
        Returns:
            Optimized ecommerce title string
        """
        
        # Step 1: Validate and enhance product information with web research
        enhanced_product_data = self._enhance_with_web_research(product_data)
        
        # Step 2: Verify category classification makes sense
        category_validation = self._validate_category_with_web_search(
            enhanced_product_data, category_info
        )
        
        # Step 3: Use best available category information
        final_category_info = category_validation.get('corrected_category', category_info)
        
        # Step 4: Generate title with enriched data
        return self._generate_title_with_context(enhanced_product_data, final_category_info)
    
    def _enhance_with_web_research(self, product_data: Dict) -> Dict:
        """Enhance product data by researching current market information"""
        
        enhanced_data = product_data.copy()
        
        # Extract key product identifiers for search
        search_terms = []
        
        # Get brand if available
        if 'brand' in product_data:
            search_terms.append(product_data['brand'])
        
        # Get product type/description
        for field in ['producto_tipo', 'description', 'original_title']:
            if field in product_data and product_data[field]:
                # Take first few meaningful words
                words = product_data[field].split()[:4]
                search_terms.extend(words)
                break
        
        # Construct search query
        search_query = ' '.join(search_terms[:6])  # Limit to avoid too long queries
        
        try:
            # Use OpenAI to research the product and get market context
            research_prompt = f"""You are a product research specialist focusing on construction and hardware products. Research this product and provide current market information:

PRODUCT TO RESEARCH: {search_query}

Analyze this product and provide a JSON response with:
{{
    "verified_brand": "Most likely correct brand name or empty string if unknown",
    "verified_product_type": "What type of product this actually is (be specific)",
    "product_category": "What department/category this product belongs to",
    "common_specifications": ["list", "of", "typical", "specs", "for", "this", "product"],
    "seo_keywords": ["important", "keywords", "for", "ecommerce"],
    "typical_naming_pattern": "How products like this are usually named",
    "is_construction_hardware": true or false,
    "suggested_department": "Construction/Hardware department if applicable"
}}

Focus on construction, hardware, plumbing, electrical, and home improvement context. Be accurate and specific.

IMPORTANT: Respond with valid JSON only, no additional text."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a product research expert specializing in construction and hardware products. Always respond with valid JSON."},
                    {"role": "user", "content": research_prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            # Parse research results
            research_text = response.choices[0].message.content.strip()
            
            # Clean up JSON if it has markdown formatting
            if research_text.startswith('```json'):
                research_text = research_text.replace('```json', '').replace('```', '').strip()
            
            try:
                research_data = json.loads(research_text)
                
                # Enhance original data with research findings
                enhanced_data['web_research'] = research_data
                enhanced_data['verified_brand'] = research_data.get('verified_brand', product_data.get('brand', ''))
                enhanced_data['verified_product_type'] = research_data.get('verified_product_type', product_data.get('producto_tipo', ''))
                enhanced_data['seo_keywords'] = research_data.get('seo_keywords', [])
                enhanced_data['suggested_category'] = research_data.get('product_category', '')
                enhanced_data['is_construction_hardware'] = research_data.get('is_construction_hardware', False)
                
                # Store for debugging
                self._last_research_data = research_data
                
                print(f"   ✓ Web research enhanced: {research_data.get('verified_product_type', 'Unknown')}")
                
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Could not parse research JSON: {e}")
                enhanced_data['web_research'] = {'error': 'JSON parse failed', 'raw_response': research_text}
                self._last_research_data = {'error': 'JSON parse failed'}
        
        except Exception as e:
            print(f"   ⚠️  Web research failed: {e}")
            enhanced_data['web_research'] = {'error': str(e)}
            self._last_research_data = {'error': str(e)}
        
        return enhanced_data
    
    def _validate_category_with_web_search(self, product_data: Dict, category_info: Dict) -> Dict:
        """Validate if the assigned category makes sense based on web research"""
        
        validation_result = {
            'original_category': category_info,
            'validation_passed': True,
            'confidence': 0.8,
            'corrected_category': None
        }
        
        # Check if we have web research data
        web_research = product_data.get('web_research', {})
        if 'error' in web_research:
            return validation_result
        
        suggested_category = web_research.get('product_category', '')
        verified_product_type = web_research.get('verified_product_type', '')
        is_construction_hardware = web_research.get('is_construction_hardware', False)
        
        if not suggested_category:
            return validation_result
        
        try:
            # Ask AI to compare categories
            comparison_prompt = f"""Compare these product categorizations and determine which is more accurate:

PRODUCT: {product_data.get('original_title', 'Unknown')}
VERIFIED TYPE: {verified_product_type}
IS CONSTRUCTION/HARDWARE: {is_construction_hardware}

CURRENT CLASSIFICATION:
- Category: {category_info.get('categoria', 'Unknown')}
- Department: {category_info.get('departamento', 'Unknown')}
- Family: {category_info.get('familia', 'Unknown')}

WEB RESEARCH SUGGESTS:
- Product Category: {suggested_category}
- Department: {web_research.get('suggested_department', 'Unknown')}

Analysis Questions:
1. Does the current category make sense for this product type?
2. Is there a significant mismatch between categories?
3. Which classification is more accurate for ecommerce purposes?

Respond with JSON only:
{{
    "category_makes_sense": true or false,
    "confidence": 0.0 to 1.0,
    "recommendation": "keep_current" or "use_research" or "needs_review",
    "reasoning": "Brief explanation of your decision",
    "severity": "low" or "medium" or "high" 
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a product categorization expert. Always respond with valid JSON."},
                    {"role": "user", "content": comparison_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            validation_text = response.choices[0].message.content.strip()
            
            # Clean up JSON formatting
            if validation_text.startswith('```json'):
                validation_text = validation_text.replace('```json', '').replace('```', '').strip()
            
            validation_data = json.loads(validation_text)
            
            validation_result['validation_passed'] = validation_data.get('category_makes_sense', True)
            validation_result['confidence'] = validation_data.get('confidence', 0.5)
            
            # If category doesn't make sense, create a corrected version
            if not validation_data.get('category_makes_sense', True) and validation_data.get('severity') in ['medium', 'high']:
                corrected_category = category_info.copy()
                corrected_category['categoria'] = suggested_category
                corrected_category['web_research_corrected'] = True
                corrected_category['original_categoria'] = category_info.get('categoria')
                corrected_category['correction_reason'] = validation_data.get('reasoning', 'Web research suggested different category')
                
                validation_result['corrected_category'] = corrected_category
                print(f"   ⚠️  Category corrected: {category_info.get('categoria')} → {suggested_category}")
                print(f"      Reason: {validation_data.get('reasoning', 'Category mismatch detected')}")
            
        except Exception as e:
            print(f"   ⚠️  Category validation failed: {e}")
        
        return validation_result
    
    def _generate_title_with_context(self, enhanced_product_data: Dict, category_info: Dict) -> str:
        """Generate title using enhanced product data and validated category"""
        
        # Extract the naming format from category info
        naming_rule = category_info.get('nomenclatura_sugerida', 'Marca + Tipo + Especificaciones')
        example = category_info.get('ejemplo_aplicado', '')
        category = category_info.get('categoria', 'General')
        
        # Use verified information from web research when available
        verified_brand = enhanced_product_data.get('verified_brand', enhanced_product_data.get('brand', ''))
        verified_type = enhanced_product_data.get('verified_product_type', enhanced_product_data.get('producto_tipo', ''))
        seo_keywords = enhanced_product_data.get('seo_keywords', [])
        
        # Check if category was corrected
        was_corrected = category_info.get('web_research_corrected', False)
        correction_note = f" (CORRECTED from {category_info.get('original_categoria', 'unknown')})" if was_corrected else ""
        
        # Build enhanced prompt
        prompt = f"""You are an expert ecommerce title specialist with access to current market research. Create a compelling, SEO-optimized product title for a construction/hardware product.

PRODUCT RESEARCH FINDINGS:
- Original Input: {enhanced_product_data.get('original_title', 'Unknown')}
- Verified Brand: {verified_brand or 'Unknown Brand'}
- Verified Product Type: {verified_type or 'Unknown Type'}
- SEO Keywords: {', '.join(seo_keywords[:5]) if seo_keywords else 'None found'}
- Category{correction_note}: {category}

CATEGORY NAMING RULES:
- Format: {naming_rule}
- Example: {example}

PRODUCT SPECIFICATIONS:
{self._format_product_data(enhanced_product_data)}

TITLE GENERATION INSTRUCTIONS:
1. Use VERIFIED brand and product type when available
2. Follow the category naming format: {naming_rule}
3. Include important SEO keywords naturally
4. Make it specific and compelling for customers
5. Include key specifications (size, color, material, finish, etc.)
6. Keep under 150 characters for optimal ecommerce display
7. Use proper capitalization and professional formatting
8. Prioritize the most important product attributes first
9. Ensure the title accurately represents what the customer will receive

Generate ONE optimized ecommerce title that will drive sales and rank well in search results."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert ecommerce title writer specializing in construction and hardware products. You create titles that convert sales and rank well in search."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            title = response.choices[0].message.content.strip()
            
            # Clean up any quotes or extra formatting
            title = title.replace('"', '').replace("'", "").strip()
            
            # Remove any leading numbers or bullets if present
            import re
            title = re.sub(r'^\d+\.\s*', '', title)
            title = re.sub(r'^[-•]\s*', '', title)
            
            return title
            
        except Exception as e:
            print(f"Error generating enhanced title: {e}")
            # Fallback: create basic title from enhanced data
            return self._create_enhanced_fallback_title(enhanced_product_data, category_info)
    
    def _format_product_data(self, product_data: Dict) -> str:
        """Format product data for the prompt, prioritizing verified information"""
        formatted = []
        
        # Priority fields from web research
        priority_fields = ['verified_brand', 'verified_product_type']
        
        for field in priority_fields:
            if field in product_data and product_data[field]:
                display_name = field.replace('verified_', '').replace('_', ' ').title()
                formatted.append(f"- {display_name}: {product_data[field]}")
        
        # Other relevant fields (skip internal/debug fields)
        skip_fields = ['web_research', 'verified_brand', 'verified_product_type', 'seo_keywords', 'suggested_category']
        
        for key, value in product_data.items():
            if key not in skip_fields and value and str(value).strip():
                display_name = key.replace('_', ' ').title()
                formatted.append(f"- {display_name}: {value}")
        
        return "\n".join(formatted) if formatted else "- No additional specifications available"
    
    def _create_enhanced_fallback_title(self, product_data: Dict, category_info: Dict) -> str:
        """Create a fallback title using enhanced data"""
        parts = []
        
        # Use verified brand if available
        brand = product_data.get('verified_brand') or product_data.get('brand', '')
        if brand and brand.strip():
            parts.append(brand.strip())
        
        # Use verified product type
        product_type = (product_data.get('verified_product_type') or 
                       product_data.get('producto_tipo', '') or 
                       category_info.get('categoria', ''))
        if product_type and product_type.strip():
            parts.append(product_type.strip().title())
        
        # Add key specifications
        for key in ['dimensions', 'size', 'color', 'model', 'material', 'finish']:
            if key in product_data and product_data[key] and str(product_data[key]).strip():
                parts.append(str(product_data[key]).strip())
        
        # Add SEO keywords if available and we need more content
        seo_keywords = product_data.get('seo_keywords', [])
        if seo_keywords and len(parts) < 4:
            parts.extend([kw for kw in seo_keywords[:2] if kw not in ' '.join(parts)])
        
        # Ensure we have at least something
        if not parts:
            parts = [product_data.get('original_title', 'Product')]
        
        return " ".join(parts)
    
    def test_enhanced_generator(self):
        """Test the enhanced title generator with problematic cases"""
        
        test_cases = [
            {
                'name': 'Door Lock Misclassified as PVC Pipe',
                'product_data': {
                    'original_title': 'CHAPA BARI DE BAÑO CROMO COBRE ANTIGUO',
                    'brand': 'BARI',
                    'description': 'Chapa para baño con acabado cromo cobre antiguo',
                    'producto_tipo': 'chapa/cerradura para baño'
                },
                'wrong_category_info': {
                    'categoria': 'TUBERIA PVC',
                    'nomenclatura_sugerida': 'Diámetro + Longitud + Presión',
                    'ejemplo_aplicado': 'Tubo PVC 4" x 6m 250PSI'
                }
            },
            {
                'name': 'Screw Misclassified as Drill Bit',
                'product_data': {
                    'original_title': 'TOR. PUNTA DE BROCA AR. 1/4 X 1 1/2',
                    'description': 'Tornillo autorroscante con punta de broca',
                    'producto_tipo': 'tornillo autorroscante'
                },
                'wrong_category_info': {
                    'categoria': 'BROCAS Y MECHAS',
                    'nomenclatura_sugerida': 'Tipo + Diámetro + Material',
                    'ejemplo_aplicado': 'Broca HSS 1/4" Acero'
                }
            }
        ]
        
        print("🧪 Testing Enhanced Title Generator")
        print("=" * 70)
        
        for test_case in test_cases:
            print(f"\n🔍 TEST: {test_case['name']}")
            print(f"Product: {test_case['product_data']['original_title']}")
            print(f"Wrong Category: {test_case['wrong_category_info']['categoria']}")
            print("-" * 50)
            
            title = self.generate_ecommerce_title(
                test_case['product_data'], 
                test_case['wrong_category_info']
            )
            
            print(f"✨ ENHANCED TITLE: {title}")
            print(f"📏 Length: {len(title)} characters")
            
            # Show research data if available
            if hasattr(self, '_last_research_data') and self._last_research_data:
                research = self._last_research_data
                if 'error' not in research:
                    print(f"🔬 Research Found: {research.get('verified_product_type', 'N/A')}")
                    print(f"🏷️  Suggested Category: {research.get('product_category', 'N/A')}")
            
            print("=" * 70)

if __name__ == "__main__":
    # Test the enhanced generator
    generator = EnhancedTitleGenerator()
    generator.test_enhanced_generator()