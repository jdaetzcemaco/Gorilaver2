import openai
import os
import json
import re
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

class RobustEnhancedTitleGenerator:
    def __init__(self, api_key: str = None):
        """Initialize OpenAI client with web search capabilities"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self._last_research_data = {}  # Store last research for debugging
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """
        Generate SEO-optimized ecommerce title with web research validation
        """
        
        try:
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
            
        except Exception as e:
            print(f"   ⚠️  Enhanced generation failed: {e}")
            # Fallback to basic title generation
            return self._create_enhanced_fallback_title(product_data, category_info)
    
    def _safe_json_parse(self, text: str) -> Dict:
        """Safely parse JSON with multiple fallback strategies"""
        
        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Clean up markdown formatting
        try:
            cleaned = text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            elif cleaned.startswith('```'):
                cleaned = cleaned.replace('```', '').strip()
            
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract JSON from text using regex
        try:
            json_pattern = r'\{[^{}]*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            if matches:
                # Try the largest match (most likely to be complete)
                largest_match = max(matches, key=len)
                return json.loads(largest_match)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Strategy 4: Extract key-value pairs manually
        try:
            result = {}
            
            # Look for common patterns
            patterns = {
                'verified_brand': r'"verified_brand":\s*"([^"]*)"',
                'verified_product_type': r'"verified_product_type":\s*"([^"]*)"',
                'product_category': r'"product_category":\s*"([^"]*)"',
                'is_construction_hardware': r'"is_construction_hardware":\s*(true|false)',
                'category_makes_sense': r'"category_makes_sense":\s*(true|false)',
                'confidence': r'"confidence":\s*([0-9.]+)',
                'recommendation': r'"recommendation":\s*"([^"]*)"'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if key in ['is_construction_hardware', 'category_makes_sense']:
                        result[key] = value.lower() == 'true'
                    elif key == 'confidence':
                        result[key] = float(value)
                    else:
                        result[key] = value
            
            if result:
                return result
                
        except Exception:
            pass
        
        # Strategy 5: Return error object
        return {'error': 'JSON parsing failed', 'raw_response': text[:200] + '...' if len(text) > 200 else text}
    
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
            research_prompt = f"""Analyze this product and provide market information. Respond with valid JSON only.

PRODUCT: {search_query}

Provide JSON with these exact fields:
{{
    "verified_brand": "Brand name or empty if unknown",
    "verified_product_type": "What this product actually is",
    "product_category": "Department/category this belongs to",
    "seo_keywords": ["keyword1", "keyword2", "keyword3"],
    "is_construction_hardware": true or false,
    "suggested_department": "Best department for this product"
}}

IMPORTANT: Return only valid JSON, no additional text or formatting."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a product expert. Always respond with valid JSON only, no markdown or extra text."},
                    {"role": "user", "content": research_prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            # Parse research results with robust error handling
            research_text = response.choices[0].message.content.strip()
            research_data = self._safe_json_parse(research_text)
            
            if 'error' not in research_data:
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
            else:
                print(f"   ⚠️  Web research parsing failed: {research_data.get('error', 'Unknown error')}")
                enhanced_data['web_research'] = research_data
                self._last_research_data = research_data
        
        except Exception as e:
            print(f"   ⚠️  Web research failed: {e}")
            enhanced_data['web_research'] = {'error': str(e)}
            self._last_research_data = {'error': str(e)}
        
        return enhanced_data
    
    def _validate_category_with_web_search(self, product_data: Dict, category_info: Dict) -> Dict:
        """Validate if the assigned category makes sense based on web research"""

        # Defensive: ensure category_info is a dict
        if category_info is None:
            category_info = {}

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

        if not suggested_category:
            return validation_result

        try:
            # Ask AI to compare categories
            comparison_prompt = f"""Compare these product categorizations. Respond with valid JSON only.

PRODUCT: {product_data.get('original_title', 'Unknown')}
VERIFIED TYPE: {verified_product_type}

CURRENT: {category_info.get('categoria', 'Unknown')}
SUGGESTED: {suggested_category}

Return JSON with these exact fields:
{{
    "category_makes_sense": true or false,
    "confidence": 0.5,
    "recommendation": "keep_current" or "use_research",
    "reasoning": "Brief explanation"
}}

IMPORTANT: Return only valid JSON, no additional text."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a categorization expert. Always respond with valid JSON only."},
                    {"role": "user", "content": comparison_prompt}
                ],
                temperature=0.1,
                max_tokens=250
            )

            validation_text = response.choices[0].message.content.strip()
            validation_data = self._safe_json_parse(validation_text)

            if 'error' not in validation_data:
                validation_result['validation_passed'] = validation_data.get('category_makes_sense', True)
                validation_result['confidence'] = validation_data.get('confidence', 0.5)

                # If category doesn't make sense, create a corrected version
                if not validation_data.get('category_makes_sense', True):
                    corrected_category = category_info.copy()
                    corrected_category['categoria'] = suggested_category
                    corrected_category['web_research_corrected'] = True
                    corrected_category['original_categoria'] = category_info.get('categoria')
                    corrected_category['correction_reason'] = validation_data.get('reasoning', 'Category mismatch detected')

                    validation_result['corrected_category'] = corrected_category
                    print(f"   ⚠️  Category corrected: {category_info.get('categoria')} → {suggested_category}")
                    print(f"      Reason: {validation_data.get('reasoning', 'Category mismatch detected')}")
            else:
                print(f"   ⚠️  Category validation parsing failed: {validation_data.get('error', 'Unknown')}")

        except Exception as e:
            print(f"   ⚠️  Category validation failed: {e}")

        return validation_result
    
    def _generate_title_with_context(self, enhanced_product_data: Dict, category_info: Dict) -> str:
        """Generate title using enhanced product data and validated category"""

        # Defensive: ensure category_info is a dict
        if category_info is None:
            category_info = {}

        naming_rule = category_info.get('nomenclatura_sugerida', 'Marca + Tipo + Especificaciones')
        example = category_info.get('ejemplo_aplicado', '')
        category = category_info.get('categoria', 'General')
        was_corrected = category_info.get('web_research_corrected', False)
        
        # Use verified information from web research when available
        verified_brand = enhanced_product_data.get('verified_brand', enhanced_product_data.get('brand', ''))
        verified_type = enhanced_product_data.get('verified_product_type', enhanced_product_data.get('producto_tipo', ''))
        seo_keywords = enhanced_product_data.get('seo_keywords', [])
        
        # Check if category was corrected
        was_corrected = category_info.get('web_research_corrected', False)
        
        # Build enhanced prompt
        prompt = f"""Create an optimized ecommerce title for this product.

PRODUCT INFO:
- Original: {enhanced_product_data.get('original_title', 'Unknown')}
- Verified Type: {verified_type or 'Unknown Type'}
- Brand: {verified_brand or 'Generic'}
- Category: {category}

NAMING RULES:
- Format: {naming_rule}
- Example: {example}

REQUIREMENTS:
- Follow the naming format above
- Include brand, type, and key specifications
- Keep under 150 characters
- Use professional formatting
- Include important keywords naturally

Generate ONE optimized title that follows the format and will appeal to customers."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an ecommerce title expert. Create compelling, professional product titles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            title = response.choices[0].message.content.strip()
            
            # Clean up any quotes or extra formatting
            title = title.replace('"', '').replace("'", "").strip()
            
            # Remove any leading numbers or bullets if present
            title = re.sub(r'^\d+\.\s*', '', title)
            title = re.sub(r'^[-•]\s*', '', title)
            
            return title
            
        except Exception as e:
            print(f"   ⚠️  Title generation failed: {e}")
            # Fallback: create basic title from enhanced data
            return self._create_enhanced_fallback_title(enhanced_product_data, category_info)
    
    def _create_enhanced_fallback_title(self, product_data: Dict, category_info: Dict) -> str:
        """Create a fallback title using enhanced data"""

        # Defensive: ensure category_info is a dict
        if category_info is None:
            category_info = {}

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
# For backward compatibility, create an alias
EnhancedTitleGenerator = RobustEnhancedTitleGenerator