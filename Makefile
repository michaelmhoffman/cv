## variables
SRC = cv.md
PANDOC = pandoc --standalone --smart

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL)

.PHONY: all

## pattern rules

%.docx : %.md
	$(PANDOC) $< -o $@

%.html : %.md
	$(PANDOC) --toc $< -o $@
