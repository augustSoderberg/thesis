class PriorityQueue:
    def __init__(self, capacity):
        self.heap = [None] * capacity
        self.capacity = capacity
        self.size = 0

    def push(self, id, priority):
        for i in range(self.size):
            if self.heap[i].id == id:
                if priority < self.heap[i].priority:
                    self.heap[i].priority = priority
                    self.heapify_up(i)
                    return True
                else:
                    return False
        if self.capacity <= self.size + 1:
            self.heap.append(None)
        self.heap[self.size] = PriorityQueueElement(id, priority)
        self.heapify_up(self.size)
        self.size += 1
        return True
    
    def heapify_up(self, index):
        if index != 0 and self.heap[(index - 1) // 2].priority > self.heap[index].priority:
            temp = self.heap[index]
            self.heap[index] = self.heap[(index - 1) // 2]
            self.heap[(index - 1) // 2] = temp
            self.heapify_up((index - 1) // 2)
    
    def heapify_down(self, index):
        if index < (self.size + 1) // 2:
            if self.heap[index].priority > self.heap[(index * 2) + 1].priority \
                    or ((index * 2) + 2 < self.size \
                    and self.heap[index].priority > self.heap[(index * 2) + 2].priority):
                min_index = (index * 2) + 1
                if ((index * 2) + 2 and self.heap[min_index].priority > self.heap[min_index + 1].priority):
                    min_index += 1
                temp = self.heap[index]
                self.heap[index] = self.heap[min_index]
                self.heap[min_index] = temp
                self.heapify_down(min_index)

    def pop(self):
        if self.size == 0:
            return None
        self.size -= 1
        rtn = self.heap[0]
        self.heap[0] = self.heap[self.size]
        self.heapify_down(0)
        return (rtn.id, rtn.priority)
    
    def peek(self):
        if self.size == 0:
            return None
        else:
            return (self.heap[0].id, self.heap[0].priority)

class PriorityQueueElement:
    def __init__(self, id, priority):
        self.priority = priority
        self.id = id