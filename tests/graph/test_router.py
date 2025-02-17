import pytest
from langchain_core.messages import HumanMessage, AIMessage

from ai_companion.graph.utils.chains import get_router_chain
from ai_companion.graph.state import AICompanionState

@pytest.mark.asyncio
async def test_router_detects_rag_for_oncology():
    """Test that router correctly identifies oncology/medical queries for RAG."""
    chain = get_router_chain()
    
    # Test cases for RAG detection
    rag_test_messages = [
        [HumanMessage(content="What are the benefits of the POLA card?")],
        [HumanMessage(content="Can you tell me about oncology treatment options?")],
        [HumanMessage(content="How does the POLA card discount work for public transport?")],
    ]
    
    for messages in rag_test_messages:
        response = await chain.ainvoke({"messages": messages})
        assert response.response_type == "rag", f"Failed to detect RAG for message: {messages[0].content}"

@pytest.mark.asyncio
async def test_router_normal_conversation():
    """Test that router correctly identifies normal conversation."""
    chain = get_router_chain()
    
    # Test cases for normal conversation
    conv_test_messages = [
        [HumanMessage(content="How are you today?")],
        [HumanMessage(content="What's your favorite food?")],
        [HumanMessage(content="Tell me about your work.")],
    ]
    
    for messages in conv_test_messages:
        response = await chain.ainvoke({"messages": messages})
        assert response.response_type == "conversation", f"Incorrectly classified normal conversation: {messages[0].content}"

@pytest.mark.asyncio
async def test_router_context_awareness():
    """Test that router maintains context awareness for RAG decisions."""
    chain = get_router_chain()
    
    # Test conversation flow leading to RAG
    messages = [
        HumanMessage(content="Hi, I need some information."),
        AIMessage(content="Sure, I'd be happy to help! What would you like to know?"),
        HumanMessage(content="I have questions about the POLA card benefits."),
    ]
    
    response = await chain.ainvoke({"messages": messages})
    assert response.response_type == "rag", "Failed to detect RAG in conversation context"

    # Test conversation flow that shouldn't trigger RAG
    messages = [
        HumanMessage(content="Hi, I need some information."),
        AIMessage(content="Sure, I'd be happy to help! What would you like to know?"),
        HumanMessage(content="What's your favorite place in San Francisco?"),
    ]
    
    response = await chain.ainvoke({"messages": messages})
    assert response.response_type == "conversation", "Incorrectly triggered RAG in normal conversation" 