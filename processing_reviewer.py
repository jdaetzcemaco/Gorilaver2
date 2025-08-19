# processing_reviewer.py - CORRECTED VERSION
import json
from typing import Dict, List
import pandas as pd

class ProcessingReviewer:
    """Review and validate processing results before download"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_title_length': 5,
            'max_title_length': 80,
            'min_confidence': 0.3,
            'required_fields': ['input_title', 'optimized_title', 'success']
        }
    
    def analyze_batch_results(self, results: List[Dict]) -> Dict:
        """Analyze batch processing results and provide quality metrics"""
        
        analysis = {
            'total_processed': len(results),
            'successful': 0,
            'failed': 0,
            'web_search_used': 0,
            'web_search_failed': 0,
            'quality_issues': [],
            'recommendations': [],
            'detailed_stats': {}
        }
        
        quality_scores = []
        confidence_scores = []
        
        for i, result in enumerate(results, 1):
            # Basic success tracking
            if result.get('success', False):
                analysis['successful'] += 1
                
                # Check web search usage
                if 'web_research' in result.get('parsed_data', {}):
                    analysis['web_search_used'] += 1
                    web_research = result['parsed_data']['web_research']
                    if 'error' in web_research:
                        analysis['web_search_failed'] += 1
                
                # Quality assessment
                quality_score = self._assess_result_quality(result, i)
                quality_scores.append(quality_score)
                
                # Track confidence
                confidence = result.get('parsed_data', {}).get('research_confidence', 0.5)
                confidence_scores.append(confidence)
                
            else:
                analysis['failed'] += 1
                analysis['quality_issues'].append({
                    'item': i,
                    'title': result.get('input_title', 'Unknown'),
                    'issue': 'Processing failed',
                    'errors': result.get('errors', [])
                })
        
        # Calculate averages
        if quality_scores:
            analysis['detailed_stats'] = {
                'average_quality_score': sum(quality_scores) / len(quality_scores),
                'average_confidence': sum(confidence_scores) / len(confidence_scores),
                'high_quality_count': len([s for s in quality_scores if s >= 0.8]),
                'low_quality_count': len([s for s in quality_scores if s < 0.5])
            }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _assess_result_quality(self, result: Dict, item_num: int) -> float:
        """Assess the quality of a single processing result"""
        quality_score = 1.0
        issues = []
        
        original_title = result.get('input_title', '')
        optimized_title = result.get('optimized_title', '')
        
        # Check title length
        if len(optimized_title) < self.quality_thresholds['min_title_length']:
            quality_score -= 0.3
            issues.append('Title too short')
        elif len(optimized_title) > self.quality_thresholds['max_title_length']:
            quality_score -= 0.2
            issues.append('Title too long')
        
        # Check if title was actually improved
        if optimized_title.lower() == original_title.lower():
            quality_score -= 0.2
            issues.append('No improvement detected')
        
        # Check web search quality
        parsed_data = result.get('parsed_data', {})
        if 'web_research' in parsed_data:
            web_research = parsed_data['web_research']
            if 'error' in web_research:
                quality_score -= 0.3
                issues.append('Web search failed')
            else:
                # Bonus for successful web search
                quality_score += 0.1
        
        # Check confidence level
        confidence = parsed_data.get('research_confidence', 0.5)
        if confidence < self.quality_thresholds['min_confidence']:
            quality_score -= 0.2
            issues.append('Low confidence')
        
        return max(0.0, min(1.0, quality_score))
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Success rate recommendations
        total_processed = analysis.get('total_processed', 0)
        successful = analysis.get('successful', 0)
        
        if total_processed > 0:
            success_rate = successful / total_processed
            if success_rate < 0.8:
                recommendations.append(f"Low success rate ({success_rate:.1%}). Consider checking input data quality.")
        
        # Web search recommendations
        web_search_used = analysis.get('web_search_used', 0)
        web_search_failed = analysis.get('web_search_failed', 0)
        
        if web_search_used > 0:
            web_search_failure_rate = web_search_failed / web_search_used
            if web_search_failure_rate > 0.3:
                recommendations.append(f"High web search failure rate ({web_search_failure_rate:.1%}). Consider reducing API request frequency.")
        elif web_search_failed > 0:
            recommendations.append("Web search failed for all attempts. Check API key and connectivity.")
        
        # Quality recommendations
        stats = analysis.get('detailed_stats', {})
        avg_quality = stats.get('average_quality_score', 0)
        if avg_quality > 0 and avg_quality < 0.7:
            recommendations.append("Low average quality score. Review failed items and consider manual adjustments.")
        
        low_quality_count = stats.get('low_quality_count', 0)
        high_quality_count = stats.get('high_quality_count', 0)
        if low_quality_count > 0 and low_quality_count > high_quality_count:
            recommendations.append("More low-quality results than high-quality. Consider reprocessing with adjusted parameters.")
        
        if not recommendations:
            recommendations.append("Processing quality looks good! Results are ready for download.")
        
        return recommendations

    def generate_quality_report(self, results: List[Dict], output_file: str = None) -> str:
        """Generate a detailed quality report"""
        
        analysis = self.analyze_batch_results(results)
        
        report = f"""
📊 PROCESSING QUALITY REPORT
{'=' * 50}

📈 SUMMARY STATISTICS:
• Total Products Processed: {analysis['total_processed']}
• Successful: {analysis['successful']} ({analysis['successful']/analysis['total_processed']:.1%} if total > 0)
• Failed: {analysis['failed']} ({analysis['failed']/analysis['total_processed']:.1%} if total > 0)

🔍 WEB SEARCH PERFORMANCE:
• Web Search Used: {analysis['web_search_used']} products
• Web Search Failed: {analysis['web_search_failed']} products"""

        # Safe web search success rate calculation
        if analysis['web_search_used'] > 0:
            success_rate = (analysis['web_search_used'] - analysis['web_search_failed'])/analysis['web_search_used']
            report += f"\n• Web Search Success Rate: {success_rate:.1%}"
        else:
            report += f"\n• Web Search Success Rate: N/A (no web searches performed)"

        report += f"""

⭐ QUALITY METRICS:
"""
        
        if analysis['detailed_stats']:
            stats = analysis['detailed_stats']
            report += f"""• Average Quality Score: {stats['average_quality_score']:.2f}/1.0
• Average Confidence: {stats['average_confidence']:.2f}/1.0
• High Quality Results: {stats['high_quality_count']}
• Low Quality Results: {stats['low_quality_count']}
"""
        else:
            report += "• No quality metrics available (no successful results)\n"
        
        report += f"""
🔧 RECOMMENDATIONS:
"""
        for i, rec in enumerate(analysis['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        if analysis['quality_issues']:
            report += f"""
⚠️  QUALITY ISSUES FOUND:
"""
            for issue in analysis['quality_issues'][:10]:  # Show first 10 issues
                report += f"• Item {issue['item']}: {issue['title'][:40]}... - {issue['issue']}\n"
            
            if len(analysis['quality_issues']) > 10:
                report += f"... and {len(analysis['quality_issues']) - 10} more issues.\n"
        
        report += f"""
{'=' * 50}
"""
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def create_filtered_results(self, results: List[Dict], min_quality: float = 0.5) -> List[Dict]:
        """Create filtered results excluding low-quality items"""
        
        filtered = []
        for result in results:
            if result.get('success', False):
                quality_score = self._assess_result_quality(result, 0)
                if quality_score >= min_quality:
                    result['quality_score'] = quality_score
                    filtered.append(result)
        
        return filtered
    
    def export_detailed_csv(self, results: List[Dict], filename: str):
        """Export results with detailed quality information"""
        
        export_data = []
        
        for i, result in enumerate(results, 1):
            quality_score = self._assess_result_quality(result, i) if result.get('success') else 0.0
            
            row = {
                'item_number': i,
                'original_title': result.get('input_title', ''),
                'optimized_title': result.get('optimized_title', ''),
                'store_label': result.get('store_label', ''),
                'success': result.get('success', False),
                'quality_score': quality_score,
                'web_search_used': 'web_research' in result.get('parsed_data', {}),
                'web_search_success': 'web_research' in result.get('parsed_data', {}) and 'error' not in result.get('parsed_data', {}).get('web_research', {}),
                'research_confidence': result.get('parsed_data', {}).get('research_confidence', 'N/A'),
                'category_found': result.get('category_match', {}).get('categoria', 'NOT FOUND'),
                'errors': '; '.join(result.get('errors', []))
            }
            
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        return df