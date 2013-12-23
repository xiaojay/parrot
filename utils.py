#coding=utf-8
def trunc(f, n=5):
    if f is None:
        return 0
    a = 10 ** n
    return int(float(f) * a) * 1.0/a
