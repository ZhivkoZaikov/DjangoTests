def show_kwargs(a='', b='', **kwargs):
    print(kwargs)
    print(kw_arg['1'])
    if a:
        print(a)
    if b:
        print(b)


kw_arg = {'1': 23, '2': 45, '3': 11}

show_kwargs(a=5,b=3, **kw_arg)
data = {'abc': 123}
print(type(data))
print(list(data.keys())[0])
print(list(data.values())[0])
