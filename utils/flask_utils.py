from flask import session
from typing import Dict, Any
import uuid

# In-memory storage for user sessions (in production, consider using Redis or database)
user_data: Dict[str, Dict[str, Any]] = {}
user_ai_status: Dict[str, Dict[str, Any]] = {}

def get_user_id() -> str:
    """
    Get or create a unique user ID for the session
    
    Returns:
        str: Unique user identifier stored in the session
    """
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def get_user_result(user_id: str) -> Dict[str, Any]:
    """
    Get user-specific result data, creating default structure if it doesn't exist
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        Dict containing user's benchmark results and analysis data
    """
    if user_id not in user_data:
        user_data[user_id] = {
            "Func1Times": [], 
            "Func2Times": [], 
            "Func1Score": 0, 
            "Func2Score": 0
        }
    return user_data[user_id]

def get_user_ai_status(user_id: str) -> Dict[str, Any]:
    """
    Get user-specific AI feedback status, creating default structure if it doesn't exist
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        Dict containing AI feedback generation status and progress
    """
    if user_id not in user_ai_status:
        user_ai_status[user_id] = {
            "status": "pending", 
            "progress": 0
        }
    return user_ai_status[user_id]

def reset_user_ai_status(user_id: str) -> None:
    """
    Reset AI feedback status for a user
    
    Args:
        user_id: Unique identifier for the user
    """
    ai_status = get_user_ai_status(user_id)
    ai_status.clear()
    ai_status.update({"status": "pending", "progress": 0})

def cleanup_old_sessions(max_sessions: int = 100, cleanup_count: int = 50) -> None:
    """
    Clean up old user data to prevent memory leaks
    
    Args:
        max_sessions: Maximum number of sessions before cleanup triggers
        cleanup_count: Number of oldest sessions to remove during cleanup
    """
    if len(user_data) > max_sessions:
        # Remove oldest sessions (simple FIFO approach)
        old_keys = list(user_data.keys())[:cleanup_count]
        for key in old_keys:
            user_data.pop(key, None)
            user_ai_status.pop(key, None)
        print(f"Cleaned up {len(old_keys)} old sessions")

def get_session_stats() -> Dict[str, int]:
    """
    Get statistics about current sessions
    
    Returns:
        Dict containing session count and memory usage info
    """
    return {
        "active_sessions": len(user_data),
        "ai_status_sessions": len(user_ai_status),
        "total_results": sum(1 for data in user_data.values() if data.get("Func1Times"))
    }

def clear_user_data(user_id: str) -> bool:
    """
    Clear all data for a specific user
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        bool: True if data was found and cleared, False otherwise
    """
    cleared = False
    if user_id in user_data:
        del user_data[user_id]
        cleared = True
    if user_id in user_ai_status:
        del user_ai_status[user_id]
        cleared = True
    return cleared

def user_has_complete_data(user_id: str) -> bool:
    """
    Check if user has all required data for displaying results
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        bool: True if all required data is present
    """
    result = get_user_result(user_id)
    required_keys = [
        "Func1Times", "Func2Times", "Func1Score", "Func2Score", 
        "AI_Feedback1", "AI_Feedback2", "Comparative_Feedback", 
        "Program1Code", "Program2Code"
    ]
    
    return all(result.get(key) is not None for key in required_keys)

def initialize_ai_feedback_placeholders(user_id: str) -> None:
    """
    Initialize AI feedback placeholders for a user
    
    Args:
        user_id: Unique identifier for the user
    """
    result = get_user_result(user_id)
    result.update({
        "AI_Feedback1": "Analyzing function performance...",
        "AI_Feedback2": "Analyzing function performance...",
        "Comparative_Feedback": "Generating comparative analysis..."
    })

def update_user_benchmark_results(user_id: str, benchmark_result: Dict[str, Any], 
                                 program1_code: str, program2_code: str) -> None:
    """
    Update user's benchmark results with new data
    
    Args:
        user_id: Unique identifier for the user
        benchmark_result: Results from the benchmark function
        program1_code: Source code of the first function
        program2_code: Source code of the second function
    """
    result = get_user_result(user_id)
    
    # Update with benchmark results
    result.update(benchmark_result)
    
    # Store original code for display
    result["Program1Code"] = program1_code
    result["Program2Code"] = program2_code
    
    # Initialize AI feedback placeholders
    initialize_ai_feedback_placeholders(user_id)
    
    # Reset AI feedback status
    reset_user_ai_status(user_id)