# Chomsky Grammar Tools for Context Free Grammars (CFG)

[![Build Status](https://travis-ci.org/evandrocoan/ContextFreeGrammars.svg?branch=master)](https://travis-ci.org/evandrocoan/ContextFreeGrammars)
[![Build status](https://ci.appveyor.com/api/projects/status/github/evandrocoan/ContextFreeGrammars?branch=master&svg=true)](https://ci.appveyor.com/project/evandrocoan/ContextFreeGrammars/branch/master)
[![codecov](https://codecov.io/gh/evandrocoan/ContextFreeGrammars/branch/master/graph/badge.svg)](https://codecov.io/gh/evandrocoan/ContextFreeGrammars)
[![Coverage Status](https://coveralls.io/repos/github/evandrocoan/ContextFreeGrammars/badge.svg?branch=master)](https://coveralls.io/github/evandrocoan/ContextFreeGrammars?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9191d17b91814f8caf17c9e537a22904)](https://www.codacy.com/app/evandrocoan/ContextFreeGrammars?utm_source=github.com&utm_medium=referral&utm_content=evandrocoan/ContextFreeGrammars&utm_campaign=badger)
[![Latest Release](https://img.shields.io/github/tag/evandrocoan/ContextFreeGrammars.svg?label=version)](https://github.com/evandrocoan/ContextFreeGrammars/releases)


## Installation/running

1. Clone this project: `git clone https://github.com/evandrocoan/ContextFreeGrammars`
1. Open a command line on the projects main folder: `cd ContextFreeGrammars`
1. Install its dependencies: `python -m pip install -r requirements.txt`
1. And run it with `python source/main.py`


## I - Definition:

An application,
with graphical interface to manipulate CFG,
involving the following operations:
1. Edit CFG's verbatim;
2. Check whether L (G) is empty, finite or infinite;
3. Transform a CFG into Proper CFG,
   providing: Intermediate grammars, Nf, Vi, Ne and Na;
4. Calculate First (A),
   Follow (A) and First-NT (A) (defined as the set of symbols of Vn that can start sequences derived from A) for all A ∈ Vn;
5. Check if G is factored or if it is factored in n steps;
6. Check whether or not G has Left Recursion - identifying the recursive non-terminals
   on the left and the type of recursions (direct and / or indirect) and,
   if it has left recursions,
   eliminate recursions.

![Imgur](https://i.imgur.com/5LDYWab.png)


## II - Observations:
1. Represent the CFG in a textual way, following the pattern of the examples below:

   **a)**
   ```
   E -> E + T | E-T | T
   T -> T * F | T / F | F
   F -> (E) | id
   ```

   **b)**
   ```
    E -> T E1
   E1 -> + T E1 | &
    T -> F T1
   T1 -> * F T1 | &
    F -> (E) | id
   ```
2. Leave a blank space between the symbols on the right.
3. Represent non-terminals by capital letter (followed by 0 or + digits).
4. Represent terminals with one or more contiguous characters (any characters,
   except uppercase letters).
5. Use & to represent epsilon.
6. Present the intermediate results obtained.


## Licensing

```python
#
# Chomsky Grammar Tools for Context Free Grammars (CFG)
# Copyright (C) 2018 Evandro Coan <https://github.com/evandrocoan>
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
```
