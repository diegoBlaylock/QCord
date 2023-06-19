'''simple heap based priority queue

'''

import heapq
import itertools

class PQueue():
    
    def __init__(self):
        self.heap = []
        heapq.heapify(self.heap)
        self.counter = itertools.count()
        
    def add_task(self, task, priority=0):
        heapq.heappush(self.heap, [priority, next(self.counter), task])
        
    def pop_task(self):
        p, c, t = heapq.heappop(self.heap)
        return t
    
    def pull(self, amount=1):
        for _ in amount:
            if self.heap:
                yield self.pop_task()
                
    def __bool__(self):
        return bool(self.heap)
    
    def __len__(self):
        return len(self.heap)

if __name__ == "__main__":
    list = PQueue()
    
    for i in range(4).__reversed__():
        list.add_task(i)
        
        list.add_task(i+4, -1)
        
    while list:
        print(list.pop_task())