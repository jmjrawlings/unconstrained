# Build the book
build-book: FORCE
	jupyter-book build book

# Open Jupyer Lab
jupyter: FORCE
	jupyter lab \
		--allow-root \
		--notebook-dir ./unconstrained/examples


# Build the Book when source files change
watch-book:
	inotifywait \
		--quiet \
		--monitor \
		--event delete \
		--event close_write \
		--exclude __pycache__ \
		--exclude _build \
		book \
		| \
		while read dir event file; do \
			echo "${file} changed - building book" ; \
			make build-book ;\
		done

FORCE:

.phony: build-book watch-book FORCE