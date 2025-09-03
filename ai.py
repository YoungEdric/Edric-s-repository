# ai.py - OpenAI integration for AI reasoning, Q&A, and summarization

import openai
import requests
import json
from datetime import datetime
from utils import log_message, retry_operation, speak
from config import *

class AIHandler:
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.max_history_length = 10  # Keep last 10 exchanges
        self.initialize_openai()
    
    def initialize_openai(self):
        """Initialize OpenAI client"""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
            log_message("OpenAI API key not configured", "WARNING")
            return False
        
        try:
            openai.api_key = OPENAI_API_KEY
            self.client = openai
            
            # Test the connection
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            log_message("OpenAI client initialized successfully")
            return True
            
        except Exception as e:
            log_message(f"Failed to initialize OpenAI client: {e}", "ERROR")
            return False
    
    def ask_question(self, question, context=None):
        """
        Ask a question to GPT and get an answer
        Args:
            question (str): The question to ask
            context (str): Optional context for the question
        Returns:
            str: AI response or error message
        """
        if not self.client:
            return "AI service is not available. Please check your API key configuration."
        
        def make_request():
            messages = []
            
            # Add system message with context
            system_message = f"You are Sarah, a helpful AI assistant. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            if context:
                system_message += f" Context: {context}"
            
            messages.append({"role": "system", "content": system_message})
            
            # Add conversation history
            for entry in self.conversation_history[-5:]:  # Last 5 exchanges
                messages.append({"role": "user", "content": entry["user"]})
                messages.append({"role": "assistant", "content": entry["assistant"]})
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            answer = retry_operation(make_request)
            
            if answer:
                # Add to conversation history
                self.add_to_history(question, answer)
                log_message(f"AI Question: {question}")
                log_message(f"AI Answer: {answer}")
                return answer
            else:
                return "I'm sorry, I couldn't get an answer right now. Please try again later."
                
        except Exception as e:
            log_message(f"Error in ask_question: {e}", "ERROR")
            return "I encountered an error while processing your question."
    
    def summarize_text(self, text, max_length=100):
        """
        Summarize the given text
        Args:
            text (str): Text to summarize
            max_length (int): Maximum length of summary in words
        Returns:
            str: Summary or error message
        """
        if not self.client:
            return "AI service is not available."
        
        if len(text.split()) < 20:
            return "The text is too short to summarize effectively."
        
        def make_request():
            messages = [
                {
                    "role": "system", 
                    "content": f"Summarize the following text in approximately {max_length} words. Be concise and capture the key points."
                },
                {"role": "user", "content": text}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=max_length * 2,  # Allow some buffer
                temperature=0.3,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            summary = retry_operation(make_request)
            
            if summary:
                log_message(f"Text summarized: {len(text)} chars -> {len(summary)} chars")
                return summary
            else:
                return "I couldn't summarize the text right now."
                
        except Exception as e:
            log_message(f"Error in summarize_text: {e}", "ERROR")
            return "I encountered an error while summarizing."
    
    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text
        Args:
            text (str): Text to analyze
        Returns:
            dict: Sentiment analysis results
        """
        if not self.client:
            return {"sentiment": "unknown", "confidence": 0, "explanation": "AI service not available"}
        
        def make_request():
            messages = [
                {
                    "role": "system", 
                    "content": "Analyze the sentiment of the following text. Respond with a JSON object containing 'sentiment' (positive/negative/neutral), 'confidence' (0-1), and 'explanation'."
                },
                {"role": "user", "content": text}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=200,
                temperature=0.1,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            result = retry_operation(make_request)
            
            if result:
                # Try to parse JSON response
                try:
                    sentiment_data = json.loads(result)
                    return sentiment_data
                except json.JSONDecodeError:
                    # Fallback parsing if JSON fails
                    sentiment = "neutral"
                    if "positive" in result.lower():
                        sentiment = "positive"
                    elif "negative" in result.lower():
                        sentiment = "negative"
                    
                    return {
                        "sentiment": sentiment,
                        "confidence": 0.5,
                        "explanation": result
                    }
            else:
                return {"sentiment": "unknown", "confidence": 0, "explanation": "Could not analyze"}
                
        except Exception as e:
            log_message(f"Error in analyze_sentiment: {e}", "ERROR")
            return {"sentiment": "error", "confidence": 0, "explanation": str(e)}
    
    def generate_ideas(self, topic, count=5):
        """
        Generate ideas about a given topic
        Args:
            topic (str): Topic to generate ideas about
            count (int): Number of ideas to generate
        Returns:
            list: List of generated ideas
        """
        if not self.client:
            return ["AI service is not available."]
        
        def make_request():
            messages = [
                {
                    "role": "system", 
                    "content": f"Generate {count} creative and practical ideas about the topic. Return them as a numbered list."
                },
                {"role": "user", "content": f"Topic: {topic}"}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=400,
                temperature=0.8,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            result = retry_operation(make_request)
            
            if result:
                # Parse the numbered list
                ideas = []
                lines = result.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Remove numbering and clean up
                        idea = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                        if idea:
                            ideas.append(idea)
                
                return ideas[:count] if ideas else [result]
            else:
                return ["I couldn't generate ideas right now."]
                
        except Exception as e:
            log_message(f"Error in generate_ideas: {e}", "ERROR")
            return ["I encountered an error while generating ideas."]
    
    def explain_concept(self, concept, complexity="simple"):
        """
        Explain a concept at different complexity levels
        Args:
            concept (str): Concept to explain
            complexity (str): "simple", "intermediate", or "advanced"
        Returns:
            str: Explanation
        """
        if not self.client:
            return "AI service is not available."
        
        complexity_instructions = {
            "simple": "Explain this concept in simple terms that a child could understand. Use analogies and examples.",
            "intermediate": "Provide a clear explanation suitable for a high school student. Include key details and examples.",
            "advanced": "Give a comprehensive explanation with technical details, suitable for someone studying the subject."
        }
        
        instruction = complexity_instructions.get(complexity, complexity_instructions["simple"])
        
        def make_request():
            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"Explain: {concept}"}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=600,
                temperature=0.5,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            explanation = retry_operation(make_request)
            
            if explanation:
                log_message(f"Explained concept: {concept} (complexity: {complexity})")
                return explanation
            else:
                return "I couldn't explain that concept right now."
                
        except Exception as e:
            log_message(f"Error in explain_concept: {e}", "ERROR")
            return "I encountered an error while explaining."
    
    def translate_text(self, text, target_language):
        """
        Translate text to target language
        Args:
            text (str): Text to translate
            target_language (str): Target language (e.g., "Spanish", "French")
        Returns:
            str: Translated text
        """
        if not self.client:
            return "AI service is not available."
        
        def make_request():
            messages = [
                {
                    "role": "system", 
                    "content": f"Translate the following text to {target_language}. Only provide the translation, no additional text."
                },
                {"role": "user", "content": text}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=len(text.split()) * 3,  # Allow for language expansion
                temperature=0.1,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            translation = retry_operation(make_request)
            
            if translation:
                log_message(f"Translated text to {target_language}")
                return translation
            else:
                return "I couldn't translate the text right now."
                
        except Exception as e:
            log_message(f"Error in translate_text: {e}", "ERROR")
            return "I encountered an error while translating."
    
    def solve_math_problem(self, problem):
        """
        Solve a math problem with step-by-step explanation
        Args:
            problem (str): Math problem to solve
        Returns:
            str: Solution with explanation
        """
        if not self.client:
            return "AI service is not available."
        
        def make_request():
            messages = [
                {
                    "role": "system", 
                    "content": "Solve the math problem step by step. Show your work and explain each step clearly."
                },
                {"role": "user", "content": f"Solve: {problem}"}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.1,
                timeout=OPENAI_TIMEOUT
            )
            
            return response.choices[0].message.content.strip()
        
        try:
            solution = retry_operation(make_request)
            
            if solution:
                log_message(f"Solved math problem: {problem}")
                return solution
            else:
                return "I couldn't solve the math problem right now."
                
        except Exception as e:
            log_message(f"Error in solve_math_problem: {e}", "ERROR")
            return "I encountered an error while solving the problem."
    
    def add_to_history(self, user_message, assistant_response):
        """Add exchange to conversation history"""
        self.conversation_history.append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        log_message("Conversation history cleared")
    
    def get_history_summary(self):
        """Get a summary of recent conversation"""
        if not self.conversation_history:
            return "No recent conversation history."
        
        history_text = ""
        for entry in self.conversation_history[-3:]:  # Last 3 exchanges
            history_text += f"User: {entry['user']}\nSarah: {entry['assistant']}\n\n"
        
        return f"Recent conversation:\n{history_text}"
    
    def is_available(self):
        """Check if AI service is available"""
        return self.client is not None

# Create global AI handler instance
ai_handler = AIHandler()

# Convenience functions for easy import
def ask_question(question, context=None):
    """Ask a question to the AI"""
    return ai_handler.ask_question(question, context)

def summarize_text(text, max_length=100):
    """Summarize text"""
    return ai_handler.summarize_text(text, max_length)

def analyze_sentiment(text):
    """Analyze text sentiment"""
    return ai_handler.analyze_sentiment(text)

def generate_ideas(topic, count=5):
    """Generate ideas about a topic"""
    return ai_handler.generate_ideas(topic, count)

def explain_concept(concept, complexity="simple"):
    """Explain a concept"""
    return ai_handler.explain_concept(concept, complexity)

def translate_text(text, target_language):
    """Translate text"""
    return ai_handler.translate_text(text, target_language)

def solve_math_problem(problem):
    """Solve math problem"""
    return ai_handler.solve_math_problem(problem)

def clear_conversation_history():
    """Clear conversation history"""
    ai_handler.clear_history()

def get_conversation_summary():
    """Get conversation summary"""
    return ai_handler.get_history_summary()

def is_ai_available():
    """Check if AI is available"""
    return ai_handler.is_available()

# Log successful module initialization
log_message("AI module initialized successfully")