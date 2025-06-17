#!/usr/bin/env python3
"""
Test script for the Meta Agent functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from agents.meta_agent import (
            generate_meta_agent_response,
            create_agent,
            list_agents,
            get_agent,
            update_agent,
            delete_agent,
            search_agents,
            generate_agent_code,
            test_agent,
            create_simple_agent
        )
        print("✅ All meta agent imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_weaviate_connection():
    """Test Weaviate connection and schema initialization."""
    print("\nTesting Weaviate connection...")
    
    try:
        from libs.weaviate_lib import initialize_schema, client
        initialize_schema()
        print("✅ Weaviate connection and schema initialization successful")
        return True
    except Exception as e:
        print(f"❌ Weaviate connection error: {e}")
        return False

def test_simple_agent_creation():
    """Test creating a simple agent."""
    print("\nTesting simple agent creation...")
    
    try:
        from agents.meta_agent import create_simple_agent
        
        agent = create_simple_agent(
            name="Test Agent",
            description="A test agent for validation",
            system_prompt="You are a helpful test agent.",
            author="test_user"
        )
        
        if "error" not in agent:
            print(f"✅ Simple agent created: {agent}")
            return agent.get("agent_id")
        else:
            print(f"❌ Agent creation failed: {agent}")
            return None
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return None

def test_agent_management(agent_id):
    """Test agent management functions."""
    if not agent_id:
        print("❌ Skipping agent management tests - no agent ID")
        return False
    
    print(f"\nTesting agent management for agent {agent_id}...")
    
    try:
        from agents.meta_agent import get_agent, update_agent, list_agents
        
        # Test get agent
        agent = get_agent(agent_id)
        if "error" not in agent:
            print(f"✅ Agent retrieved: {agent.get('name')}")
        else:
            print(f"❌ Get agent failed: {agent}")
            return False
        
        # Test update agent
        update_result = update_agent(
            agent_id=agent_id,
            description="Updated test agent description"
        )
        if "error" not in update_result:
            print("✅ Agent updated successfully")
        else:
            print(f"❌ Update agent failed: {update_result}")
            return False
        
        # Test list agents
        agents = list_agents(author="test_user", limit=5)
        if agents and "error" not in agents[0]:
            print(f"✅ Listed {len(agents)} agents")
        else:
            print(f"❌ List agents failed: {agents}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Agent management error: {e}")
        return False

def test_agent_testing(agent_id):
    """Test agent testing functionality."""
    if not agent_id:
        print("❌ Skipping agent testing - no agent ID")
        return False
    
    print(f"\nTesting agent testing for agent {agent_id}...")
    
    try:
        from agents.meta_agent import test_agent
        
        test_result = test_agent(
            agent_id=agent_id,
            test_input="Hello, this is a test message."
        )
        
        if "error" not in test_result:
            print(f"✅ Agent test successful: {test_result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Agent test failed: {test_result}")
            return False
    except Exception as e:
        print(f"❌ Agent testing error: {e}")
        return False

def test_code_generation(agent_id):
    """Test code generation functionality."""
    if not agent_id:
        print("❌ Skipping code generation - no agent ID")
        return False
    
    print(f"\nTesting code generation for agent {agent_id}...")
    
    try:
        from agents.meta_agent import get_agent, generate_agent_code
        
        agent_config = get_agent(agent_id)
        if "error" in agent_config:
            print(f"❌ Could not get agent config: {agent_config}")
            return False
        
        code = generate_agent_code(agent_config)
        if code and "Error generating code" not in code:
            print(f"✅ Code generated successfully ({len(code)} characters)")
            return True
        else:
            print(f"❌ Code generation failed: {code}")
            return False
    except Exception as e:
        print(f"❌ Code generation error: {e}")
        return False

def test_meta_agent_conversation():
    """Test the meta agent conversation functionality."""
    print("\nTesting meta agent conversation...")
    
    try:
        from agents.meta_agent import generate_meta_agent_response
        from data_classes.common_classes import Message, Language
        
        messages = [
            Message(role="user", content="Hello! Can you help me create an AI agent?")
        ]
        
        response = generate_meta_agent_response(
            messages=messages,
            language=Language.EN
        )
        
        if response and "Error generating response" not in response:
            print(f"✅ Meta agent conversation successful: {response[:100]}...")
            return True
        else:
            print(f"❌ Meta agent conversation failed: {response}")
            return False
    except Exception as e:
        print(f"❌ Meta agent conversation error: {e}")
        return False

def cleanup_test_agent(agent_id):
    """Clean up the test agent."""
    if not agent_id:
        return
    
    print(f"\nCleaning up test agent {agent_id}...")
    
    try:
        from agents.meta_agent import delete_agent
        
        result = delete_agent(agent_id)
        if "error" not in result:
            print("✅ Test agent cleaned up successfully")
        else:
            print(f"❌ Cleanup failed: {result}")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def main():
    """Run all tests."""
    print("🧪 Meta Agent Test Suite")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "WEAVIATE_URL", "WEAVIATE_API_KEY", "EMBEDDING_MODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ Environment variables configured")
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Weaviate Connection", test_weaviate_connection),
        ("Simple Agent Creation", test_simple_agent_creation),
        ("Meta Agent Conversation", test_meta_agent_conversation),
    ]
    
    agent_id = None
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        if test_name == "Simple Agent Creation":
            agent_id = test_func()
            if agent_id:
                passed_tests += 1
                # Run additional tests that depend on having an agent
                dependent_tests = [
                    ("Agent Management", lambda: test_agent_management(agent_id)),
                    ("Agent Testing", lambda: test_agent_testing(agent_id)),
                    ("Code Generation", lambda: test_code_generation(agent_id)),
                ]
                
                for dep_test_name, dep_test_func in dependent_tests:
                    print(f"\n{'='*20} {dep_test_name} {'='*20}")
                    if dep_test_func():
                        passed_tests += 1
                    total_tests += 1
        else:
            if test_func():
                passed_tests += 1
    
    # Cleanup
    cleanup_test_agent(agent_id)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Meta agent is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 