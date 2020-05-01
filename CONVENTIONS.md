# PCBmodE coding conventions

## Formatting
For formatting we use `black`. This isn't perfect but makes it easy to maintain
consistency throughout the code and across developers. It's OK to break `black`
if absolutely necessary in order to maintain readability.

## Naming
For variable names use `lowercase_separated_by_underscores`. For Classes use
`UpperCamelCase`. For constants use `CAPITALIZED_WITH_UNDERSCORES`.

(Apply this as the code it refactored from previous conventions.)

## Prefixes and suffixes
In variable names, use the following suffixes to indicate what's in them

`_d` or `_dict` for dictionaries,
`_l` or `_list` for lists, and
`_p` or `_point` for instances of `Point()`.

When naming a path, suffix it with `_path` and prefix it with

`r_` for a relative path,
`p_` for a parsed path, and
`s_` for a string'd path.
