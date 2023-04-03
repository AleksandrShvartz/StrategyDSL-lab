import unittest

from dsl.interpreter import simple_transform, parse_file


class TestTranslator(unittest.TestCase):

    def test_simple(self):
        code = simple_transform()
        self.assertEqual(code, 'import numpy as np\nreturn  0 ')

    def test_mordovin_simple(self):
        s_test = '''NUM score1 = 0
NUM score2 = 0
NUM tmp = 0
FOREACH i IN RANGE(0, 6){
IF GET(i) > 6 - i {
    tmp = 6 - i
}
ELSE{
    tmp = GET(i)
    }
score1 += tmp
GET(i) -= tmp

IF GET(i) > 6{
    tmp = 6
    }
ELSE{
    tmp = GET(i)
}
score2 += tmp
GET(i) -= tmp
NUM mult = 0
IF (GET(i) > 13){
    mult = state[i] DIV 13
}
score1 += mult * 7
score2 += mult * 6
GET(i) -= mult * 13

IF (GET(i) > 7){
    score1 += 7
    score2 += GET(i) - 7
}
ELSE{
    score1 += GET(i)
    }
}
RETURN (GET(6) - GET(13)) * 14 + score1 - score2'''
        actual = '''import numpy as np
score1 = 0 
score2 = 0 
tmp = 0 
for i in range(0, 6)  : 
    if state[i]> 6 - i  : 
        tmp = 6 - i 
        
    else : 
        tmp = state[i]
        
    score1 += tmp 
    state[i]-= tmp 
    
    if state[i]> 6  : 
        tmp = 6 
        
    else : 
        tmp = state[i]
        
    score2 += tmp 
    state[i]-= tmp 
    mult = 0 
    if (GET(i) > 13)  : 
        mult = state[i] // 13 
        
    score1 += mult * 7 
    score2 += mult * 6 
    state[i]-= mult * 13 
    
    if (GET(i) > 7)  : 
        score1 += 7 
        score2 += state[i]- 7 
        
    else : 
        score1 += state[i]
        
    
return (GET(6) - state[13)]* 14 + score1 - score2 '''
        res = simple_transform(s_test)
        self.assertEqual(res, actual)
    def test_file_simple(self):
        actual = '''import numpy as np
score1 = 0 
score2 = 0 
tmp = 0 
for i in range(0, 6)  : 
    if state[i]> 6 - i  : 
        tmp = 6 - i 
        
    else : 
        tmp = state[i]
        
    score1 += tmp 
    state[i]-= tmp 
    
    if state[i]> 6  : 
        tmp = 6 
        
    else : 
        tmp = state[i]
        
    score2 += tmp 
    state[i]-= tmp 
    mult = 0 
    if (GET(i) > 13)  : 
        mult = state[i] // 13 
        
    score1 += mult * 7 
    score2 += mult * 6 
    state[i]-= mult * 13 
    
    if (GET(i) > 7)  : 
        score1 += 7 
        score2 += state[i]- 7 
        
    else : 
        score1 += state[i]
        
    
return ( state[6]- state[13]) * 14 + score1 - score2 '''
        # s_test_file = parse_file('C:\\Users\\Aleksandr\\Documents\\HW\\8\\DSL\\discr-game-lab\\mail_test\\test.str')
        with open('C:\\Users\\Aleksandr\\Documents\\HW\\8\\DSL\\discr-game-lab\\mail_test\\test.str', "r") as f:
            s_test = f.read()
        res = simple_transform(s_test)
        self.assertEqual(res, actual)

if __name__ == '__main__':
    unittest.main()