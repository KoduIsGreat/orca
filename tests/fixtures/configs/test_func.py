def do_something(arg1, arg2, arg3):
    return arg1 + arg2 + arg3


def do_something2(arg1, arg2):
    return arg1 + arg2


def do_something_dict(arg1, arg2):
    return {
        "sum": arg1 + arg2,
        "difference": arg1 - arg2,
        "product": arg1 * arg2,
        "quotient": arg1 / arg2,
    }


def do_something_no_return(dict):
    print(dict)


def do_something_no_args():
    return "wow"
