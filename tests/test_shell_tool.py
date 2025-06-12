import pytest
from pathlib import Path
import shutil # For cleaning up temp directory

# Assuming 'mcp' is the FastMCP instance from shell_server.py
# and shell_tool is a method bound to it.
# Adjust the import path if your project structure or how you access shell_tool is different.
from src.shell_server import mcp, ERROR_INVALID_WORKING_DIR
from mcp.server.fastmcp.exceptions import FastMCPError

# Helper to get the absolute path of the tests directory
TESTS_DIR = Path(__file__).parent.resolve()

@pytest.fixture(scope="function")
def temp_test_dir_fixture():
    """Creates a temporary directory with a test file for CWD tests."""
    temp_dir = TESTS_DIR / "temp_test_dir_for_shell_tool"
    temp_file = temp_dir / "test_file.txt"

    if temp_dir.exists():
        shutil.rmtree(temp_dir) # Clean up if exists from previous failed run
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file.write_text("dummy content")

    yield temp_dir # Provide the path to the test

    # Teardown: remove the temporary directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

# 1. Basic command execution
def test_shell_tool_basic_echo():
    result = mcp.tool_functions["shell_tool"](command="echo 'hello world'")
    assert "hello world" in result["stdout"] # echo might add a newline
    assert result["stderr"] == ""
    assert result["returncode"] == 0

# 2. Command with stderr output
def test_shell_tool_stderr_output():
    result = mcp.tool_functions["shell_tool"](command="sh -c 'echo \"error message\" >&2'")
    assert result["stdout"] == ""
    # Exact stderr can be tricky due to potential newlines, so checking for substring is safer.
    assert "error message" in result["stderr"]
    assert result["returncode"] == 0

# 3. Command with non-zero return code
def test_shell_tool_nonzero_return_code():
    result = mcp.tool_functions["shell_tool"](command="sh -c 'exit 123'")
    assert result["returncode"] == 123

# 4. working_dir functionality
def test_shell_tool_working_dir_ls(temp_test_dir_fixture):
    # temp_test_dir_fixture provides the path to the temp dir
    result = mcp.tool_functions["shell_tool"](command="ls", working_dir=str(temp_test_dir_fixture))
    assert "test_file.txt" in result["stdout"]
    assert result["returncode"] == 0

def test_shell_tool_working_dir_pwd(temp_test_dir_fixture):
    # temp_test_dir_fixture provides the path to the temp dir
    abs_temp_dir_path = str(temp_test_dir_fixture.resolve()) # Get absolute path
    result = mcp.tool_functions["shell_tool"](command="pwd", working_dir=str(temp_test_dir_fixture))
    assert result["stdout"].strip() == abs_temp_dir_path
    assert result["returncode"] == 0

# 5. Error case: Invalid working_dir (non-existent)
def test_shell_tool_invalid_working_dir_non_existent():
    with pytest.raises(FastMCPError) as excinfo:
        mcp.tool_functions["shell_tool"](command="ls", working_dir="non_existent_dir_6789")
    assert excinfo.value.code == ERROR_INVALID_WORKING_DIR
    assert "Working directory not found" in excinfo.value.message

# 5b. Error case: Invalid working_dir (is a file)
# This requires creating a file and trying to use it as a CWD.
# Note: This test might behave differently on minimal Docker images if `touch` isn't available,
# but for a standard Python image, `touch` or similar ways to create a file should work.
def test_shell_tool_invalid_working_dir_is_file(temp_test_dir_fixture):
    file_as_cwd = temp_test_dir_fixture / "i_am_a_file.txt"
    file_as_cwd.write_text("I am a file, not a directory.")

    with pytest.raises(FastMCPError) as excinfo:
        mcp.tool_functions["shell_tool"](command="ls", working_dir=str(file_as_cwd))

    assert excinfo.value.code == ERROR_INVALID_WORKING_DIR
    assert "Specified working_dir is not a directory" in excinfo.value.message

# 6. Input validation for command
def test_shell_tool_invalid_command_type():
    with pytest.raises(FastMCPError) as excinfo:
        mcp.tool_functions["shell_tool"](command=12345) # Pass an integer instead of string
    # Check for the generic invalid params error code or a specific one if defined
    # FastMCP default for type mismatch from signature is -32602
    assert excinfo.value.code == -32602
    assert "Invalid input: command must be a string" in excinfo.value.message

def test_shell_tool_missing_command_argument():
    # This test case assumes that the tool dispatcher or FastMCP itself
    # would catch a missing 'command' argument based on the tool's signature.
    # If shell_tool itself has specific handling for a None command, that would be different.
    # Based on current implementation, FastMCP should raise error if required arg is missing.
    with pytest.raises(TypeError): #TypeError from python if required arg is missing
         mcp.tool_functions["shell_tool"]() # Call without command

# 7. Input validation for working_dir type
def test_shell_tool_invalid_working_dir_type():
    with pytest.raises(FastMCPError) as excinfo:
        mcp.tool_functions["shell_tool"](command="ls", working_dir=123) # Pass an integer
    assert excinfo.value.code == -32602
    assert "Invalid input: working_dir must be a string if provided" in excinfo.value.message

# Test that working_dir=None works as expected (default cwd)
def test_shell_tool_working_dir_none():
    # This essentially re-tests a basic command but explicitly passes working_dir=None
    # to ensure the conditional logic for cwd in shell_tool handles None correctly.
    result = mcp.tool_functions["shell_tool"](command="echo 'hello none cwd'", working_dir=None)
    assert "hello none cwd" in result["stdout"]
    assert result["stderr"] == ""
    assert result["returncode"] == 0

# Test with a command that might be tricky with shell=True if not handled well by subprocess
# (though current implementation is straightforward)
def test_shell_tool_command_with_special_chars():
    # Example: list files in a directory that might have spaces, though /tmp usually doesn't.
    # This is more about ensuring the command string is passed through correctly.
    # A command like "find /tmp -name '*.txt' -print" could also be used.
    result = mcp.tool_functions["shell_tool"](command="ls -d /tmp")
    assert "/tmp" in result["stdout"]
    assert result["returncode"] == 0

# Test for empty command string
def test_shell_tool_empty_command_string():
    # Behavior of an empty command string can be shell-dependent.
    # Often it's a no-op and returns 0, or it might return an error.
    # We'll check what our current setup does.
    # sh -c '' typically exits 0.
    result = mcp.tool_functions["shell_tool"](command="")
    assert result["stdout"] == ""
    # Stderr might vary: some shells print nothing, others a newline or warning.
    # For `sh -c ''`, stderr is usually empty.
    # We'll be flexible or pin down if a specific shell behavior is guaranteed.
    # assert result["stderr"] == ""
    assert result["returncode"] == 0
