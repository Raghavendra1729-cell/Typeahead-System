import hashlib                                                                                                                    
import bisect                                                                                                                     
                                                                                                                                                                                                                                             
class ConsistentHash:                                                                                                             
    def __init__(self, nodes=None, replicas=100):                                                                                 
        """                                                                                                                       
        :param nodes: List of Redis node identifiers (e.g., connection strings).                                                  
        :param replicas: Number of virtual nodes per physical node for better distribution.                                       
        """                                                                                                                       
        self.replicas = replicas                                                                                                  
        self.ring = {}                                                                                                            
        self.sorted_keys = []                                                                                                     
                                                                                                                                    
        if nodes:                                                                                                                 
            for node in nodes:                                                                                                    
                self.add_node(node)                                                                                               
                                                                                                                                    
    def _hash(self, key: str) -> int:                                                                                             
        """Generates a consistent integer hash using MD5."""                                                                      
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)                                                              
                                                                                                                                    
    def add_node(self, node: str):                                                                                                
        """Adds a physical node and its virtual replicas to the hash ring."""                                                     
        for i in range(self.replicas):                                                                                            
            virtual_node_key = f"{node}:replica:{i}"                                                                              
            key_hash = self._hash(virtual_node_key)                                                                               
            self.ring[key_hash] = node                                                                                            
            bisect.insort(self.sorted_keys, key_hash)                                                                             
                                                                                                                                    
    def remove_node(self, node: str):                                                                                             
        """Removes a node and its virtual replicas from the hash ring."""                                                         
        for i in range(self.replicas):
            virtual_node_key = f"{node}:replica:{i}"
            key_hash = self._hash(virtual_node_key)
            if key_hash in self.ring:
                del self.ring[key_hash]
                self.sorted_keys.remove(key_hash)

    def get_node(self, key: str) -> str:
        """Returns the appropriate node for a given string key (like a search prefix)."""
        if not self.ring:
            return None
        
        key_hash = self._hash(key)
        
        # Find the first node on the ring with a hash greater than or equal to the key's hash
        index = bisect.bisect_right(self.sorted_keys, key_hash)
        
        # If the key hash is greater than all node hashes, wrap around to the first node
        if index == len(self.sorted_keys):
            index = 0
            
        return self.ring[self.sorted_keys[index]]