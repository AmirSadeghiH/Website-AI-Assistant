import os; d1 = os.path.join(r'D:\ai-support-platform\.tmp-test', 'tmpABC123'); os.makedirs(d1, exist_ok=True)
try:
    open(os.path.join(d1,'x.txt'),'w').write('y'); print('tmp-named dir: OK')
except PermissionError:
    print('tmp-named dir: DENIED')
d2 = os.path.join(r'D:\ai-support-platform\.tmp-test', 'uuidA1B2C3'); os.makedirs(d2, exist_ok=True)
try:
    open(os.path.join(d2,'x.txt'),'w').write('y'); print('uuid-named dir: OK')
except PermissionError:
    print('uuid-named dir: DENIED')
