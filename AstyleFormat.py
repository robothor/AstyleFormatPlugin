"""
This is a simple plugin that runs AStyle (http://astyle.sourceforge.net/).  The
plugin will only run on C/C++/C#/Java programs.  It can operate in two modes:
1. As a "save-hook" (to use emacs parlance)
2. As a command ("astyle_format")

Caveats:
1. astyle must be in your path
2. astyle will pull its config options from ~/.astylerc (see astyle docs)
"""

import os
import re
import subprocess
import tempfile
import sublime
import sublime_plugin

def write_to_tempfile(file_name, lines):
    """
        Create a temporary file and write the text denoted by _lines_ into it.
        _file_name_ is used to determine the type of file being written, as
        astyle will use this.

        Returns the name of the temporary file -- this file is not deleted.
    """
    _, extension = os.path.splitext(file_name)
    in_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    in_file.writelines(lines)
    in_file.flush()
    in_file.close()
    return in_file.name

def read_from_tempfile(file_name):
    """
        Open and read all data from the file referenced by _file_name_.  This
        list of lines is then joined to a string and returned.  The file is
        removed.
    """
    processed_file = file(file_name)
    pretty_code = processed_file.readlines()
    processed_file.close()
    os.remove(file_name)
    return "".join(pretty_code)

def is_enabled(view):
    """
        Check if we can work on this file -- astyle only works on c/C++/c#/Java.

        H/T to the AutoFormat plugin for this.
    """
    lang = re.search(".*/([^/]*)\.tmLanguage$",
               view.settings().get("syntax")).group(1)
    lang = lang.lower()
    if ["c", "c++", "c#", "java"].count(lang) > 0:
        return True
    else:
        return False

def reformat_text(view, edit):
    """
        Actually reformat the text.  This does the following:
        1. Check whether we _can_ reformat.
        2. Grab the whole buffer.
        3. Write it to a temp file
        4. Call astyle on that file
        5. Grab the new content and push them back to the view.
    """
    if not is_enabled(view):
        return sublime.status_message('Nothing to tidy!')

    text_region = sublime.Region(0L, view.size())
    file_name = write_to_tempfile(view.file_name(), view.substr(text_region))
    # should be good enough!
    current_region = view.sel()[0]

    command = ["astyle", file_name]
    astyle_process = subprocess.Popen(command)
    astyle_process.wait()

    pretty_code = read_from_tempfile(file_name)
    view.replace(edit, text_region, pretty_code)
    view.replace(edit,
                 sublime.Region(current_region.begin(), current_region.begin()),
                 "")
    view.show(current_region)
    sublime.status_message("Reformatted and wrote " + view.file_name())

class AstyleFormatCommand(sublime_plugin.TextCommand):
    """
        Text command version -- bind this to a key combo in the user key prefs:

        { "keys": ["ctrl+alt+f"], "command": "astyle_format" }
    """
    def run(self, edit):
        reformat_text(self.view, edit)

class AstyleFormatListener(sublime_plugin.EventListener):
    """
        Event listener version -- should run on save for the appropriate files.
    """
    def on_pre_save(self, view):
        sublime.status_message(view.file_name() + " is about to be saved")
        edit = view.begin_edit()
        try:
            reformat_text(view, edit)
        finally:
            view.end_edit(edit)