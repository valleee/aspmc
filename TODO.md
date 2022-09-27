- properly integrate a fvs solver
- in the cnf module:
    * replace the compile functionality with an evaluate function, which chooses the correct solving strategy based on the semiring and returns the solution
    * make it so that compile actually compiles the cnf
- in the semiring modules make it so that every idempotent semiring supports conversion to a maxsat problem itself
- PRIME IMPLICATES
- find out what causes the error in ./main.py -m problog -c test/test_smokers_10.lp -p -k miniC2D
- handle queries in asp mode
- when atoms are both guessed and entailed by the program, we run into errors. Ex.:
```
0.5::a.
a.
```
fix this by not only checking for multiple rules that probabilistically derive a but checking for multiple rules period.
- handle evidence for problog programs
- set probabilistics facts with probabilities 0/1 to false/true.
- use magic set transformation idea to reduce the size of the ground program
- remove temp files even when interrupted
- raise errors instead of doing exit(-1)
Maybe:
- timeout for compile()?
- handle cnfs that become trivial by unit propagation
