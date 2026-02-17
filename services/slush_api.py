"""
Slush API integration for fetching real business data
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SlushAPIError(Exception):
    """Custom exception for Slush API errors"""
    pass

class SlushAPI:
    def __init__(self):
        self.base_url = os.getenv("SLUSH_SNAPSHOT_BASE_URL")
        self.token = os.getenv("SLUSH_SNAPSHOT_TOKEN")
        
        if not self.base_url or not self.token:
            raise SlushAPIError("SLUSH_SNAPSHOT_BASE_URL and SLUSH_SNAPSHOT_TOKEN must be set")
        
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        
    async def fetch_snapshot_data(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Fetch business snapshot data from Slush API
        
        Args:
            days_back: Number of days of data to fetch
            
        Returns:
            Dictionary containing business metrics and data
        """
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                logger.info(f"Fetching Slush data from {start_date.date()} to {end_date.date()}")
                
                # Make API request to snapshot endpoint
                response = await client.get(
                    f"{self.base_url}/internal/insights/snapshot",
                    headers={
                        "X-Internal-Agent-Token": self.token,
                        "Content-Type": "application/json"
                    },
                    params={
                        "range": "last_7_days"
                    }
                )
                
                if response.status_code == 401:
                    raise SlushAPIError("Invalid Slush API token")
                elif response.status_code == 404:
                    raise SlushAPIError("Slush snapshot endpoint not found")
                elif response.status_code != 200:
                    raise SlushAPIError(f"Slush API error: {response.status_code} - {response.text}")
                
                data = response.json()
                logger.info(f"Successfully fetched Slush data: {len(str(data))} characters")
                
                return data
                
        except httpx.TimeoutException:
            raise SlushAPIError("Timeout connecting to Slush API")
        except httpx.RequestError as e:
            raise SlushAPIError(f"Network error connecting to Slush API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Slush data: {str(e)}")
            raise SlushAPIError("Unexpected error occurred while fetching Slush data")

    def format_data_for_memo(self, raw_data: Dict[str, Any]) -> str:
        """
        Format raw Slush API data into a readable format for Claude
        
        Args:
            raw_data: Raw data from Slush API
            
        Returns:
            Formatted string for inclusion in memo generation
        """
        
        try:
            formatted = []
            formatted.append("=== SLUSH BUSINESS DATA ===")
            formatted.append(f"Data fetched: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            formatted.append("")
            
            # Extract key metrics if available
            if "metrics" in raw_data:
                metrics = raw_data["metrics"]
                formatted.append("## Key Metrics")
                
                for key, value in metrics.items():
                    if isinstance(value, dict):
                        formatted.append(f"### {key.title()}")
                        for subkey, subvalue in value.items():
                            formatted.append(f"- {subkey}: {subvalue}")
                    else:
                        formatted.append(f"- {key}: {value}")
                
                formatted.append("")
            
            # Extract funnel data if available
            if "funnel" in raw_data:
                funnel = raw_data["funnel"]
                formatted.append("## Funnel Performance")
                
                for stage, data in funnel.items():
                    formatted.append(f"### {stage.title()}")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            formatted.append(f"- {key}: {value}")
                    else:
                        formatted.append(f"- Count: {data}")
                
                formatted.append("")
            
            # Include any other top-level data
            for key, value in raw_data.items():
                if key not in ["metrics", "funnel"]:
                    formatted.append(f"## {key.title()}")
                    if isinstance(value, (dict, list)):
                        formatted.append(f"{str(value)[:500]}{'...' if len(str(value)) > 500 else ''}")
                    else:
                        formatted.append(str(value))
                    formatted.append("")
            
            return "\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Error formatting Slush data: {str(e)}")
            return f"=== SLUSH DATA ===\n{str(raw_data)[:1000]}{'...' if len(str(raw_data)) > 1000 else ''}"

async def fetch_slush_data_for_memo(days_back: int = 7) -> str:
    """
    Convenience function to fetch and format Slush data for memo generation
    
    Args:
        days_back: Number of days of data to fetch
        
    Returns:
        Formatted data string ready for Claude analysis
    """
    
    try:
        slush = SlushAPI()
        raw_data = await slush.fetch_snapshot_data(days_back)
        formatted_data = slush.format_data_for_memo(raw_data)
        return formatted_data
        
    except SlushAPIError as e:
        logger.warning(f"Failed to fetch Slush data: {str(e)}")
        return f"=== SLUSH DATA UNAVAILABLE ===\nError: {str(e)}\nMemo will be generated without real business data."