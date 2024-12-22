import pytest
from unittest.mock import patch, mock_open
from get_changes import get_last_release_tag, get_changes_since_last_release, main

from unittest.mock import MagicMock, patch

def test_get_last_release_tag():
    with patch('get_changes.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='v1.2.3\n')
        tag = get_last_release_tag()
        assert tag == 'v1.2.3'
        mock_run.assert_called_with(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        )

def test_get_last_release_tag_error():
    with patch('subprocess.run') as mock_run, \
         patch('logging.error') as mock_log:
        mock_run.side_effect = Exception("Command failed")
        tag = get_last_release_tag()
        assert tag is None
        mock_log.assert_called_once()

def test_get_changes_since_last_release():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'commit1\ncommit2\n'
        mock_run.return_value.check_returncode.return_value = None
        changes = get_changes_since_last_release('v1.2.3')
        assert changes == 'commit1\ncommit2\n'
        mock_run.assert_called_with(
            ["git", "log", "v1.2.3..HEAD", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )

def test_get_changes_since_last_release_error():
    with patch('subprocess.run') as mock_run, \
         patch('logging.error') as mock_log:
        mock_run.side_effect = Exception("Command failed")
        changes = get_changes_since_last_release('v1.2.3')
        assert changes is None
        mock_log.assert_called_once()

def test_main_success(capsys):
    with patch('get_changes.get_last_release_tag') as mock_tag, \
         patch('get_changes.get_changes_since_last_release') as mock_changes:
        mock_tag.return_value = 'v1.2.3'
        mock_changes.return_value = 'commit1\ncommit2\n'
        main()
        captured = capsys.readouterr()
        assert 'Last release tag: v1.2.3' in captured.out
        assert 'commit1\ncommit2\n' in captured.out

def test_main_no_tag(capsys):
    with patch('get_changes.get_last_release_tag') as mock_tag:
        mock_tag.return_value = None
        main()
        captured = capsys.readouterr()
        assert 'Could not determine last release tag.' in captured.out

def test_main_no_changes(capsys):
    with patch('get_changes.get_last_release_tag') as mock_tag, \
         patch('get_changes.get_changes_since_last_release') as mock_changes:
        mock_tag.return_value = 'v1.2.3'
        mock_changes.return_value = None
        main()
        captured = capsys.readouterr()
        assert 'No changes found since last release.' in captured.out
import pytest
from unittest.mock import patch, mock_open
from get_changes import get_last_release_tag, get_changes_since_last_release, main

def test_get_last_release_tag():
    with patch('get_changes.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='v1.2.3\n')
        tag = get_last_release_tag()
        assert tag == 'v1.2.3'

def test_get_changes_since_last_release():
    with patch('get_changes.get_last_release_tag', return_value='v1.2.3'), \
         patch('get_changes.subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'commit1\ncommit2\n'
        mock_run.return_value.check_returncode.return_value = None
        changes = get_changes_since_last_release('v1.2.3')
        assert changes == 'commit1\ncommit2\n'

def test_main(capsys):
    with patch('get_changes.get_changes_since_last_release', return_value='commit1\ncommit2\n'), \
         patch('get_changes.get_last_release_tag', return_value='v1.2.3'), \
         patch('get_changes.print') as mock_print:
        main()
        mock_print.assert_any_call('Last release tag: v1.2.3')
        mock_print.assert_any_call("\nCommit messages since last release:\n")
        mock_print.assert_any_call('commit1\ncommit2\n')
