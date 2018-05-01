# Settings
# --------

build_dir:=$(CURDIR)/.build
iele_submodule:=$(build_dir)/iele
k_submodule:=$(build_dir)/k
k_bin:=$(k_submodule)/k-distribution/target/release/k/bin

.PHONY: all clean build deps ocaml-deps iele \
        execution translation erc20 typing \
        test test-passing test-failing test-verify test-verify-commented \
        iele
        # Somehow SECONDEXPANSION and PHONY are interacting poorly, meaning these can't be PHONY
        # test-execution test-erc20 test-typing test-translation

all: build

clean:
	rm -rf .build

# Dependencies
# ------------

deps: $(k_bin)/krun ocaml-deps iele

%/.git: .git/HEAD
	git submodule update --recursive --init -- $(dir $*)

$(k_bin)/krun: $(k_submodule)/.git
	cd $(k_submodule) \
		&& mvn package -q -DskipTests

ocaml-deps:
	opam init --quiet --no-setup
	opam repository add k "$(k_submodule)/k-distribution/target/release/k/lib/opam" \
	    || opam repository set-url k "$(k_submodule)/k-distribution/target/release/k/lib/opam"
	opam update
	opam switch 4.03.0+k
	eval $$(opam config env) \
	opam install --yes mlgmp zarith uuidm

# Setting BYTE=true tells IELE to build staticly, avoiding incorrect setting
# of rpath in IELE's build scripts.
# We set `make deps`'s input to `/dev/null` to prevent IELE's opam
# invocation from asking us to modify our bashrc
iele: $(iele_submodule)/.git ocaml-deps
	bash -c '  . bin/activate                                                \
            && cd $(iele_submodule)                                          \
            && (   cd .build/secp256k1                                       \
                && ./autogen.sh                                              \
                && ./configure --prefix "$$PLUTUS_PREFIX"                    \
                               --enable-module-recovery --enable-module-ecdh \
                               --enable-experimental                         \
                && make                                                      \
                && make install)                                             \
            && make BYTE=yes deps </dev/null                                 \
            && make BYTE=yes '

# Build
# -----

# Allow expansion of $* in wildcard; See https://stackoverflow.com/questions/15948822/directory-wildcard-in-makefile-pattern-rule
.SECONDEXPANSION:

.build/%/plutus-core-kompiled/interpreter: src/%/plutus-core.k $(wildcard src/*.k) $$(wildcard src/$$*/*.k) $(k_bin)/krun
	eval $$(opam config env) \
	$(k_bin)/kompile --debug --verbose --directory .build/$*/ \
					 --syntax-module PLUTUS-CORE-SYNTAX src/$*/plutus-core.k
# Since the `interpreter` targets aren't explicitly mentioned as targets, it treats
# them as intermediate targets and deletes them when it is done. Marking
# them as PRECIOUS prevents this.
.PRECIOUS: .build/%/plutus-core-kompiled/interpreter

build: build-passing build-failing
build-passing: execution translation
build-failing: erc20 typing

execution:   .build/execution/plutus-core-kompiled/interpreter
translation: .build/translation/plutus-core-kompiled/interpreter
erc20:       .build/erc20/plutus-core-kompiled/interpreter
typing:      .build/typing/plutus-core-kompiled/interpreter

# Testing
# -------

test: test-passing test-failing
test-passing: translate-to-iele
	bash -c '. bin/activate && pytest --failed-first -n 4'
test-failing: test-erc20 test-verify test-verify-commented

execution_tests:=$(wildcard test/execution/*.plc)
erc20_tests:=$(wildcard test/erc20/*.plc)

translate_plc:=test/arith-ops.plc test/cmp-ops.plc test/case-simple.plc \
               test/recursion.plc test/modules.plc
translate-to-iele: $(translate_plc:.plc=.iele)
test-erc20: $(erc20_tests:=.test)

test/%.iele: test/%.plc .build/translation/plutus-core-kompiled/interpreter
	bash -c 'source bin/activate                                          && \
	         ./bin/kplc run translation $< | bin/config-to-iele > $@'

test-verify: .build/execution/plutus-core-kompiled/interpreter
	./bin/kplc prove execution verification/int-addition_spec.k             verification/dummy.plcore
	./bin/kplc prove execution verification/int-addition-with-import_spec.k verification/int-addition-lib.plcore
	./bin/kplc prove execution verification/equality_spec.k                 verification/dummy.plcore
	./bin/kplc prove execution verification/inequality_spec.k               verification/dummy.plcore
	./bin/kplc prove execution verification/sum_spec.k                      verification/sum.plcore
	./bin/kplc prove execution verification/const_spec.k                    verification/prelude.plc
	./bin/kplc prove execution verification/flip_spec.k                     verification/prelude.plc
	./bin/kplc prove execution verification/flip-no-prelude_spec.k          verification/dummy.plcore
	./bin/kplc prove execution verification/applyTo_spec.k                  verification/prelude.plc
	./bin/kplc prove execution verification/applyTo-no-prelude_spec.k       verification/dummy.plcore
	./bin/kplc prove execution verification/compose-no-prelude_spec.k       verification/dummy.plcore
	./bin/kplc prove execution verification/compose2-no-prelude_spec.k      verification/dummy.plcore
	./bin/kplc prove execution verification/curry_spec.k                    verification/prelude.plc
	./bin/kplc prove execution verification/curry-no-prelude_spec.k         verification/dummy.plcore
	./bin/kplc prove execution verification/uncurry_spec.k                  verification/prelude.plc
	./bin/kplc prove execution verification/swap_spec.k                     verification/prelude.plc
	./bin/kplc prove execution verification/maybe-nothing_spec.k            verification/prelude.plc
	./bin/kplc prove execution verification/maybe-just_spec.k               verification/prelude.plc

test-verify-commented: .build/execution/plutus-core-kompiled/timestamp
	./bin/kplc prove execution verification/id_spec.k                       verification/prelude.plc
	./bin/kplc prove execution verification/fst_spec.k                      verification/prelude.plc
	./bin/kplc prove execution verification/snd_spec.k                      verification/prelude.plc
	./bin/kplc prove execution verification/fromJust_spec.k                 verification/prelude.plc
	./bin/kplc prove execution verification/fromMaybe-nothing_spec.k        verification/prelude.plc
	./bin/kplc prove execution verification/fromMaybe-just_spec.k           verification/prelude.plc
	./bin/kplc prove execution verification/mapMaybe-nothing_spec.k         verification/prelude.plc
	./bin/kplc prove execution verification/mapMaybe-just_spec.k            verification/prelude.plc
	./bin/kplc prove execution verification/either-left_spec.k              verification/prelude.plc
	./bin/kplc prove execution verification/either-right_spec.k             verification/prelude.plc
	./bin/kplc prove execution verification/eitherToMaybe-left_spec.k       verification/prelude.plc
	./bin/kplc prove execution verification/eitherToMaybe-right_spec.k      verification/prelude.plc
	./bin/kplc prove execution verification/maybeToEither-nothing_spec.k    verification/prelude.plc
	./bin/kplc prove execution verification/maybeToEither-just_spec.k       verification/prelude.plc
