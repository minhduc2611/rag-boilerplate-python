#!/usr/bin/env python3
"""
Example script demonstrating how to use the Meta Agent to create and manage AI agents.
"""

import os
from dotenv import load_dotenv
from agents.meta_agent import (
    generate_meta_agent_response,
    create_simple_agent,
    list_agents,
    get_agent,
    test_agent
)
from data_classes.common_classes import Message, Language

# Load environment variables
load_dotenv()

def main():
    """Main function to demonstrate the meta agent capabilities."""
    
    print("🤖 AI Agent Builder - Meta Agent Demo")
    print("=" * 50)
    
    # Example 1: Create a simple agent
    print("\n1. Creating a simple customer service agent...")
    
    customer_service_agent = create_simple_agent(
        name="Customer Service Agent",
        description="A helpful customer service agent that can answer common questions",
        system_prompt="""You are a helpful customer service agent. Your role is to:
- Answer customer questions about products and services
- Help with order status and tracking
- Provide information about returns and refunds
- Be polite, professional, and helpful
- Escalate complex issues to human agents when necessary

Always greet customers warmly and end conversations professionally.""",
        author="demo_user"
    )
    
    print(f"✅ Created agent: {customer_service_agent}")
    
    # Example 2: List all agents
    print("\n2. Listing all agents...")
    agents = list_agents(author="demo_user")
    print(f"Found {len(agents)} agents:")
    for agent in agents:
        if "error" not in agent:
            print(f"  - {agent.get('name', 'Unknown')} (ID: {agent.get('uuid', 'N/A')})")
    
    # Example 3: Test an agent
    if agents and "error" not in agents[0]:
        agent_id = agents[0].get('uuid')
        print(f"\n3. Testing agent {agent_id}...")
        
        test_result = test_agent(
            agent_id=agent_id,
            test_input="Hello, I have a question about my recent order. Can you help me?"
        )
        
        print(f"Test result: {test_result}")
    
    # Example 4: Using the meta agent for conversation
    print("\n4. Using the meta agent for conversation...")
    
    # Create a conversation with the meta agent
    messages = [
        Message(role="user", content="Hello! I want to create an AI agent that can help with data analysis. Can you help me?")
    ]
    
    response = generate_meta_agent_response(
        messages=messages,
        language=Language.EN
    )
    
    print(f"Meta Agent Response: {response}")
    
    # Continue the conversation
    messages.append(Message(role="assistant", content=response))
    messages.append(Message(role="user", content="What tools should I include for data analysis?"))
    
    response2 = generate_meta_agent_response(
        messages=messages,
        language=Language.EN
    )
    
    print(f"Meta Agent Response: {response2}")

def interactive_demo():
    """Interactive demo where users can chat with the meta agent."""
    
    print("\n🎯 Interactive Meta Agent Demo")
    print("Type 'quit' to exit")
    print("-" * 30)
    
    messages = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not user_input:
            continue
        
        # Add user message
        messages.append(Message(role="user", content=user_input))
        
        # Get response from meta agent
        try:
            response = generate_meta_agent_response(
                messages=messages,
                language=Language.EN
            )
            
            print(f"\nMeta Agent: {response}")
            
            # Add assistant response
            messages.append(Message(role="assistant", content=response))
            
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY", "WEAVIATE_URL", "WEAVIATE_API_KEY", "EMBEDDING_MODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        exit(1)
    
    # Run the demo
    main()
    
    # Ask if user wants interactive demo
    choice = input("\nWould you like to try the interactive demo? (y/n): ").strip().lower()
    if choice in ['y', 'yes']:
        interactive_demo() 