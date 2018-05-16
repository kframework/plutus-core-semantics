Plutus Core Semantics
=====================

This repository will contains the K Framework implementation of the core
language of the Plutus language ([a prototype of Plutus can be viewed
here](https://github.com/input-output-hk/plutus-prototype)).

Usage
-----

The `build` script is responsible for building and running tests.
For the first build, run `./build deps [options for pytest]`.
This will build all dependencies, including K, IELE and its dependencies,
and a `virtualenv` with `pytest` installed.

For subsequent builds run `./build [options for pytest]`.

To execute a Plutus program, run: `./build exec <pgm.plc> <module> <main> --args <args..>`,
where `<module>` is the module in which a function `<main>` is defined and 
`<args>` is a list of arguments to pass to that program with bytestrings prefixed
with a `#` character. For example, `./build exec test/arith-ops.pre.plc Foo add --args 5 6`.
The `<k>` cell will contain the return value of that function.

To translate to IELE, run: `./build trans <pgm.plc>`.

To Do
-----

### Execution

- Remove let, tests that involve let
- `define` can only take in a `Val` not a `Tm`. Some tests probably will fail
  but first we need to rewrite all tests to be syntactically valid now.
- Check if [test/execution/import-nonexistent.expected] should get stuck?

See tests marked `xfail` for more To-dos.

Issues
------


### Unresolved Issues

*. The behaviour of `takeByteString` of a non-zero value from the empty
   bytestring is not defined in the spec. We assume we should get stuck and
   fail?

* In IELE, the last contract is the public interface. Is something similar the case for Plutus modules?

### Resolved Issues

1. Is Prelude assumed to be imported always? If not, how do comparison operators work with returning something of type `(con Prelude.Bool)`
   - On the same note, should we be able to write `(define myTrue (Prelude.True))` without importing Prelude?

   > Nishant: All implementations of prelude must define data constructors
   > for `True` and `False`. Note that it does not specify behaviour for `combbuiltin` `blocktime`
   > needing `(con DateTime)`.

2. In `con` rule for `checks`, the condition with `forall` is not syntactically valid (does not parse as a `Type`). The application should be wrapped in `con`?
   > Answer: no, this judgment is not supposed to parse as a `Type`, it is just supposed to look like a `Type`

3. What do the Oxford (semantic) brackets mean?

   > Answer: `[[_]]` is shorthand for that unique `U` such that `T => U` (ie `T` evaluates to `U`)

6. Just to confirm, a program like `(define r [f 3])` is not valid?

   > Answer: No this is not valid. Execution is done with validator/redeemer and bind. Is there an example of this?

11. The spec has `Prelude.Boolean` but the prelude has `Prelude.Bool`

### Old Issues

1. Typo in the `abs` rule for `checks`, lower case `k` should be capital `K`.

4. In the CK machine, the ~5th to last rule has syntax of the form `case on ... of ...` which doesn't seem to be defined anywhere
5. 2nd sentence of Section IV: "... executes and leads true ..." should either be "leaves" or "leads to"

7. The `S'` is confusing in `case` rule for checks. Can you elaborate what this refers to?
8. \bar{alt} checks c \bar{T} used in a few place (`con-valid-local` for example) but not defined anywhere as far as I can tell
9. The spec has `(isa Ty Tm)` but the prelude has `(isa Tm Ty)`
10. The spec has `builtin addInt`, `builtin multiplyInt`, etc. but the prelude has `builtin addInteger`, etc.
12. Can you elaborate on what the \bar{S} and \bar{alpha} refers to in the `con` rule for checks and `case` rule? It seems it is related to the specific `Alt` that matches the constructor but this is not very clear and a bit confusing to me.
13. There doesn't seem to be any rule for `declare`. Related, I thought `define` should do a checking judgment against the declared type (if such a type exists), there doesn't seem to be a rule for this either.
14. Can you please point us to where in the spec judgments check for well-kindedness? For example should it be in the `isa` judgment?

In general, when new variables appear in the conditions of a rule that are not in the conclusion of a rule, it is often confusing as to where they came from, at least for me.
