# Code Conventions

## Ruff
We make use of the tool Ruff to enforce the majority of the rules in our code convention. For more information regarding what rules are enforced by Ruff, please check the [Ruff Settings File](https://github.com/zerohour-phishing-detection/zpd-server/blob/main/ruff.toml).

## Docstrings
We follow NumPy's docstring conventions, which can be found [here](https://numpydoc.readthedocs.io/en/latest/format.html).

Here is an example of a function documented in such manner:
```py
def do_stuff(a, b, c: int = 0) -> tuple[int, str]:
    """
    This function does some stuff.

    Transforms the given 3 integers into a tuple 
    in some manner.

    Parameters
    ----------
    a : int
        Description of parameter `a`.
    b
        Description of parameter `b` (with type not specified).
    c : int, default 0

    Returns
    -------
    d : int
        Non-zero value indicates error code, or zero on success.
    e : str
        Human readable error message
    """
```

## Indentation
We use 4 space for indentation.
