import hashlib
import io

from .EvalError import EvalError
from .casts import bls12_381_generator, bls12_381_to_bytes, bls12_381_from_bytes
from .serialize import sexp_from_stream, sexp_to_stream


def op_sha256(args):
    h = hashlib.sha256()
    for _ in args.as_iter():
        h.update(_.as_atom())
    return args.to(h.digest())


MASK_128 = ((1 << 128) - 1)


def truncate_int(v):
    v1 = abs(v) & MASK_128
    if v < 0:
        v1 = -v1
    return v1


def op_add(args):
    total = 0
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("+ takes integer arguments", args)
        total += r
    total = truncate_int(total)
    return args.to(total)


def op_subtract(args):
    if args.nullp():
        return args.to(0)
    sign = 1
    total = 0
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("- takes integer arguments", args)
        total += sign * r
        total = truncate_int(total)
        sign = -1
    return args.to(total)


def op_multiply(args):
    v = 1
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("* takes integer arguments", args)
        v = truncate_int(v * r)
    return args.to(v)


def op_unwrap(items):
    try:
        return sexp_from_stream(io.BytesIO(items.first().as_atom()), items.to)
    except (IndexError, ValueError):
        raise EvalError("bad stream", items)


def op_wrap(items):
    if items.nullp() or not items.rest().nullp():
        raise EvalError("wrap expects exactly one argument", items)
    f = io.BytesIO()
    sexp_to_stream(items.first(), f)
    return items.to(f.getvalue())


def op_pubkey_for_exp(items):
    if items.nullp() or not items.rest().nullp():
        raise EvalError("op_pubkey_for_exp expects exactly one argument", items)
    try:
        return items.to(bls12_381_to_bytes(bls12_381_generator * items.first().as_int()))
    except Exception as ex:
        raise EvalError("problem in op_pubkey_for_exp: %s" % ex, items)


def op_point_add(items):
    p = bls12_381_generator.infinity()
    for _ in items.as_iter():
        try:
            p += bls12_381_from_bytes(_.as_atom())
        except Exception as ex:
            raise EvalError("point_add expects blob, got %s: %s" % (_, ex), items)
    return items.to(bls12_381_to_bytes(p))