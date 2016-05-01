from pymonkey import make_entry_point


main = make_entry_point(('patchingmod',), 'targetmod')


if __name__ == '__main__':
    exit(main())
