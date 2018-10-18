import numpy as np
import os, sys
import unittest
def append_to_path(dir0): # A convenience function
    if dir0 not in sys.path:
        sys.path.append(dir0)
append_to_path(os.getcwd()+'/..')
import pairio
 
class Test001(unittest.TestCase):
    def setUp(self):
      pass
        
    def tearDown(self):
        pass
     
    def test_001(self):
      key0='testkey'
      val0='testval000'
      pairio.set(key0,val0)
      val=pairio.get(key0)
      self.assertEqual(val,val0)
      pairio.set(key0,val0+'abc')
      val=pairio.get(key0)
      self.assertEqual(val,val0+'abc')


 
if __name__ == '__main__':
    unittest.main()
