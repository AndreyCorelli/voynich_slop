"""Shared constant transition/acceptance arrays and bounded word traversal."""
import z3


class AutomatonMembership:
    def __init__(self,automaton,alphabet):
        self.alphabet=alphabet;self.root=automaton.root
        self.transitions=z3.K(z3.IntSort(),z3.IntVal(0))
        self.accepting=z3.K(z3.IntSort(),z3.BoolVal(False))
        width=len(alphabet.symbols)
        for state,(terminal,edges) in enumerate(automaton.states):
            if terminal:self.accepting=z3.Store(self.accepting,state,True)
            for symbol,child in edges:
                self.transitions=z3.Store(self.transitions,state*width+alphabet.index(symbol),child)

    def membership(self,symbols,size):
        width=len(self.alphabet.symbols);state=z3.IntVal(self.root)
        padding=[]
        for i,symbol in enumerate(symbols):
            active=i<size
            padding.append(z3.If(active,z3.And(symbol>=0,symbol<width),symbol==width))
            state=z3.If(active,z3.Select(self.transitions,state*width+symbol),state)
        return z3.And(size>=1,size<=len(symbols),*padding,z3.Select(self.accepting,state))
