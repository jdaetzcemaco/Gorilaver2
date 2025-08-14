import re
from typing import Dict

class LabelFormatter:
    def __init__(self, max_length: int = 36):
        """Initialize with maximum character limit for store labels"""
        self.max_length = max_length
    
    def format_store_label(self, full_title: str) -> str:
        """
        Convert full ecommerce title to 36-character store label
        
        Args:
            full_title: Complete ecommerce title from Agent 2
            
        Returns:
            Truncated label optimized for 36 characters
        """
        
        if len(full_title) <= self.max_length:
            return full_title
        
        # Strategy 1: Smart abbreviation
        abbreviated = self._smart_abbreviate(full_title)
        if len(abbreviated) <= self.max_length:
            return abbreviated
        
        # Strategy 2: Keep most important words
        important = self._keep_important_words(full_title)
        if len(important) <= self.max_length:
            return important
        
        # Strategy 3: Simple truncation with clean cut
        return self._clean_truncate(full_title)
    
    def _smart_abbreviate(self, title: str) -> str:
        """Apply smart abbreviations to common terms"""
        
        abbreviations = {
            # Common construction materials
            'Fibra de Vidrio': 'Fibra Vid',
            'Poliestireno': 'Poliestir',
            'Aislamiento': 'Aisl',
            'Térmico': 'Term',
            'Accesorios': 'Acc',
            'Dimensiones': 'Dim',
            'Construcción': 'Const',
            'Material': 'Mat',
            'Resistencia': 'Resist',
            
            # Colors (Spanish)
            'Blanco': 'Blco',
            'Negro': 'Neg',
            'Azul': 'Az',
            'Rojo': 'Rj',
            'Verde': 'Vrd',
            'Amarillo': 'Amar',
            'Naranja': 'Nar',
            'Gris': 'Gris',  # Already short
            
            # Measurements
            'Pulgadas': 'in',
            'Centímetros': 'cm',
            'Metros': 'm',
            'Milímetros': 'mm',
            'Piezas': 'pz',
            'Unidades': 'un',
            
            # Common words
            'Precio': 'P',
            'Especial': 'Esp',
            'Premium': 'Prem',
            'Standard': 'Std',
            'Professional': 'Prof'
        }
        
        result = title
        for full_word, abbrev in abbreviations.items():
            result = re.sub(rf'\b{re.escape(full_word)}\b', abbrev, result, flags=re.IGNORECASE)
        
        return result
    
    def _keep_important_words(self, title: str) -> str:
        """Keep only the most important words for product identification"""
        
        words = title.split()
        
        # Analyze what type of product this is to prioritize correctly
        product_type = self._identify_product_type(title)
        
        # Create priority scoring system
        word_scores = {}
        for i, word in enumerate(words):
            score = self._calculate_word_importance(word, product_type, i, len(words))
            word_scores[word] = score
        
        # Debug: show scoring for troubleshooting
        if "Grapas" in title:
            print(f"   DEBUG - Product type: {product_type}")
            print(f"   DEBUG - Word scores: {word_scores}")
        
        # Sort words by importance score (descending)
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Keep adding words until we hit character limit
        selected_words = []
        current_length = 0
        
        for word, score in sorted_words:
            word_length = len(word)
            # Add 1 for space (except first word)
            total_length = word_length + (1 if selected_words else 0)
            
            if current_length + total_length <= self.max_length:
                selected_words.append(word)
                current_length += total_length
            elif score >= 800:  # Force include critical words even if tight
                # Try abbreviating less important words we already selected
                continue
        
        if "Grapas" in title:
            print(f"   DEBUG - Selected words: {selected_words}")
        
        # Rebuild in logical order (not score order)
        result_words = []
        for word in words:
            if word in selected_words:
                result_words.append(word)
        
        # Clean up result - remove trailing connectors
        if result_words and result_words[-1].lower() in ['y', 'de', 'para', '-']:
            result_words.pop()
        
        result = ' '.join(result_words)
        
        # If we're missing critical info for accessories, force a better solution
        if product_type == 'accessory' and "Grapas" in title:
            if not any(re.search(r'\d+pz', word) for word in result_words):
                # We're missing the quantity! Create a forced solution
                result = self._force_accessory_format(title)
        
        return result
    
    def _force_accessory_format(self, title: str) -> str:
        """Force a good format for accessories when automatic selection fails"""
        words = title.split()
        
        # Find the critical components
        product_type = None
        quantity = None
        color = None
        
        for word in words:
            if any(key in word.lower() for key in ['grapas', 'accesorio', 'acc']):
                product_type = word
            elif re.search(r'\d+pz', word):
                quantity = word
            elif word.lower() in ['blanco', 'negro', 'azul', 'rojo', 'verde', 'gris', 'amarillo']:
                color = word
        
        # Build the optimal short format
        parts = []
        if product_type:
            parts.append(product_type)
        if quantity:
            parts.append(quantity)
        if color:
            parts.append(color)
        
        result = ' '.join(parts)
        
        # If still too long, abbreviate
        if len(result) > self.max_length:
            if product_type and 'Accesorios' in product_type:
                result = result.replace('Accesorios', 'Acc')
            if len(result) > self.max_length:
                # Remove 'para Aislante' if present
                result = result.replace(' para Aislante', '')
        
        return result if len(result) <= self.max_length else result[:self.max_length-3] + "..."
    
    def _identify_product_type(self, title: str) -> str:
        """Identify what type of product this is"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['grapas', 'accesorios', 'acc']):
            return 'accessory'
        elif any(word in title_lower for word in ['fibra', 'aislam', 'aisl']):
            return 'insulation'
        elif any(word in title_lower for word in ['caseton', 'poliestir']):
            return 'panel'
        elif any(word in title_lower for word in ['foamular', 'foam']):
            return 'foam'
        else:
            return 'generic'
    
    def _calculate_word_importance(self, word: str, product_type: str, position: int, total_words: int) -> int:
        """Calculate importance score for a word (higher = more important)"""
        
        score = 0
        word_lower = word.lower()
        
        # CRITICAL: Product identification words (these MUST be included)
        if product_type == 'accessory':
            if any(key in word_lower for key in ['grapas', 'accesorio', 'acc']):
                score += 1000  # Increased dramatically
            if re.search(r'\d+pz', word):  # Quantity is CRITICAL for accessories
                score += 950   # Very high priority
            # For accessories, color is also critical to distinguish products
            colors = ['blanco', 'negro', 'azul', 'rojo', 'verde', 'gris', 'amarillo', 'blco', 'neg', 'az']
            if word_lower in colors:
                score += 900
        
        elif product_type == 'insulation':
            if any(key in word_lower for key in ['fibra', 'aislam', 'aisl']):
                score += 1000
            if re.search(r'r-\d+', word_lower):  # R-value critical for insulation
                score += 950
        
        elif product_type == 'panel':
            if any(key in word_lower for key in ['caseton', 'poliestir']):
                score += 1000
        
        # VERY HIGH PRIORITY: Specifications that identify the exact product
        if re.search(r'\d+["\']?x\d+x\d+', word):  # 3D dimensions (highest)
            score += 920
        elif re.search(r'\d+["\']?x\d+', word):  # 2D dimensions
            score += 900
        
        if re.search(r'\d+pz', word) and product_type != 'accessory':  # Piece count (already handled above for accessories)
            score += 880
        
        if re.search(r'r-\d+', word_lower) and product_type != 'insulation':  # R-values (already handled above for insulation)
            score += 850
        
        # HIGH PRIORITY: Brand names (usually capitalized)
        if word[0].isupper() and len(word) > 2 and word.isalpha():
            if position < total_words / 2:  # Brands usually come early
                score += 800
        
        # MEDIUM-HIGH: Colors (important for identification) - general case
        if product_type != 'accessory':  # Already handled above for accessories
            colors = ['blanco', 'negro', 'azul', 'rojo', 'verde', 'gris', 'amarillo', 'blco', 'neg', 'az']
            if word_lower in colors:
                score += 700
        
        # MEDIUM: Size descriptors
        if any(size in word_lower for size in ['cm', 'mm', 'in', '"']):
            score += 650
        
        # LOW-MEDIUM: Keep connecting words only if they're short and help readability
        if word_lower in ['para', 'de'] and len(word) <= 4:
            score += 200
        
        # LOW: Generic descriptive words (can be removed if needed)
        generic_words = ['con', 'el', 'la', 'y', 'térm', 'term', 'construcción', 'const', 'decorativo', 'alta', 'calidad']
        if word_lower in generic_words:
            score += 50
        
        # VERY LOW: Common filler words and hyphens
        filler_words = ['premium', 'especial', 'profesional', 'estándar', 'standard', 'térmicas', '-']
        if word_lower in filler_words or word == '-':
            score += 10
        
        # Position bonus: important info often comes first, but not as strong as content
        if position < total_words * 0.3:  # First 30% of title
            score += 50
        
        return score
    
    def _clean_truncate(self, title: str) -> str:
        """Truncate at word boundary, not mid-word"""
        
        if len(title) <= self.max_length:
            return title
        
        # Find last complete word that fits
        truncated = title[:self.max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            return title[:last_space]
        else:
            # No spaces found, hard truncate
            return title[:self.max_length-3] + "..."
    
    def test_formatter(self):
        """Test the label formatter with various title lengths"""
        
        test_titles = [
            "Fibra de Vidrio Owens Corning R-13 15x93x3.5 Gris Aislamiento Térmico",
            "Caseton Poliestireno 60x60x2cm Blanco",
            "Accesorios para Aislante Grapas 1000pz Azul",
            "Foamular XPS R-10 2x4'x8' Plata Premium Construcción",
            "Material de Construcción Profesional Extra Resistente Color Negro Especial"
        ]
        
        print("Testing Label Formatter...")
        print(f"Max length: {self.max_length} characters\n")
        
        for i, title in enumerate(test_titles, 1):
            label = self.format_store_label(title)
            print(f"Test {i}:")
            print(f"  Original ({len(title)}): {title}")
            print(f"  Label ({len(label)}):    {label}")
            print(f"  Fits: {'✓' if len(label) <= self.max_length else '✗'}")
            print()

if __name__ == "__main__":
    # Test the label formatter
    formatter = LabelFormatter()
    formatter.test_formatter()