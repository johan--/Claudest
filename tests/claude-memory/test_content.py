"""Tests for memory_lib.content — message content extraction and tool detection."""

from memory_lib.content import (
    extract_commits,
    extract_files_modified,
    extract_text_content,
    is_tool_result,
)


# --- extract_text_content ---


class TestExtractTextContent:
    def test_plain_string(self):
        text, has_tool, has_think, summary = extract_text_content("Hello world")
        assert text == "Hello world"
        assert has_tool is False
        assert has_think is False
        assert summary is None

    def test_string_with_command_artifacts(self):
        raw = "prefix <command-name>foo</command-name> middle <command-args>bar</command-args> end"
        text, _, _, _ = extract_text_content(raw)
        assert "<command-name>" not in text
        assert "<command-args>" not in text
        assert "prefix" in text
        assert "middle" in text
        assert "end" in text

    def test_string_with_local_command_stdout(self):
        raw = "before <local-command-stdout>some output</local-command-stdout> after"
        text, _, _, _ = extract_text_content(raw)
        assert "<local-command-stdout>" not in text
        assert "before" in text
        assert "after" in text

    def test_string_with_command_message(self):
        raw = "start <command-message>msg content</command-message> finish"
        text, _, _, _ = extract_text_content(raw)
        assert "<command-message>" not in text

    def test_list_with_text_blocks(self):
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        text, has_tool, has_think, summary = extract_text_content(content)
        assert text == "Hello\nWorld"
        assert has_tool is False
        assert has_think is False
        assert summary is None

    def test_list_with_tool_use(self):
        content = [
            {"type": "text", "text": "Let me check."},
            {"type": "tool_use", "name": "Read", "input": {"file": "test.py"}},
            {"type": "tool_use", "name": "Read", "input": {"file": "other.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
        ]
        text, has_tool, has_think, summary = extract_text_content(content)
        assert text == "Let me check."
        assert has_tool is True
        assert summary is not None
        import json
        counts = json.loads(summary)
        assert counts == {"Read": 2, "Bash": 1}

    def test_list_with_thinking(self):
        content = [
            {"type": "thinking", "thinking": "Let me reason..."},
            {"type": "text", "text": "The answer is 42."},
        ]
        text, has_tool, has_think, summary = extract_text_content(content)
        assert text == "The answer is 42."
        assert has_tool is False
        assert has_think is True
        assert summary is None

    def test_list_with_all_types(self):
        content = [
            {"type": "thinking", "thinking": "hmm"},
            {"type": "text", "text": "Here's what I found."},
            {"type": "tool_use", "name": "Grep", "input": {"pattern": "foo"}},
        ]
        text, has_tool, has_think, summary = extract_text_content(content)
        assert text == "Here's what I found."
        assert has_tool is True
        assert has_think is True
        import json
        assert json.loads(summary) == {"Grep": 1}

    def test_list_with_tool_use_no_name(self):
        """tool_use without a name should still flag has_tool_use but not appear in summary."""
        content = [{"type": "tool_use", "input": {}}]
        _, has_tool, _, summary = extract_text_content(content)
        assert has_tool is True
        assert summary is None  # No tool name -> no counts -> None

    def test_empty_string(self):
        text, has_tool, has_think, summary = extract_text_content("")
        assert text == ""
        assert summary is None

    def test_none_input(self):
        text, has_tool, has_think, summary = extract_text_content(None)
        assert text == ""
        assert has_tool is False
        assert has_think is False
        assert summary is None

    def test_unexpected_type(self):
        text, has_tool, has_think, summary = extract_text_content(42)
        assert text == ""
        assert has_tool is False

    def test_empty_list(self):
        text, has_tool, has_think, summary = extract_text_content([])
        assert text == ""
        assert has_tool is False
        assert summary is None


# --- is_tool_result ---


class TestIsToolResult:
    def test_tool_result_content(self):
        content = [{"type": "tool_result", "tool_use_id": "abc", "content": "ok"}]
        assert is_tool_result(content) is True

    def test_normal_text_content(self):
        content = [{"type": "text", "text": "Hello"}]
        assert is_tool_result(content) is False

    def test_string_content(self):
        assert is_tool_result("Hello") is False

    def test_empty_list(self):
        assert is_tool_result([]) is False

    def test_none(self):
        assert is_tool_result(None) is False


# --- extract_files_modified ---


class TestExtractFilesModified:
    def test_edit_and_write(self):
        content = [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b.py"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/c/d.py"}},
        ]
        assert extract_files_modified(content) == ["/a/b.py", "/c/d.py"]

    def test_multi_edit(self):
        content = [
            {"type": "tool_use", "name": "MultiEdit", "input": {"file_path": "/e/f.py"}},
        ]
        assert extract_files_modified(content) == ["/e/f.py"]

    def test_non_file_tools_ignored(self):
        content = [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/x.py"}},
        ]
        assert extract_files_modified(content) == []

    def test_string_content(self):
        assert extract_files_modified("hello") == []

    def test_missing_file_path(self):
        content = [{"type": "tool_use", "name": "Edit", "input": {"old_string": "a"}}]
        assert extract_files_modified(content) == []


# --- extract_commits ---


class TestExtractCommits:
    def test_git_commit_double_quotes(self):
        content = [
            {"type": "tool_use", "name": "Bash", "input": {"command": 'git commit -m "Fix bug in parser"'}},
        ]
        assert extract_commits(content) == ["Fix bug in parser"]

    def test_git_commit_single_quotes(self):
        content = [
            {"type": "tool_use", "name": "Bash", "input": {"command": "git commit -m 'Add new feature'"}},
        ]
        assert extract_commits(content) == ["Add new feature"]

    def test_non_commit_bash(self):
        content = [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls -la"}},
        ]
        assert extract_commits(content) == []

    def test_non_bash_tool(self):
        content = [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/a.py"}},
        ]
        assert extract_commits(content) == []

    def test_long_commit_message_truncated(self):
        long_msg = "x" * 200
        content = [
            {"type": "tool_use", "name": "Bash", "input": {"command": f'git commit -m "{long_msg}"'}},
        ]
        commits = extract_commits(content)
        assert len(commits) == 1
        assert len(commits[0]) == 100

    def test_string_content(self):
        assert extract_commits("hello") == []
