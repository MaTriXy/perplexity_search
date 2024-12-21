import os
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch

def run_cli_command(args, env=None):
    """Helper to run the CLI command"""
    cmd = ["poetry", "run", "plexsearch"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result

@pytest.mark.integration
def test_cli_basic_search():
    """Test basic search using CLI"""
    if "PERPLEXITY_API_KEY" not in os.environ:
        pytest.skip("PERPLEXITY_API_KEY environment variable not set")
    
    with patch('plexsearch.core.perform_search') as mock_search:
        mock_search.return_value = "test response"
        result = run_cli_command(["What is Python?"], env=os.environ)
        assert result.returncode == 0
        assert len(result.stdout) > 0

@pytest.mark.integration
def test_cli_with_model():
    """Test CLI search with specific model"""
    if "PERPLEXITY_API_KEY" not in os.environ:
        pytest.skip("PERPLEXITY_API_KEY environment variable not set")
        
    with patch('plexsearch.core.perform_search') as mock_search:
        mock_search.return_value = "test response"
        result = run_cli_command([
            "--model", "llama-3.1-sonar-small-128k-online",
            "What is Python?"
        ], env=os.environ)
        assert result.returncode == 0
        assert len(result.stdout) > 0

@pytest.mark.integration
def test_cli_error_handling():
    """Test CLI error handling with invalid API key"""
    # Temporarily override API key
    env = os.environ.copy()
    env["PERPLEXITY_API_KEY"] = "invalid_key"
    
    cmd = ["poetry", "run", "plexsearch", "test query"]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert result.returncode != 0
