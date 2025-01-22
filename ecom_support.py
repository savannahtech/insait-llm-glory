
import os
import csv
from datetime import datetime
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from evaluator import ChatbotEvaluator
from langchain_openai import ChatOpenAI
class EcommerceSupport:
    def __init__(self, model_type:str, api_key: str):
        """Initialize the support system with LangChain components."""
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        self.model_type = model_type.lower()
        
        # Configure the appropriate model based on user input
        if self.model_type == "gemini":
            genai.configure(api_key=api_key)
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.3,
                google_api_key=api_key,
                convert_system_message_to_human=True
            )
        elif self.model_type == "openai":
            self.llm = ChatOpenAI(api_key=api_key, temperature=0.3)
       
        else:
            raise ValueError("Unsupported model type. Please use 'gemini', 'openai', or 'cohere'.")
        # Define conversation memory
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True
        )
        self.collecting_contact = False
        self.contact_info = {
            "name": None,
            "email": None,
            "phone": None
        }
        
        # Initialize return policies
        self.return_policies = {
            "general": "You can return most items within 30 days of purchase for a full refund or exchange. Items must be in their original condition, with all tags and packaging intact. Please bring your receipt or proof of purchase when returning items.",
            "exceptions": "Yes, certain items such as clearance merchandise, perishable goods, and personal care items are non-returnable. Please check the product description or ask a store associate for more details.",
            "refund_process": "Refunds will be issued to the original form of payment. If you paid by credit card, the refund will be credited to your card. If you paid by cash or check, you will receive a cash refund."
        }
        
        # Mock order database
        self.order_database = {
            "ORD123": {"status": "Delivered", "date": "2024-01-15"},
            "ORD124": {"status": "In Transit", "date": "2024-01-18"},
            "ORD125": {"status": "Processing", "date": "2024-01-20"}
        }
        
        # Setup conversation prompt template
        self.template = """You are a helpful e-commerce customer support agent. Use the following rules:
        1. Be polite and professional
        2. For order status queries, ask for the order ID if not provided
        3. For human representative requests, ask for name, email, and phone number
        4. For return policy questions, provide accurate information from the stored policies
        5. Keep responses concise but informative

        Current conversation:
        {chat_history}
        Human: {input}
        Assistant:"""
        
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=self.template
        )
        
        # Setup main conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=True
        )
        
        # Setup output parser for structured responses
        self.response_schemas = [
            ResponseSchema(name="intent", description="The detected intent of the user's message"),
            ResponseSchema(name="requires_order_id", description="Boolean indicating if an order ID is needed"),
            ResponseSchema(name="requires_contact_info", description="Boolean indicating if contact information is needed"),
            ResponseSchema(name="response", description="The response to send to the user")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)

    def save_contact_info(self, name: str, email: str, phone: str) -> None:
        """Save customer contact information to CSV file using LangChain's utilities."""
        filename = "customer_requests.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Name', 'Email', 'Phone', 'Timestamp'])
            writer.writerow([name, email, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    def check_order_status(self, order_id: str) -> str:
        """Check order status from mock database."""
        if order_id in self.order_database:
            order = self.order_database[order_id]
            return f"Order {order_id} is currently {order['status']} (as of {order['date']})."
        return "Sorry, I couldn't find that order. Please check the order ID and try again."

    def get_return_policy(self, query_type: str) -> str:
        """Get specific return policy information."""
        return self.return_policies.get(query_type, "I don't have information about that specific aspect of our return policy.")

    def process_message(self, message: str) -> str:
        """Process message using LangChain conversation chain."""
        # Direct order ID check
        if "ORD" in message:
            order_id = message[message.find("ORD"):message.find("ORD")+6]
            if order_id in self.order_database:
                return self.check_order_status(order_id)
        
        # Get response from conversation chain
        response = self.conversation.predict(input=message)
        
        # Check if response contains order check command
        if "CHECK_ORDER:" in response:
            order_id = response.split(":")[1].strip()
            return self.check_order_status(order_id)
            
        return response
    def save_contact_info(self) -> None:
        """Save the collected contact information to CSV file."""
        filename = "customer_requests.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Name', 'Email', 'Phone', 'Timestamp'])
            writer.writerow([
                self.contact_info['name'],
                self.contact_info['email'],
                self.contact_info['phone'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

    def handle_contact_collection(self, message: str) -> str:
        """Handle the contact information collection process."""
        if not self.contact_info['name']:
            self.contact_info['name'] = message
            return "Thank you! Please provide your email address."
            
        if not self.contact_info['email']:
            if self.validate_email(message):
                self.contact_info['email'] = message
                return "Thank you! Finally, please provide your phone number."
            return "That doesn't look like a valid email address. Please provide a valid email."
            
        if not self.contact_info['phone']:
            if self.validate_phone(message):
                self.contact_info['phone'] = message
                self.save_contact_info()
                # Reset collection state
                self.collecting_contact = False
                self.contact_info = {"name": None, "email": None, "phone": None}
                return "Thank you! Your information has been saved. A customer service representative will contact you shortly."
            return "That doesn't look like a valid phone number. Please provide a valid phone number."

    def process_message(self, message: str) -> str:
        """Process message using LangChain conversation chain."""
        # Handle ongoing contact collection
        if self.collecting_contact:
            return self.handle_contact_collection(message)

        # Direct order ID check
        if "ORD" in message:
            order_id = message[message.find("ORD"):message.find("ORD")+6]
            if order_id in self.order_database:
                return self.check_order_status(order_id)
        
        # Get response from conversation chain
        response = self.conversation.predict(input=message)
        
        # Check for special commands
        if "CHECK_ORDER:" in response:
            order_id = response.split(":")[1].strip()
            return self.check_order_status(order_id)
        
        if "COLLECT_CONTACT" in response:
            self.collecting_contact = True
            return "I'll connect you with a customer service representative. First, please provide your full name."
            
        return response