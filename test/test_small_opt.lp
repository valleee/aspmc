p(a).
p(b).
edge(a,b).
edge(b,a).

% guess of backdoor vars
{ abs(X) } :- p(X).

in(X) :- not abs(X), p(X).

r(V,W) :- in(V), edge(V,W), in(W).
r(V,W) :- in(Y), edge(Y,W), r(V,Y).
:- r(V,V).


% limit abs costs
:~ abs(X). [1,X,b]
:~ p(X). [1,X,a]

