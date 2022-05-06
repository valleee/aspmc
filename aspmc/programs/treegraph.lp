{ abs(X) :p(X)}.

parent(X,Y):- not abs(X), not abs(Y),edge(X,Y),not parent(Y,X).

:- parent(X,Y),parent(Z,Y), Z!=X.

r(X,Y):- parent(X,Y).
r(X,Y):- r(X,Z), parent(Z,Y). 

:- r(X,X). 

:~ abs(X). [1,X]

#show abs/1.
