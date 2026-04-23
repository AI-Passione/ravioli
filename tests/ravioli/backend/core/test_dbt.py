from unittest.mock import patch, MagicMock
from ravioli.backend.core.dbt import run_dbt_command

def test_run_dbt_command_success():
    with patch("subprocess.run") as mock_run:
        # Mocking successful run
        mock_result = MagicMock()
        mock_result.stdout = "dbt build successful"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output = run_dbt_command("build")
        
        assert "dbt build successful" in output
        mock_run.assert_called_once()
        # Verify it was called with 'dbt' and the command
        args, kwargs = mock_run.call_args
        assert args[0] == ["dbt", "build"]

def test_run_dbt_command_error():
    with patch("subprocess.run") as mock_run:
        # Mocking run with errors
        mock_result = MagicMock()
        mock_result.stdout = "some output"
        mock_result.stderr = "database connection failed"
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        output = run_dbt_command("build")
        
        assert "some output" in output
        assert "Errors:" in output
        assert "database connection failed" in output

def test_run_dbt_command_exception():
    with patch("subprocess.run", side_effect=Exception("Execution failed")):
        output = run_dbt_command("build")
        assert "Error running dbt: Execution failed" in output
