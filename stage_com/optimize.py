from clvm import KEYWORD_TO_ATOM


QUOTE_KW = KEYWORD_TO_ATOM["q"]
ARGS_KW = KEYWORD_TO_ATOM["a"]
EVAL_KW = KEYWORD_TO_ATOM["e"]


def seems_constant(sexp):
    if sexp.nullp() or not sexp.listp():
        return False
    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return True
        if as_atom == ARGS_KW:
            return False
    return all(seems_constant(_) for _ in sexp.rest().as_iter())


def constant_optimizer(r, eval_f):
    if seems_constant(r):
        r1 = eval_f(eval_f, r, r.null())
        r = r.to([QUOTE_KW, r1])
    return r


def eval_q_a_optimizer(r, eval_f):
    if r.nullp() or not r.listp():
        return r
    operator = r.first()
    if operator.listp():
        return r

    as_atom = operator.as_atom()
    if as_atom != EVAL_KW:
        return r
    first_arg = r.rest().first()
    if not first_arg.listp() or first_arg.nullp():
        return r
    op_2 = first_arg.first()
    if op_2.listp() or op_2.as_atom() != QUOTE_KW:
        return r
    if r.rest().rest().as_python() != [[ARGS_KW]]:
        return r
    return first_arg.rest().first()


def children_optimizer(r, eval_f):
    operator = r.first()
    if operator.listp():
        return r
    op = operator.as_atom()
    if op == QUOTE_KW:
        return r
    return r.to([op] + [optimize_sexp(_, eval_f) for _ in r.rest().as_iter()])


def optimize_sexp(r, eval_f):
    if r.nullp() or not r.listp():
        return r

    OPTIMIZERS = [
        constant_optimizer,
        eval_q_a_optimizer,
        children_optimizer,
    ]

    while True:
        start_r = r
        for opt in OPTIMIZERS:
            r = opt(r, eval_f)
        if start_r == r:
            return r


def do_opt(args, eval_f):
    return optimize_sexp(args.first(), eval_f)
