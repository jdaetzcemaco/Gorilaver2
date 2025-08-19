# agents/enhanced_title_generator.py (ROBUST VERSION)
import json
import re
import time
from typing import Dict, List, Optional
from openai import OpenAI
import random

class RobustEnhancedTitleGenerator:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key and robust settings"""
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.web_search_enabled = True
            print("✓ Robust Enhanced Title Generator with web search initialized")
        else:
            self.client = None
            self.web_search_enabled = False
            print("⚠️  Enhanced Title Generator initialized without web search (no API key)")
        
        self._last_research_data = {}
        self.api_call_count = 0
        self.failed_requests = 0
        self.successful_requests = 0
        
        # Rate limiting settings
        self.base_delay = 0.5  # Base delay between requests
        self.max_retries = 3
        self.backoff_multiplier = 2
    
    def _safe_api_call(self, prompt: str, max_tokens: int = 300, retries: int = 3) -> Optional[str]:
        """Make a safe API call with retries and exponential backoff"""
        
        for attempt in range(retries):
            try:
                # Progressive delay to avoid rate limits
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                if attempt > 0:
                    print(f"   🔄 Retry attempt {attempt + 1}/{retries} (waiting {delay:.1f}s)")
                    time.sleep(delay)
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a product expert. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=max_tokens,
                    timeout=15  # 15 second timeout
                )
                
                self.api_call_count += 1
                self.successful_requests += 1
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                self.failed_requests += 1
                error_msg = str(e).lower()
                
                if "rate limit" in error_msg:
                    print(f"   ⚠️  Rate limit hit, waiting longer...")
                    time.sleep(5 + (attempt * 2))  # Longer wait for rate limits
                elif "timeout" in error_msg:
                    print(f"   ⚠️  Timeout on attempt {attempt + 1}")
                else:
                    print(f"   ⚠️  API error: {str(e)[:50]}...")
                
                if attempt == retries - 1:
                    print(f"   ❌ All {retries} attempts failed")
                    return None
        
        return None
    
    def _extract_json_safely(self, text: str) -> Optional[dict]:
        """Extract JSON from text with multiple fallback strategies"""
        
        if not text:
            return None
        
        # Strategy 1: Direct JSON parse
        try:
            return json.loads(text)
        except:
            pass
        
        # Strategy 2: Remove markdown formatting
        try:
            cleaned = text.strip()
            if '```json' in cleaned:
                start = cleaned.find('{')
                end = cleaned.rfind('}') + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]
            elif '```' in cleaned:
                lines = cleaned.split('\n')
                json_lines = [line for line in lines if not line.strip().startswith('```')]
                cleaned = '\n'.join(json_lines)
            
            return json.loads(cleaned)
        except:
            pass
        
        # Strategy 3: Find JSON block in text
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_block = text[start:end]
                return json.loads(json_block)
        except:
            pass
        
        # Strategy 4: Try to fix common JSON issues
        try:
            # Fix common issues like trailing commas, single quotes, etc.
            fixed = text.strip()
            fixed = re.sub(r',\s*}', '}', fixed)  # Remove trailing commas
            fixed = re.sub(r',\s*]', ']', fixed)  # Remove trailing commas in arrays
            fixed = fixed.replace("'", '"')  # Replace single quotes
            return json.loads(fixed)
        except:
            pass
        
        return None
    
    def _enhance_with_web_search(self, product_data: Dict) -> Dict:
        """Enhanced web search with comprehensive error handling"""
        enhanced_data = product_data.copy()
        
        if not self.web_search_enabled:
            print("   ⚠️  Web search disabled (no API key)")
            return enhanced_data
        
        try:
            # Create search query
            title = product_data.get('original_title', product_data.get('description', ''))
            brand = product_data.get('brand', '')
            product_type = product_data.get('producto_tipo', '')
            
            search_query = f"{title} {brand} {product_type}".strip()
            
            print(f"   🔍 Researching: {search_query[:50]}...")
            
            # Simplified, robust prompt
            research_prompt = f"""Analyze this construction/hardware product: {search_query}

Return ONLY this JSON (no other text):
{{
    "verified_product_type": "specific product type",
    "product_category": "department category",
    "is_construction_hardware": true,
    "confidence": 0.8
}}"""

            # Make safe API call
            research_text = self._safe_api_call(research_prompt, max_tokens=200, retries=3)
            
            if not research_text:
                print("   ⚠️  API call failed completely, using fallback")
                enhanced_data['web_research'] = {
                    'error': 'api_failed',
                    'fallback_used': True
                }
                enhanced_data['verified_product_type'] = title
                enhanced_data['is_construction_hardware'] = True
                return enhanced_data
            
            # Extract JSON safely
            research_data = self._extract_json_safely(research_text)
            
            if research_data and isinstance(research_data, dict):
                # Validate required fields
                required_fields = ['verified_product_type']
                if all(field in research_data for field in required_fields):
                    # Success!
                    enhanced_data['web_research'] = research_data
                    enhanced_data['verified_product_type'] = research_data.get('verified_product_type', title)
                    enhanced_data['is_construction_hardware'] = research_data.get('is_construction_hardware', True)
                    enhanced_data['research_confidence'] = research_data.get('confidence', 0.8)
                    
                    print(f"   ✓ Web research enhanced: {research_data.get('verified_product_type', 'Unknown')}")
                    return enhanced_data
            
            # If we get here, JSON parsing failed
            print("   ⚠️  JSON parsing failed, using intelligent fallback")
            
            # Intelligent fallback - extract what we can from the text
            fallback_type = title
            if research_text:
                # Try to extract product type from text even if JSON failed
                type_patterns = [
                    r'"verified_product_type":\s*"([^"]+)"',
                    r'product.type.*?:\s*"?([^",\n]+)',
                    r'type.*?:\s*([A-Za-z\s]+)'
                ]
                for pattern in type_patterns:
                    match = re.search(pattern, research_text, re.IGNORECASE)
                    if match:
                        fallback_type = match.group(1).strip()
                        break
            
            enhanced_data['web_research'] = {
                'error': 'json_parse_failed',
                'raw_response': research_text[:100] if research_text else 'No response',
                'fallback_used': True
            }
            enhanced_data['verified_product_type'] = fallback_type
            enhanced_data['is_construction_hardware'] = True
            enhanced_data['research_confidence'] = 0.3  # Low confidence for fallback
            
            print(f"   ⚠️  Using fallback type: {fallback_type}")
            
        except Exception as e:
            print(f"   ❌ Web research failed completely: {str(e)[:50]}...")
            enhanced_data['web_research'] = {
                'error': 'complete_failure',
                'error_details': str(e)[:100]
            }
            enhanced_data['verified_product_type'] = product_data.get('original_title', 'Unknown')
            enhanced_data['is_construction_hardware'] = True
            enhanced_data['research_confidence'] = 0.1
        
        return enhanced_data
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """Generate optimized ecommerce title with robust error handling"""
        
        try:
            # Enhance with web search
            enhanced_data = self._enhance_with_web_search(product_data)
            
            # Extract key information with multiple fallbacks
            brand = (enhanced_data.get('verified_brand') or 
                    enhanced_data.get('brand', '') or 
                    self._extract_brand_from_title(enhanced_data.get('original_title', '')))
            
            product_type = (enhanced_data.get('verified_product_type') or 
                           enhanced_data.get('producto_tipo', '') or
                           enhanced_data.get('original_title', ''))
            
            specifications = enhanced_data.get('specifications', enhanced_data.get('especificaciones', ''))
            color = enhanced_data.get('color', '')
            
            # Build optimized title intelligently
            title_parts = []
            
            # Start with verified product type
            if product_type and len(product_type.strip()) > 3:
                # Clean and format product type
                clean_type = product_type.strip().title()
                # Remove redundant words
                clean_type = re.sub(r'\b(Product|Item|Producto)\b', '', clean_type, flags=re.IGNORECASE).strip()
                if clean_type:
                    title_parts.append(clean_type)
            
            # Add specifications if meaningful
            if specifications and len(specifications.strip()) > 2:
                specs = specifications.strip()
                if not any(spec.lower() in product_type.lower() for spec in specs.split()):
                    title_parts.append(specs)
            
            # Add color if specific
            if color and len(color.strip()) > 2 and color.lower() not in ['n/a', 'none', 'standard']:
                title_parts.append(color.title())
            
            # Add brand if reliable
            if brand and len(brand.strip()) > 2 and brand.lower() not in ['n/a', 'unknown', 'generic']:
                title_parts.append(brand)
            
            # Construct final title
            if title_parts:
                optimized_title = ' '.join(title_parts)
                # Clean up the title
                optimized_title = re.sub(r'\s+', ' ', optimized_title).strip()
                optimized_title = optimized_title[:60]  # Reasonable length limit
            else:
                # Ultimate fallback
                optimized_title = enhanced_data.get('original_title', enhanced_data.get('description', 'Product'))
            
            print(f"   ✓ Generated title: {optimized_title}")
            return optimized_title
            
        except Exception as e:
            print(f"   ❌ Title generation failed: {e}")
            # Ultimate fallback
            return product_data.get('original_title', product_data.get('description', 'Product'))
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract potential brand from title using common patterns"""
        if not title:
            return ""
        
        # Common brand patterns in construction/hardware
        known_brands = ['BOSCH', 'MAKITA', 'DEWALT', 'MILWAUKEE', 'STANLEY', 'BLACK+DECKER', 
                       'RYOBI', 'CRAFTSMAN', 'KOBALT', 'HUSKY', 'RIDGID', 'PORTER-CABLE']
        
        title_upper = title.upper()
        for brand in known_brands:
            if brand in title_upper:
                return brand.title()
        
        # Look for brand-like patterns (capitalized words)
        words = title.split()
        for word in words:
            if word.isupper() and len(word) > 2:
                return word.title()
        
        return ""
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        total_requests = self.successful_requests + self.failed_requests
        success_rate = (self.successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_api_calls': self.api_call_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{success_rate:.1f}%"
        }

# Backward compatibility - keep the same class name
EnhancedTitleGenerator = RobustEnhancedTitleGenerator