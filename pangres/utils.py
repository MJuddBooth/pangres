# +
from __future__ import absolute_import
import pandas as pd
from pangres.logger import log
from itertools import izip

# -

# # Function to fix bad column names for psycopg2

def fix_psycopg2_bad_cols(df, replacements={'%':'', '(':'', ')':''}):
    """
    Replaces '%', '(' and ')' (characters that won't play nicely or even
    at all with psycopg2) in column and index names in a deep copy of df.
    This is a workaround for the unresolved issue
    described here: https://github.com/psycopg/psycopg2/issues/167

    **IMPORTANT**:
    You will need to apply the same changes in the database as
    well if the SQL table already exists for a given DataFrame.
    Otherwise you will for instance end up with a column
    "total_%" and "total_" in your SQL table.

    Parameters
    ----------
    df : pd.DataFrame
    replacements : dict {'%':str, '(':str, ')':str}, default {'%':'', '(':'', ')':''}
        The keys '%', '(' and ')' are mandatory.
        There cannot be any extra keys.

    Returns
    -------
    new_df : pd.DataFrame

    Examples
    --------
    * fix bad col/index names with default replacements (empty string for '(', ')' and '%')
    >>> import pandas as pd
    >>> df = pd.DataFrame({'test()':[0],
    ...                    'foo()%':[0]}).set_index('test()')
    >>> print(df.to_markdown())
    |   test() |   foo()% |
    |---------:|---------:|
    |        0 |        0 |

    >>> df_fixed = fix_psycopg2_bad_cols(df)
    >>> print(df_fixed.to_markdown())
    |   test |   foo |
    |-------:|------:|
    |      0 |     0 |

    * fix bad col/index names with custom replacements - you MUST provide replacements for '(', ')' and '%'!
    >>> import pandas as pd
    >>> df = pd.DataFrame({'test()':[0],
    ...                    'foo()%':[0]}).set_index('test()')
    >>> print(df.to_markdown())
    |   test() |   foo()% |
    |---------:|---------:|
    |        0 |        0 |

    >>> df_fixed = fix_psycopg2_bad_cols(df, replacements={'%':'percent', '(':'', ')':''})
    >>> print(df_fixed.to_markdown())
    |   test |   foopercent |
    |-------:|-------------:|
    |      0 |            0 |
    """
    # verify all index levels are named
    index_names = list(df.index.names)
    if any([ix_name is None for ix_name in index_names]):
        raise IndexError("All index levels must be named!")
    # verify duplicated columns
    fields = list(df.index.names) + df.columns.tolist()
    if len(set(fields)) != len(fields):
        raise ValueError(("There cannot be duplicated names amongst "
                          "index levels and/or columns!"))
    # verify replacements arg
    expected_keys = ('%', '(', ')')
    if ((not isinstance(replacements, dict)) or
        (set(replacements.keys()) - set(expected_keys) != set()) or 
        (len(replacements) != len(expected_keys))):
        raise TypeError('replacements must be a dict containing the following keys (and none other): {}'.format(expected_keys))
    if not all((isinstance(v, str) for v in replacements.values())):
        raise TypeError('The values of replacements must all be strings')
    # replace bad col names
    translator = dict((ord(k), v) for k, v in replacements.items())
    new_df = df.copy(deep=True)
    renamer = lambda col: col.translate(translator) if isinstance(col, str) else col
    new_df = new_df.rename(columns=renamer).rename_axis(index=renamer)
    # check columns are unique after renaming
    fields = list(new_df.index.names) + new_df.columns.tolist()
    if len(set(fields)) != len(fields):
        raise ValueError("Columns/index are not unique after renaming!")
    # compare columns (and index)
    before = df.reset_index().columns.tolist()
    after = new_df.reset_index().columns.tolist()
    changed = []
    for i, j in izip(before, after):
        if (isinstance(i, str) and isinstance(j, str)
            and i!=j):
            log('Renamed column/index "{}" to "{}s"'.format(i, j))
    return new_df


# # Test with doctest

if __name__ == '__main__':
    import doctest
    doctest.testmod()
