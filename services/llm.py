"""
LLM service for Agent Ops Backend
Integrates with Anthropic Claude API for research and analysis workflows.
"""

import os
import logging
from typing import Optional
import anthropic
from anthropic import APIError, APIConnectionError, APITimeoutError

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass

def generate(system_prompt: str, user_prompt: str) -> str:
    """
    Generate content using Claude API
    
    Args:
        system_prompt: System instructions for Claude
        user_prompt: User query/request
        
    Returns:
        Generated text response
        
    Raises:
        LLMError: If API call fails or configuration is invalid
    """
    
    # Get configuration from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY environment variable not set")
    
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    max_output_chars = int(os.getenv("LLM_MAX_OUTPUT_CHARS", "9000"))
    
    try:
        # Initialize client (API key not logged)
        client = anthropic.Anthropic(api_key=api_key)
        
        logger.info(f"Making Claude API call with model: {model}")
        
        # Make API call
        response = client.messages.create(
            model=model,
            max_tokens=max_output_chars // 4,  # Rough character to token conversion
            temperature=0.1,  # Low temperature for consistent, factual output
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract text content
        if response.content and len(response.content) > 0:
            generated_text = response.content[0].text
            
            # Enforce character limit
            if len(generated_text) > max_output_chars:
                generated_text = generated_text[:max_output_chars] + "\n\n[Output truncated to character limit]"
            
            logger.info(f"Claude API call successful, generated {len(generated_text)} characters")
            return generated_text
        else:
            raise LLMError("Empty response from Claude API")
            
    except APITimeoutError as e:
        logger.error("Claude API timeout")
        raise LLMError("API request timed out. Please try again.")
    
    except APIConnectionError as e:
        logger.error("Claude API connection error")
        raise LLMError("Failed to connect to Claude API. Please check your internet connection.")
    
    except APIError as e:
        logger.error(f"Claude API error: {str(e)}")
        # Sanitize error message to avoid exposing sensitive info
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise LLMError("API authentication failed. Please check your ANTHROPIC_API_KEY.")
        elif "rate limit" in str(e).lower():
            raise LLMError("API rate limit exceeded. Please try again later.")
        else:
            raise LLMError("Claude API error occurred. Please try again.")
    
    except Exception as e:
        logger.error(f"Unexpected error in LLM generation: {str(e)}")
        raise LLMError("Unexpected error occurred during text generation.")