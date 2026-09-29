#InvestTrack DSA engine.
from collections import deque
import heapq


class HashTable:
    #Separate-chaining hash table
    def __init__(self, size=31):
        self.size = size
        self.table = [[] for _ in range(size)]

    def _index(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        bucket = self.table[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))

    def get(self, key, default=None):
        for k, v in self.table[self._index(key)]:
            if k == key:
                return v
        return default

    def contains(self, key):
        return self.get(key, None) is not None

    def items(self):
        for bucket in self.table:
            yield from bucket


class LinkedListNode:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    #Singly linked list used for ordered transaction history.
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def append(self, data):
        node = LinkedListNode(data)
        if self.head is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.length += 1

    def to_list(self):
        out, cur = [], self.head
        while cur:
            out.append(cur.data)
            cur = cur.next
        return out


class Stack:
    #LIFO stack for recent transaction/analysis history.
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def peek(self):
        return self.items[-1] if self.items else None

    def __len__(self):
        return len(self.items)


class OrderQueue:
    #FIFO queue representing paper orders before processing.
    def __init__(self):
        self.items = deque()

    def enqueue(self, order):
        self.items.append(order)

    def dequeue(self):
        return self.items.popleft() if self.items else None

    def __len__(self):
        return len(self.items)


class BSTNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class PriceBST:
    #Binary search tree indexed by stock price.
    def __init__(self):
        self.root = None

    def insert(self, key, value):
        def rec(node):
            if node is None:
                return BSTNode(key, value)
            if key < node.key:
                node.left = rec(node.left)
            else:
                node.right = rec(node.right)
            return node
        self.root = rec(self.root)

    def inorder(self):
        out = []
        def rec(node):
            if not node:
                return
            rec(node.left)
            out.append((node.key, node.value))
            rec(node.right)
        rec(self.root)
        return out


class SectorGraph:
    #Undirected graph connecting stocks that belong to the same sector.
    def __init__(self):
        self.adj = {}

    def add_edge(self, a, b):
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set()).add(a)

    def bfs(self, start):
        if start not in self.adj:
            return []
        visited, q, order = {start}, deque([start]), []
        while q:
            node = q.popleft(); order.append(node)
            for nxt in self.adj.get(node, ()):
                if nxt not in visited:
                    visited.add(nxt); q.append(nxt)
        return order


def insertion_sort(items, key=lambda x: x):
    arr = list(items)
    for i in range(1, len(arr)):
        current = arr[i]
        j = i - 1
        while j >= 0 and key(arr[j]) > key(current):
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = current
    return arr


def selection_sort(items, key=lambda x: x):
    arr = list(items)
    for i in range(len(arr)):
        smallest = i
        for j in range(i + 1, len(arr)):
            if key(arr[j]) < key(arr[smallest]):
                smallest = j
        arr[i], arr[smallest] = arr[smallest], arr[i]
    return arr


def merge_sort(items, key=lambda x: x):
    arr = list(items)
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key)
    right = merge_sort(arr[mid:], key)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    return out + left[i:] + right[j:]


def binary_search(items, target, key=lambda x: x):
    #Returns index of target in an already sorted list; O(log n).
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = key(items[mid])
        if value == target:
            return mid
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def max_heap_top(items, key=lambda x: x, limit=5):
    #Return top elements using a heap; O(n log k).
    heap = []
    for counter, item in enumerate(items):
        score = key(item)
        entry = (score, counter, item)
        if len(heap) < limit:
            heapq.heappush(heap, entry)
        elif score > heap[0][0]:
            heapq.heapreplace(heap, entry)
    return [item for _, _, item in sorted(heap, key=lambda e: e[0], reverse=True)]


def recursive_sum(values, index=0):
    """Simple recursive aggregation used to demonstrate recursion."""
    if index >= len(values):
        return 0
    return values[index] + recursive_sum(values, index + 1)
