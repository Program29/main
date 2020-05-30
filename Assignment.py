class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

#It is possible to omit node for the linked list. I have the node in place only due to personal preference as it helps me to identify the data structure being inserted. Due to the item being known as a node and this being possible to omit for head and pathway as tail.
class Linkedlist:
    def __init__(self, newhead = None):
        self.tail = None
        self.head = newhead
        
#  The node and linkedlist class are actually the same code written twice. In node the data column represents head and the next column represents tail.

    def getHead(self):
        return self.head

    def setHead(self, newhead):
        self.head = newhead

    def get_next(self):
        return self.next

    def set_next(self, next):
        self.next = next

# I have insert get_next and set_next as I prefer the syntax to getHead and setHead.
    def setTail (self, newtail):
        self.tail = newtail
        
    def getTail(self):
        return self.tail
    

    def add(self, data):
        new_node = Node (data)
        if self. head is None:
            self.head = new_node
            return
        last_node = self.head
        while last_node.next:
            last_node = last_node.next
            last_node.next = new_node
#  This entry only searches the first item in the list to identify if it is empty. If it is empty it adds the entry.
#The complexity of adding one item to the beginning of the list is O(1) as there is only one node being searched and inserted into the list.
# The function add works by identify a new node is going to be inserted to the linked list.
# When the program is identified as head is none then it inserts a new head. This complexity is 0(1) as there is only one new head.
#The second part of this function looks for the last node as being next. This code can insert anywhere in the program as long as it can identify the last node. This can be complexity o(n) as there may be more than one last node and (n) represents the number of last nodes.
# The complexity seen here in the second part of this code can be O(n). This is because the probram needs to identify where the node is in the script and insert an entry into the place after the last node.
         
    def Delete (self, data):
        if self.head and self.head.data == data:
            self.head = self.head.next
            self.head = None
            return
        prev = None
        while self.head and self.head.data != data:
            prev = self.head
            self.head = self.head.next

        if self.head is None:
            return
        self.head = self.head.next
        self.head.next = None


               
        
        
#The complexity of removing the head of the list is O(1) because there is only one item at the head of the list.
        
# The code works by matching the searched item for deletion with the entry in the list. This then removes it from the head of the list.

        
# The code grows in complexity when the list requires searching before deletion. As a result the complexity incresaes to O(n) with (n) representing the numbers in the list.

#I have put deletion functions of removing the first entry in a linked list (o(1)), an entry anywhere in the list (o(n)) and the ability to move nodes to keep the linked list structure.

    def size(self):
        self.head = self.head
        count = 0
        while self.head:
            count += 1
            self.head = self.head.next
            return count 
    
    
#  This function identiifed as size looks for the size of the list by stating that the beginning is 0 and counting from there.
#  The complexity for this function is O(n) as it the program searches the linked list for the number of entries. In this instance (n) represents the entries.
    
    def Search (self, target):
        current = self.head
        while current != None:
            if self.head == target:
                print ("located")
                return True
            else:
                current = self.head.next ()
                print ("not located")
                return False
# The search function has a complexity of O(n) where (n) represents the number of nodes being searched in the linked list.
# The function starts at the list start or head and searches from there. If the search function finds the entry it lists as True.
# Technically if the start of the list was the item being searched the complexity would be O(1). This is because there would only be one item being searched.

            
        
bestlist = Linkedlist()
bestlist.add (5)
bestlist.add (6)
bestlist.add (7)
bestlist.Delete(5)