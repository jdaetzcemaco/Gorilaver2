import pandas as pd
import os
from typing import Dict, Optional, List

class ImprovedCategoryClassifier:
    def __init__(self, csv_path: str = None):
        """Initialize with enhanced category matching logic"""
        if csv_path is None:
            if os.path.exists("data/nomenclatura_gorila.csv"):
                csv_path = "data/nomenclatura_gorila.csv"
            elif os.path.exists("../data/nomenclatura_gorila.csv"):
                csv_path = "../data/nomenclatura_gorila.csv"
            else:
                raise FileNotFoundError("Cannot find nomenclatura_gorila.csv in data/ folder")
                
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()
        
        # Create category keyword mappings for better matching
        self.category_keywords = self._build_category_keywords()
        
        print(f"Loaded {len(self.df)} category mappings with enhanced matching")
    
    def _build_category_keywords(self) -> Dict:
        """Build keyword mappings for each category"""
        keywords = {}
        
        for _, row in self.df.iterrows():
            categoria = row['Categoria'].strip().upper()
            
            # Extract keywords from category name
            cat_keywords = categoria.replace('Y', '').replace('PARA', '').split()
            
            # Add common synonyms and variations
            enhanced_keywords = set(cat_keywords)
            
            # Hardware-specific mappings
            if 'CHAPA' in categoria or 'CERRADURA' in categoria:
                enhanced_keywords.update(['MANIJA', 'PICAPORTE', 'HERRAJE', 'PUERTA'])
            
            if 'TORNILLO' in categoria or 'FIJACION' in categoria:
                enhanced_keywords.update(['TOR', 'PERNO', 'FIJADOR', 'SUJECION'])
            
            if 'BROCA' in categoria:
                enhanced_keywords.update(['PUNTA', 'MECHA', 'PERFORACION'])
            
            if 'GRIFO' in categoria or 'LLAVE' in categoria:
                enhanced_keywords.update(['AGUA', 'PLOMERIA', 'GRIFERIA'])
            
            # Location-aware keywords
            if 'BAÑO' in categoria:
                enhanced_keywords.update(['BATHROOM', 'SANITARIO'])
            
            if 'COCINA' in categoria:
                enhanced_keywords.update(['KITCHEN'])
            
            keywords[categoria] = list(enhanced_keywords)
        
        return keywords
    
    def find_category_match(self, product_data: Dict) -> Optional[Dict]:
        """
        Enhanced category matching with construction context awareness
        """
        
        # Get construction analysis if available
        construction_analysis = product_data.get('construction_analysis', {})
        likely_category = construction_analysis.get('likely_category')
        
        # Try exact matches first (highest priority)
        exact_match = self._try_exact_match(product_data)
        if exact_match:
            return exact_match
        
        # Try construction-aware matching
        construction_match = self._try_construction_aware_match(product_data, construction_analysis)
        if construction_match:
            return construction_match
        
        # Try enhanced keyword matching
        keyword_match = self._try_enhanced_keyword_match(product_data)
        if keyword_match:
            return keyword_match
        
        # Try fuzzy matching as last resort
        fuzzy_match = self._try_fuzzy_match(product_data)
        
        return fuzzy_match
    
    def _try_exact_match(self, product_data: Dict) -> Optional[Dict]:
        """Try exact departamento/familia/categoria match"""
        
        for _, row in self.df.iterrows():
            if (product_data.get('departamento', '').upper() == row['Departamento'].upper() and
                product_data.get('familia', '').upper() == row['Familia'].upper() and
                product_data.get('categoria', '').upper() == row['Categoria'].strip().upper()):
                
                return {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'], 
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'exact',
                    'confidence': 1.0
                }
        
        return None
    
    def _try_construction_aware_match(self, product_data: Dict, construction_analysis: Dict) -> Optional[Dict]:
        """Match using construction industry context"""
        
        if not construction_analysis:
            return None
        
        producto_tipo = product_data.get('producto_tipo', '').upper()
        detected_terms = construction_analysis.get('detected_terms', {})
        
        best_match = None
        best_score = 0
        
        for _, row in self.df.iterrows():
            categoria = row['Categoria'].strip().upper()
            score = 0
            
            # High score for construction vocabulary matches
            for term in detected_terms:
                if term in categoria:
                    score += 50  # High weight for vocabulary matches
            
            # Specific construction logic
            if 'CHAPA' in detected_terms or 'CERRADURA' in producto_tipo:
                if any(hw in categoria for hw in ['CHAPA', 'CERRADURA', 'HERRAJE']):
                    score += 100
                # Penalize plumbing categories for door hardware
                if any(plumb in categoria for plumb in ['GRIFO', 'LLAVE', 'AGUA']):
                    score -= 50
            
            if 'TOR' in detected_terms and 'BROCA' in detected_terms:
                if 'TORNILLO' in categoria and ('BROCA' in categoria or 'AUTORROSCANTE' in categoria):
                    score += 100
                elif 'TORNILLO' in categoria:
                    score += 80
                # Penalize pure drill bit categories for self-drilling screws
                elif 'BROCA' in categoria and 'TORNILLO' not in categoria:
                    score -= 30
            
            if score > best_score:
                best_score = score
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'construction_aware',
                    'confidence': min(score / 100, 1.0),
                    'score': score
                }
        
        # Only return if confidence is reasonable
        return best_match if best_match and best_match['confidence'] > 0.3 else None
    
    def _try_enhanced_keyword_match(self, product_data: Dict) -> Optional[Dict]:
        """Enhanced keyword matching with better scoring"""
        
        # Extract searchable terms from product data
        search_terms = []
        
        # Add various product data fields
        for field in ['description', 'original_title', 'producto_tipo', 'categoria_especifica']:
            if field in product_data and product_data[field]:
                search_terms.extend(product_data[field].upper().split())
        
        # Add construction keywords if available
        construction_analysis = product_data.get('construction_analysis', {})
        if 'palabras_clave_categoria' in product_data:
            search_terms.extend([k.upper() for k in product_data['palabras_clave_categoria']])
        
        best_match = None
        best_score = 0
        
        for categoria, keywords in self.category_keywords.items():
            score = 0
            
            # Calculate keyword overlap
            categoria_upper = categoria.upper()
            for term in search_terms:
                if term in categoria_upper:
                    score += len(term) * 2  # Longer matches get higher scores
                
                for keyword in keywords:
                    if term in keyword.upper() or keyword.upper() in term:
                        score += len(keyword)
            
            if score > best_score:
                best_score = score
                # Find the row for this category
                row = self.df[self.df['Categoria'].str.strip().str.upper() == categoria].iloc[0]
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'enhanced_keyword',
                    'confidence': min(score / 50, 1.0),
                    'score': score
                }
        
        return best_match if best_match and best_match['confidence'] > 0.2 else None
    
    def _try_fuzzy_match(self, product_data: Dict) -> Optional[Dict]:
        """Fuzzy matching as last resort"""
        
        search_text = product_data.get('description', '') + ' ' + product_data.get('original_title', '')
        search_words = search_text.upper().split()
        
        best_match = None
        best_score = 0
        
        for _, row in self.df.iterrows():
            categoria = row['Categoria'].strip().upper()
            score = 0
            
            for word in search_words:
                if len(word) > 2:  # Only consider meaningful words
                    if word in categoria:
                        score += len(word)
                    # Partial matches
                    elif any(word in cat_word or cat_word in word for cat_word in categoria.split()):
                        score += len(word) * 0.5
            
            if score > best_score:
                best_score = score
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'fuzzy',
                    'confidence': min(score / 30, 1.0),
                    'score': score
                }
        
        return best_match if best_match and best_match['confidence'] > 0.15 else None
    
    def get_all_categories(self) -> pd.DataFrame:
        """Return all available categories"""
        return self.df
    
    def test_improved_classifier(self):
        """Test with the problematic cases"""
        
        test_cases = [
            {
                'original_title': 'CHAPA BARI DE BAÑO CROMO COBRE ANTIGUO',
                'producto_tipo': 'chapa/cerradura para baño',
                'construction_analysis': {
                    'detected_terms': {'CHAPA': 'cerradura/manija de puerta', 'BAÑO': 'ubicación: baño'},
                    'likely_category': 'HERRAJES_BAÑO'
                }
            },
            {
                'original_title': 'TOR. PUNTA DE BROCA AR. 1/4 X 1 1/2',
                'producto_tipo': 'tornillo autorroscante con punta de broca',
                'construction_analysis': {
                    'detected_terms': {'TOR': 'tornillo', 'BROCA': 'broca para taladro'},
                    'likely_category': 'TORNILLERIA/FIJACIONES'
                }
            }
        ]
        
        print("Testing improved category classification:")
        print("=" * 60)
        
        for test_case in test_cases:
            print(f"\nTEST: {test_case['original_title']}")
            match = self.find_category_match(test_case)
            
            if match:
                print(f"✓ FOUND: {match['categoria']}")
                print(f"  Confidence: {match['confidence']:.2f}")
                print(f"  Match type: {match['match_type']}")
                print(f"  Rule: {match['nomenclatura_sugerida']}")
            else:
                print("✗ NO MATCH FOUND")
            
            print("-" * 40)

if __name__ == "__main__":
    classifier = ImprovedCategoryClassifier()
    classifier.test_improved_classifier()
