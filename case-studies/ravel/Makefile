CC ?= cc
CFLAGS ?= -std=c11 -O3 -Wall -Wextra -Werror -pedantic
LDLIBS ?= -lm

.PHONY: test evidence training-test training-evidence training-check all clean

test: ravel
	./ravel >/dev/null

evidence: ravel
	./ravel | tee evidence.json

training-test: ravel_train
	./ravel_train >/dev/null

training-evidence: ravel_train
	./ravel_train | tee training-evidence.json

training-check: ravel_train
	@tmp=$$(mktemp); \
	trap 'rm -f "$$tmp"' EXIT; \
	./ravel_train > "$$tmp"; \
	diff -u training-evidence.json "$$tmp"

all: test training-check

ravel: ravel.c
	$(CC) $(CFLAGS) $< -o $@

ravel_train: ravel_train.c
	$(CC) $(CFLAGS) $< $(LDLIBS) -o $@

clean:
	rm -f ravel ravel_train evidence.json
