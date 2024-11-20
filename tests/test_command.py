# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import logging
import os
import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from check_done.command import check_done_command
from check_done.config import resolve_root_repository_path
from tests._common import (
    HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)


@pytest.mark.order(index=1)
def test_can_show_help():
    with pytest.raises(SystemExit) as error_info:
        check_done_command(["--help"])
    assert error_info.value.code == 0


@pytest.mark.order(index=2)
def test_can_show_version():
    with pytest.raises(SystemExit) as error_info:
        check_done_command(["--version"])
    assert error_info.value.code == 0


@pytest.mark.order(index=3)
@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_set_root_dir_argument():
    root_repository_path = str(resolve_root_repository_path())
    exit_code = check_done_command([f"--root-dir={root_repository_path}"])
    assert exit_code == 0


@pytest.mark.order(index=4)
@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_execute_check_done_command_and_get_warnings(caplog):
    exit_code = check_done_command([])
    assert exit_code == 0
    check_done_warning_messages = len(caplog.messages)
    assert check_done_warning_messages >= 1


@pytest.mark.order(index=5)
@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_check_done_demo_project(caplog):
    exit_code = check_done_command([])
    assert exit_code == 0

    check_done_warning_messages = len(caplog.messages)
    assert check_done_warning_messages >= 1

    expected_warning_about_missing_assignee = r"(?=.*be assigned)(?=.*#3 Warning: Closed issue without assignee)"
    warning_about_missing_assignee = caplog.messages[0]
    assert re.search(expected_warning_about_missing_assignee, warning_about_missing_assignee)

    expected_warning_about_open_issue_with_dene_state = r"(?=.*be closed)(?=.*#4 Warning: Open issue with Done state)"
    warning_about_open_issue_with_dene_state = caplog.messages[1]
    assert re.search(expected_warning_about_open_issue_with_dene_state, warning_about_open_issue_with_dene_state)

    expected_warning_about_missing_milestone = (
        r"(?=.*have a milestone)(?=.*#11 Warning: Project item without milestone)"
    )
    warning_about_missing_milestone = caplog.messages[2]
    assert re.search(expected_warning_about_missing_milestone, warning_about_missing_milestone)

    expected_warning_about_unfinished_goals = (
        r"(?=.*have all tasks completed)(?=.*#8 Warning: project item with unfinished goals)"
    )
    warning_about_unfinished_goals = caplog.messages[3]
    assert re.search(expected_warning_about_unfinished_goals, warning_about_unfinished_goals)

    expected_warning_about_pull_request_with_missing_closing_issue_reference = (
        r"(?=.*have a closing issue reference)(?=.*#6 Warning: Pull request is missing linked issue)"
    )
    warning_about_pull_request_with_missing_closing_issue_reference = caplog.messages[4]
    assert re.search(
        expected_warning_about_pull_request_with_missing_closing_issue_reference,
        warning_about_pull_request_with_missing_closing_issue_reference,
    )

    expected_warning_about_open_pull_request_with_done_state = (
        r"(?=.*be closed)(?=.*#7 Warning: Open pull request with Done state)"
    )
    warning_about_open_pull_request_with_done_state = caplog.messages[5]
    assert re.search(
        expected_warning_about_open_pull_request_with_done_state,
        warning_about_open_pull_request_with_done_state,
    )

    ok_project_item_titles = [
        "#2 Ok: Closed issue without PR",
        "#10 Ok: Properly closed issue with Done state",
        "#12 Ok: Project item with finished goals",
        "#5 Ok: Pull Request has linked issue",
    ]
    assert not any(
        ok_project_item_title in warning_message
        for ok_project_item_title in ok_project_item_titles
        for warning_message in caplog.messages
    )


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_main_script():
    path = Path(__file__).resolve().parent.parent / "check_done" / "command.py"
    command = f"poetry run python {path!s}"
    result = subprocess.run(command, capture_output=True, text=True, shell=True, executable="/bin/bash", check=False)
    assert "Checking project items" in result.stderr


def test_keyboard_interrupt_handling():
    with patch("check_done.command.Command.execute", side_effect=KeyboardInterrupt):
        exit_code = check_done_command([])
        assert exit_code == 1


def test_general_exception_handling():
    with patch("check_done.command.Command.execute", side_effect=Exception("Fake exception")):
        exit_code = check_done_command([])
        assert exit_code == 1


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_log_info_message_if_selected_project_status_is_empty(caplog):
    with caplog.at_level(logging.INFO):
        envvar_name = "CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK"
        original_envar_value = os.environ[envvar_name]
        empty_project_status_name_in_check_done_demo_project = "In progress"
        os.environ[envvar_name] = empty_project_status_name_in_check_done_demo_project
        check_done_command([])
        os.environ[envvar_name] = original_envar_value
        assert "Nothing to check. Project has no items in the selected project status." in caplog.messages[1]


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_log_info_message_if_no_warnings_were_found_for_checked_project_items(caplog):
    with caplog.at_level(logging.INFO):
        envvar_name = "CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK"
        original_envar_value = os.environ[envvar_name]
        project_status_name_in_check_done_demo_project_with_only_correct_issues = "Archived"
        os.environ[envvar_name] = project_status_name_in_check_done_demo_project_with_only_correct_issues
        check_done_command([])
        os.environ[envvar_name] = original_envar_value
        assert "All project items are correct" in caplog.messages[1]
