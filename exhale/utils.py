# -*- coding: utf8 -*-
########################################################################################
# This file is part of exhale.  Copyright (c) 2017, Stephen McDowell.                  #
# Full BSD 3-Clause license available here:                                            #
#                                                                                      #
#                     https://github.com/svenevs/exhale/LICENSE.md                     #
########################################################################################

from . import configs

import os
import sys
import types
import traceback

# Fancy error printing <3
try:
    import pygments
    from pygments import lexers, formatters
    __USE_PYGMENTS = True
except:
    __USE_PYGMENTS = False

__name__      = "utils"
__docformat__ = "reStructuredText"


AVAILABLE_KINDS = [
    "class",
    "struct",
    "function",
    "enum",
    "enumvalue",  # unused
    "namespace",
    "define",
    "typedef",
    "variable",
    "file",
    "dir",
    "group",  # unused
    "union"
]
''' A list of all potential input ``kind`` values coming from Doxygen. '''


def makeCustomSpecificationsMapping(func):
    # Make sure they gave us a function
    if not isinstance(func, types.FunctionType):
        raise ValueError(
            "The input to exhale.util.makeCustomSpecificationsMapping was *NOT* a function: {0}".format(
                type(func)
            )
        )

    # Stamp the return to ensure exhale created this function.
    ret = {configs._closure_map_sanity_check: configs._closure_map_sanity_check}
    try:
        # Because we cannot pickle a fully-fledged function object, we are going to go
        # through every kind and store its return value.
        for kind in AVAILABLE_KINDS:
            specs = func(kind)
            if type(specs) is not str:
                raise RuntimeError(
                    "The custom specifications function did not return a string for input `{kind}`".format(
                        kind=kind
                    )
                )
            ret[kind] = specs
    except Exception as e:
        raise RuntimeError("Unable to create custom specifications:\n{0}".format(e))

    # Everything went according to plan, send it back to `conf.py` :)
    return ret


def nodeCompoundXMLContents(node):
    node_xml_path = os.path.join(configs.doxygenOutputDirectory, "{0}.xml".format(node.refid))
    if os.path.isfile(node_xml_path):
        try:
            with open(node_xml_path, "r") as xml:
                node_xml_contents = xml.read()

            return node_xml_contents
        except:
            return None
    return None


########################################################################################
#
##
###
####
##### Utility / helper functions.
####
###
##
#
########################################################################################
def qualifyKind(kind):
    '''
    Qualifies the breathe ``kind`` and returns an qualifier string describing this
    to be used for the text output (e.g. in generated file headings and link names).

    The output for a given kind is as follows:

    +-------------+------------------+
    | Input Kind  | Output Qualifier |
    +=============+==================+
    | "class"     | "Class"          |
    +-------------+------------------+
    | "define"    | "Define"         |
    +-------------+------------------+
    | "enum"      | "Enum"           |
    +-------------+------------------+
    | "enumvalue" | "Enumvalue"      |
    +-------------+------------------+
    | "file"      | "File"           |
    +-------------+------------------+
    | "function"  | "Function"       |
    +-------------+------------------+
    | "group"     | "Group"          |
    +-------------+------------------+
    | "namespace" | "Namespace"      |
    +-------------+------------------+
    | "struct"    | "Struct"         |
    +-------------+------------------+
    | "typedef"   | "Typedef"        |
    +-------------+------------------+
    | "union"     | "Union"          |
    +-------------+------------------+
    | "variable"  | "Variable"       |
    +-------------+------------------+

    The following breathe kinds are ignored:

    - "autodoxygenfile"
    - "doxygenindex"
    - "autodoxygenindex"

    Note also that although a return value is generated, neither "enumvalue" nor
    "group" are actually used.

    :Parameters:
        ``kind`` (str)
            The return value of a Breathe ``compound`` object's ``get_kind()`` method.

    :Return (str):
        The qualifying string that will be used to build the reStructuredText titles and
        other qualifying names.  If the empty string is returned then it was not
        recognized.
    '''
    if kind == "dir":
        return "Directory"
    else:
        return kind.capitalize()


def kindAsBreatheDirective(kind):
    '''
    Returns the appropriate breathe restructured text directive for the specified kind.
    The output for a given kind is as follows:

    +-------------+--------------------+
    | Input Kind  | Output Directive   |
    +=============+====================+
    | "class"     | "doxygenclass"     |
    +-------------+--------------------+
    | "define"    | "doxygendefine"    |
    +-------------+--------------------+
    | "enum"      | "doxygenenum"      |
    +-------------+--------------------+
    | "enumvalue" | "doxygenenumvalue" |
    +-------------+--------------------+
    | "file"      | "doxygenfile"      |
    +-------------+--------------------+
    | "function"  | "doxygenfunction"  |
    +-------------+--------------------+
    | "group"     | "doxygengroup"     |
    +-------------+--------------------+
    | "namespace" | "doxygennamespace" |
    +-------------+--------------------+
    | "struct"    | "doxygenstruct"    |
    +-------------+--------------------+
    | "typedef"   | "doxygentypedef"   |
    +-------------+--------------------+
    | "union"     | "doxygenunion"     |
    +-------------+--------------------+
    | "variable"  | "doxygenvariable"  |
    +-------------+--------------------+

    The following breathe kinds are ignored:

    - "autodoxygenfile"
    - "doxygenindex"
    - "autodoxygenindex"

    Note also that although a return value is generated, neither "enumvalue" nor
    "group" are actually used.

    :Parameters:
        ``kind`` (str)
            The kind of the breathe compound / ExhaleNode object (same values).

    :Return (str):
        The directive to be used for the given ``kind``.  The empty string is returned
        for both unrecognized and ignored input values.
    '''
    return "doxygen{kind}".format(kind=kind)


def specificationsForKind(kind):
    '''
    Returns the relevant modifiers for the restructured text directive associated with
    the input kind.  The only considered values for the default implementation are
    ``class`` and ``struct``, for which the return value is exactly::

        "   :members:\\n   :protected-members:\\n   :undoc-members:\\n"

    Formatting of the return is fundamentally important, it must include both the prior
    indentation as well as newlines separating any relevant directive modifiers.  The
    way the framework uses this function is very specific; if you do not follow the
    conventions then sphinx will explode.

    Consider a ``struct thing`` being documented.  The file generated for this will be::

        .. _struct_thing:

        Struct thing
        ================================================================================

        .. doxygenstruct:: thing
           :members:
           :protected-members:
           :undoc-members:

    Assuming the first two lines will be in a variable called ``link_declaration``, and
    the next three lines are stored in ``header``, the following is performed::

        directive = ".. {}:: {}\\n".format(kindAsBreatheDirective(node.kind), node.name)
        specifications = "{}\\n\\n".format(specificationsForKind(node.kind))
        gen_file.write("{}{}{}{}".format(link_declaration, header, directive, specifications))

    That is, **no preceding newline** should be returned from your custom function, and
    **no trailing newline** is needed.  Your indentation for each specifier should be
    **exactly three spaces**, and if you want more than one you need a newline in between
    every specification you want to include.  Whitespace control is handled internally
    because many of the directives do not need anything added.  For a full listing of
    what your specifier options are, refer to the breathe documentation:

        http://breathe.readthedocs.io/en/latest/directives.html

    :Parameters:
        ``kind`` (str)
            The kind of the node we are generating the directive specifications for.

    :Return (str):
        The correctly formatted specifier(s) for the given ``kind``.  If no specifier(s)
        are necessary or desired, the empty string is returned.
    '''
    # use the custom directives function
    if configs.customSpecificationsMapping:
        return configs.customSpecificationsMapping[kind]

    # otherwise, just provide class and struct
    if kind == "class" or kind == "struct":
        return [":members:", ":protected-members:", ":undoc-members:"]

    return []  # use breathe defaults


class AnsiColors:
    '''
    A simple wrapper class for convenience definitions of common ANSI formats to enable
    colorizing output in various formats.  The definitions below only affect the
    foreground color of the text, but you can easily change the background color too.
    See `ANSI color codes <http://misc.flogisoft.com/bash/tip_colors_and_formatting>`_
    for a concise overview of how to use the ANSI color codes.
    '''
    BOLD          = "1m"
    ''' The ANSI bold modifier, see :ref:`utils.AnsiColors.BOLD_RED` for an example. '''
    DIM           = "2m"
    ''' The ANSI dim modifier, see :ref:`utils.AnsiColors.DIM_RED` for an example. '''
    UNDER         = "4m"
    ''' The ANSI underline modifier, see :ref:`utils.AnsiColors.UNDER_RED` for an example. '''
    INV           = "7m"
    ''' The ANSI inverted modifier, see :ref:`utils.AnsiColors.INV_RED` for an example. '''
    ####################################################################################
    BLACK         = "30m"
    ''' The ANSI black color. '''
    BOLD_BLACK    = "30;{bold}".format(bold=BOLD)
    ''' The ANSI bold black color. '''
    DIM_BLACK     = "30;{dim}".format(dim=DIM)
    ''' The ANSI dim black color. '''
    UNDER_BLACK   = "30;{under}".format(under=UNDER)
    ''' The ANSI underline black color. '''
    INV_BLACK     = "30;{inv}".format(inv=INV)
    ''' The ANSI inverted black color. '''
    ####################################################################################
    RED           = "31m"
    ''' The ANSI red color. '''
    BOLD_RED      = "31;{bold}".format(bold=BOLD)
    ''' The ANSI bold red color. '''
    DIM_RED       = "31;{dim}".format(dim=DIM)
    ''' The ANSI dim red color. '''
    UNDER_RED     = "31;{under}".format(under=UNDER)
    ''' The ANSI underline red color. '''
    INV_RED       = "31;{inv}".format(inv=INV)
    ''' The ANSI inverted red color. '''
    ####################################################################################
    GREEN         = "32m"
    ''' The ANSI green color. '''
    BOLD_GREEN    = "32;{bold}".format(bold=BOLD)
    ''' The ANSI bold green color. '''
    DIM_GREEN     = "32;{dim}".format(dim=DIM)
    ''' The ANSI dim green color. '''
    UNDER_GREEN   = "32;{under}".format(under=UNDER)
    ''' The ANSI underline green color. '''
    INV_GREEN     = "32;{inv}".format(inv=INV)
    ''' The ANSI inverted green color. '''
    ####################################################################################
    YELLOW        = "33m"
    ''' The ANSI yellow color. '''
    BOLD_YELLOW   = "33;{bold}".format(bold=BOLD)
    ''' The ANSI bold yellow color. '''
    DIM_YELLOW    = "33;{dim}".format(dim=DIM)
    ''' The ANSI dim yellow color. '''
    UNDER_YELLOW  = "33;{under}".format(under=UNDER)
    ''' The ANSI underline yellow color. '''
    INV_YELLOW    = "33;{inv}".format(inv=INV)
    ''' The ANSI inverted yellow color. '''
    ####################################################################################
    BLUE          = "34m"
    ''' The ANSI blue color. '''
    BOLD_BLUE     = "34;{bold}".format(bold=BOLD)
    ''' The ANSI bold blue color. '''
    DIM_BLUE      = "34;{dim}".format(dim=DIM)
    ''' The ANSI dim blue color. '''
    UNDER_BLUE    = "34;{under}".format(under=UNDER)
    ''' The ANSI underline blue color. '''
    INV_BLUE      = "34;{inv}".format(inv=INV)
    ''' The ANSI inverted blue color. '''
    ####################################################################################
    MAGENTA       = "35m"
    ''' The ANSI magenta (purple) color. '''
    BOLD_MAGENTA  = "35;{bold}".format(bold=BOLD)
    ''' The ANSI bold magenta (purple) color. '''
    DIM_MAGENTA   = "35;{dim}".format(dim=DIM)
    ''' The ANSI dim magenta (purple) color. '''
    UNDER_MAGENTA = "35;{under}".format(under=UNDER)
    ''' The ANSI underlined magenta (purple) color. '''
    INV_MAGENTA   = "35;{inv}".format(inv=INV)
    ''' The ANSI inverted magenta (purple) color. '''
    ####################################################################################
    CYAN          = "36m"
    ''' The ANSI cyan color. '''
    BOLD_CYAN     = "36;{bold}".format(bold=BOLD)
    ''' The ANSI bold cyan color. '''
    DIM_CYAN      = "36;{dim}".format(dim=DIM)
    ''' The ANSI dim cyan color. '''
    UNDER_CYAN    = "36;{under}".format(under=UNDER)
    ''' The ANSI underline cyan color. '''
    INV_CYAN      = "36;{inv}".format(inv=INV)
    ''' The ANSI inverted cyan color. '''
    ####################################################################################
    WHITE         = "37m"
    ''' The ANSI white color. '''
    BOLD_WHITE    = "37;{bold}".format(bold=BOLD)
    ''' The ANSI bold white color. '''
    DIM_WHITE     = "37;{dim}".format(dim=DIM)
    ''' The ANSI dim white color. '''
    UNDER_WHITE   = "37;{under}".format(under=UNDER)
    ''' The ANSI underline white color. '''
    INV_WHITE     = "37;{inv}".format(inv=INV)
    ''' The ANSI inverted white color. '''

    @classmethod
    def printAllColorsToConsole(cls):
        ''' A simple enumeration of the colors to the console to help decide :) '''
        for elem in cls.__dict__:
            # ignore specials such as __class__ or __module__
            if not elem.startswith("__"):
                color_fmt = cls.__dict__[elem]
                if type(color_fmt) is str and color_fmt != "BOLD" and color_fmt != "DIM" and \
                        color_fmt != "UNDER" and color_fmt != "INV":
                    print("\033[{fmt}AnsiColors.{name}\033[0m".format(fmt=color_fmt, name=elem))


def indent(text, prefix, predicate=None):
    '''
    This is a direct copy of ``textwrap.indent`` for availability in Python 2.

    Their documentation:

    Adds 'prefix' to the beginning of selected lines in 'text'.
    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    '''
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)

    return ''.join(prefixed_lines())


def prefix(token, msg):
    '''
    Wrapper call to :func:`exhale.utils.indent` with an always-true predicate so that
    empty lines (e.g. `\\n`) still get indented by the ``token``.

    :Parameters:
        ``token`` (str)
            What to indent the message by (e.g. ``"(!) "``).

        ``msg`` (str)
            The message to get indented by ``token``.

    :Return:
        ``str``
            The message ``msg``, indented by the ``token``.
    '''
    return indent(msg, token, predicate=lambda x: True)


def exclaim(err_msg):
    '''
    Helper method for :func:`Controller.critical`, inserts a leading `(!) `
    (with a trailing space) to every line of the input message.
    :Parameters:
        ``cls`` (class)
            The :class:`utilities.Controller` class.
        ``err_msg`` (str)
            The message to prepend `(!) ` to every line of.
    :Return (str):
        The input string with `(!) ` preceding every line.
    '''
    return "\n{}".format("(!) ").join("{}{}".format("(!) ", err_msg).splitlines())


def colorize(msg, ansi_fmt):
    return "\033[{0}{1}\033[0m".format(ansi_fmt, msg)


def _use_color(msg, ansi_fmt, output_stream):
    '''
    Based on :data:`exhale.configs.alwaysColorize`, returns the colorized or
    non-colorized output when ``output_stream`` is not a TTY (e.g. redirecting
    to a file).

    **Parameters**
        ``msg`` (str)
            The message that is going to be printed by the caller of this method.

        ``ansi_fmt`` (str)
            The ANSI color format to use when coloring is supposed to happen.

        ``output_stream`` (file)
            Assumed to be either ``sys.stdout`` or ``sys.stderr``.

    **Return**
        ``str``
            The message ``msg`` in color, or not, depending on both
            :data:`exhale.configs.alwaysColorize` and whether or not the
            ``output_stream`` is a TTY.
    '''
    if not configs.alwaysColorize and not output_stream.isatty():
        log = msg
    else:
        log = colorize(msg, ansi_fmt)
    return log


def progress(msg, ansi_fmt=AnsiColors.BOLD_GREEN, output_stream=sys.stdout):
    return _use_color(prefix("[+] ", msg), ansi_fmt, output_stream)


def info(msg, ansi_fmt=AnsiColors.BOLD_BLUE, output_stream=sys.stdout):
    return _use_color(prefix("[~] ", msg), ansi_fmt, output_stream)


def critical(msg, ansi_fmt=AnsiColors.BOLD_RED, output_stream=sys.stderr):
    return _use_color(prefix("(!) ", msg), ansi_fmt, output_stream)


def verbose_log(msg, ansi_fmt):
    if configs.verboseBuild:
        log = _use_color(msg, ansi_fmt, sys.stderr)
        sys.stderr.write("{log}\n".format(log=log))


def __fancy(text, language, fmt):
    if __USE_PYGMENTS:
        try:
            lang_lex = lexers.find_lexer_class_by_name(language)
            fmt      = formatters.get_formatter_by_name(fmt)
            highlighted = pygments.highlight(text, lang_lex(), fmt)
            return highlighted
        except:
            return text
    else:
        return text


def fancyErrorString():
    try:
        # fancy error printing aka we want the traceback, but
        # don't want the exclaimed stuff printed again
        err = traceback.format_exc()
        # shenanigans = "During handling of the above exception, another exception occurred:"
        # err = err.split(shenanigans)[0]
        return __fancy("{0}\n".format(err), "py3tb", "console")
    except:
        return "CRITICAL: could not extract traceback.format_exc!"


def fancyError(critical_msg=None, singleton_hook=None):
    if critical_msg:
        sys.stderr.write(critical(critical_msg))

    sys.stderr.write(fancyErrorString())

    if singleton_hook:
        # Only let shutdown happen once.  Useful for when singleton_hook may also create
        # errors (e.g. why you got here in the first place).
        fancyError.__defaults__ = (None, None)
        try:
            singleton_hook()
        except Exception as e:
            sys.stderr.write(critical(
                "fancyError: `singleton_hook` caused exception: {0}".format(e)
            ))

    os._exit(1)