# AI Agent Builder - Meta Agent

A powerful AI agent that helps users create, manage, and optimize other AI agents using LangChain and Weaviate.

## 🚀 Features

### Core Capabilities
- **Agent Creation**: Create new AI agents with custom system prompts, tools, and configurations
- **Agent Management**: List, update, delete, and search existing agents
- **Code Generation**: Automatically generate Python code for your agents
- **Agent Testing**: Test agents with sample inputs to verify functionality
- **Semantic Search**: Find agents using natural language queries
- **Best Practices**: Get guidance on agent design and optimization

### Tools Available
1. **create_agent**: Create a new AI agent with specified configuration
2. **list_agents**: List all agents created by a specific author
3. **get_agent**: Get a specific agent's configuration by ID
4. **update_agent**: Update an existing agent's configuration
5. **delete_agent**: Delete an agent by ID
6. **search_agents**: Search for agents using semantic search
7. **generate_agent_code**: Generate Python code for an agent
8. **test_agent**: Test an agent with a sample input

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Weaviate instance (cloud or local)
- Required environment variables

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables** in your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
EMBEDDING_MODEL=text-embedding-3-small
```

3. **Initialize the schema** (this happens automatically when you first use the meta agent):
```python
from libs.weaviate_lib import initialize_schema
initialize_schema()
```

## 📖 Usage

### Basic Usage

```python
from agents.meta_agent import generate_meta_agent_response
from data_classes.common_classes import Message, Language

# Create a conversation
messages = [
    Message(role="user", content="I want to create an AI agent for customer service. Can you help me?")
]

# Get response from meta agent
response = generate_meta_agent_response(
    messages=messages,
    language=Language.EN
)

print(response)
```

### Creating a Simple Agent

```python
from agents.meta_agent import create_simple_agent

# Create a customer service agent
agent = create_simple_agent(
    name="Customer Service Agent",
    description="A helpful customer service agent",
    system_prompt="""You are a helpful customer service agent. Your role is to:
- Answer customer questions about products and services
- Help with order status and tracking
- Be polite, professional, and helpful""",
    author="your_email@example.com"
)

print(f"Created agent: {agent}")
```

### Managing Agents

```python
from agents.meta_agent import list_agents, get_agent, update_agent, delete_agent

# List all your agents
agents = list_agents(author="your_email@example.com")
for agent in agents:
    print(f"- {agent['name']}: {agent['description']}")

# Get a specific agent
agent_id = "your-agent-uuid"
agent_config = get_agent(agent_id)

# Update an agent
update_result = update_agent(
    agent_id=agent_id,
    system_prompt="Updated system prompt here"
)

# Delete an agent
delete_result = delete_agent(agent_id)
```

### Testing Agents

```python
from agents.meta_agent import test_agent

# Test an agent with sample input
test_result = test_agent(
    agent_id="your-agent-uuid",
    test_input="Hello, I have a question about my order"
)

print(f"Agent response: {test_result['response']}")
```

### Generating Code

```python
from agents.meta_agent import get_agent, generate_agent_code

# Get agent configuration
agent_config = get_agent("your-agent-uuid")

# Generate Python code
code = generate_agent_code(agent_config)
print(code)
```

## 🎯 Example Scenarios

### Scenario 1: Customer Service Agent
```
User: "I need an AI agent that can handle customer service inquiries"
Meta Agent: "I'll help you create a customer service agent! Let me ask a few questions:
1. What types of inquiries should it handle? (orders, returns, product info, etc.)
2. What tone should it use? (formal, friendly, casual)
3. Should it escalate to humans for complex issues?
4. What specific tools or integrations do you need?"
```

### Scenario 2: Data Analysis Agent
```
User: "Create an agent for data analysis tasks"
Meta Agent: "Great! For a data analysis agent, I recommend including these tools:
- pandas for data manipulation
- matplotlib/seaborn for visualization
- scikit-learn for machine learning
- numpy for numerical operations

Let me create an agent with a system prompt focused on data analysis..."
```

### Scenario 3: Content Creation Agent
```
User: "I want an agent that can help with content creation"
Meta Agent: "Perfect! A content creation agent can be very useful. Let me suggest:
- Writing assistance tools
- SEO optimization
- Content planning
- Style guides

What type of content will it focus on? (blog posts, social media, technical docs, etc.)"
```

## 🔧 Advanced Usage

### Custom Agent with Tools

```python
from agents.meta_agent import create_agent

# Create an agent with specific tools
agent = create_agent(
    name="Data Analysis Agent",
    description="An agent specialized in data analysis and visualization",
    system_prompt="""You are a data analysis expert. You can:
- Load and clean data
- Perform statistical analysis
- Create visualizations
- Generate insights and reports""",
    tools=["pandas", "matplotlib", "scikit-learn", "numpy"],
    model="gpt-4o",
    temperature=0.1,
    author="your_email@example.com"
)
```

### Semantic Search for Agents

```python
from agents.meta_agent import search_agents

# Search for agents related to customer service
results = search_agents("customer service agent", limit=5)
for agent in results:
    print(f"- {agent['name']}: {agent['description']}")
```

## 🏗️ Architecture

### Components
- **Meta Agent**: The main agent that helps users build other agents
- **Weaviate Database**: Stores agent configurations and enables semantic search
- **LangChain Tools**: Provides the tools for agent management
- **OpenAI Integration**: Powers the language model for responses

### Data Flow
1. User interacts with meta agent
2. Meta agent uses tools to manage agents in Weaviate
3. Agent configurations are stored and retrieved from Weaviate
4. Code generation creates deployable Python classes
5. Testing validates agent functionality

## 🧪 Testing

Run the example script to test the meta agent:

```bash
python example_meta_agent.py
```

This will:
1. Create a sample customer service agent
2. List all agents
3. Test the created agent
4. Demonstrate conversation with the meta agent
5. Offer an interactive demo

## 🔒 Security Considerations

- All agent configurations are stored in Weaviate with proper access controls
- API keys should be kept secure in environment variables
- Agent testing is done in a controlled environment
- Generated code should be reviewed before deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check that all environment variables are set correctly
2. Verify your Weaviate instance is running and accessible
3. Ensure your OpenAI API key is valid
4. Check the logs for detailed error messages

For additional help, please open an issue in the repository. 