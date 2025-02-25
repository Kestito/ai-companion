import pytest
import os
from unittest.mock import patch, MagicMock
import asyncio

from src.ai_companion.modules.rag.core.query_preprocessor import LithuanianQueryPreprocessor

# Mock for LLM responses
class MockLLMResponse:
    def __init__(self, content):
        self.content = content

@pytest.fixture
def preprocessor():
    with patch('langchain_openai.AzureChatOpenAI') as mock_llm:
        preprocessor = LithuanianQueryPreprocessor()
        # Mock the LLM instance
        preprocessor.llm = MagicMock()
        yield preprocessor

@pytest.mark.asyncio
async def test_basic_cleaning(preprocessor):
    """Test that basic query cleaning works correctly."""
    query = "  POLA   kortelė?!  "
    result = preprocessor._clean_query(query)
    assert "POLA kortelė" in result
    assert "?!" not in result

@pytest.mark.asyncio
async def test_correct_misspellings(preprocessor):
    """Test correction of common misspellings."""
    # Test POLA related corrections
    assert "POLA kortelė" in preprocessor._correct_misspellings("pola kortele")
    
    # Test city names
    assert "Vilnius" in preprocessor._correct_misspellings("vilnius")
    assert "Klaipėda" in preprocessor._correct_misspellings("klaipeda")
    
    # Test medical terms
    assert "vėžys" in preprocessor._correct_misspellings("vezys")
    assert "smegenų" in preprocessor._correct_misspellings("smegenu")

@pytest.mark.asyncio
async def test_entity_detection(preprocessor):
    """Test entity detection in queries."""
    # Test POLA detection
    entities = preprocessor._detect_entities("POLA kortelė kaina")
    assert entities["pola_card"] is True
    
    # Test cancer detection
    entities = preprocessor._detect_entities("smegenų vėžys gydymas")
    assert entities["cancer"] is True
    assert entities["brain"] is True
    
    # Test location detection
    entities = preprocessor._detect_entities("savanoriai Klaipėdoje")
    assert entities["location"] is True
    assert entities["volunteer"] is True

@pytest.mark.asyncio
async def test_intent_classification(preprocessor):
    """Test intent classification for different query types."""
    assert await preprocessor._classify_intent("kaip gauti POLA kortelę") == "how_to"
    assert await preprocessor._classify_intent("kur yra POLA biuras") == "location"
    assert await preprocessor._classify_intent("kada galima kreiptis") == "time"
    assert await preprocessor._classify_intent("kiek kainuoja kortelė") == "price"
    assert await preprocessor._classify_intent("smegenų vėžys simptomai") == "medical"

@pytest.mark.asyncio
async def test_query_variation_generation(preprocessor):
    """Test generation of query variations."""
    variations = await preprocessor._generate_variations("kaip gauti POLA kortelę")
    
    # Should include original
    assert "kaip gauti POLA kortelę" in variations
    
    # Should include phrase variations
    assert any("įsigyti" in v for v in variations)
    
    # Should include POLA variations
    assert "POLA kortelė" in variations

@pytest.mark.asyncio
async def test_llm_normalization(preprocessor):
    """Test LLM-based normalization of Lithuanian text."""
    # Mock LLM response
    preprocessor.llm.ainvoke = MagicMock(return_value=MockLLMResponse("ką daryti sergant smegenų vėžiu"))
    
    # Test normalization
    normalized = await preprocessor._normalize_with_llm("ka daryti sergant smegenu veziu")
    assert normalized == "ką daryti sergant smegenų vėžiu"
    
    # Ensure LLM was called with correct prompt
    call_args = preprocessor.llm.ainvoke.call_args[0][0]
    assert "ka daryti sergant smegenu veziu" in call_args

@pytest.mark.asyncio
async def test_full_query_processing(preprocessor):
    """Test full query processing with common misspellings."""
    # Mock LLM responses
    preprocessor.llm.ainvoke = MagicMock(return_value=MockLLMResponse("POLA kortelė kaina"))
    
    # Test with original examples from user
    test_cases = [
        ("Pola kortele", "POLA kortelė"),
        ("kokios ismokos vilnius miegste", "išmokos Vilniaus mieste"),
        ("ka daryti sergant smegenu veziu", "smegenų vėžys"),
        ("smegenu vezys", "smegenų vėžys"),
        ("pola savanoris klaipedoje", "POLA savanoriai Klaipėdoje")
    ]
    
    for query, expected_substring in test_cases:
        result = await preprocessor.process_query(query)
        assert result["success"] is True
        # Either the enhanced query or the LLM-normalized query should contain the expected substring
        assert expected_substring.lower() in result["enhanced_query"].lower() or \
               expected_substring.lower() in result["corrected_query"].lower()
        # Check that variations were generated
        assert len(result["variations"]) > 1 