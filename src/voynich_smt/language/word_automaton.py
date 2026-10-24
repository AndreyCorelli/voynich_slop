"""Minimal acyclic deterministic membership for a sorted finite word inventory."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WordAutomaton:
    # State zero is rejecting sink; missing edges go there. Children precede parents.
    root: int
    states: tuple[tuple[bool,tuple[tuple[str,int],...]],...]

    def accepts(self,word):
        state=self.root
        for symbol in word:
            state=dict(self.states[state][1]).get(symbol,0)
        return self.states[state][0]

    def accepted_word_count(self):
        counts=[]
        for i,(terminal,edges) in enumerate(self.states):
            if any(child>=i for _,child in edges):raise ValueError('Not an acyclic bottom-up automaton')
            counts.append(int(terminal)+sum(counts[child] for _,child in edges))
        return counts[self.root]

    @classmethod
    def from_sorted(cls,words):
        registry={};states=[(False,())];registry[(False,())]=0
        # Active prefix frontier only; frozen suffix states are shared.
        root=[False,{}];frontier=[root];previous='';seen=False
        def minimize(depth):
            for i in range(len(frontier)-1,depth,-1):
                node=frontier.pop();signature=(node[0],tuple(sorted(node[1].items())))
                state=registry.get(signature)
                if state is None:state=len(states);states.append(signature);registry[signature]=state
                frontier[-1][1][previous[i-1]]=state
        for word in words:
            if not isinstance(word,str) or not word:raise ValueError('Expected nonempty strings')
            if seen and word<=previous:raise ValueError('Words must be strictly sorted and unique')
            common=0
            for a,b in zip(previous,word):
                if a!=b:break
                common+=1
            minimize(common)
            for symbol in word[common:]:
                node=[False,{}];frontier[-1][1][symbol]=node;frontier.append(node)
            frontier[-1][0]=True;previous=word;seen=True
        if not seen:raise ValueError('Empty inventory')
        minimize(0);signature=(root[0],tuple(sorted(root[1].items())))
        state=registry.get(signature)
        if state is None:state=len(states);states.append(signature)
        return cls(state,tuple(states))
