"""RAG monitoring and metrics tracking module."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from langchain.schema import Document
import asyncio

logger = logging.getLogger(__name__)

class RAGMonitor:
    """Monitor RAG system performance and errors."""
    
    def __init__(self):
        """Initialize monitor with default metrics."""
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'verified_responses': 0,
            'insufficient_info': 0,
            'validation_failures': 0,
            'error_types': {
                'insufficient_info': 0,
                'query_processing': 0,
                'retrieval': 0,
                'response_generation': 0,
                'system': 0
            },
            'performance': {
                'avg_query_time': 0.0,
                'avg_retrieval_time': 0.0,
                'avg_response_time': 0.0
            },
            'hourly_stats': {},
            'daily_stats': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # Set up metrics file path
        metrics_dir = os.environ.get('METRICS_DIR', 'metrics')
        os.makedirs(metrics_dir, exist_ok=True)
        self.metrics_file = os.path.join(metrics_dir, 'rag_metrics.json')
        self.logger = logger
        
        # Load existing metrics if available
        self._load_metrics()
        
        # Start periodic save task
        self._start_periodic_save()
        
    async def log_error(
        self,
        error_type: str,
        query: str,
        error_details: str
    ) -> None:
        """Log error information."""
        try:
            # Update error counts
            if error_type in self.metrics['error_types']:
                self.metrics['error_types'][error_type] += 1
            else:
                self.metrics['error_types']['system'] += 1
            
            # Update general metrics
            self.metrics['failed_queries'] += 1
            self.metrics['total_queries'] += 1
            
            # Update specific error types
            if error_type == 'insufficient_info':
                self.metrics['insufficient_info'] += 1
            elif error_type == 'validation_failure':
                self.metrics['validation_failures'] += 1
                
            # Update timestamp
            self.metrics['last_updated'] = datetime.now().isoformat()
            
            # Update daily and hourly stats
            self._update_time_stats(success=False)
            
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
            
    async def log_success(
        self,
        question: str,
        num_docs: int,
        response_metadata: Dict[str, Any]
    ) -> None:
        """Log successful query information."""
        try:
            # Extract and update performance metrics
            query_time = response_metadata.get('query_time', 0.0)
            retrieval_time = response_metadata.get('retrieval_time', 0.0)
            response_time = response_metadata.get('response_time', 0.0)
            generation_time = response_metadata.get('generation_time', 0.0)
            
            # Extract search source information
            source_distribution = response_metadata.get('source_distribution', {})
            vector_count = source_distribution.get('vector_count', 0)
            keyword_count = source_distribution.get('keyword_count', 0)
            
            # Update search source metrics
            if 'search_sources' not in self.metrics:
                self.metrics['search_sources'] = {
                    'vector_only': 0,
                    'keyword_only': 0,
                    'hybrid': 0,
                    'total_vector_docs': 0,
                    'total_keyword_docs': 0
                }
            
            # Update search source counts
            if vector_count > 0 and keyword_count > 0:
                self.metrics['search_sources']['hybrid'] += 1
            elif vector_count > 0:
                self.metrics['search_sources']['vector_only'] += 1
            elif keyword_count > 0:
                self.metrics['search_sources']['keyword_only'] += 1
            
            # Update total document counts
            self.metrics['search_sources']['total_vector_docs'] += vector_count
            self.metrics['search_sources']['total_keyword_docs'] += keyword_count
            
            # Update performance metrics with exponential moving average
            current_values = self.metrics['performance']
            
            # Update with 10% weight for new values (exponential moving average)
            self.metrics['performance'] = {
                'avg_query_time': current_values['avg_query_time'] * 0.9 + query_time * 0.1,
                'avg_retrieval_time': current_values['avg_retrieval_time'] * 0.9 + retrieval_time * 0.1,
                'avg_response_time': current_values['avg_response_time'] * 0.9 + response_time * 0.1,
                'avg_generation_time': current_values.get('avg_generation_time', 0) * 0.9 + generation_time * 0.1,
                'avg_total_time': current_values.get('avg_total_time', 0) * 0.9 + (query_time + retrieval_time + response_time) * 0.1
            }
            
            # Update general metrics
            self.metrics['successful_queries'] += 1
            self.metrics['total_queries'] += 1
            
            # Update average document count
            if 'avg_document_count' not in self.metrics:
                self.metrics['avg_document_count'] = num_docs
            else:
                self.metrics['avg_document_count'] = (
                    self.metrics['avg_document_count'] * 0.9 + num_docs * 0.1
                )
            
            # Update verified responses if applicable
            if response_metadata.get('verified', False):
                self.metrics['verified_responses'] += 1
            
            # Update timestamp
            self.metrics['last_updated'] = datetime.now().isoformat()
            
            # Update daily and hourly stats
            self._update_time_stats(success=True)
            
        except Exception as e:
            logger.error(f"Error logging success: {str(e)}", exc_info=True)
            
    def _update_time_stats(self, success: bool = True) -> None:
        """Update time-based statistics."""
        try:
            now = datetime.now()
            
            # Update hourly stats
            hourly_key = now.strftime("%Y-%m-%d-%H")
            if hourly_key not in self.metrics['hourly_stats']:
                self.metrics['hourly_stats'][hourly_key] = {
                    'queries': 0,
                    'successful': 0,
                    'failed': 0
                }
            
            self.metrics['hourly_stats'][hourly_key]['queries'] += 1
            if success:
                self.metrics['hourly_stats'][hourly_key]['successful'] += 1
            else:
                self.metrics['hourly_stats'][hourly_key]['failed'] += 1
                
            # Update daily stats
            daily_key = now.strftime("%Y-%m-%d")
            if daily_key not in self.metrics['daily_stats']:
                self.metrics['daily_stats'][daily_key] = {
                    'queries': 0,
                    'successful': 0,
                    'failed': 0
                }
            
            self.metrics['daily_stats'][daily_key]['queries'] += 1
            if success:
                self.metrics['daily_stats'][daily_key]['successful'] += 1
            else:
                self.metrics['daily_stats'][daily_key]['failed'] += 1
                
        except Exception as e:
            logger.error(f"Error updating time stats: {str(e)}")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics to initial values"""
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'verified_responses': 0,
            'insufficient_info': 0,
            'validation_failures': 0,
            'error_types': {
                'insufficient_info': 0,
                'query_processing': 0,
                'retrieval': 0,
                'response_generation': 0,
                'system': 0
            },
            'performance': {
                'avg_query_time': 0.0,
                'avg_retrieval_time': 0.0,
                'avg_response_time': 0.0
            },
            'hourly_stats': {},
            'daily_stats': {},
            'last_updated': datetime.now().isoformat()
        }
        self._save_metrics()
    
    def _save_metrics(self) -> None:
        """Save metrics to file if specified"""
        if hasattr(self, 'metrics_file') and self.metrics_file:
            try:
                with open(self.metrics_file, 'w') as f:
                    json.dump(self.metrics, f, indent=2)
                logger.debug("Metrics saved successfully")
            except Exception as e:
                self.logger.error(f"Failed to save metrics: {str(e)}")
    
    def _start_periodic_save(self) -> None:
        """Start a background task to periodically save metrics."""
        try:
            # Create a background task that runs every 5 minutes
            async def periodic_save():
                while True:
                    await asyncio.sleep(300)  # 5 minutes
                    self._save_metrics()
                    self._cleanup_old_stats()
            
            # Schedule the task to run in the background
            loop = asyncio.get_event_loop()
            loop.create_task(periodic_save())
            logger.info("Periodic metrics save scheduled")
        except Exception as e:
            logger.error(f"Failed to start periodic save: {str(e)}")
    
    async def log_query(self, query: str, response: str = None, success: bool = True, question: str = None, retry_count: int = 0, retrieval_params: Dict[str, Any] = None, response_metadata: Dict[str, Any] = None) -> None:
        """Log query and response details
        
        Args:
            query: The query string
            response: The response string
            success: Whether the query was successful
            question: Alternative to query parameter (for backward compatibility)
            retry_count: Number of retries for this query
            retrieval_params: Parameters used for retrieval
            response_metadata: Metadata about the response
        """
        # For backward compatibility
        query_text = question if question is not None else query
        status = "SUCCESS" if success else "FAILURE"
        
        self.logger.info(f"Query [{status}] (Retry: {retry_count}): {query_text}")
        
        if response:
            self.logger.debug(f"Response: {response}")
            
        if retrieval_params:
            self.logger.debug(f"Retrieval params: {retrieval_params}")
            
        if response_metadata:
            self.logger.debug(f"Response metadata: {response_metadata}")
    
    def _load_metrics(self) -> None:
        """Load metrics from file if it exists."""
        try:
            if hasattr(self, 'metrics_file') and self.metrics_file and os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    loaded_metrics = json.load(f)
                    # Update metrics while preserving structure
                    for key, value in loaded_metrics.items():
                        if key in self.metrics:
                            self.metrics[key] = value
                logger.info("Metrics loaded from file")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def _cleanup_old_stats(self) -> None:
        """Remove stats older than 30 days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Clean hourly stats
            if 'hourly_stats' in self.metrics:
                self.metrics["hourly_stats"] = {
                    k: v for k, v in self.metrics["hourly_stats"].items()
                    if datetime.strptime(k, "%Y-%m-%d-%H") > cutoff_date
                }
            
            # Clean daily stats
            if 'daily_stats' in self.metrics:
                self.metrics["daily_stats"] = {
                    k: v for k, v in self.metrics["daily_stats"].items()
                    if datetime.strptime(k, "%Y-%m-%d") > cutoff_date
                }
            
            logger.debug("Old stats cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up old stats: {e}")
    
    def get_performance_report(self) -> Dict:
        """Generate a performance report."""
        try:
            total_queries = self.metrics.get("total_queries", 0)
            if total_queries == 0:
                return {"status": "No queries recorded"}
            
            # Safely get values with defaults
            verified_responses = self.metrics.get("verified_responses", 0)
            insufficient_info = self.metrics.get("insufficient_info", 0)
            validation_failures = self.metrics.get("validation_failures", 0)
            daily_stats = self.metrics.get("daily_stats", {})
            
            # Calculate success rate
            success_rate = self.metrics.get("successful_queries", 0) / total_queries if total_queries > 0 else 0
            
            # Calculate average response times
            avg_response_time = self.metrics.get("performance", {}).get("avg_response_time", 0)
            
            return {
                "accuracy": {
                    "success_rate": success_rate,
                    "verification_rate": verified_responses / total_queries if total_queries > 0 else 0,
                    "insufficient_info_rate": insufficient_info / total_queries if total_queries > 0 else 0,
                    "failure_rate": validation_failures / total_queries if total_queries > 0 else 0
                },
                "performance": {
                    "avg_response_time": avg_response_time,
                    "avg_query_time": self.metrics.get("performance", {}).get("avg_query_time", 0),
                    "avg_retrieval_time": self.metrics.get("performance", {}).get("avg_retrieval_time", 0)
                },
                "volume": {
                    "total_queries": total_queries,
                    "daily_average": sum(
                        day.get("queries", 0) for day in daily_stats.values()
                    ) / len(daily_stats) if daily_stats else 0
                },
                "errors": {
                    "top_types": dict(sorted(
                        self.metrics.get("error_types", {}).items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5])
                },
                "last_updated": self.metrics.get("last_updated", datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"status": "Error generating report", "error": str(e)} 