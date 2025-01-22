from typing import Dict, List, Optional
from datetime import datetime
class ChatbotEvaluator:
    def __init__(self):
        """Initialize the evaluator with metrics tracking."""
        self.metrics = {
            'accuracy': [],
            'relevance': [],
            'user_satisfaction': [],
            'response_times': [],
            'conversation_logs': []
        }
        
        # Expected responses for known queries
        self.expected_responses = {
            'order_status': {
                'ORD123': "Order ORD123 is currently Delivered (as of 2024-01-15).",
                'ORD124': "Order ORD124 is currently In Transit (as of 2024-01-18).",
                'ORD125': "Order ORD125 is currently Processing (as of 2024-01-20)."
            },
            'return_policy': [
                "You can return most items within 30 days of purchase",
                "Items must be in their original condition",
                "bring your receipt or proof of purchase"
            ]
        }

    def evaluate_response(self, user_input: str, bot_response: str, response_time: float) -> Dict:
        """
        Evaluate a single bot response based on multiple criteria.
        """
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'bot_response': bot_response,
            'response_time': response_time,
            'metrics': {}
        }

        accuracy = self._evaluate_accuracy(user_input, bot_response)
        
        relevance = self._evaluate_relevance(user_input, bot_response)
        
        # Calculate response time score (1-5 scale)
        time_score = 5 if response_time < 1.0 else (4 if response_time < 2.0 else 3)

        evaluation['metrics'] = {
            'accuracy': accuracy,
            'relevance': relevance,
            'response_time': time_score
        }

        # Store evaluation
        self.metrics['accuracy'].append(accuracy)
        self.metrics['relevance'].append(relevance)
        self.metrics['response_times'].append(response_time)
        self.metrics['conversation_logs'].append(evaluation)

        return evaluation

    def _evaluate_accuracy(self, user_input: str, bot_response: str) -> float:
        """
        Evaluate response accuracy based on expected responses.
        Returns a score between 0 and 1.
        """
        # Check for order status queries
        if 'ORD' in user_input:
            order_id = user_input[user_input.find('ORD'):user_input.find('ORD')+6]
            if order_id in self.expected_responses['order_status']:
                expected = self.expected_responses['order_status'][order_id]
                return 1.0 if expected.lower() in bot_response.lower() else 0.0

        # Check for return policy queries
        if 'return' in user_input.lower():
            matches = sum(1 for phrase in self.expected_responses['return_policy'] 
                        if phrase.lower() in bot_response.lower())
            return matches / len(self.expected_responses['return_policy'])

        return 0.8  # Default score for other responses

    def _evaluate_relevance(self, user_input: str, bot_response: str) -> float:
        """
        Evaluate response relevance based on context matching.
        Returns a score between 0 and 1.
        """
        # Check if response addresses key terms in user input
        user_keywords = set(user_input.lower().split())
        response_keywords = set(bot_response.lower().split())
        
        # Remove common words
        common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but'}
        user_keywords = user_keywords - common_words
        
        if not user_keywords:
            return 0.8  # Default score for simple queries
            
        # Calculate overlap
        keyword_overlap = len(user_keywords.intersection(response_keywords))
        return min(1.0, keyword_overlap / len(user_keywords))

    def get_summary_metrics(self) -> Dict:
        """
        Return summary statistics of all evaluations.
        """
        if not self.metrics['accuracy']:
            return {
                'total_conversations': 0,
                'average_accuracy': 0,
                'average_relevance': 0,
                'average_response_time': 0
            }

        return {
            'total_conversations': len(self.metrics['conversation_logs']),
            'average_accuracy': sum(self.metrics['accuracy']) / len(self.metrics['accuracy']),
            'average_relevance': sum(self.metrics['relevance']) / len(self.metrics['relevance']),
            'average_response_time': sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        }