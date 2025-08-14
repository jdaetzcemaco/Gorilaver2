import re
import openai
import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class TitleParser:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI for intelligent parsing"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def parse_title_to_product_data(self, raw_title: str) -> Dict:
        """
        Parse a raw title into structured product data
        
        Args:
            raw_title: Raw product title from user
            
        Returns:
            Dict with extracted product information
        """
        
        # First try rule-based extraction (fast)
        extracted_data = self._rule_based_extraction(raw_title)
        
        # Then enhance with AI parsing (more accurate)
        ai_enhanced = self._ai_enhanced_parsing(raw_title, extracted_data)
        
        return ai_enhanced
    
    def _rule_based_extraction(self, title: str) -> Dict:
        """Extract obvious patterns from title using regex"""
        
        data = {
            'original_title': title,
            'description': title  # Keep original as description
        }
        
        # Extract dimensions (various formats)
        dimension_patterns = [
            r'(\d+)["\']?\s*x\s*(\d+)["\']?\s*x\s*(\d+)["\']?',  # 3D: 15x93x3.5
            r'(\d+)["\']?\s*x\s*(\d+)["\']?',  # 2D: 60x60
            r'(\d+)\s*cm\s*x\s*(\d+)\s*cm',   # with cm
            r'(\d+)\s*mm\s*x\s*(\d+)\s*mm',   # with mm
        ]
        
        for pattern in dimension_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                data['dimensions'] = match.group(0)
                break
        
        # Extract quantities
        quantity_match = re.search(r'(\d+)\s*(pz|pzs|piezas|unidades|un)', title, re.IGNORECASE)
        if quantity_match:
            data['quantity'] = quantity_match.group(0)
        
        # Extract R-values  
        r_value_match = re.search(r'R-?\s*(\d+)', title, re.IGNORECASE)
        if r_value_match:
            data['r_value'] = r_value_match.group(0)
        
        # Extract colors (Spanish)
        colors = ['blanco', 'negro', 'azul', 'rojo', 'verde', 'gris', 'amarillo', 'naranja', 'rosa', 'café', 'marrón']
        for color in colors:
            if re.search(rf'\b{color}\b', title, re.IGNORECASE):
                data['color'] = color.title()
                break
        
        # Extract potential brands (capitalized words at the beginning)
        words = title.split()
        for i, word in enumerate(words[:3]):  # Check first 3 words
            if word[0].isupper() and word.isalpha() and len(word) > 2:
                if word.lower() not in ['para', 'con', 'sin', 'tipo', 'marca']:
                    data['potential_brand'] = word
                    break
        
        return data
    
    def _ai_enhanced_parsing(self, title: str, rule_data: Dict) -> Dict:
        """Use AI to extract more complex product information"""
        
        prompt = f"""You are a product data extraction expert for construction materials and hardware.

TITLE TO ANALYZE: "{title}"

INITIAL EXTRACTION (from rules): {rule_data}

Extract the following information from this product title:

1. DEPARTMENT/CATEGORY TYPE: What department would this belong to? (construction materials, tools, hardware, etc.)
2. PRODUCT TYPE: What specific type of product is this? (fibra de vidrio, caseton, grapas, etc.)
3. BRAND: Any brand name mentioned?
4. SPECIFICATIONS: Technical specs, measurements, quantities
5. COLOR: Any color mentioned?
6. INTENDED USE: What is this product used for?

Respond in this EXACT JSON format:
{{
    "departamento_guess": "best guess for department",
    "producto_tipo": "specific product type",
    "brand": "brand name if found, null if not",
    "color": "color if found, null if not", 
    "specifications": "key specs like dimensions, R-value, quantity",
    "uso": "what this product is used for",
    "categoria_keywords": ["keyword1", "keyword2", "keyword3"]
}}

Be precise and concise. Only include information you're confident about."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured product data from Spanish construction material titles. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            import json
            ai_data = json.loads(response.choices[0].message.content)
            
            # Merge AI results with rule-based extraction
            final_data = rule_data.copy()
            final_data.update(ai_data)
            
            return final_data
            
        except Exception as e:
            print(f"AI parsing failed: {e}")
            # Fallback to rule-based only
            return rule_data
    
    def batch_parse_titles(self, titles: List[str]) -> List[Dict]:
        """Parse multiple titles at once"""
        
        results = []
        print(f"🔍 Parsing {len(titles)} product titles...\n")
        
        for i, title in enumerate(titles, 1):
            print(f"--- Title {i}/{len(titles)} ---")
            print(f"Raw: {title}")
            
            parsed = self.parse_title_to_product_data(title)
            results.append(parsed)
            
            print(f"Type: {parsed.get('producto_tipo', 'Unknown')}")
            print(f"Specs: {parsed.get('specifications', 'None found')}")
            print()
        
        return results
    
    def test_parser(self):
        """Test the title parser with sample titles"""
        
        test_titles = [
            "Fibra de Vidrio R-13 15x93x3.5 Gris Owens Corning",
            "Grapas para aislante 1000 piezas azul",
            "Caseton poliestireno 60x60x2cm blanco decorativo",
            "Foamular XPS aislante 2 pulgadas R-10 plata",
            "Tornillos autorroscantes 1/4x2 galvanizados 100pz"
        ]
        
        results = self.batch_parse_titles(test_titles)
        
        print("📊 PARSING RESULTS:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['original_title']}")
            print(f"   → Type: {result.get('producto_tipo')}")
            print(f"   → Specs: {result.get('specifications')}")
            print()
        
        return results

if __name__ == "__main__":
    parser = TitleParser()
    parser.test_parser()