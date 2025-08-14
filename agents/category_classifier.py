import pandas as pd
import os
from typing import Dict, Optional

class CategoryClassifier:
    def __init__(self, csv_path: str = None):
        if csv_path is None:
            # Handle both running from root and from agents/ folder
            if os.path.exists("data/nomenclatura_gorila.csv"):
                csv_path = "data/nomenclatura_gorila.csv"
            elif os.path.exists("../data/nomenclatura_gorila.csv"):
                csv_path = "../data/nomenclatura_gorila.csv"
            else:
                raise FileNotFoundError("Cannot find nomenclatura_gorila.csv in data/ folder")
        """Initialize with the category mapping CSV file"""
        self.df = pd.read_csv(csv_path)
        # Clean column names - remove extra spaces
        self.df.columns = self.df.columns.str.strip()
        print(f"Loaded {len(self.df)} category mappings")
    
    def find_category_match(self, product_data: Dict) -> Optional[Dict]:
        """
        Find the best category match for a product
        
        Args:
            product_data: Dict with keys like 'departamento', 'familia', 'categoria', 'description', etc.
        
        Returns:
            Dict with category info and naming rules, or None if no match
        """
        
        # Extract search terms from product data
        search_terms = []
        if 'departamento' in product_data:
            search_terms.append(product_data['departamento'].upper())
        if 'familia' in product_data:
            search_terms.append(product_data['familia'].upper())
        if 'categoria' in product_data:
            search_terms.append(product_data['categoria'].upper())
        if 'description' in product_data:
            search_terms.extend(product_data['description'].upper().split())
            
        # Try exact matches first
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
                    'match_type': 'exact'
                }
        
        # Try partial matches on categoria
        best_match = None
        best_score = 0
        
        for _, row in self.df.iterrows():
            score = 0
            categoria = row['Categoria'].strip().upper()
            
            # Check if any search terms appear in the category
            for term in search_terms:
                if term in categoria:
                    score += len(term)  # Longer matches get higher scores
                    
            if score > best_score:
                best_score = score
                best_match = {
                    'departamento': row['Departamento'],
                    'familia': row['Familia'],
                    'categoria': row['Categoria'].strip(), 
                    'nomenclatura_sugerida': row['Nomenclatura sugerida'],
                    'ejemplo_aplicado': row['Ejemplo aplicado'],
                    'match_type': 'partial',
                    'score': score
                }
        
        return best_match
    
    def get_all_categories(self) -> pd.DataFrame:
        """Return all available categories for debugging"""
        return self.df
    
    def test_classifier(self):
        """Test the classifier with sample data"""
        test_cases = [
            {
                'departamento': 'MATERIALES DE CONSTRUCCION',
                'familia': 'AISLANTE S', 
                'categoria': 'FIBRA DE VIDRIO',
                'description': 'Fibra de vidrio para aislamiento'
            },
            {
                'description': 'Caseton de poliestireno para techo'
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest case {i+1}: {test_case}")
            match = self.find_category_match(test_case)
            if match:
                print(f"Match found: {match['categoria']}")
                print(f"Naming rule: {match['nomenclatura_sugerida']}")
                print(f"Example: {match['ejemplo_aplicado']}")
            else:
                print("No match found")

if __name__ == "__main__":
    # Test the classifier
    classifier = CategoryClassifier()
    classifier.test_classifier()