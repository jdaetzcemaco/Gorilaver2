import pandas as pd
import os
import re
from typing import Dict, Optional, List

class TileFixedCategoryClassifier:
    def __init__(self, csv_path: str = None):
        """Initialize with tile-aware category matching logic"""
        if csv_path is None:
            if os.path.exists("data/nomenclatura_gorila.csv"):
                csv_path = "data/nomenclatura_gorila.csv"
            elif os.path.exists("../data/nomenclatura_gorila.csv"):
                csv_path = "../data/nomenclatura_gorila.csv"
            elif os.path.exists("nomenclatura_gorila2.csv"):
                csv_path = "nomenclatura_gorila2.csv"
            else:
                raise FileNotFoundError("Cannot find nomenclatura_gorila.csv")
                
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()
        
        print(f"Loaded {len(self.df)} category mappings with tile classification")
    
    def _classify_tile_products(self, product_data: Dict) -> Optional[Dict]:
        """Special classification logic for ceramic tiles and floor products"""
        
        title = product_data.get('original_title', '').upper()
        description = product_data.get('description', '').upper()
        
        # Tile pattern names that are commonly misclassified
        tile_patterns = {
            'BAMBOO': 'MADERAS',      # Wood-look tiles
            'CAPRI': 'MONOCOLOR',     # Solid color tiles  
            'CLAY': 'RUSTICO',        # Rustic tiles
            'WOOD': 'MADERAS',
            'STONE': 'PIEDRA',
            'MARBLE': 'MARMOL',
            'CEMENT': 'CEMENTO'
        }
        
        # Tile size patterns (dimensions in cm)
        tile_size_pattern = re.search(r'(\d+)[xX×](\d+)', title)
        
        # Check if this looks like a tile product
        is_likely_tile = False
        detected_pattern = None
        
        # Pattern-based detection
        for pattern, category_type in tile_patterns.items():
            if pattern in title:
                is_likely_tile = True
                detected_pattern = category_type
                break
        
        # Size-based detection (common tile sizes)
        if tile_size_pattern:
            width, height = int(tile_size_pattern.group(1)), int(tile_size_pattern.group(2))
            common_tile_sizes = [
                (20, 20), (21, 31), (25, 40), (30, 30), (29, 36), (33, 33),
                (40, 40), (45, 45), (60, 60), (80, 80), (20, 120)
            ]
            
            if (width, height) in common_tile_sizes or (height, width) in common_tile_sizes:
                is_likely_tile = True
                if not detected_pattern:
                    detected_pattern = 'MONOCOLOR'  # Default for unrecognized patterns
        
        if not is_likely_tile:
            return None
        
        # Find matching ceramic category
        best_match = None
        target_departamento = 'REVESTIMIENTOS'
        
        # Try ceramic floors first
        target_familia = 'CERAMICA DE PISOS'
        target_categoria = detected_pattern or 'MONOCOLOR'
        
        for _, row in self.df.iterrows():
            if (row['Departamento'].upper() == target_departamento and
                row['Familia'].upper() == target_familia and
                row['Categoria'].upper() == target_categoria):
                
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'tile_pattern_match',
                    'confidence': 0.95,
                    'detected_pattern': detected_pattern
                }
                break
        
        # If no exact pattern match, try generic ceramic floor
        if not best_match:
            for _, row in self.df.iterrows():
                if (row['Departamento'].upper() == target_departamento and
                    row['Familia'].upper() == target_familia and
                    'BALDOSA' in row['Categoria'].upper()):
                    
                    best_match = {
                        'departamento': row['Departamento'],
                        'familia': row['Familia'],
                        'categoria': row['Categoria'].strip(),
                        'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                        'ejemplo_aplicado': row['Ejemplo aplicado'],
                        'match_type': 'tile_generic_match',
                        'confidence': 0.85,
                        'detected_pattern': 'GENERIC_TILE'
                    }
                    break
        
        return best_match
    
    def find_category_match(self, product_data: Dict) -> Optional[Dict]:
        """Enhanced category matching with structured data priority"""
        
        # FIRST: Try exact structured data match if available
        if (product_data.get('departamento') and 
            product_data.get('familia') and 
            product_data.get('categoria')):
            
            print(f"   📋 Using structured data: {product_data.get('departamento')} > {product_data.get('familia')} > {product_data.get('categoria')}")
            
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
                        'match_type': 'exact_structured',
                        'confidence': 1.0
                    }
            
            print(f"   ⚠️  No exact match found for structured data")
        
        # SECOND: Try tile pattern detection for unstructured data
        tile_match = self._classify_tile_products(product_data)
        if tile_match:
            print(f"   🎯 Tile pattern detected: {tile_match['detected_pattern']}")
            return tile_match
        
        # THIRD: Try keyword matching as fallback
        search_terms = []
        for field in ['description', 'original_title']:
            if field in product_data and product_data[field]:
                search_terms.extend(product_data[field].upper().split())
        
        best_match = None
        best_score = 0
        
        for _, row in self.df.iterrows():
            categoria = row['Categoria'].strip().upper()
            score = 0
            
            for term in search_terms:
                if term in categoria:
                    score += len(term)
            
            if score > best_score:
                best_score = score
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(),
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'keyword',
                    'confidence': min(score / 30, 1.0),
                    'score': score
                }
        
        return best_match if best_match and best_match['confidence'] > 0.2 else None
    
    def get_all_categories(self) -> pd.DataFrame:
        """Return all available categories"""
        return self.df

if __name__ == "__main__":
    classifier = TileFixedCategoryClassifier()
    
    # Test structured data
    test_data = {
        'original_title': 'BAMBOO AMARILLO 21X31',
        'description': 'BAMBOO AMARILLO 21X31',
        'departamento': 'PISOS Y PAREDES',
        'familia': 'CERAMICA DE MUROS Y COMPLEMENTOS', 
        'categoria': 'LISTELOS Y MALLAS'
    }
    
    print("\nTesting structured data:")
    result = classifier.find_category_match(test_data)
    if result:
        print(f"✓ Category: {result['categoria']}")
        print(f"  Match type: {result['match_type']}")
        print(f"  Confidence: {result['confidence']:.2f}")
    else:
        print("✗ No match found")
