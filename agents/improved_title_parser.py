import re
import openai
import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class ImprovedTitleParser:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI for intelligent parsing"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        
        # Construction vocabulary mapping
        self.construction_vocab = {
            # Hardware terms
            'CHAPA': 'cerradura/manija de puerta',
            'CERRADURA': 'cerradura de puerta',
            'MANIJA': 'manija de puerta',
            'PICAPORTE': 'manija de puerta',
            
            # Fasteners
            'TOR': 'tornillo',
            'TORNILLO': 'tornillo',
            'PERNO': 'perno',
            'TUERCA': 'tuerca',
            'ARANDELA': 'arandela',
            
            # Drill/cutting tools
            'BROCA': 'broca para taladro',
            'PUNTA': 'punta de herramienta',
            'MECHA': 'broca',
            
            # Plumbing vs Hardware
            'GRIFO': 'grifería',
            'LLAVE': 'grifería o herramienta',
            'VALVULA': 'grifería',
            
            # Materials
            'GALV': 'galvanizado',
            'INOX': 'acero inoxidable',
            'CROMO': 'cromado',
            'COBRE': 'cobre',
            
            # Tile patterns
            'BAMBOO': 'patrón bambú',
            'CAPRI': 'patrón capri',
            'CLAY': 'patrón clay',
            
            # Locations (context, not product type)
            'BAÑO': 'ubicación: baño',
            'COCINA': 'ubicación: cocina',
            'JARDIN': 'ubicación: jardín'
        }
    
    def parse_title_to_product_data(self, raw_title: str) -> Dict:
        """Parse a raw title into structured product data"""
        
        # Simple rule-based extraction
        extracted_data = self._rule_based_extraction(raw_title)
        
        # Skip AI parsing to avoid JSON errors for now
        return extracted_data
    
    def _rule_based_extraction(self, title: str) -> Dict:
        """Extract obvious patterns from title using regex"""
        
        data = {
            'original_title': title,
            'description': title
        }
        
        # Extract dimensions
        dimension_patterns = [
            r'(\d+)[xX×](\d+)',  # 21x31
            r'(\d+)\s*[xX×]\s*(\d+)',  # 21 x 31
        ]
        
        for pattern in dimension_patterns:
            match = re.search(pattern, title)
            if match:
                data['dimensions'] = match.group(0)
                break
        
        # Extract quantities
        quantity_match = re.search(r'(\d+)\s*(pz|pzs|piezas|unidades)', title, re.IGNORECASE)
        if quantity_match:
            data['quantity'] = quantity_match.group(0)
        
        # Extract colors
        colors = ['blanco', 'negro', 'azul', 'rojo', 'verde', 'gris', 'amarillo', 'naranja', 'cafe']
        for color in colors:
            if re.search(rf'\b{color}\b', title, re.IGNORECASE):
                data['color'] = color.title()
                break
        
        # Detect tile patterns
        tile_patterns = ['BAMBOO', 'CAPRI', 'CLAY']
        for pattern in tile_patterns:
            if pattern.upper() in title.upper():
                data['tile_pattern'] = pattern
                data['producto_tipo'] = f'{pattern.lower()} tile pattern'
                break
        
        return data

if __name__ == "__main__":
    parser = ImprovedTitleParser()
    
    test_titles = [
        "BAMBOO AMARILLO 21X31",
        "CAPRI BEIGE 30X30"
    ]
    
    for title in test_titles:
        print(f"\nTitle: {title}")
        result = parser.parse_title_to_product_data(title)
        print(f"Product type: {result.get('producto_tipo', 'Unknown')}")
        print(f"Dimensions: {result.get('dimensions', 'None')}")
        print(f"Color: {result.get('color', 'None')}")
