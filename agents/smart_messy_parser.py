import re
import pandas as pd
from typing import Dict, Optional, List

class SmartMessyParser:
    def __init__(self, csv_path: str = None):
        """Initialize with the nomenclatura database for intelligent parsing"""
        if csv_path is None:
            if os.path.exists("nomenclatura_gorila2.csv"):
                csv_path = "nomenclatura_gorila2.csv"
            elif os.path.exists("data/nomenclatura_gorila.csv"):
                csv_path = "data/nomenclatura_gorila.csv"
            else:
                raise FileNotFoundError("Cannot find nomenclatura CSV")
                
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()
        
        # Build keyword mappings for intelligent parsing
        self.department_keywords = set()
        self.family_keywords = set()
        self.category_keywords = set()
        
        for _, row in self.df.iterrows():
            # Extract keywords from each level
            dept_words = row['Departamento'].upper().replace('*', '').split()
            self.department_keywords.update(dept_words)
            
            family_words = row['Familia'].upper().split()
            self.family_keywords.update(family_words)
            
            cat_words = row['Categoria'].upper().split()
            self.category_keywords.update(cat_words)
        
        print(f"Smart parser initialized with {len(self.df)} categories")
    
    def parse_messy_title(self, messy_input: str) -> Dict:
        """Parse messy input and extract structured data"""
        
        # Clean the input
        cleaned = messy_input.strip().replace('\n', ' ').replace('\r', '')
        
        # Extract the main product part (usually at the beginning)
        product_match = re.match(r'^([A-Z0-9\s]+(?:\d+[xX]\d+)?[A-Z]*)', cleaned)
        product_title = product_match.group(1).strip() if product_match else ""
        
        # Look for department/family/category patterns in the remaining text
        remaining_text = cleaned[len(product_title):].upper()
        
        result = {
            'original_title': product_title,
            'description': product_title,
            'messy_input': messy_input,
            'parsed_structure': None
        }
        
        # Try to extract structured information
        extracted_structure = self._extract_structure_from_messy(remaining_text)
        if extracted_structure:
            result.update(extracted_structure)
            result['parsed_structure'] = 'structured_data_found'
        
        return result
    
    def _extract_structure_from_messy(self, text: str) -> Optional[Dict]:
        """Extract department/family/category from messy text"""
        
        text_upper = text.upper()
        
        # Look for known department patterns
        found_dept = None
        found_family = None
        found_category = None
        
        # Check against actual departments in database
        for _, row in self.df.iterrows():
            dept = row['Departamento'].upper()
            family = row['Familia'].upper()
            category = row['Categoria'].upper()
            
            # Check if department appears in text
            if self._text_contains_phrase(text_upper, dept):
                # Check if family appears
                if self._text_contains_phrase(text_upper, family):
                    # Check if category appears  
                    if self._text_contains_phrase(text_upper, category):
                        found_dept = row['Departamento']
                        found_family = row['Familia']
                        found_category = row['Categoria']
                        break
        
        if found_dept and found_family and found_category:
            return {
                'departamento': found_dept,
                'familia': found_family,
                'categoria': found_category,
                'confidence': 0.9
            }
        
        # Try partial matching
        return self._try_partial_matching(text_upper)
    
    def _text_contains_phrase(self, text: str, phrase: str) -> bool:
        """Check if text contains the phrase (allowing for word order differences)"""
        phrase_words = phrase.split()
        
        # All words from phrase must appear in text
        for word in phrase_words:
            if len(word) > 2 and word not in text:  # Skip very short words
                return False
        
        return True
    
    def _try_partial_matching(self, text: str) -> Optional[Dict]:
        """Try to match even with partial information"""
        
        # Look for key category indicators
        category_indicators = {
            'LISTELOS': ('REVESTIMIENTOS', 'CERAMICA DE MUROS Y COMPLEMENTOS', 'LISTELOS'),
            'MALLAS': ('REVESTIMIENTOS', 'CERAMICA DE MUROS Y COMPLEMENTOS', 'LISTELOS'),
            'CERAMICA': ('REVESTIMIENTOS', 'CERAMICA DE PISOS', 'BALDOSA'),
            'PISOS': ('REVESTIMIENTOS', 'CERAMICA DE PISOS', 'BALDOSA'),
            'PAREDES': ('REVESTIMIENTOS', 'CERAMICA DE MUROS Y COMPLEMENTOS', 'CERAMICA DE MURO')
        }
        
        for indicator, (dept, family, cat) in category_indicators.items():
            if indicator in text:
                # Verify this combination exists in database
                match = self.df[
                    (self.df['Departamento'].str.upper() == dept) &
                    (self.df['Familia'].str.upper() == family) &
                    (self.df['Categoria'].str.upper() == cat)
                ]
                
                if not match.empty:
                    row = match.iloc[0]
                    return {
                        'departamento': row['Departamento'],
                        'familia': row['Familia'],
                        'categoria': row['Categoria'],
                        'confidence': 0.7
                    }
        
        return None
    
    def find_best_category_match(self, product_data: Dict) -> Optional[Dict]:
        """Find the best category match using extracted structure or intelligent fallback"""
        
        # If we have structured data, use it
        if all(k in product_data for k in ['departamento', 'familia', 'categoria']):
            for _, row in self.df.iterrows():
                if (row['Departamento'].upper() == product_data['departamento'].upper() and
                    row['Familia'].upper() == product_data['familia'].upper() and
                    row['Categoria'].upper() == product_data['categoria'].upper()):
                    
                    return {
                        'departamento': row['Departamento'],
                        'familia': row['Familia'],
                        'categoria': row['Categoria'],
                        'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                        'ejemplo_aplicado': row['Ejemplo aplicado'],
                        'match_type': 'intelligent_structured',
                        'confidence': product_data.get('confidence', 1.0)
                    }
        
        # Fallback to tile pattern detection
        title = product_data.get('original_title', '').upper()
        
        # Tile patterns
        if any(pattern in title for pattern in ['BAMBOO', 'CAPRI', 'CLAY']):
            # Look for LISTELOS category (since your data suggests these are listelos)
            listelos_match = self.df[self.df['Categoria'].str.upper().str.contains('LISTELOS')]
            if not listelos_match.empty:
                row = listelos_match.iloc[0]
                return {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'],
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'intelligent_tile_pattern',
                    'confidence': 0.8
                }
        
        return None

if __name__ == "__main__":
    parser = SmartMessyParser()
    
    # Test with your messy input
    messy_input = "BAMBOO AMARILLO 21X31PISOS Y PAREDES CERAMICA DE MUROS Y COMPLEMENTOS LISTELOS Y MALLAS"
    
    print(f"Testing messy input: {messy_input}")
    result = parser.parse_messy_title(messy_input)
    
    print(f"Extracted product: {result['original_title']}")
    if 'departamento' in result:
        print(f"Found structure: {result['departamento']} > {result['familia']} > {result['categoria']}")
    
    match = parser.find_best_category_match(result)
    if match:
        print(f"Final match: {match['categoria']} (confidence: {match['confidence']})")
    else:
        print("No match found")
