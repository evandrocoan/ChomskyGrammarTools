# Chomsky Grammar Tools for Context Free Grammars (CFG)


## I - Definition:

An application,
with graphical interface to manipulate CFG,
involving the following checks / operations:
1. Edit CFG's verbatim;
2. Check whether L (G) is empty, finite or infinite;
3. Transform a CFG into Proper CFG,
   providing: Intermediate grammars, Nf, Vi, Ne and Na;
4. Calculate First (A),
   Follow (A) and First-NT (A) (defined as the set of symbols of Vn that can start sequences derived from A) for all A ∈ Vn;
5. Check if G is factored or if it is factorial in n steps;
6. Check whether or not G has Rec.
   the Left - identifying the recursive non-terminals on the left and the type of recursions (direct and / or indirect) and, if it has,
   eliminate recursions.


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
7. The work should be done in pairs and the programming language is of free choice (however it must be dominated by the 2 members of the team).
8. The work must be sent by email until **27/06**,
   in a single zipped file,
   containing report (describing implementation), source (documented),
   executable and testing.
   Use the file name of the team components (ex.
   JoaoF-MariaG.zip).
9. In addition to the correctness,
   aspects of usability and robustness of the application will be evaluated.


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
