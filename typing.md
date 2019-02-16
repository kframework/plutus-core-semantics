Syntax
======

We separate the parsing of `Name` tokens from the rest of the synax to reduce conflicts when
defining rules:

```k
require "substitution.k"

module PLUTUS-CORE-TYPING-SYNTAX
    imports PLUTUS-CORE-SYNTAX-BASE

    syntax Name ::= r"[a-zA-Z][a-zA-Z0-9_']*" [notInRules, token, autoReject]
                  | #LowerId                  [notInRules, token, autoReject]
                  | #UpperId                  [notInRules, token, autoReject]
endmodule
```

```k
module PLUTUS-CORE-COMMON
    imports INT
    imports BUILTIN-ID-TOKENS

    syntax Name

    // TODO: This should not allow negative integers
    syntax Size ::= Int
endmodule
```

```k
module PLUTUS-CORE-SYNTAX-TYPES
    imports PLUTUS-CORE-COMMON

    syntax TyVar ::= Name

    syntax TyBuiltinName ::= Name
                           | "integer" | "bytestring" | "size"

    syntax TyConstant ::= Size
                        | TyBuiltinName

    syntax Type ::= TyVar
                  | "(" "fun" Type Type ")"       [seqstrict]
                  | "(" "all" TyVar Kind Type ")" [binder]
                  | "[" Type Type "]"             [klabel(tyapp), seqstrict]
                  | TyValue

    syntax TyValue ::= "(" "con" TyConstant ")"
                     | "(" "lam" TyVar Kind Type ")" [kabel(tylam)]
                     | NeutralTy

    syntax NeutralTy ::= TyVar
                       | "[" NeutralTy TyValue "]"

    syntax Kind ::= "(" "type" ")"
                  | "(" "size" ")"
                  | "(" "fun" Kind Kind ")"
endmodule
```

```k
module PLUTUS-CORE-SYNTAX-BASE
    imports PLUTUS-CORE-SYNTAX-TYPES

    syntax Var           ::= Name
    syntax BuiltinName   ::= Name

    syntax ByteString ::= r"\\#[a-fA-F0-9][a-fA-F0-9]*" [notInRules, token, autoReject]

    syntax BuiltinName   ::= NullaryBuiltin | BinaryBuiltin
                           | UnaryBuiltin | TernaryBuiltin
    syntax NullaryBuiltin ::= "txhash"
    syntax UnaryBuiltin   ::= "sha2_256" | "sha3_256"
                            | "blocknum"
    syntax BinaryBuiltin  ::= "addInteger"         | "subtractInteger"
                           |  "multiplyInteger"    | "divideInteger"
                           |  "quotientInteger"    | "remainderInteger"
                           |  "modInteger"
                           |  "lessThanInteger"    | "lessThanEqualsInteger"
                           |  "greaterThanInteger" | "greaterThanEqualsInteger"
                           |  "equalsInteger"
                           |  "resizeInteger"      | "sizeOfInteger"
                           |  "intToByteString"
                           |  "concatenate"        | "takeByteString"
                           |  "dropByteString"
                           |  "resizeByteString"   | "equalsByteString"
    syntax TernaryBuiltin ::= "verifySignature"

    syntax Version ::= r"[0-9]+(\\.[0-9]+)*" [token]

    syntax Constant ::= Size "!" Int
                      | Size "!" ByteString
                      | Size

    syntax Term ::= Var
                  | "{" Term Type "}"    [seqstrict]
                  | "[" Term Term "]"    [klabel(termapp), seqstrict]
                  | "(" "error" Type ")" [strict]
                  | Value

    syntax Value ::= "(" "abs" TyVar Kind Value ")" [binder]
                   | "(" "lam" Var Type Term ")"    [kabel(termlam), strict(2)]
                   | "(" "con" Constant ")"
                   | "(" "builtin" BuiltinName ")"

    syntax Program ::= "(" "program" Version Term ")"
endmodule
```

Typing
======

The configuration has the K cell, and an environment cell. The environment cell
holds the types and kinds of variables.

```k
module PLUTUS-CORE-TYPING-CONFIGURATION
    imports PLUTUS-CORE-SYNTAX-BASE

    configuration <k> $PGM:Program </k>
                  <env> .K </env>
```

Program version has no semantic meaning:

```k
    rule (program V TM) => TM
```

```k
    // `Term`s evaluate to their `Type`
    syntax Term ::= Type

    // `Type`s evaluate to `Type` with their `Kind`
    syntax KindedType ::= Type "::" Kind [klabel(kindedType)]
    syntax Type       ::= KindedType 
    syntax KResult    ::= KindedType
endmodule
```

Typing and kinding basic plutus constructs and builtins.

```k
module PLUTUS-CORE-TYPING-BUILTINS
    imports PLUTUS-CORE-TYPING-CONFIGURATION
    imports SUBSTITUTION

    // types of integer, bytestring, and size terms
    rule (con S ! _:Int) => #int((con S))
    rule (con S ! _:ByteString) => #bystr((con S))
    rule (con (S:Size):Constant) => #size((con S))

    // macros for basic types
    syntax Type ::= #int(Type)     [function]
                  | #size(Type)    [function]
                  | #bystr(Type)   [function]

    rule #int(T)   => tyapp((con integer), T)
    rule #size(T)  => tyapp((con size), T)
    rule #bystr(T) => tyapp((con bytestring), T)

    // kind of integer, bytestring and size
    rule (con integer)    => (con integer)    :: (fun (size) (type))
    rule (con bytestring) => (con bytestring) :: (fun (size) (type))
    rule (con size)       => (con size)       :: (fun (size) (type))

    // kind of size type
    rule (con S:Size):Type => (con S) :: (size)

    // macros for complex types
    syntax Type ::= "#bool"        [function]
                  | "#IntIntInt"   [function]
                  | "#IntIntBool"  [function]
                  | "#IntIntByStr" [function]
                  | "#sha"         [function]

    syntax TyVar ::= "$s" | "$s0" | "$s1" | "$s2" | "$a"

    rule #bool
      => (all $a (type)
           (fun $a (fun $a $a)))

    rule #IntIntInt
      => (all $s (size)
           (fun #int($s) (fun #int($s) #int($s))))

    rule #IntIntBool
      => (all $s (size)
           (fun #int($s) (fun #int($s) #bool)))

    rule #IntIntByStr
      => (all $s0 (size) (all $s1 (size)
           (fun #int($s0) (fun #bystr($s1) #bystr($s1)))))

    rule #sha
      => (all $s (size)
           (fun #bystr($s) #bystr((con 32))))

    // builtins
    rule (builtin addInteger)       => #IntIntInt
    rule (builtin subtractInteger)  => #IntIntInt
    rule (builtin multiplyInteger)  => #IntIntInt
    rule (builtin divideInteger)    => #IntIntInt
    rule (builtin quotientInteger)  => #IntIntInt
    rule (builtin remainderInteger) => #IntIntInt

    rule (builtin lessThanInteger)          => #IntIntBool
    rule (builtin lessThanEqualsInteger)    => #IntIntBool
    rule (builtin greaterThanInteger)       => #IntIntBool
    rule (builtin greaterThanEqualsInteger) => #IntIntBool
    rule (builtin equalsInteger)            => #IntIntBool

    rule (builtin resizeInteger)
      => (all $s0 (size) (all $s1 (size)
           (fun #size($s1) (fun #int($s0) #int($s1)))))

    rule (builtin sizeOfInteger)
      => (all $s (size) (fun #int($s) #size($s)))

    rule (builtin intToByteString)
      => (all $s0 (size) (all $s1 (size)
           (fun #size($s1) (fun #int($s0) #bystr($s1)))))

    rule (builtin concatenate)
      => (all $s (size)
           (fun #bystr($s) (fun #bystr($s) #bystr($s))))

    rule (builtin takeByteString) => #IntIntByStr
    rule (builtin dropByteString) => #IntIntByStr

    rule (builtin sha2_256) => #sha
    rule (builtin sha3_256) => #sha

    rule (builtin verifySignature)
      => (all $s0 (size) (all $s1 (size) (all $s2 (size)
           (fun #bystr($s0) (fun #bystr($s1) (fun #bystr($s2) #bool))))))

    rule (builtin resizeByteString)
      => (all $s0 (size) (all $s1 (size)
           (fun #size($s1) (fun #bystr($s0) #bystr($s1)))))

    rule (builtin equalsByteString)
      => (all $s (size)
           (fun #bystr($s) (fun #bystr($s) #bool)))

    rule (builtin txhash) => #bystr((con 32))

    rule (builtin blocknum)
      => (all $s (size)
           (fun #size($s) #int($s)))

endmodule
```

Typing and kinding all constructs according to Figures 4 and 5

```k
module PLUTUS-CORE-TYPING
    imports PLUTUS-CORE-TYPING-AUX

    // var, tyvar
    rule <k> X => #lookup(GAMMA, X) ... </k>
         <env> GAMMA </env>
      requires isVar(X) orBool isTyVar(X)

    // Used for manual heating and cooling.
    syntax Hole ::= "#HOLE"
    syntax Kind ::= Hole
    syntax Type ::= Hole
    syntax KResult ::= Hole

    // abs heating
    rule <k> (abs ALPHA K TM) => TM ~> (all ALPHA K #HOLE) ... </k>
         <env> (. => (ALPHA :: K)) ... </env>

    // tyall heating
    rule <k> (all ALPHA K TY) => TY ~> (all ALPHA K #HOLE) ... </k>
         <env> (. => (ALPHA :: K)) ... </env>

    // abs cooling, tyall cooling
    rule <k> TY:Type :: (type) ~> (all ALPHA K #HOLE) => (all ALPHA K TY) :: (type) ... </k>
         <env> ((ALPHA :: K) => .) ... </env>

    // tyapp
    rule tyapp(T1 :: (fun K1 K2), T2 :: K1)  => tyapp(T1, T2) :: K2

    // For K's builtin substitution to work properly
    syntax KVariable ::= TyVar

    // inst
    rule { ((all ALPHA K T) :: (type)) (A :: K) } => T[A / ALPHA]

    // lam heating
    rule <k> (lam X:Var (TY:Type :: (type)) TM:Term) => TM ~> (fun (TY :: (type)) #HOLE) ... </k>
         <env> (. => (X !! TY)) ... </env>

    // lam cooling
    rule <k> TY2 :: K ~> (fun (TY1 :: (type)) #HOLE) => (fun (TY1 :: (type)) (TY2 :: K)) ... </k>
         <env> ((X !! TY1) => .) ... </env>

    // tylam heating
    rule <k> (lam ALPHA:TyVar J:Kind TY:Type) => TY ~> (fun J #HOLE) ... </k>
         <env> (. => (ALPHA :: J)) ... </env>

    // tylam cooling
    rule <k> TY :: K ~> (fun J:Kind #HOLE) => (fun J K) ... </k>
         <env> ((ALPHA :: J) => .) ... </env>

    // tyfun
    rule (fun (TY1 :: (type)) (TY2 :: (type))) => (fun TY1 TY2) :: (type)

    // app
    rule termapp((fun T1:Type T2:Type) :: K1, T3 :: K2) => T2
      requires #alphaEquiv(T1, T3)

    // error
    rule (error A :: (type)) => A :: (type)
```

Reduction at the type level.

```k
    rule tyapp((lam ALPHA:TyVar J:Kind TY1:Type), TY2:Type) => TY1[TY2/ALPHA]
```

```k
endmodule
```

Auxiliary functions.

```k
module PLUTUS-CORE-TYPING-AUX
    imports PLUTUS-CORE-TYPING-CONFIGURATION
    imports PLUTUS-CORE-TYPING-BUILTINS
    imports LIST
    imports STRING
    imports ID

    // We use this notation in the environment to state a variable has a
    // certain type
    syntax KItem ::= Var "!!" Type

    // Lookup first occurrence variable in typing/kinding environment
    syntax K ::= #lookup(K, K)
    rule #lookup((ALPHA :: K) ~> REST:K, ALPHA) => ALPHA :: K
    rule #lookup((X:Var !! T) ~> REST:K, X    ) => T
    rule #lookup((ALPHA :: K) ~> REST:K, V    ) => #lookup(REST, V)
      requires ALPHA =/=K V
    rule #lookup((X:Var !! T) ~> REST:K, V    ) => #lookup(REST, V)
      requires X =/=K V

    // Alpha equivalence of types. K's matching does not know about alpha
    // equivalence, so we must do it manually (for now).
    syntax Bool ::= #alphaEquiv(Type, Type) [function]
    rule #alphaEquiv(ALPHA:TyVar, BETA:TyVar)  => true
    rule #alphaEquiv(T, T)                     => true
    rule #alphaEquiv([T1 T2], [T3 T4])         => #alphaEquiv(T1, T3) andBool #alphaEquiv(T2, T4)
    rule #alphaEquiv((fun T1 T2), (fun T3 T4)) => #alphaEquiv(T1, T3) andBool #alphaEquiv(T2, T4)
    rule #alphaEquiv((all ALPHA (type) T1), (all BETA (type) T2)) => #alphaEquiv(T1, T2)
    rule #alphaEquiv(T1, T2) => false [owise]

    syntax Name ::= freshName(Int)    [freshGenerator, function, functional]
    rule freshName(I:Int) => {#parseToken("Name", "_" +String Int2String(I))}:>Name

endmodule
```
