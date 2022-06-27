# Commands and twitchio

Adding commands using `twitchio` can be done in python as follows:

```python
from twitchio.ext import commands


@commands.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello {ctx.author.name}")
```

This is a problem as commands can only be added before runtime and and a basic function of a twitch bot is to have an `addcommand` command where commands are added at runtime.

## Adding twitchio commands 

Writing the function actions in bytecode allows use to bind functions to commands at runtime allowing for new commands to be added with an `addcommand` command.

We need to make custom commands that can still be understood by `twitchio`.

```python
from twitchio.ext import commands as twitch

class Command(twitch.Command):
    def __init__(self, _name, _func):
        super().__init__(name=_name, func=_func)
```

A twitchio command takes two arguments, name and func which are a types string and function respectivly.

We can create a function type using the `FunctionType` class from the `types` module. Before we can use `FunctionType` another type is required, `CodeType`.

```python
from types import FunctionType, CodeType
```

To for the new function to be accepted by `twitchio` the `CodeType` has the following properties that must be set as follows:

```python
argcount = 1        # Reffers to the number of elements in varnames
posonlyargcount = 0
kwonlyargcount = 0
nlocals = 1
flags = 195         # Is used to validate the type by twitchio
varnames = ("ctx",) # Parameters given to the function 
filename = ""       # abspath of the file the command comes from
name = ""           # name of the function
firstlineno = 0     # Line number the function is defined on
lnotab = b"\x02\x02"# ROT_TWO
freevars = ()
cellvars = ()
```

The following properties are set to define the actions the function takes:

```python
code    # :bytes: b"..."  
consts  # :tuple: None, ...
names   # :tuple: "send", ...
stacksize # :int: ...
```

The `code` property is the bytecode that manipulates the `consts` and `names` properties:
```python
b'\x81\x01|\x00\xa0\x00d\x01|\x00j\x01j\x02\x9b\x00\x9d\x02\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00'
```

The `consts` property is a tuple (that always starts with `None`) defining the order of the static values used in the return statment:
```python
(None, 'Hello ')
```

The `names` property is a tuple (that always starts `'send'`) followed by the methods used in the return statment: 
```python
('send', 'author', 'name')
```

The `stacksize` is the number of elements used in the return statment plus 2:
```python
await ctx.send(f"Hello World!")
stacksize = 3

await ctx.send(f"Hello World! @{ctx.author.name}")
stacksize = 4

await ctx.send(f"Hello World! @{ctx.author.name}!")
stacksize = 5

await ctx.send(f"@{ctx.author.name} said {ctx.message.content}!")
stacksize = 7
```

The only difficult part of writing commands in this form is forming the correct bytecode, which in python3 is quite tricky as there is currenty no module to write bytecode from a human-readable format. Thankfully we can still insepct the bytecode using a dissasembler in python.

## Bytecode

Using the `dis` python module we can get a better understanding of how the function is structured.

```python
import dis
dis.dis(b"\x81\x01|\x00\xa0\x00d\x01|\x00j\x01j\x02\x9b\x00\x9d\x02\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00") 
    0 GEN_START                1    
    2 LOAD_FAST                0 (0)
    4 LOAD_METHOD              0 (0)
    6 LOAD_CONST               1 (1)
    8 LOAD_FAST                0 (0)
    10 LOAD_ATTR                1 (1)
    12 LOAD_ATTR                2 (2)
    14 FORMAT_VALUE             0    
    16 BUILD_STRING             2    
    18 CALL_METHOD              1    
    20 GET_AWAITABLE
    22 LOAD_CONST               0 (0)
    24 YIELD_FROM
    26 POP_TOP
    28 LOAD_CONST               0 (0)
    30 RETURN_VALUE
```

All `twitchio` commands start with:
```python
dis.dis(b"\x81\x01|\x00\xa0\x00")

    0 GEN_START                1    
    2 LOAD_FAST                0 (0)
    4 LOAD_METHOD              0 (0)
```

and end with:
```python
dis.dis(b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00")
    0 CALL_METHOD              1    
    2 GET_AWAITABLE
    4 LOAD_CONST               0 (0)
    6 YIELD_FROM
    8 POP_TOP
    10 LOAD_CONST               0 (0)
    12 RETURN_VALUE
```

Which leave us with the rest to figure out:
```python
dis.dis(b"d\x01|\x00j\x01j\x02\x9b\x00\x9d\x02") 
    0 LOAD_CONST               1 (1)
    2 LOAD_FAST                0 (0)
    4 LOAD_ATTR                1 (1)
    6 LOAD_ATTR                2 (2)
    8 FORMAT_VALUE             0
    10 BUILD_STRING             2
```

To load a const value from the `consts` property:
```python
dis.dis(b"d\x01")
    0 LOAD_CONST               1 (1)
```

That means if we want a simple command to return `Hello World!` then the properties set would be as follows:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
code = _START + LOAD_CONST_1 + _END
consts=(None, "Hello World!"),
names=("send",),
stacksize=3
```

Now we want to be able to use variables from the twitch context like in the first command. The following will print the author name:


```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
code = _START + LOAD_NAME_1 + _END
consts=(None,),
names=("send", "author", "name"),
stacksize=3
```

### TODO: Add explaination for the combine values

Putting these two together:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
COMBINE_VALUES = b"\x9d\x02"
code = _START + LOAD_CONST_1 + LOAD_NAME_1 + COMBINE_VALUES + _END
consts=(None, "Hello World!"),
names=("send", "author", "name"),
stacksize=4
```

Now lets swap the values:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
COMBINE_2_VALUES = b"\x9d\x02"
code = _START  + LOAD_NAME_1 + LOAD_CONST_1 + COMBINE_2_VALUES + _END
consts=(None, "Hello World!"),
names=("send", "author", "name"),
stacksize=4
```

Now lets try to add another constant after the author name:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
COMBINE_3_VALUES = b"\x9d\x03"
code = _START  + LOAD_CONST_1 + LOAD_NAME_1 + LOAD_CONST_2 + COMBINE_3_VALUES + _END
consts=(None, "Hello ", "!"),
names=("send", "author", "name"),
stacksize=5
```

Now lets try to add the author name after the last constant again:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
COMBINE_4_VALUES = b"\x9d\x04"
code = _START  + LOAD_CONST_1 + LOAD_NAME_1 + LOAD_CONST_2 + LOAD_NAME_1 + COMBINE_4_VALUES + _END
consts=(None, "Hello ", "!"),
names=("send", "author", "name"),
stacksize=6
```

Now lets try to adding a differnt name after the last constant:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
LOAD_NAME_2 = b"|\x00j\x03j\x04\x9b\x00"
COMBINE_4_VALUES = b"\x9d\x04"
code = _START  + LOAD_CONST_1 + LOAD_NAME_1 + LOAD_CONST_2 + LOAD_NAME_2 + COMBINE_4_VALUES + _END
consts=(None, "Hello ", "!"),
names=("send", "author", "name", "message", "content"),
stacksize=7
```


Now lets try and split the message:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02"
LOAD_NAME_2 = b"|\x00j\x03j\x04"
SPLIT_NAME = b"\xa0\x05\xa1\x00d\x03\x19\x00"
END_NAME = b"\x9b\x00"
COMBINE_4_VALUES = b"\x9d\x04"
code = _START  + LOAD_CONST_1 + LOAD_NAME_1 + END_NAME + LOAD_CONST_2 + LOAD_NAME_2 + SPLIT_NAME + END_NAME + COMBINE_4_VALUES + _END
consts=(None, "Hello ", "!", 0),
names=("send", "author", "name", "message", "content", "split"),
stacksize=7
```

Now lets try reverse the variables:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02"
LOAD_NAME_2 = b"|\x00j\x03j\x04"
SPLIT_NAME = b"\xa0\x05\xa1\x00d\x03\x19\x00"
END_NAME = b"\x9b\x00"
COMBINE_4_VALUES = b"\x9d\x04"
code = _START  + LOAD_CONST_1 + LOAD_NAME_2 + SPLIT_NAME + END_NAME + LOAD_CONST_2 + LOAD_NAME_1 + END_NAME + COMBINE_4_VALUES + _END
consts=(None, "Hello ", "!", 0),
names=("send", "author", "name", "message", "content", "split"),
stacksize=7
```

This is the final version:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02"
LOAD_NAME_2 = b"|\x00j\x03j\x04"
SPLIT_START = b"\xa0"
SPLIT_INDEX = b"\x05"
SPLIT_INDEX_END = b"\xa1\x00"
SPLIT_VALUE_1 = b"d\x03"
SPLIT_END = b"\x19\x00"
END_NAME = b"\x9b\x00"
COMBINE_4_VALUES = b"\x9d\x04"
code = _START  + LOAD_CONST_1 + LOAD_NAME_1 + END_NAME + LOAD_CONST_2 + LOAD_NAME_2 + SPLIT_START + SPLIT_INDEX + SPLIT_INDEX_END + SPLIT_VALUE_1 + SPLIT_END + END_NAME + COMBINE_4_VALUES + _END
consts=(None, "Hello ", "!", 0, 1),
names=("send", "author", "name", "message", "content", "split"),
stacksize=7
```

<!-- Now lets put another const after the author name:
Putting these two together:
```python
_START = b"\x81\x01|\x00\xa0\x00"
_END = b"\xa1\x01I\x00d\x00H\x00\x01\x00d\x00S\x00"
LOAD_CONST_1 = b"d\x01"
LOAD_CONST_2 = b"d\x02"
LOAD_NAME_1 = b"|\x00j\x01j\x02\x9b\x00"
COMBINE_VALUES = b"\x9d\x02"
code = _START + LOAD_CONST_1 + LOAD_NAME_1 + COMBINE_VALUES + _END
consts=(None, "Hello "," !"),
names=("send", "author", "name"),
stacksize=4
``` -->
