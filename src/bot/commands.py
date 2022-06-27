import json
from os import path
from types import CodeType, FunctionType
from twitchio.ext import commands as twitch

COMMANDS_FPATH = path.join(path.dirname(path.abspath(__file__)), "commands.json")


class Command(twitch.Command):
    def __init__(self, cmd_name, cmd_str):
        super().__init__(name=cmd_name, func=self.get_func(cmd_str))

    def get_func(self, command_string: str):
        def disassemble(command_string: str):
            def get_index(items, value):
                i = 1
                for item in items:
                    if value == item:
                        return i
                    i += 1
                print("Something went wrong!")

            _START = b"\x81\x01|\x00\xa0\x00"
            _END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
            NAME_START = b"|\x00"
            NAME_END = b"\x9b\x00"
            SPLIT_START = b"\xa0"
            SPLIT_END = b"\x19\x00"
            items = [item for item in command_string.split("$") if item != ""]
            consts = items[0::2]
            cii = []  # const int index
            names = []
            for x in items[1::2]:
                if x.startswith("{") and x.endswith("}"):
                    const = int(x.strip("{").strip("}"))
                    cii.append(len(consts))
                    consts.append(const)
                    if not ("message" in names and "content" in names and "split" in names):
                        names.append("message")
                        names.append("content")
                        names.append("split")
                else:
                    values = x.split(".")
                    for value in values:
                        if value not in names:
                            names.append(value)

            i = 0
            bytecode = [_START]
            for item in items:
                if item in consts:
                    bytecode.append(b"d" + bytes([get_index(consts, item)]))  # const n
                else:
                    bytecode.append(NAME_START)
                    if item.startswith("{") and item.endswith("}"):
                        for name in ["message", "content"]:
                            bytecode.append(b"j" + bytes([get_index(names, name)]))
                        bytecode.append(SPLIT_START)
                        bytecode.append(bytes([get_index(names, "split")]) + b"\xa1\x00")
                        bytecode.append(b"d" + bytes([get_index(consts, consts[cii[i]])]))  # const n
                        i += 1
                        bytecode.append(SPLIT_END)
                    else:
                        for name in item.split("."):
                            bytecode.append(b"j" + bytes([get_index(names, name)]))  # name n
                    bytecode.append(NAME_END)  # name end
            if len(items) > 1:
                bytecode.append(b"\x9d" + bytes([len(items)]))  # combine n values
            bytecode.append(_END)

            code = b"".join(bytecode)
            names.insert(0, "send")
            consts.insert(0, None)

            return (*names,), (*consts,), code

        names, consts, code = disassemble(command_string)
        code = self.get_code(
            _code=code,
            _consts=consts,
            _names=names,
        )

        return FunctionType(code, {})

    def get_code(self, _code, _consts, _names):
        co_argcount = 1
        co_posonlyargcount = 0
        co_kwonlyargcount = 0
        co_nlocals = 1
        co_stacksize = 5
        co_flags = 195
        co_code = _code
        co_consts = _consts
        co_names = _names
        co_varnames = ("ctx",)
        co_filename = ""
        co_name = ""
        co_firstlineno = 0
        co_lnotab = b"\x02\x02"
        co_freevars = ()
        co_cellvars = ()
        return CodeType(
            co_argcount,
            co_posonlyargcount,
            co_kwonlyargcount,
            co_nlocals,
            co_stacksize,
            co_flags,
            co_code,
            co_consts,
            co_names,
            co_varnames,
            co_filename,
            co_name,
            co_firstlineno,
            co_lnotab,
            co_freevars,
            co_cellvars,
        )


def attach_commands_from_file_to_bot(bot):
    with open(COMMANDS_FPATH, "r") as f:
        data = f.read()
    _json = json.loads(data)
    for cmd_name, cmd_str in _json.items():
        bot.add_command(Command(cmd_name, cmd_str))
    print("Commands loaded from file!")
