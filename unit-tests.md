Here, we define unit tests as reachability claims.

```k
module SPEC-IDS
    imports BUILTIN-ID-TOKENS
    syntax Name ::= #LowerId [token, autoReject]
                  | #UpperId [token, autoReject]
endmodule
```

```k
module UNIT-TESTS-SPEC
    imports PLUTUS-CORE-LAZY
    imports SPEC-IDS
```

Lambda Calculus
---------------

Basic application:

```k
rule <k> [ (lam x a x) (con 1 ! 1) ] => (con 1 ! 1) </k>
     <env> .Map => .Map </env>
     <store> .Map => _ </store>

rule <k> [ (lam y a x) (con 1 ! 1) ] => x ~> .Map </k>
     <env> .Map => _ </env>
     <store> .Map => _ </store>
```

Nested application:

```k
rule <k> [[(lam x a (lam y b x)) (con 1 ! 0)] (con 2 ! 123)] => (con 1 ! 0) </k>
     <env> .Map => .Map </env>
     <store> .Map => _ </store>
```

Application uses capture-free substitution:

```k
rule <k> [ (lam x a (lam x b x)) (con 1 ! 1) ] => closure(_, x, x) </k>
     <env> .Map => .Map </env>
     <store> .Map => _ </store>
```

Integer arithmetic
------------------

Addition:

```k
rule [[(con addInteger) (con 1 ! 1) ] (con 1 ! 1) ] => (con 1 ! 2)
rule [[(con addInteger) (con 1 ! 66)] (con 1 ! 66)] => #failure
```

Subtraction:

```k
rule [[(con subtractInteger) (con 3 ! 10)] (con 3 ! 8) ] => (con 3 ! 2)
rule [[(con subtractInteger) (con 3 ! 7)] (con 3 ! 10) ] => (con 3 ! -3)
rule [[(con subtractInteger) (con 1 ! 66)] (con 1 ! -66) ] => #failure
```

Multiplication:

```k
rule [[(con multiplyInteger) (con 3 ! 10)] (con 3 ! 8) ] => (con 3 ! 80)
rule [[(con multiplyInteger) (con 1 ! 12)] (con 1 ! 11)] => #failure
```

Division:

```k
rule [[(con divideInteger) (con 3 ! 10)] (con 3 ! 3) ] => (con 3 ! 3)
rule [[(con divideInteger) (con 3 ! 0)] (con 3 ! 10) ] => (con 3 ! 0)
rule [[(con divideInteger) (con 2 ! 66)] (con 2 ! 0) ] => #failure
```

Remainder:

```k
rule [[(con remainderInteger) (con 3 ! 10)] (con 3 ! 3)] => (con 3 ! 1)
rule [[(con remainderInteger) (con 3 ! 0)]  (con 3 ! 10)] => (con 3 ! 0)
rule [[(con remainderInteger) (con 2 ! 66)] (con 2 ! 0) ] => #failure
```

Complex nested expressions:

```k
rule [[(con addInteger) [[(con remainderInteger) (con 3 ! 10)] (con 3 ! 3)]]
                            [[(con multiplyInteger ) (con 3 ! 2 )] (con 3 ! 2)]
         ]
      => (con 3 ! 5)

rule <k> [[(con addInteger) [[(con remainderInteger) (con 1 ! 10)] (con 1 ! 3)]]
                            [[(con multiplyInteger ) (con 1 ! 15 )] (con 1 ! 16)]
         ]
      => #failure ~> _ </k>

rule <k> [[(con addInteger) [[(con remainderInteger) (con 3 ! 66)] (con 3 ! 0)]]
                            [[(con multiplyInteger ) (con 3 ! 2 )] (con 3 ! 2)]
         ]
      => #failure ~> _ </k>

```

Less than:

```k
rule [[(con lessThanInteger) (con 3 ! 10)] (con 3 ! 3)]  => #false
rule [[(con lessThanInteger) (con 3 ! 3)] (con 3 ! 10)]  => #true
rule [[(con lessThanInteger) (con 3 ! 10)] (con 3 ! 10)] => #false
```

Less than or equal to:

```k
rule [[(con lessThanEqualsInteger) (con 3 ! 10)] (con 3 ! 3)]  => #false
rule [[(con lessThanEqualsInteger) (con 3 ! 3)] (con 3 ! 10)]  => #true
rule [[(con lessThanEqualsInteger) (con 3 ! 10)] (con 3 ! 10)] => #true
```

Greater than:

```k
rule [[(con greaterThanInteger) (con 3 ! 10)] (con 3 ! 3)]  => #true
rule [[(con greaterThanInteger) (con 3 ! 3)] (con 3 ! 10)]  => #false
rule [[(con greaterThanInteger) (con 3 ! 10)] (con 3 ! 10)] => #false
```

Greater than or equal to:

```k
rule [[(con greaterThanEqualsInteger) (con 3 ! 10)] (con 3 ! 3)]  => #true
rule [[(con greaterThanEqualsInteger) (con 3 ! 3)] (con 3 ! 10)]  => #false
rule [[(con greaterThanEqualsInteger) (con 3 ! 10)] (con 3 ! 10)] => #true
```

Equal to

```k
rule [[(con equalsInteger) (con 3 ! 10)] (con 3 ! 3)]  => #false
rule [[(con equalsInteger) (con 3 ! 3)] (con 3 ! 10)]  => #false
rule [[(con equalsInteger) (con 3 ! 10)] (con 3 ! 10)] => #true
```

Resize integer

```k
rule [[(con resizeInteger) (con 1)] (con 2 ! 100)] => (con 1 ! 100)
rule [[(con resizeInteger) (con 1)] (con 2 ! 128)] => #failure
```

Booleans & Unit
---------------

`#true`:

```k
rule <k> [[ [[(con equalsInteger) (con 3 ! 3)] (con 3 ! 3)]
              (lam x a (con 3 ! 1))] (lam x a (con 3 ! 2))]
       => (con 3 ! 1)
     </k>
     <env> .Map => .Map </env>
     <store> .Map => _ </store>
```

`#false`:

```k
rule <k> [[ [[(con equalsInteger) (con 3 ! 3)] (con 3 ! 2)]
             (lam x a (con 3 ! 1))] (lam x a (con 3 ! 2))]
       => (con 3 ! 2)
     </k>
     <env> .Map => .Map </env>
     <store> .Map => _ </store>
```

Bytestrings
-----------

```k
rule (con 2 ! #token("0",                "ByteString"):ByteString) => (con 2 !      0 : nilBytes)
rule (con 2 ! #token("00",               "ByteString"):ByteString) => (con 2 !      0 : nilBytes)
rule (con 2 ! #token("0000",             "ByteString"):ByteString) => (con 2 ! 0  : 0 : nilBytes)
rule (con 2 ! #token("1000",             "ByteString"):ByteString) => (con 2 ! 16 : 0 : nilBytes)
rule (con 8 ! #token("0123456789abcdef", "ByteString"):ByteString) => (con 8 ! 1 : 35 : 69 : 103 : 137 : 171 : 205 : 239 : nilBytes)
```

Integer to ByteString

```k
rule [[(con intToByteString) (con 1)] (con 2 ! 100)]
  => (con 1 ! 100 : nilBytes)
rule [[(con intToByteString) (con 3)] (con 2 ! 100)]
  => (con 3 ! 0 : 0 : 100 : nilBytes)
rule [[(con intToByteString) (con 5)] (con 2 ! 100)]
  => (con 5 ! 0 : 0 : 0 : 0 : 100 : nilBytes)
rule [[(con intToByteString) (con 1)] (con 2 ! 999)]
  => #failure
```

TODO: The behaviour of converting negative integers to bytestrings is not specified:

```k
// rule <k> [[(con intToByteString) (con 3)] (con 2 ! -100)]
//       => bytestring(3, TODO_WHAT_GOES_HERE : 0 : 0 : nilBytes) </k>
```

Concatentate:

```k
rule [ [ (con concatenate) (con 2 ! #token("01",   "ByteString"):ByteString) ]
                           (con 2 ! #token("03",   "ByteString"):ByteString) ]
  => (con 2 ! 01 : 03 : nilBytes)
rule [ [ (con concatenate) (con 2 ! #token("0102", "ByteString"):ByteString) ]
                           (con 2 ! #token("0304", "ByteString"):ByteString) ]
  => #failure
```

`takeByteString`
: returns the prefix of `xs` of length `n`, or `xs` itself if `n > length xs`.

```k
rule [[(con takeByteString) (con 1 ! 2)] (con 8 ! #token("0123456789abcdef", "ByteString"):ByteString)]
  => (con 8 ! 1 : 35 : nilBytes)
rule [[(con takeByteString) (con 1 ! 31)] (con 8 ! #token("0123456789abcdef", "ByteString"):ByteString)]
  => (con 8 ! 1 : 35 : 69 : 103 : 137 : 171 : 205 : 239 : nilBytes)
rule [[(con takeByteString) (con 1 ! 0)] (con 8 ! #token("0123456789abcdef", "ByteString"):ByteString)]
  => (con 8 ! nilBytes)
// This is the observed Haskell behaviour for negative lengths.
rule [[(con takeByteString) (con 1 ! -1)] (con 8 ! #token("0123456789abcdef", "ByteString"):ByteString)]
  => (con 8 ! nilBytes)
```

Resize ByteString

```k
rule [[(con resizeByteString) (con 3)] (con 5 ! #token("abcdef", "ByteString"):ByteString)]
  => (con 3 ! 171 : 205 : 239 : nilBytes )

rule [[(con resizeByteString) (con 5)] (con 3 ! #token("abcdef", "ByteString"):ByteString)]
  => (con 5 ! 171 : 205 : 239 : nilBytes )

rule <k> [[(con resizeByteString) (con 2)] (con 5 ! #token("abcdef", "ByteString"):ByteString)]
  => #failure ~> _ </k>
```

Equals (ByteStrings)

```k
rule [[(con equalsByteString) (con 3 ! #token("abcd", "ByteString"):ByteString)]
                              (con 3 ! #token("abcde", "ByteString"):ByteString)]
  => #false
rule [[(con equalsByteString) (con 3 ! #token("abcde", "ByteString"):ByteString)]
                              (con 3 ! #token("abcd", "ByteString"):ByteString)]
  => #false
rule [[(con equalsByteString) (con 2 ! #token("0001", "ByteString"):ByteString)]
                              (con 2 ! #token("01", "ByteString"):ByteString)]
  => #false
rule [[(con equalsByteString) (con 3 ! #token("abcd", "ByteString"):ByteString)]
                              (con 3 ! #token("abcd", "ByteString"):ByteString)]
  => #true
```

TODO: Bounds checking needs to happen separately in a well formedness check, so that terms that
never reach the top of the `K` cell are checked too.

```todo-well-formedness-check
rule (con 2 ! #token("00000", "ByteString"):ByteString) => #failure
rule <k> [[(con equalsByteString) (con 1 ! #token("abcd", "ByteString"):ByteString)]
                                  (con 1 ! #token("abcd", "ByteString"):ByteString)]
  => #failure ~> _ </k>
```


Cryptographic constructs
------------------------

```todo
rule <k> [(con sha2_256) (con 8 ! `0123456789abcdef)]
      // TODO: Verify that this is the correct SHA2
      => bytestring ( 256 , 85   : 197 : 63  : 93  : 73  : 2
                          : 151  : 144 : 12  : 239 : 168 : 37
                          : 208  : 200 : 232 : 233 : 83  : 46
                          : 232  : 161 : 24  : 171 : 231 : 216
                          : 87   : 7   : 98  : 205 : 56  : 190
                          : 152  : 24  : nilBytes)
    </k>                                                                            [specification]
```

Error Terms
-----------

```k
rule <k> [[(con addInteger) (con 1 ! 66)] (error (con integer))]     => (error (con integer))    </k>
rule <k> [[(con addInteger) (error (con integer))] (con 1 ! 66)]     => (error (con integer))    </k>
rule <k> [[(con resizeByteString) (con 3)] (error (con bytestring))] => (error (con bytestring)) </k>
```

```k
endmodule
```
