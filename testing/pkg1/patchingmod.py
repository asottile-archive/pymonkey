def pymonkey_patch(module, args):
    if module.__name__ != 'targetmod':
        return
    module.global_var = args.patch


def pymonkey_argparse(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--patch', default=2, type=int)
    return parser.parse_known_args(argv)
