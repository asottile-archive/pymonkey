def pymonkey_patch(module):
    if module.__name__ != 'targetmod':
        return
    module.global_var = 2
