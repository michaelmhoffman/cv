## variables
SRC = cv.md
PANDOC = pandoc
PANDOCFINAL = $(PANDOC) --standalone --smart

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL)

.PHONY: all

## pattern rules

%.docx : %.md
	$(PANDOCFINAL) $< -o $@

%.html : %.md
	$(PANDOCFINAL) --toc $< -o $@

%.json : %.md
	$(PANDOC) $< -o $@

cv-%.docx: cv.md %.yaml
	$(PANDOC) $< --smart --to=json | ./panfilter.py --config=$(*F).yaml | $(PANDOCFINAL) --from=json -o $@

## explicit rules

