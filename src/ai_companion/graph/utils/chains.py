from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Dict, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from ai_companion.core.prompts import CHARACTER_CARD_PROMPT, ROUTER_PROMPT
from ai_companion.graph.utils.helpers import AsteriskRemovalParser, get_chat_model


class RouterResponse(BaseModel):
    response_type: str = Field(
        description="The response type to give to the user. It must be one of: 'conversation', 'image', 'audio', or 'rag'"
    )


def get_rag_chain():
    """Get the RAG chain for knowledge retrieval and response generation."""
    from ai_companion.modules.rag.core.rag_chain import get_rag_chain as get_lithuanian_rag_chain
    
    # Return the LithuanianRAGChain instance instead of creating a new LLMChain
    return get_lithuanian_rag_chain()
    
    # The code below is commented out as we're now using the proper RAG chain
    # Original implementation:
    # template = """You are Evelina, a knowledgeable AI assistant. Use the provided context to answer questions accurately.
    # Always base your responses on the retrieved information from the knowledge base.
    # 
    # Context: {context}
    # Question: {question}
    # 
    # Instructions:
    # 1. Base your response ONLY on the provided context
    # 2. If the context doesn't contain relevant information, acknowledge that and suggest seeking more information
    # 3. Maintain a friendly and helpful tone while staying factual
    # 4. Respond in Lithuanian language
    # 5. Never make up information - only use what's in the context
    # 
    # Response:"""
    #
    # prompt = PromptTemplate(
    #     template=template,
    #     input_variables=["context", "question"]
    # )
    #
    # return LLMChain(
    #     llm=get_chat_model(),
    #     prompt=prompt,
    #     verbose=True
    # )


def get_router_chain() -> LLMChain:
    """Get the router chain for determining the conversation workflow."""
    template = """Analyze the following conversation and determine the appropriate workflow.
    
    Conversation:
    {messages}
    
    Available workflows:
    - conversation: For general conversation and knowledge-based responses
    - image: For image generation requests
    - audio: For text-to-speech conversion
    
    Return ONLY the workflow name without any explanation.
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["messages"]
    )
    
    return LLMChain(
        llm=get_chat_model(),
        prompt=prompt,
        verbose=True
    )


def get_character_response_chain(summary: str = ""):
    model = get_chat_model()
    system_message = CHARACTER_CARD_PROMPT

    if summary:
        system_message += (
            f"\n\nSummary of conversation earlier between Evelina and the user: {summary}"
        )

    # Add RAG handling instructions
    system_message += """
    
    IMPORTANT: All responses must be based on retrieved knowledge
    1. Only provide information that is supported by the RAG context
    2. If information is not available in the context, acknowledge that
    3. Never make up or assume information
    4. Keep responses factual and grounded in the available knowledge
    5. Maintain personality while staying true to the retrieved information
    
    FORMATTING INSTRUCTIONS:
    - When using information directly retrieved from documents, start those sentences with [RAG]
    - When generating your own explanations or transitional text, start those sentences with [AI]
    - Every sentence or paragraph in your response must start with either [RAG] or [AI]
    - Preserve any [RAG] or [AI] tags that already exist in the context
    - The final line of your response MUST end with either [RAG] or [AI] based on the type of information in that line
    
    Current Activity Context: {current_activity}
    Memory Context: {memory_context}

    Remember to:
    1. Only use information from the RAG system or conversation history
    2. Be transparent about knowledge limitations
    3. Suggest seeking more information when needed
    4. Always use the [RAG] prefix for retrieved information and [AI] for your own content
    5. Ensure your response ends with either [RAG] or [AI]
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ]
    )

    chain = prompt | model

    return chain
