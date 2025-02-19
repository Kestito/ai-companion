import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ai_companion.graph.graph import create_workflow_graph, graph
from ai_companion.graph.state import AICompanionState
from ai_companion.graph.nodes import (
    router_node,
    conversation_node,
    rag_node,
    memory_extraction_node,
    memory_injection_node
)
from ai_companion.utils.logger import QALogger

# Initialize logger
qa_logger = QALogger(log_dir="tests/logs/qa_logs")

# Test cases for RAG questions (questions that should use knowledge base)
RAG_TEST_CASES = [
    (
        "kaip gauti pola kortele?",
        "POLA kortelę galite gauti nemokamai užsiregistravę internetu arba artimiausiame POLA skyriuje.",
        "Uses RAG because it's directly about POLA card acquisition process"
    ),
    (
        "kokias nuolaidas suteikia pola kortele?",
        "POLA kortelė suteikia įvairias nuolaidas parduotuvėse, įskaitant nuolaidas vaistinėse, parduotuvėse ir kitose vietose.",
        "Uses RAG because it's asking about specific POLA card benefits"
    ),
    (
        "kur galima naudoti pola kortele?",
        "POLA kortelę galima naudoti įvairiose parduotuvėse, vaistinėse ir kitose prekybos vietose, kurios yra POLA partneriai.",
        "Uses RAG because it's asking about POLA card usage locations"
    ),
    (
        "ar pola kortele mokama?",
        "Ne, POLA kortelė yra nemokama. Ją galite gauti nemokamai užsiregistravę.",
        "Uses RAG because it's asking about POLA card cost"
    ),
    (
        "kiek galioja pola kortele?",
        "POLA kortelė galioja neribotą laiką nuo jos išdavimo momento.",
        "Uses RAG because it's asking about POLA card validity period"
    )
]

# Test cases for non-RAG questions (questions that should use general knowledge)
NON_RAG_TEST_CASES = [
    (
        "koks dabar oras?",
        "Atsiprašau, bet negaliu pateikti realaus laiko orų informacijos. Rekomenduoju pasitikrinti orų prognozę oficialiuose šaltiniuose.",
        "Doesn't use RAG because it's about real-time weather information"
    ),
    (
        "kaip tavo diena?",
        "Ačiū, kad klausiate! Kaip dirbtinis intelektas, aš neturiu dienos pojūčio, bet visada esu pasiruošęs padėti jums!",
        "Doesn't use RAG because it's casual conversation"
    ),
    (
        "kiek dabar valandų?",
        "Atsiprašau, bet negaliu pateikti tikslaus laiko. Aš neturiu prieigos prie realaus laiko informacijos.",
        "Doesn't use RAG because it's about current time"
    ),
    (
        "ar tu žmogus?",
        "Ne, aš esu dirbtinio intelekto asistentas, sukurtas padėti jums su įvairiais klausimais.",
        "Doesn't use RAG because it's about assistant's identity"
    ),
    (
        "kas yra sostinė?",
        "Lietuvos sostinė yra Vilnius. Tai didžiausias Lietuvos miestas ir šalies administracinis centras.",
        "Doesn't use RAG because it's general knowledge question"
    )
]

# Mixed conversation test cases (combining RAG and non-RAG questions)
MIXED_CONVERSATION_TEST_CASES = [
    (
        [
            ("koks dabar oras?", False, "General conversation about weather"),
            ("ar galiu gauti pola kortele?", True, "Switches to RAG for POLA card info"),
            ("ačiū už informaciją!", False, "Back to general conversation")
        ],
        "Tests conversation flow switching between RAG and non-RAG responses"
    ),
    (
        [
            ("kaip gauti pola kortele?", True, "Starts with RAG question"),
            ("ar ji tikrai nemokama?", True, "Follows up with related RAG question"),
            ("puiku, ačiū!", False, "Ends with general response")
        ],
        "Tests maintaining context in POLA card conversation"
    ),
    (
        [
            ("kaip gauti pola kortele?", True, "Starts with RAG question"),
            ("testi", True, "Follows up with related RAG question"),
            ("puiku, ačiū!", False, "Ends with general response")
        ],
        "Tests maintaining context in POLA card conversation"
    )
]


@pytest.fixture
def base_state() -> AICompanionState:
    return {
        "messages": [],
        "metadata": {"session_id": "test_session"},
        "memory": {},
        "workflow": None,
        "current_activity": None
    }

@pytest.fixture
def mock_chat_model():
    with patch("ai_companion.graph.utils.helpers.get_chat_model") as mock:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = {
            "text": "Aš esu dirbtinio intelekto asistentas, pasiruošęs padėti!",
            "type": "assistant"
        }
        mock.return_value = mock_chain
        yield mock

@pytest.fixture
def mock_rag_chain():
    with patch("ai_companion.graph.utils.chains.get_rag_chain") as mock:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = {
            "text": "POLA kortelė suteikia nuolaidas įvairiose parduotuvėse. Ją galite gauti nemokamai užsiregistravę internetu arba artimiausiame POLA skyriuje.",
            "type": "assistant"
        }
        mock.return_value = mock_chain
        yield mock

class TestGraphNodes:
    @pytest.mark.asyncio
    async def test_router_node(self, base_state, mock_chat_model):
        """Test router node correctly determines workflow"""
        base_state["messages"] = [
            {"role": "user", "content": "Tell me a story"}
        ]
        result = await router_node(base_state)
        assert "workflow" in result
        assert result["workflow"] == "conversation_node"

    @pytest.mark.asyncio
    async def test_rag_node_pola_card(self, base_state, mock_rag_chain):
        """Test RAG node handles POLA card questions correctly"""
        base_state["messages"] = [
            {"role": "user", "content": "kaip gauti pola kortele?"}
        ]
        result = await rag_node(base_state, {})
        assert "rag_response" in result
        assert result["rag_response"]["has_relevant_info"] is True
        assert "response" in result["rag_response"]

    @pytest.mark.asyncio
    async def test_rag_node_weather(self, base_state, mock_rag_chain):
        """Test RAG node handles questions without context gracefully"""
        base_state["messages"] = [
            {"role": "user", "content": "koks dabar oras?"}
        ]
        result = await rag_node(base_state, {})
        assert "rag_response" in result
        assert result["rag_response"]["has_relevant_info"] is False

    @pytest.mark.asyncio
    async def test_rag_node_pola_discounts(self, base_state, mock_rag_chain):
        """Test RAG node handles POLA discount questions"""
        base_state["messages"] = [
            {"role": "user", "content": "kokias nuolaidas suteikia pola kortele?"}
        ]
        result = await rag_node(base_state, {})
        assert "rag_response" in result
        assert result["rag_response"]["has_relevant_info"] is True
        assert "response" in result["rag_response"]

    @pytest.mark.parametrize("question,expected_answer,explanation", RAG_TEST_CASES)
    @pytest.mark.asyncio
    async def test_rag_questions(self, base_state, mock_rag_chain, question, expected_answer, explanation):
        """Test various RAG questions about POLA card"""
        base_state["messages"] = [
            {"role": "user", "content": question}
        ]
        result = await rag_node(base_state, {})
        assert result["rag_response"]["has_relevant_info"] is True
        assert "response" in result["rag_response"]
        
        # Log the interaction
        qa_logger.log_interaction(
            question=question,
            answer=result["rag_response"]["response"],
            is_rag=True,
            metadata={
                "explanation": explanation,
                "expected_answer": expected_answer
            }
        )
        
        # Log for clarity
        print(f"\nTesting RAG question: {question}")
        print(f"Explanation: {explanation}")

    @pytest.mark.parametrize("question,expected_answer,explanation", NON_RAG_TEST_CASES)
    @pytest.mark.asyncio
    async def test_non_rag_questions(self, base_state, mock_rag_chain, question, expected_answer, explanation):
        """Test various non-RAG general questions"""
        base_state["messages"] = [
            {"role": "user", "content": question}
        ]
        result = await rag_node(base_state, {})
        assert result["rag_response"]["has_relevant_info"] is False
        
        # Log the interaction
        qa_logger.log_interaction(
            question=question,
            answer=result["rag_response"]["response"],
            is_rag=False,
            metadata={
                "explanation": explanation,
                "expected_answer": expected_answer
            }
        )
        
        # Log for clarity
        print(f"\nTesting non-RAG question: {question}")
        print(f"Explanation: {explanation}")

class TestGraphFlow:
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, base_state, mock_rag_chain, mock_chat_model):
        """Test a complete conversation flow through the graph"""
        workflow = create_workflow_graph()
        base_state["messages"] = [
            {"role": "user", "content": "kaip gauti pola kortele?"}
        ]
        config = {}
        result = await workflow.ainvoke(base_state, config)
        assert "messages" in result
        assert len(result["messages"]) > len(base_state["messages"])

    @pytest.mark.parametrize("input_message,expected_workflow", [
        ("kaip gauti pola kortele?", "conversation_node"),
        ("koks dabar oras?", "conversation_node"),
        ("kokias nuolaidas suteikia pola kortele?", "conversation_node")
    ])
    @pytest.mark.asyncio
    async def test_workflow_selection(self, base_state, input_message, expected_workflow, mock_chat_model):
        """Test correct workflow selection for different inputs"""
        base_state["messages"] = [
            {"role": "user", "content": input_message}
        ]
        result = await router_node(base_state)
        assert result["workflow"] == expected_workflow

class TestConversationFlow:
    @pytest.mark.parametrize("conversation,explanation", MIXED_CONVERSATION_TEST_CASES)
    @pytest.mark.asyncio
    async def test_mixed_conversation(self, base_state, mock_rag_chain, mock_chat_model, conversation, explanation):
        """Test mixed conversations with both RAG and non-RAG questions"""
        workflow = create_workflow_graph()
        
        # Prepare conversation log
        conversation_messages = []
        
        # Process each message in the conversation
        current_state = base_state
        for message, should_use_rag, msg_explanation in conversation:
            current_state["messages"].append({"role": "user", "content": message})
            result = await workflow.ainvoke(current_state, {})
            
            # Verify RAG usage
            rag_response = result.get("rag_response", {})
            assert rag_response.get("has_relevant_info", False) == should_use_rag
            
            # Log individual interaction
            qa_logger.log_interaction(
                question=message,
                answer=rag_response.get("response", "No direct response"),
                is_rag=should_use_rag,
                metadata={
                    "explanation": msg_explanation,
                    "conversation_context": explanation
                }
            )
            
            # Add to conversation log
            conversation_messages.append({
                "role": "user",
                "content": message,
                "used_rag": should_use_rag,
                "explanation": msg_explanation
            })
            
            # Handle assistant messages
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                # Handle both dict and AIMessage objects
                message_content = (
                    last_message.content if hasattr(last_message, 'content')
                    else last_message.get("content", "No response")
                )
                conversation_messages.append({
                    "role": "assistant",
                    "content": message_content,
                    "used_rag": should_use_rag
                })
            
            # Update state for next message
            current_state = result
            
            # Log for clarity
            print(f"\nMessage: {message}")
            print(f"Should use RAG: {should_use_rag}")
            print(f"Explanation: {msg_explanation}")
        
        # Log complete conversation
        qa_logger.log_conversation(
            messages=conversation_messages,
            metadata={"test_case": explanation}
        )

    @pytest.mark.asyncio
    async def test_conversation_context_maintenance(self, base_state, mock_rag_chain, mock_chat_model):
        """Test that conversation context is maintained properly"""
        workflow = create_workflow_graph()
        
        # Start with a POLA card question
        base_state["messages"] = [
            {"role": "user", "content": "kaip gauti pola kortele?"}
        ]
        
        # Process first message
        result1 = await workflow.ainvoke(base_state, {})
        assert "messages" in result1
        
        # Add follow-up question
        result1["messages"].append(
            {"role": "user", "content": "ar reikia už ją mokėti?"}
        )
        
        # Process follow-up
        result2 = await workflow.ainvoke(result1, {})
        
        # Verify context maintenance
        assert any("pola" in str(msg).lower() for msg in result2["messages"])
        assert any("mokėti" in str(msg).lower() for msg in result2["messages"])

class TestStateManagement:
    def test_state_transitions(self, base_state):
        """Test state transitions through different nodes"""
        initial_state = base_state.copy()
        initial_state["memory"] = {"test": "data"}
        state_after_memory = memory_injection_node(initial_state)
        assert "memory_context" in state_after_memory

    @pytest.mark.asyncio
    async def test_state_persistence(self, base_state, mock_rag_chain, mock_chat_model):
        """Test state persistence across node transitions"""
        workflow = create_workflow_graph()
        base_state["messages"] = [
            {"role": "user", "content": "kaip gauti pola kortele?"},
            {"role": "assistant", "content": "Let me tell you about POLA card"}
        ]
        result1 = await workflow.ainvoke(base_state, {})
        result1["messages"].append(
            {"role": "user", "content": "kokias nuolaidas suteikia?"}
        )
        result2 = await workflow.ainvoke(result1, {})
        assert any("pola" in str(msg).lower() for msg in result2["messages"])

def test_graph_creation():
    """Test graph creation and structure"""
    workflow = create_workflow_graph()
    assert workflow is not None
    assert hasattr(workflow, "ainvoke")

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files after tests"""
    yield
    # Get statistics before cleanup
    stats = qa_logger.get_qa_statistics()
    print("\nTest Run Statistics:")
    print(f"Total Interactions: {stats['total_interactions']}")
    print(f"RAG Interactions: {stats['rag_interactions']}")
    print(f"Non-RAG Interactions: {stats['non_rag_interactions']}")
    print(f"RAG Usage Percentage: {stats['rag_percentage']:.2f}%")
    print(f"Unique Questions: {stats['unique_questions']}")
    
    # Optionally clean up logs (comment out if you want to keep them)
    # for file in Path("tests/logs/qa_logs").glob("*"):
    #     file.unlink() 