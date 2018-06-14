# Chomsky Grammar Tools


## I - Definition:

An application,
with graphical interface to manipulate GLC,
involving the following checks / operations:
1. Edit GLC's verbatim;
2. Check whether L (G) is empty, finite or infinite;
3. Transform a GLC into Own GLC,
   providing: Intermediate grammars, NF, Vi, Ne and NA;
4. Calculate First (A),
   Follow (A) and First-NT (A) (defined as the set of symbols of Vn that can start sequences derived from A) for all A ∈ Vn;
5. Check if G is factored or if it is factorial in n steps;
6. Check whether or not G has Rec.
   the Left - identifying the recursive non-terminals on the left and the type of recursions (direct and / or indirect) and, if it has,
   eliminate recursions.


## II - Observations:
1. Represent the GLC in a textual way, following the pattern of the examples below:
    ### a)
    ```
    E -> E + T | E-T | T
    T -> T * F | T / F | F
    F -> (E) | id
    ```

    ### B)
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
