# File: forge_sdk/client.py

from typing import Optional, Dict, Any, List, Union
import requests
import time
import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ReasoningSpeed(str, Enum):
    """Reasoning speed presets"""
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"

class ForgeError(Exception):
    """Base exception for all Forge API errors"""
    pass

class ForgeTimeoutError(ForgeError):
    """Raised when a completion request times out"""
    pass

class ForgeAuthError(ForgeError):
    """Raised when authentication fails"""
    pass

@dataclass
class ForgeResponse:
    """Structured response from Forge API"""
    task_id: str
    status: str
    result: Dict[str, Any]
    completion_time: float
    
    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"
    
    @property
    def failed(self) -> bool:
        return self.status in ["failed", "cancelled"]

class ForgeClient:
    """
    Client for interacting with the Forge API.
    
    Example:
        >>> client = ForgeClient(api_key="your-key-here")
        >>> response = client.complete("Tell me a joke")
        >>> if response.succeeded:
        >>>     print(response.result)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://forge-api.nousresearch.com/v1"
    ):
        """
        Initialize the Forge client.
        
        Args:
            api_key: API key for authentication. If not provided, will look for FORGE_API_KEY env var
            base_url: Base URL for the API. Defaults to production API
        
        Raises:
            ForgeAuthError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("FORGE_API_KEY")
        if not self.api_key:
            raise ForgeAuthError("No API key provided. Set FORGE_API_KEY environment variable or pass key to constructor")
        
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def complete(
        self,
        prompt: str,
        reasoning_speed: Union[ReasoningSpeed, str] = ReasoningSpeed.MEDIUM,
        track: bool = False,
        timeout: int = 300,
        poll_interval: int = 5,
        max_retries: int = 5
    ) -> ForgeResponse:
        """
        Send a completion request and wait for results.
        
        Args:
            prompt: The text prompt to complete
            reasoning_speed: Speed preset (fast/medium/slow)
            track: Whether to return detailed trace information
            timeout: Maximum seconds to wait for completion
            poll_interval: Seconds between polling attempts
            max_retries: Maximum number of failed polling attempts
        
        Returns:
            ForgeResponse containing the completion results
            
        Raises:
            ForgeTimeoutError: If completion takes longer than timeout
            ForgeError: For other API-related errors
        """
        if isinstance(reasoning_speed, str):
            reasoning_speed = ReasoningSpeed(reasoning_speed.lower())
            
        # Start completion request
        completion_url = f"{self.base_url}/asyncplanner/completions"
        payload = {
            "prompt": prompt,
            "reasoning_speed": reasoning_speed.value,
            "track": track
        }
        
        try:
            logger.info(f"Starting completion with prompt: {prompt}")
            response = requests.post(
                completion_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            
        except requests.exceptions.RequestException as e:
            raise ForgeError(f"Failed to start completion: {str(e)}")
            
        # Poll for results
        poll_url = f"{completion_url}/{task_id}"
        start_time = time.time()
        retries = 0
        
        while (time.time() - start_time) < timeout:
            try:
                poll_response = requests.get(
                    poll_url,
                    headers=self.headers,
                    timeout=10
                )
                poll_response.raise_for_status()
                result = poll_response.json()
                
                status = result.get("metadata", {}).get("status", "unknown")
                completion_time = time.time() - start_time
                
                if status in ["succeeded", "failed", "cancelled"]:
                    return ForgeResponse(
                        task_id=task_id,
                        status=status,
                        result=result,
                        completion_time=completion_time
                    )
                    
                logger.info(f"Status: {status}, waited: {completion_time:.1f}s")
                time.sleep(poll_interval)
                retries = 0
                
            except requests.exceptions.RequestException:
                retries += 1
                if retries >= max_retries:
                    raise ForgeError(f"Polling failed after {max_retries} retries")
                time.sleep(1)
                
        raise ForgeTimeoutError(f"Completion timed out after {timeout} seconds")
