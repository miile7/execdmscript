import os
import re
import sys
import time
import errno
import types
import random
import typing
import pathlib
import collections

try:
    test_error = ModuleNotFoundError()
except NameError:
    # for python <3.6, ModuleNotFound error does not exist
    # https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError
    class ModuleNotFoundError(ImportError):
        pass

try:
    import DigitalMicrograph as DM
except (ModuleNotFoundError, ImportError) as e:
    raise RuntimeError("This class can onle be used inside the Gatan " + 
                       "Microscopy Suite program.")
    DM = None

class DMScriptError(RuntimeError):
    """Error in executed dm-script code."""
    # The doc is shown in the GMS error message. Keeping the real doc string
    # makes the error message very big and fills it with completely useless
    # information
    # 
    # """This represents an error in the executed dm-script code.
    # 
    # Parameters
    # ----------
    # msg : str
    #     The text to show
    # script_origin : str
    #     The name of the executed script that the error occurres in
    # line_in_origin : int
    #     The line in the executed script (the `script_origin`) where the error
    #     occurres
    # line_in_complete : int
    #     The line in the compound script (including the setvars and readvars 
    #     code)
    # """

    def __init__(self, msg: str, script_origin: str, line_in_origin: int, 
                 line_in_complete: int) -> None:
        """
        Parameters
        ----------
        msg : str
            The text to show
        script_origin : str
            The name of the executed script that the error occurres in
        line_in_origin : int
            The line in the executed script (the `script_origin`) where the error
            occurres
        line_in_complete : int
            The line in the compound script (including the setvars and readvars 
            code)
        """
        super(DMScriptError, self).__init__(msg)
        self.script_origin = script_origin
        self.line_in_origin = line_in_origin
        self.line_in_complete = line_in_complete
        self.msg = msg
    
    def __str__(self) -> str:
        """Get the error as a a string.

        Returns
        -------
        str
            The error with (most of) the details
        """

        return ("Error in dm-script code {} in line {} (line {} in complete " + 
                "code): {}").format(self.script_origin, self.line_in_origin,
                                    self.line_in_complete, self.msg)

Convertable = typing.Union[int, float, bool, str, dict, list, tuple, None]

_python_dm_type_map = ({
        "python": int,
        "TagGroup": "Long",
        "dmscript": "number",
        "names": ("long", "integer", "int")
    }, {
        "python": float,
        "TagGroup": "Float",
        "dmscript": "number",
        "names": ("float", "double", "decimal", "realnumber", "number")
    }, {
        "python": bool,
        "TagGroup": "Boolean",
        "dmscript": "number",
        "names": ("bool", "boolean")
    }, {
        "python": str,
        "TagGroup": "String",
        "dmscript": "string",
        "names": ("string", "text")
    }, {
        "python": dict,
        "TagGroup": "TagGroup",
        "dmscript": "TagGroup",
        "names": ("TagGroup", "dict")
    }, {
        "python": (list, tuple),
        "TagGroup": "TagGroup",
        "dmscript": "TagGroup",
        "names": ("TagList", "list")
    }
)

Script = typing.Union[str, pathlib.PurePath, typing.Tuple[str, typing.Union[str, pathlib.PurePath]]]

def exec_dmscript(*scripts: Script, 
                  readvars: typing.Optional[dict]=None,
                  setvars: typing.Optional[dict]=None,
                  separate_thread: typing.Optional[typing.Union[str, pathlib.PurePath, typing.Sequence[Script]]]=None,
                  debug: typing.Optional[bool]=False,
                  debug_file: typing.Optional[typing.Union[str, pathlib.PurePath]]=None):
    """Execute the `scripts` and prepare the `vars` for getting their values.

    The `scripts` can either be filenames of dm-script files to execute or 
    scripts as strings. The type is guessed automatically. To explicitly set
    the type use a tuple with either 'file' or 'script' at index 0 and the 
    corresponding value at index 1.

    The `readvars` are the variables to read after the script has been executed.
    Those variables have to be defined in the dm-script and they have to be in 
    the global scope, otherwise they will not be readable.

    The `readvars` has to be a dict with the dm-script variable name as the key
    and the variable type as the value. The type can either be a python type or 
    a dm-script type expression. Note that only basic types are supported. 

    `TagGroup` structures can be expressed by a dict. Use the `TagGroup` key as 
    the dict key, the value is the type that is expected at this index. 
    `TagList`s are the same, use a python list and set the types to the indices.
    Both can be replaced with callback functions that will get the path of 
    keys/indices as their only parameter. If a `TagGroup` or `TagList` 
    strucutre is not given, it is auto-guessed. Note that this may have 
    problems because dm-script type definitions in `TagGroup`s are not definite 
    (e.g. float complex and float point are stored in the exact same way and 
    return the same type).

    Supported types:
    - int, aliases: Integer, short, long
    - float, aliases: Float, Double, realnumber, number, decimal
    - boolean
    - string, alias: Text
    - dict, alias: TagGroup
    - list, alias: TagList

    Note that dm-script variabels are case-insensitive. But the python 
    mechanism is not. This means you can use any typing as the key but you can 
    only get the value (on python side) with this exact typing.

    Note that there are some variables that will be accessable in the dm-script
    even if no `setvars` are given. Those are:
    - `__file__`, string: the location of the dm-script file if the `scripts`
      is a file path, otherwise it will be "<inline>", this is updated for 
      every included file

    Example
    -------
    >>> prefix = "\n".join((
    ...     "string command = \"select-image\";",
    ...     "number preselected_image = {};".format(show_image)
    ... ))
    >>> # those values will be accessable if they are defined in the dm-script
    >>> rv = {"sel_img_start": "Integer",
    ...         "sel_img_end": int,
    ...         "options": str}
    >>> # those values will be accessable in dm-script (and later in python)
    >>> sv = {"a": 20}
    >>> with exec_dmscript(prefix, filepath, readvars=rv, setvars=sv) as script:
    ...     for k in script.synchronized_vars:
    ...         # show the variables value
    ...         print("Variable {} has the value {}".format(k, script[k]))
    ...         # script[k] is equal to script.synchronized_vars[k]

    Parameters
    ----------
    scripts : str, pathlib.PurePath or tuple
        The file path of the dmscript to execute or the dm-script code or a 
        tuple with 'file' or 'script' at index 0 and the file path or the 
        script code at index 1
    readvars : dict, optional
        The variables to read from the dm-script executed code (after the code
        execution) and to allow getting the value of, the key has to be the 
        name in dm-script, the value is the type, for defining `TagGroup` and 
        `TagList` structures use dicts and tuples or callbacks
    setvars : dict, optional
        The variables to set before the code is executed (note that they must 
        not be declared), the key is the variable name, the value is the value,
        the setvars will automatically be added to the `readvars` if there is
        no conflict (setvars will not overwrite)
    separate_thread: sequence or str or pathlib.PurePath, Optional
        Script fragments to execute in a separate thread (thread is created in
        the dm-script, not in python), this is useful for showing dialogs while 
        performing python operations, note that this is an executed functions 
        content on dm-script side so no definitions are allowed, default: None
    debug : boolean, optional
        If True the dm-script will not be executed but written to the 
        `debug_file`, this way errors in the dm-script can be debugged
    debug_file : str or pathlib.PurePath, optional
        The file to save the dm-script to, this will be overwritten if it 
        exists, if not given the file is called "tmp-execdmscript.s" and will
        be placed in the current working directory, default: None

    Returns
    -------
    str
        The code to append to the dm-script code
    """

    return DMScriptWrapper(*scripts, readvars=readvars, setvars=setvars,
                           separate_thread=separate_thread, 
                           debug=debug, debug_file=debug_file)

def convert_to_taggroup(tags: typing.Union[typing.Dict[str, Convertable], 
                                           typing.List[Convertable], 
                                           typing.Tuple[Convertable, ...]],
                        path: typing.Optional[list]=[]) -> DM.Py_TagGroup:
    """Convert the given `tags` to a DigitalMicrograph `TagGroup`.

    Note that this function can be used to set tags of images easily. Create 
    the `TagGroup` with this function, then copy the tags to the image 
    `TagGroup`.

    See
    ---
    DigitalMicrograph.Py_TagGroup.CopyTagsFrom()

    Raises
    ------
    ValueError
        When one of the tags contents is not convertable.

    Parameters
    ----------
    tags : dict, list or tuple
        A dict, list or tuple that can contain the basic types int, float, 
        bool, str or None or dicts, lists or tuples of the same kind
    path : list, optional
        The path of the keys, this is for the error message only, do not 
        set this, default: []
    
    Returns
    -------
    DM.Py_TagGroup
        The tag group object
    """

    if isinstance(tags, (list, tuple)):
        datatype = list
        iterator = enumerate(tags)
        tag_group = DM.NewTagList()
    else:
        datatype = dict
        iterator = tags.items()
        tag_group = DM.NewTagGroup()
    
    for key, value in iterator:
        if isinstance(value, int):
            if datatype == list:
                tag_group.InsertTagAsLong(key, value)
            else:
                tag_group.SetTagAsLong(key, value)
        elif isinstance(value, float):
            if datatype == list:
                tag_group.InsertTagAsFloat(key, value)
            else:
                tag_group.SetTagAsFloat(key, value)
        elif isinstance(value, bool):
            if datatype == list:
                tag_group.InsertTagAsBool(key, value)
            else:
                tag_group.SetTagAsBoolean(key, value)
        elif isinstance(value, str):
            if datatype == list:
                tag_group.InsertTagAsString(key, value)
            else:
                tag_group.SetTagAsString(key, value)
        elif isinstance(value, (dict, list, tuple)):
            value = convert_to_taggroup(value, path + [key])
            if datatype == list:
                tag_group.InsertTagAsTagGroup(key, value)
            else:
                tag_group.SetTagAsTagGroup(key, value)
        elif value is None:
            if datatype == list:
                tag_group.InsertTagAsShort(key, 0)
            else:
                tag_group.SetTagAsShort(key, 0)
        else:
            raise ValueError(("The type {} of the tag value of {} is not " + 
                              "supported. Use int, float, bool, str or None " + 
                              "instead.").format(type(value), ":".join(path)))
        
    return tag_group

def get_dm_type(datatype: typing.Union[str, type], 
                for_taggroup: typing.Optional[bool]=False):
    """Get the dm-script equivalent for the given `datatype`.

    Note that not all types are supported, even if there is an equvalent in 
    dm-script.

    Raises
    ------
    LookupError
        When the `datatype` is not known

    Parameters
    ----------
    datatype : str or type
        The type to get the dm-script type of, python types and common type 
        expressions are supported
    for_taggroup : boolean, optional
        Whether the datatype should be returned so it can be used directly in 
        `taggroup.GetTagAs<datatype>()` function or not, default: False
    
    Returns
    -------
    str
        The datatype name in dm-script
    """

    global _python_dm_type_map

    if isinstance(datatype, str):
        datatype = datatype.lower()
    
    for type_def in _python_dm_type_map:
        names = list(map(lambda x: x.lower() if isinstance(x, str) else x, 
                         type_def["names"]))
        if datatype in names or (isinstance(type_def["python"], (list, tuple)) and
           datatype in type_def["python"]) or datatype == type_def["python"]:
            if for_taggroup:
                return type_def["TagGroup"]
            else:
                return type_def["dmscript"]
    
    raise LookupError("Cannot find the dm-script type for '{}'".format(datatype))

def get_python_type(datatype: typing.Union[str, type]):
    """Get the python equivalent for the given `datatype`.

    Note that not all types are supported, even if there is an equvalent in 
    dm-script.

    Raises
    ------
    LookupError
        When the `datatype` is not known

    Parameters
    ----------
    datatype : str or type
        The type to get the python type of, python types and common type 
        expressions are supported
    
    Returns
    -------
    type
        The datatype name in python
    """

    global _python_dm_type_map

    if isinstance(datatype, str):
        datatype = datatype.lower()
    
    for type_def in _python_dm_type_map:
        names = list(map(lambda x: x.lower() if isinstance(x, str) else x, 
                         type_def["names"]))
        if datatype in names or (isinstance(type_def["python"], (list, tuple)) and
           datatype in type_def["python"]) or datatype == type_def["python"]:
            if isinstance(type_def["python"], (list, tuple)):
                return type_def["python"][0]
            else:
                return type_def["python"]
    
    raise LookupError("Cannot find the python type for '{}'".format(datatype))

_replace_dm_variable_name_reg = re.compile(r"[^\w\d_]")
def escape_dm_variable(variable_name: str):
    """Replace all special characters that are not allowed with underlines.

    Raises
    ------
    ValueError:
        When the variable is not a valid name (this is only when it is an empty
        string at the moment)
    
    Parameters
    ----------
    variable_name : str
        The name of the variable
    
    Returns
    -------
    str
        The valid variable name
    """

    global _replace_dm_variable_name_reg

    name = re.sub(_replace_dm_variable_name_reg, "_", str(variable_name))

    if name == "":
        raise ValueError(("The variable name '{}' is not a valid (dm-script) " + 
                          "variable name.").format(variable_name))
    
    return name

def escape_dm_string(str_content: str):
    """Escape all special characters so the `str_content` can safely be used 
    in dm-script strings.

    Parameters
    ----------
    str_content : str
        The text that should be added to a dm-script string
    
    Returns
    -------
    str
        The str with additional escape characters
    """

    return (str(str_content)
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\0", "\\0"))


class DMScriptWrapper:
    """Wraps one or more dm-scripts.
    """

    def __init__(self,
                 *scripts: Script, 
                 readvars: typing.Optional[dict]=None,
                 setvars: typing.Optional[dict]=None,
                 separate_thread: typing.Optional[typing.Union[str, pathlib.PurePath, typing.Sequence[Script]]]=None,
                 debug: typing.Optional[bool]=False,
                 debug_file: typing.Optional[typing.Union[str, pathlib.PurePath]]=None) -> None:
        """Initialize the script wrapper.

        Parameters
        ----------
        scripts : str, pathlib.PurePath or tuple
            The file path of the dmscript to execute or the dm-script code or a 
            tuple with 'file' or 'script' at index 0 and the file path or the 
            script code at index 1
        readvars : dict, optional
            The variables to read from the dm-script executed code (after the 
            code execution) and to allow getting the value of, the key has to 
            be the name in dm-script, the value is the type, for defining 
            `TagGroup` and `TagList` structures use dicts and tuples or 
            callbacks
        setvars : dict, optional
            The variables to set before the code is executed (note that they 
            must not be declared), the key is the variable name, the value is 
            the value, the setvars will automatically be added to the 
            `readvars` if there is no conflict (setvars will not overwrite)
        separate_thread: sequence or str or pathlib.PurePath, Optional
            Script fragments to execute in a separate thread (thread is created 
            in the dm-script, not in python), this is useful for showing 
            dialogs while performing python operations, note that this is an 
            executed functions content on dm-script side so no definitions are 
            allowed, default: None
        debug : boolean, optional
            If True the dm-script will not be executed but written to the 
            `debug_file`, this way errors in the dm-script can be debugged
        debug_file : str or pathlib.PurePath, optional
            The file to save the dm-script to, this will be overwritten if it 
            exists, if not given the file is called "tmp-execdmscript.s" and 
            will be placed in the current working directory, default: None
        """
        self.scripts = DMScriptWrapper.normalizeScripts(scripts)
        self._creation_time_id = str(round(time.time() * 100))
        self.persistent_tag = "python-dm-communication-" + self._creation_time_id
        self.readvars = readvars
        self.setvars = setvars
        self.synchronized_vars = {}
        self.separate_thread = separate_thread
        if isinstance(self.separate_thread, str) and self.separate_thread != "":
            # convert to sequence
            self.separate_thread = (self.separate_thread, )
        
        self.debug = bool(debug)
        self.debug_file = debug_file
        self._slash_split_reg = re.compile("(?<!/)/(?!/)")
        self._script_sources = []

        # add all setvars to the readvars to allow accessing them after the 
        # script is executed
        if isinstance(self.setvars, dict):
            if not isinstance(self.readvars, dict):
                self.readvars = {}
            
            for key, val in self.setvars.items():
                if not key in self.readvars:
                    self.readvars[key] = type(val)
    
    def __del__(self) -> None:
        """Desctruct the object."""
        self.freeAllSyncedVars()
    
    def __call__(self) -> bool:
        """Execute the code.

        Returns
        -------
        bool
            Success
        """
        
        dmscript = self.getExecDMScriptCode()

        path = self.debug_file
        if not isinstance(path, (str, pathlib.PurePath)):
            path = os.path.join(os.getcwd(), "tmp-execdmscript.s")
        
        if self.debug:
            with open(path, "w+") as f:
                f.write(dmscript)
                f.close()
                print(("execdmscript: Did not execute script but saved to {} " + 
                      "because file is running in debug mode.").format(path))
            return True
        else:
            try:
                DM.ExecuteScriptString(dmscript)
            except RuntimeError as e:
                matches = re.match(r"Error in line ([\d]+)\s*\n(.*)", str(e))

                if matches is not None:
                    # there is an error in the executed script, read the line
                    # and check in which script the error is, then calculate
                    # the line in the script, this is better information for
                    # the user as he/she doesn't know what code is prefixed 
                    # and suffixed
                    line = int(matches.group(1))

                    for script_src in self._script_sources:
                        if (script_src["start"] <= line and 
                            line <= script_src["end"]):
                            msg = matches.group(2)
                            src = script_src["origin-name"]
                            l = line - script_src["start"] + 1

                            error = DMScriptError(msg, src, l, line)
                            
                            # GMS shows the docstring in their error message,
                            # so to offer a useful text, overwrite the docstring
                            error.__doc__ = str(error)
                            type(error).__doc__ = str(error)
                            DMScriptError.__doc__ = str(error)

                            raise error from e
                else:
                    raise e
            self._loadVariablesFromDMScript()
            return True
            
        return False
    
    def __enter__(self) -> "DMScriptWrapper":
        """Enter the `with`-block."""
        self.exec()

        return self
    
    def __exit__(self, exc_type: typing.Optional[typing.Type[BaseException]],
                 exc_instance: typing.Optional[BaseException],
                 exc_traceback: typing.Optional[types.TracebackType]) -> bool:
        """Exit the `with`-block."""
        self.freeAllSyncedVars()

    def __getitem__(self, var: typing.Any) -> typing.Any:
        """Get the dm script variable with the `var`."""
        return self.getSyncedVar(var)

    def __iter__(self) -> typing.Iterator:
        """Get the iterator to iterate over the dm-script variables."""
        return self.synchronized_vars.__iter__

    def __len__(self) -> int:
        """Get the number of synchronized variables."""
        return len(self.synchronized_vars)

    def __contains__(self, var: typing.Any) -> bool:
        """Get whether the `var` is a synchronized dm-script variable."""
        return var in self.synchronized_vars
    
    def exec(self) -> bool:
        """Execute the code.

        Returns
        -------
        bool
            Success
        """
        return self()
    
    def getExecDMScriptCode(self) -> str:
        """Get the dm-script code to execute.

        The returned code contains all files, all code fragments and 
        the complete synchronizing mechanism.

        Returns
        -------
        str
            The code to execute
        """
        self._script_sources = []
        dmscript = []
        startpos = 1

        # write some comments
        code = [
            "// This code is created automatically by concatenating files and ",
            "// code fragments.",
            "// ",
            "// This code is generated with the exedmscript module.",
            "//",
            "//" + " =" * 50
        ]
        dmscript, startpos = self._addCode(
            dmscript, code, "<comments>", None, startpos
        )

        # the code for the set variables
        code = self.getSetVarsDMCode()
        dmscript, startpos = self._addCode(
            dmscript, code, "<setvars>", self.getSetVarsDMCode, startpos
        )
        
        # add the real code to execute
        dm_file_added = False
        for i, (kind, script) in enumerate(self.scripts):
            if isinstance(kind, str):
                kind = kind.lower()

            if kind == "file":
                source = script
                dm__file__ = script
                comment = "// File {}".format(escape_dm_string(source))
                with open(script, "r") as f:
                    code = f.read()
            elif kind == "script":
                source = "<inline script in parameter {}>".format(i)
                comment = "// Directly given script"
                dm__file__ = "<inline>"
                code = script

            dmscript, startpos = self._addCode(
                dmscript, 
                DMScriptWrapper.getDMCodeForVariable("__file__", dm__file__, not dm_file_added), 
                "<__file__>", 
                None, 
                startpos
            )
            dmscript, startpos = self._addCode(
                dmscript, comment, "<comments>", None, startpos
            )
            dmscript, startpos = self._addCode(
                dmscript, code, source, script, startpos
            )

            if not dm_file_added:
                dm_file_added = True

        wait_for_signals = []
        # execute in a separate thread
        if isinstance(self.separate_thread, collections.Sequence):
            for i, (kind, script) in enumerate(DMScriptWrapper.normalizeScripts(self.separate_thread)):
                wait_for_signals.append(i)

                code = self.getSeparateThreadStartCode(i)
                dmscript, startpos = self._addCode(
                    dmscript, code, "<prepare separate thread>", 
                    self.getSeparateThreadStartCode, startpos
                )

                if isinstance(kind, str):
                    kind = kind.lower()

                if kind == "file":
                    source = script
                    comment = "// File {}".format(escape_dm_string(source))
                    with open(script, "r") as f:
                        code = f.read()
                elif kind == "script":
                    source = "<separate_thread parameter {}>".format(i)
                    comment = "// Directly given script"
                    code = script

                dmscript, startpos = self._addCode(
                    dmscript, comment, "<comments>", None, startpos
                )
                dmscript, startpos = self._addCode(
                    dmscript, code, source, script, startpos
                )

                code = self.getSeparateThreadEndCode(i)
                dmscript, startpos = self._addCode(
                    dmscript, code, "<prepare separate thread>", 
                    self.getSeparateThreadEndCode, startpos
                )
        
        # for i in wait_for_signals:
        #     code = self.getSeparateThreadWaitCode(i)
        #     dmscript, startpos = self._addCode(
        #         dmscript, code, "<wait for signal {}>".format(i), 
        #         self.getSeparateThreadWaitCode, startpos
        #     )

        # the code for the readvars
        code = self.getSyncDMCode()
        dmscript, startpos = self._addCode(
            dmscript, code, "<readvars>", self.getSyncDMCode, startpos
        )

        return "\n".join(dmscript)
    
    def _addCode(self, dmscript: list, code: typing.Union[list, tuple, str], 
                 origin_name: str, origin_detail: typing.Any,
                 startpos: typing.Optional[int]=1) -> typing.Tuple[list, int]:
        """Add the `code` to the `dmscript` and save its position in 
        `DMScriptWrapper._script_sources`.

        Parameters
        ----------
        dmscript : list
            The list of code fragments that create the dmscript
        code : str, list or tuple
            One or more code fragments to add to the `dmscript`
        origin_name : str
            A human readable short name to identify where this code fragment 
            comes from, this is shown in error messages
        origin_detail : any
            The real origin to use in the code to identify (as) exactly (as
            possible) where the code comes from, this is for programmatic use 
            only
        startpos : int, optional
            The line where the code starts, default: 1
        
        Returns
        -------
        list, int
            The dmscript list with the added code fragment at index 0, the 
            start position of the next code fragment at index 1
        """
        # the number of lines (minus one)
        code_lines = 0
        if isinstance(code, (list, tuple)):
            code_lines = sum([c.count("\n") for c in code]) + len(code) - 1
            dmscript += code
        elif isinstance(code, str):
            code_lines = code.count("\n")
            dmscript.append(code)
        else:
            raise ValueError(("The code neither is a list, nor a tuple nor " + 
                              "nor a string but a '{}' which is not " + 
                              "supported").format(type(code)))

        self._script_sources.append({
            "start": startpos, 
            "end": startpos + code_lines,
            "origin-name": origin_name,
            "origin-detail": origin_detail
        })
        
        return dmscript, startpos + code_lines + 1
    
    def getSeparateThreadStartCode(self, index: int) -> str:
        """Get the dm-script code for executing the complete script in a 
        separate thread.

        Note that this needs to surround the complete code. Add the code 
        returned by `DMScriptWrapper.getSeparateThreadStartCode()` before your
        code and end it with the code returned by 
        `DMScriptWrapper.getSeparateThreadEndCode()`.

        Parameters
        ----------
        index : int
            The thread index

        Returns
        -------
        str
            The code to append to the dm-script code
        """

        return "\n".join((
            "object thread_cancel_signal{}_{} = NewCancelSignal();".format(self._creation_time_id, index),
            "object thread_done_signal{}_{} = NewSignal(0);".format(self._creation_time_id, index),
            "class ExecDMScriptThread{}_{} : Thread{{".format(self._creation_time_id, index),
            "void RunThread(object self){"
        ))
    
    def getSeparateThreadEndCode(self, index: int) -> str:
        """Get the dm-script code for executing the complete script in a 
        separate thread.

        Note that this needs to surround the complete code. Add the code 
        returned by `DMScriptWrapper.getSeparateThreadStartCode()` before your
        code and end it with the code returned by 
        `DMScriptWrapper.getSeparateThreadEndCode()`.

        Parameters
        ----------
        index : int
            The thread index

        Returns
        -------
        str
            The code to append to the dm-script code
        """

        return "\n".join((
            "// inform that the thread is done now",
            "thread_done_signal{}_{}.setSignal();".format(self._creation_time_id, index),
            "}", # end ExecDMScriptThread<id>::RunThread()
            "}", # end ExecDMScriptThread<id> class
            "alloc(ExecDMScriptThread{}_{}).StartThread();".format(
                self._creation_time_id, index
            )
        ))
    
    def getSeparateThreadWaitCode(self, index: int) -> str:
        """Get the dm-script code for waiting to complete all separately 
        started threads.

        Parameters
        ----------
        index : int
            The thread index

        Returns
        -------
        str
            The code to append to the dm-script code
        """

        return "\n".join((
            "// wait for the thread {}".format(index),
            "thread_done_signal{id}_{i}.WaitOnSignal(infinity(), thread_cancel_signal{id}_{i});".format(
                id=self._creation_time_id, i=index
            )
        ))
    
    def getSetVarsDMCode(self) -> str:
        """Get the dm-script code for defining the `setvars`.

        Returns
        -------
        str
            The code to append to the dm-script code
        """

        if not isinstance(self.setvars, dict):
            return ""

        dmscript = [
            "// Setting variables from python values"
        ]
        for name, val in self.setvars.items():
            dmscript.append(DMScriptWrapper.getDMCodeForVariable(name, val))
        
        return "\n".join(dmscript)

    def getSyncDMCode(self) -> str:
        """Get the `dm-script` code that has to be added to the executed code 
        for synchronizing.

        Returns
        -------
        str
            The code to append to the dm-script code
        """
        if not isinstance(self.readvars, dict) or len(self.readvars) == 0:
            return ""
        
        # the name of the tag group to use
        sync_code_tg_name = "sync_taggroup_" + self._creation_time_id
        
        # declare and initialize the used variables
        sync_code_prefix = "\n".join((
            "",
            "// Adding synchronizing machanism by using persistent tags.",
            "TagGroup {tg}_user = GetPersistentTagGroup();",
            "number {tg}_index = {tg}_user.TagGroupCreateNewLabeledTag(\"{pt}\");",
            "TagGroup {tg}_tg = NewTagGroup();",
            "{tg}_user.TagGroupSetIndexedTagAsTagGroup({tg}_index, {tg}_tg);",
            ""
        ))
        
        # the template to use for each line
        sync_code_template = "\n".join((
            "// Synchronizing {{val}}",
            "{tg}_index = {tg}_tg.TagGroupCreateNewLabeledTag(\"{{key}}\");",
            "{tg}_tg.TagGroupSetIndexedTagAs{{type}}({tg}_index, {{val}});"
        )).format(tg=sync_code_tg_name, pt=self.persistent_tag)
        
        dmscript = [sync_code_prefix.format(
            tg=sync_code_tg_name, pt=self.persistent_tag
        )]
        
        linearize_functions_added = False

        for var_name, var_type in self.readvars.items():
            if isinstance(var_type, (dict, list, tuple)):
                dmscript += self._recursivelyGetTagGroupDefCode(
                    sync_code_tg_name, var_type, var_name
                )
            else:
                py_type = get_python_type(var_type)

                if py_type in (dict, list, tuple):
                    # autoguess a TagGroup/TagList
                    if not linearize_functions_added:
                        linearize_functions_added = True
                        dmscript.append(
                            DMScriptWrapper._getLinearizeTagGroupFunctionsCode()
                        )
                    
                    dmscript.append(
                        "__exec_dmscript_linearizeTags({tg}_tg, {var_name}, \"{key}\", \"{key}\");".format(
                            var_name=escape_dm_variable(var_name),
                            key=escape_dm_string(var_name), 
                            tg=sync_code_tg_name
                    ))
                else:
                    dmscript.append(sync_code_template.format(
                        key=escape_dm_string(var_name), 
                        val=escape_dm_variable(var_name), 
                        type=get_dm_type(var_type, for_taggroup=True)
                    ))
        
        return "\n".join(dmscript)
    
    def _recursivelyGetTagGroupDefCode(self, dm_tg_name: str, 
                                       type_def: typing.Union[list, dict], 
                                       var_name: str, 
                                       path: typing.Optional[list]=[]) -> list:
        """Get the code for saving a `TagGroup` or `TagList` to the persistent
        tags with a known structure.

        The tagname where the data to synchronize is saved to (direct child of 
        the persistent tags) is the `dm_tg_name` ("_tg" will be appended). 
        
        The `type_def` is either a list or a dict that defines the structure. 
        It can contain more dicts and lists or the name tag name as the key and 
        the datattype as a value (python types and common expressions allowed).

        The `var_name` is the dm-script variable name to synchronize.

        The `path` is for recursive use only. It contains the indices of the 
        parent `TagGroup`/`TagList´/`type_def`-dict. A number (has to be int)
        indicates that this was a `TagList`, a string (also numeric strings 
        supported) indicate that this was a `TagGroup`.

        The executed code will save the `var_name` linearized to the persistent
        tags, each tag name (or index) is separated by "/" (escape: "//"). The 
        type is present for each key called "{{type}}<key name>".

        Raises
        ------
        ValueError
            When the `type_def` neither is a dict nor a list nor a tuple

        Parameters
        ----------
        dm_tg_name : str
            The name of the `TagGroup` to use in the background, this `TagGroup`
            is a direct child of the persistent tags and used for 
            synchronization (this is defined in 
            `DMScriptWrapper::getDMSyncCode()`)
        type_def : dict, list, tuple
            A list or tuple to define datatypes of `TagList`s, a dict to define
            `TagGroup` structures, can contain other dicts, lists or tuples, 
            each value is the datatype, each key is the `TagGroup` key, each
            index is the `TagList` index
        var_name : str
            The dm-script variable name to synchronize
        path : list, optional
            Contains the path to the current value for recursive use, never set 
            this value!
        
        Returns
        -------
        str
            The dm-script code to execute for saving the defined structure to
            the persistent tags
        """
        dmscript = []
        list_mode = False

        if isinstance(type_def, (list, tuple)):
            iterator = enumerate(type_def)
            list_mode = True
        elif isinstance(type_def, dict):
            iterator = type_def.items()
            list_mode = False
        else:
            raise ValueError("The type_def has to be a dict or a list.")

        path = list(path)

        dmscript.append("\n".join((
            "if(!{tg}_tg.TagGroupDoesTagExist(\"{{{{available-paths}}}}{key}\")){{",
                "number index_{var}_{t}{r} = {tg}_tg.TagGroupCreateNewLabeledTag(\"{{{{available-paths}}}}{key}\");",
                "{tg}_tg.TagGroupSetIndexedTagAsString(index_{var}_{t}{r}, \"\");",
            "}}"
        )).format(tg=escape_dm_variable(dm_tg_name), 
                  key=escape_dm_string(var_name), 
                  var=escape_dm_variable(var_name), t=round(time.time() * 100),
                  r=random.randint(0, 99999999)))
        
        for var_key, var_type in iterator:
            dms = ""
            if isinstance(var_type, (dict, list, tuple)):
                if list_mode:
                    # important so future calls knwo that this was a list
                    var_key = int(var_key)
                else:
                    var_key = str(var_key)
                
                dmscript += self._recursivelyGetTagGroupDefCode(
                    dm_tg_name, var_type, var_name, path + [var_key]
                )

                if isinstance(var_type, dict):
                    tg_type = "TagGroup"
                else:
                    tg_type = "TagList"
                
                var_type = tg_type
            else:
                dms = "\n".join((
                    "{scripttype} {var}_{varkey}_{t}{r};",
                    "{var}.TagGroupGetTagAs{tgtype}(\"{srcpath}\", {var}_{varkey}_{t}{r});",
                    "{tg}_index = {tg}_tg.TagGroupCreateNewLabeledTag(\"{destpath}\")",
                    "{tg}_tg.TagGroupSetIndexedTagAs{tgtype}({tg}_index, {var}_{varkey}_{t}{r});",
                ))
                tg_type = get_dm_type(var_type, for_taggroup=True)

            source_path = ":".join(map(
                lambda x: "[{}]".format(x) if isinstance(x, int) else x,
                path + [var_key]
            ))
            destination_path = "/".join(map(
                lambda x: x.replace("/", "//") if isinstance(x, str) else str(x),
                [var_name] + path + [var_key]
            ))
            dms = "\n".join((
                dms,
                "{tg}_index = {tg}_tg.TagGroupCreateNewLabeledTag(\"{{{{type}}}}{destpath}\")",
                "{tg}_tg.TagGroupSetIndexedTagAsString({tg}_index, \"{tgtype}\");",
                "string available_index_{var}_{varkey}_{t}{r};",
                "{tg}_tg.TagGroupGetTagAsString(\"{{{{available-paths}}}}{key}\", available_index_{var}_{varkey}_{t}{r});",
                "available_index_{var}_{varkey}_{t}{r} += \"{destpath};\";",
                "{tg}_tg.TagGroupSetTagAsString(\"{{{{available-paths}}}}{key}\", available_index_{var}_{varkey}_{t}{r});",
            )).format(
                tg=escape_dm_variable(dm_tg_name), 
                var=escape_dm_variable(var_name), 
                key=escape_dm_string(var_name),
                varkey=escape_dm_variable(var_key),
                scripttype=get_dm_type(var_type, for_taggroup=False),
                tgtype=escape_dm_variable(tg_type),
                srcpath=escape_dm_string(source_path),
                destpath=escape_dm_string(destination_path),
                t=round(time.time() * 100),
                r=random.randint(0, 99999999)
            )

            dmscript.append(dms)

        return dmscript
    
    def _loadVariablesFromDMScript(self) -> None:
        """Load the variables from the persistent tags to dm-script."""

        self.synchronized_vars = {}
        
        if not isinstance(self.readvars, dict):
            return
        
        for var_name, var_type in self.readvars.items():
            path = self.persistent_tag + ":" + var_name
            
            var_type = self.readvars[var_name]
            if isinstance(var_type, (dict, list, tuple)):
                py_type = type(var_type)
            else:
                py_type = get_python_type(var_type)
            
            if py_type in (dict, list, tuple):
                value = None

                # get the paths of all elements added to this group, recursive
                # travelling is not possible because TagGroups cannot be saved
                # to variables
                success, tg_keys = (DM.GetPersistentTagGroup().
                                    GetTagAsString(
                                        self.persistent_tag + ":{{available-paths}}" + str(var_name)
                                    ))

                if success:
                    tg_keys = list(filter(lambda x: x != "", tg_keys.split(";")))
                    
                    for tg_key in tg_keys:
                        paths = list(filter(lambda x: x != "", 
                                            self._slash_split_reg.split(tg_key)))
                        
                        for i, path in enumerate(paths):
                            # build the value structure
                            if i == 0:
                                # set the variables values as the "base"
                                if py_type == dict:
                                    cur_type = "TagGroup"
                                    if value is None:
                                        value = {}
                                    value_ref = value
                                else:
                                    cur_type = "TagList"
                                    if value is None:
                                        value = []
                                    value_ref = value
                            else:
                                # parse the key depending on the parent
                                # type, cur_type is not overwritten yet
                                if cur_type == "TagList":
                                    key = int(path)
                                    while key >= len(value_ref):
                                        # also prepare the current index 
                                        # with none so it can be set by 
                                        # value_ref[key] = v, if the 
                                        # key already exists and is None
                                        # append was wrong
                                        value_ref.append(None)
                                elif cur_type == "TagGroup":
                                    key = path
                                    if key not in value_ref:
                                        value_ref[key] = None
                                else:
                                    break
                                
                                # the the current path that the persistent
                                # TagGroup contains the key of
                                cur_path = "/".join(map(str, paths[0:(i + 1)]))
                                
                                # get the current datatype
                                s, cur_type = (DM.GetPersistentTagGroup().
                                        GetTagAsString(
                                            self.persistent_tag + 
                                            ":{{type}}" + str(cur_path)
                                        ))
                                
                                if cur_type == "TagGroup":
                                    # create a new dict and save it in 
                                    # the current key, then set the
                                    # reference to this new dict
                                    if not isinstance(value_ref[key], dict):
                                        value_ref[key] = {}
                                    value_ref = value_ref[key]
                                elif cur_type == "TagList":
                                    # create a new list, add as many times
                                    # None as necessary to reach the
                                    # current index
                                    if not isinstance(value_ref[key], list):
                                        value_ref[key] = []
                                    value_ref = value_ref[key]
                                else:
                                    # the current type is a real value, 
                                    # get the parsed value and stop (there 
                                    # should not be any more paths coming,
                                    # just to be sure)
                                    s, v = self._getParsedValueFromPersistentTags(
                                        "{}:{}".format(
                                            self.persistent_tag, cur_path
                                        ), 
                                        cur_type
                                    )

                                    if s:
                                        value_ref[key] = v
                                    else:
                                        success = False
                                    break
            else:
                success, value = self._getParsedValueFromPersistentTags(
                    path, var_type
                )
            
            if success:
                self.synchronized_vars[var_name] = value
        
        self.freeAllSyncedVars()

    def _getParsedValueFromPersistentTags(self, path, var_type):
        """Get the value at the `path` from the persistent tags.

        Parameters
        ----------
        path : str
            The path in the persistent tags
        var_type : str or type
            The type to get the value as
        
        Returns
        -------
        bool, any
            A tuple with success at index 0 and the value (if existing) at 
            index 1
        """
        
        dm_type = get_dm_type(var_type, for_taggroup=True)
        # UserTags are enough but they are not supported in python :(
        # do not save the persistent tags to a variable, this way they do 
        # not work anymore (for any reason)
        if dm_type == "Long":
            success, value = DM.GetPersistentTagGroup().GetTagAsLong(path)
        elif dm_type == "Float":
            success, value = DM.GetPersistentTagGroup().GetTagAsFloat(path)
        elif dm_type == "Boolean":
            success, value = DM.GetPersistentTagGroup().GetTagAsBoolean(path)
        elif dm_type == "String":
            success, value = DM.GetPersistentTagGroup().GetTagAsString(path)
        else:
            raise ValueError("The datatype '{}' is not supported".format(var_type))
        
        return success, value

    def getSyncedVar(self, var_name: str) -> typing.Any:
        """Get the value of the `var_name` dm-script variable.

        If the `var_name` is synchronized via the `getSyncDMCode()` function, 
        the value of the variabel can be received by this function.

        Parameters
        ----------
        var_name : str
            The name of the variable in the dm-script code

        Returns
        -------
        mixed
            The variable value
        """

        if var_name not in self.synchronized_vars:
            return None
        else:
            return self.synchronized_vars[var_name]

    def freeAllSyncedVars(self) -> None:
        """Delete all synchronization from the persistent tags.

        Make sure to always execute this function. Otherwise the persistent 
        tags will be filled with a lot of garbage.
        """
        # python way does not work
        # user_tags = DM.GetPersistentTagGroup()
        # user_tags.TagGroupDeleteTagWithLabel(persistent_tag)

        if not self.debug and DM is not None:
            DM.ExecuteScriptString(
                "GetPersistentTagGroup()." + 
                "TagGroupDeleteTagWithLabel(\"" + self.persistent_tag + "\");"
            )
    
    @staticmethod
    def getDMCodeForVariable(name: str, value: Convertable, 
                             declare_type: typing.Optional[bool]=True):
        """Create the dm-script code for defining and declaring a variable.

        Parameters
        ----------
        name : str
            The variable name, can only be digits and letters and must not 
            start with a digit
        value : int, float, str, boolean, dict, list, tuple or None
            The value to set
        declare_type : bool, optional
            Whether to declare the type or not, default: True
        
        Returns
        -------
        str
            The dm-code that defines this variable
        """

        dmscript = []
        py_type = type(value)
        dm_type = get_dm_type(py_type, for_taggroup=False)

        if py_type in (dict, list, tuple):
            dmscript += DMScriptWrapper._getTagGroupDMCodeForVariable(
                name, value, declare_type
            )
        else:
            if isinstance(value, str):
                value = "\"{}\"".format(escape_dm_string(value))
            
            if declare_type:
                line = "{type} {var} = {val};"
            else:
                line = "{var} = {val};"
            
            dmscript.append(line.format(type=dm_type, 
                                        var=escape_dm_variable(name), 
                                        val=value))
        
        return "\n".join(dmscript)
    
    @staticmethod
    def _getTagGroupDMCodeForVariable(name: str, 
                                      value: Convertable,
                                      declare_type: typing.Optional[bool]=True,
                                      prefix: typing.Optional[str]="",
                                      depth: typing.Optional[int]=0):
        """Create the dm-script code for defining and declaring a `TagGroup` or
        a `TagList`.

        Parameters
        ----------
        name : str
            The variable name, can only be digits and letters and must not 
            start with a digit
        value : dict, list, tuple
            The dict, list or tuple to express as a `TagGroup` or `TagList`
        declare_type : bool, optional
            Whether to declare the type or not, default: True
        prefix : str, optional
            A prefix to add before the `TagGroup` variable name
        depth : int, optional
            The current depth
        
        Returns
        -------
        str
            The dm-code that defines this `TagGroup` or `TagList`
        """
        dmscript = []
        py_type = type(value)
        dm_type = get_dm_type(py_type, for_taggroup=False)

        # prepare creator function
        if py_type == dict:
            creator = "NewTagGroup()"
            iterator = value.items()
        else:
            creator = "NewTagList()"
            iterator = enumerate(value)
        
        # set variable
        if declare_type:
            line = "{type} {var} = {val};"
        else:
            line = "{var} = {val};"
        
        dmscript.append(line.format(type=dm_type, 
                                    var=escape_dm_variable(prefix + name), 
                                    val=creator))

        index = None
        if py_type == dict:
            # declare the index for TagGroups
            index = "__exec_dmscript_{}_index".format(escape_dm_variable(name))
            dmscript.append("number {};".format(index))

        for i, (key, value) in enumerate(iterator):
            if value is None:
                # fix none type
                value_py_type = None
                value_dm_type = "Number"
                value = 0
            else:
                # get the type of the variable to express
                value_py_type = type(value)
                value_dm_type = get_dm_type(value_py_type, for_taggroup=True)

            if value_py_type == str:
                # add quotes to str values
                value = "\"{}\"".format(escape_dm_string(value))
            elif value_py_type == bool:
                value = int(value)
            elif value_py_type in (dict, list, tuple):
                # current value is a TagGroup or TagList, recursively create 
                # the TagGroup or the TagList and then add it 
                dmscript.append("")
                # add a prefix to (hopefully) prevent name collision, note that
                # this name gets recursively longer, the prefix is only added
                # once
                p = "__exec_dmscript_"
                n = "{}_tg_{}_{}".format(escape_dm_variable(name), i, depth + 1)
                dmscript += DMScriptWrapper._getTagGroupDMCodeForVariable(
                    n, value, True, p, depth + 1
                )
                # rewrite the value to the variable name of the TagGroup or 
                # TagList that now exists
                value = p + n

            if py_type in (list, tuple):
                # add the next index to the list
                dmscript.append("{}.TagGroupInsertTagAs{}(infinity(), {});".format(
                    escape_dm_variable(prefix + name), value_dm_type, value
                ))
            else:
                # add the labeled tag and the value
                dmscript += [
                    "{} = {}.TagGroupCreateNewLabeledTag(\"{}\");".format(
                        index, escape_dm_variable(prefix + name), 
                        escape_dm_string(key)
                    ),
                    "{}.TagGroupSetIndexedTagAs{}({}, {});".format(
                        escape_dm_variable(prefix + name), value_dm_type, 
                        index, value
                    )
                ]
    
        return dmscript
    
    @staticmethod
    def _getLinearizeTagGroupFunctionsCode():
        """Get the dm code that defines the `__exec_dmscript_linearizeTags()`
        function to save `TagGroup`s and `TagList`s as an 1d-"array"

        Returns
        -------
        str
            The dm script defining the functions
        """

        return """
        string __exec_dmscript_replace(string subject, string search, string replace){
            if(subject.find(search) < 0){
                return subject;
            }

            String r = "";
            number l = search.len();
            number pos;
            while((pos = subject.find(search)) >= 0){
                r.stringAppend(subject.left(pos) + replace);
                subject = subject.right(subject.len() - pos - l);
            }

            return r;
        }

        void __exec_dmscript_linearizeTags(TagGroup &linearized, TagGroup tg, string var_name, string path){
            string available_paths = "";
            if(linearized.TagGroupDoesTagExist("{{available-paths}}" + var_name)){
                linearized.TagGroupGetTagAsString("{{available-paths}}" + var_name, available_paths);
            }

            if(tg.TagGroupIsValid()){
                for(number i = 0; i < tg.TagGroupCountTags(); i++){
                    String label;
                    if(tg.TagGroupIsList()){
                        label = i + "";
                    }
                    else{
                        label = tg.TagGroupGetTagLabel(i).__exec_dmscript_replace("/", "//");
                    }
                    number type = tg.TagGroupGetTagType(i, 0);
                    string type_name = "";
                    number index;
                    string p = path + "/" + label;

                    if(type == 0){
                        // TagGroup
                        TagGroup value;
                
                        // save the available paths for the next function call
                        if(!linearized.TagGroupDoesTagExist("{{available-paths}}" + var_name)){
                            number ind = linearized.TagGroupCreateNewLabeledTag("{{available-paths}}" + var_name);
                            linearized.TagGroupSetIndexedTagAsString(ind, available_paths);
                        }
                        else{
                            linearized.TagGroupSetTagAsString("{{available-paths}}" + var_name, available_paths);
                        }
                        
                        tg.TagGroupGetIndexedTagAsTagGroup(i, value);
                        __exec_dmscript_linearizeTags(linearized, value, var_name, p);

                        // there may have been added some paths
                        if(linearized.TagGroupDoesTagExist("{{available-paths}}" + var_name)){
                            linearized.TagGroupGetTagAsString("{{available-paths}}" + var_name, available_paths);
                        }
                                
                        if(value.TagGroupIsList()){
                            type_name = "TagList";
                        }
                        else{
                            type_name = "TagGroup";
                        }
                    }
                    else if(type == 2){
                        // tag is a short
                        number value

                        tg.TagGroupGetIndexedTagAsShort(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsShort(index, value);
                        type_name = "Short";
                    }
                    else if(type == 3){
                        // tag is a long
                        number value

                        tg.TagGroupGetIndexedTagAsLong(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsLong(index, value);
                        type_name = "Long";
                    }
                    else if(type == 4){
                        number value;
                        
                        tg.TagGroupGetIndexedTagAsUInt16(index, value);
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsUInt16(index, value);
                        type_name = "UInt16";
                    }
                    else if(type == 5){
                        number value;
                        
                        tg.TagGroupGetIndexedTagAsUInt32(index, value);
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsUInt32(index, value);
                        type_name = "UInt32";
                    }
                    else if(type == 6){
                        // tag is a float
                        number value

                        tg.TagGroupGetIndexedTagAsFloat(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsFloat(index, value);
                        type_name = "Float";
                    }
                    else if(type == 7){
                        // tag is a double
                        number value

                        tg.TagGroupGetIndexedTagAsDouble(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsDouble(index, value);
                        type_name = "Double";
                    }
                    else if(type == 8){
                        // tag is a boolean
                        number value

                        tg.TagGroupGetIndexedTagAsBoolean(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsBoolean(index, value);
                        type_name = "Boolean";
                    }
                    // skip type=15, this is more complicated types like rgbnumber, 
                    // shortpoint, longpoint, floatcomplex, doublecomplex, and
                    // shortrect, longrect and float rect
                    else if(type == 20){
                        // tag is a string
                        string value

                        tg.TagGroupGetIndexedTagAsString(i, value)
                        index = linearized.TagGroupCreateNewLabeledTag(p);
                        linearized.TagGroupSetIndexedTagAsString(index, value);
                        type_name = "String";
                    }
                    
                    if(type_name != ""){
                        index = linearized.TagGroupCreateNewLabeledTag("{{type}}" + p);
                        linearized.TagGroupSetIndexedTagAsString(index, type_name);

                        available_paths += p + ";";
                    }
                }
                
                if(!linearized.TagGroupDoesTagExist("{{available-paths}}" + var_name)){
                    number ind = linearized.TagGroupCreateNewLabeledTag("{{available-paths}}" + var_name);
                    linearized.TagGroupSetIndexedTagAsString(ind, available_paths);
                }
                else{
                    linearized.TagGroupSetTagAsString("{{available-paths}}" + var_name, available_paths);
                }
            }
        }
        """

    @staticmethod
    def normalizeScripts(scripts: typing.Sequence) -> typing.List[tuple]:
        """Create a tuple for each script in the `scripts` with index 0 telling
        if it is a file or script and index 1 telling the corresponding value.

        Parameters
        ----------
        scripts : list or tuple of string, pathlib.PurePath or tuple
            The scripts
        
        Returns
        -------
        list of tuple
            A list containing a tuple in each entry, each tuple contains 'file'
            or 'script' at index 0 and the path or the script at index 1
        """

        normalized = []

        for script in scripts:
            if isinstance(script, (list, tuple)) and len(script) >= 2:
                normalized.append(script)
            elif isinstance(script, pathlib.PurePath):
                normalized.append(("file", script))
            elif isinstance(script, str) and script != "":
                if os.path.isfile(script):
                    normalized.append(("file", script))
                else:
                    normalized.append(("script", script))

        return normalized