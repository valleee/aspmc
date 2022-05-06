
% guess of backdoor vars
0 { abs(X) : p(X)} B :- b(B).

in(X) :- not abs(X), p(X).

r(W,V,W) :- in(V), edge(V,W), in(W).
r(X,V,W) :- in(Y), edge(Y,X), r(Y,V,W), Y != W.
r(X,V,W) :- in(Y), edge(Y,X), r(Y,V,W), X != V.
:- r(V,V,_).


% limit abs costs
:~ abs(X). [1,X]


#show abs/1.