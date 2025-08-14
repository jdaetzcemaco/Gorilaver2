import openai
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class TitleGenerator:
    def __init__(self, api_key: str = None):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def generate_ecommerce_title(self, product_data: Dict, category_info: Dict) -> str:
        """
        Generate SEO-optimized ecommerce title following exact category format
        
        Args:
            product_data: Product information (brand, specs, color, etc.)
            category_info: Category rules from Agent 1
            
        Returns:
            Optimized ecommerce title string
        """
        
        # Extract the naming format from category info
        naming_rule = category_info['nomenclatura_sugerida']
        example = category_info['ejemplo_aplicado']
        category = category_info['categoria']
        
        # Build the prompt for title generation
        prompt = f"""You are an ecommerce title specialist. Your job is to create SEO-optimized product titles that convert sales.

CATEGORY: {category}
NAMING RULE: {naming_rule}
EXAMPLE: {example}

PRODUCT DATA:
{self._format_product_data(product_data)}

INSTRUCTIONS:
1. Follow the EXACT naming rule format: {naming_rule}
2. Use the example as a template: {example}
3. Include key SEO elements: brand, specifications, color, size/dimensions
4. Make it scannable and conversion-focused
5. Keep it under 150 characters for optimal display
6. Use proper capitalization and spacing
7. Include measurable specifications when available
8. Put the most important keywords first

Generate ONE optimized ecommerce title that follows the naming rule exactly."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert ecommerce title writer who creates titles that convert. You follow format rules exactly and optimize for search and sales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            title = response.choices[0].message.content.strip()
            
            # Clean up any quotes or extra formatting
            title = title.replace('"', '').replace("'", "").strip()
            
            return title
            
        except Exception as e:
            print(f"Error generating title: {e}")
            # Fallback: create basic title from available data
            return self._create_fallback_title(product_data, category_info)
    
    def _format_product_data(self, product_data: Dict) -> str:
        """Format product data for the prompt"""
        formatted = []
        for key, value in product_data.items():
            if value:
                formatted.append(f"- {key.title()}: {value}")
        return "\n".join(formatted)
    
    def _create_fallback_title(self, product_data: Dict, category_info: Dict) -> str:
        """Create a basic title if API fails"""
        parts = []
        
        # Add brand if available
        if 'brand' in product_data:
            parts.append(product_data['brand'])
        
        # Add category
        parts.append(category_info['categoria'].title())
        
        # Add key specs
        for key in ['size', 'dimensions', 'color', 'model']:
            if key in product_data and product_data[key]:
                parts.append(str(product_data[key]))
        
        return " ".join(parts)
    
    def test_generator(self):
        """Test the title generator with sample data"""
        
        # Sample product data
        product_data = {
            'brand': 'Owens Corning',
            'type': 'Fibra de Vidrio',
            'r_value': 'R-13',
            'dimensions': '15"x93"x3.5"',
            'color': 'Gris',
            'description': 'Aislamiento térmico para construcción'
        }
        
        # Sample category info (from Agent 1)
        category_info = {
            'categoria': 'FIBRA DE VIDRIO',
            'nomenclatura_sugerida': 'Tipo + Dimensiones y/o cantidad de piezas + Color',
            'ejemplo_aplicado': 'Fibra de Vidrio R-13 15"x93"x3.5" Gris'
        }
        
        print("Testing Title Generator...")
        print(f"Product: {product_data}")
        print(f"Category Rule: {category_info['nomenclatura_sugerida']}")
        print(f"Example: {category_info['ejemplo_aplicado']}")
        
        title = self.generate_ecommerce_title(product_data, category_info)
        print(f"\nGenerated Title: {title}")
        print(f"Length: {len(title)} characters")
        
        return title

if __name__ == "__main__":
    # Test the title generator
    generator = TitleGenerator()
    generator.test_generator()