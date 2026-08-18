# Build the CV without Overleaf.
#
#   make                 -> cv.pdf from resume.tex (local TeX Live)
#   make watch           -> rebuild on every save
#   make docker          -> build in a pinned TeX Live container instead
#   make install-fonts   -> one-time macOS setup (see FONTS below)
#   make clean           -> drop the build/ directory
#
# ENGINE: this document requires XeLaTeX. academicons selects its glyphs through
# the TU (Unicode) font encoding via fontspec, which pdfLaTeX cannot load -- it
# fails with "Encoding scheme `TU' unknown".
#
# FONTS: on macOS, XeTeX resolves fontspec font *names* through CoreText, which
# does not see TeX Live's private font tree, so a stock install fails with
# "I can't find file `FontAwesome'". Copying the two font files into
# ~/Library/Fonts fixes it; `make install-fonts` does exactly that. Linux (and
# therefore the container) resolves them via fontconfig and needs no such step.
#
# latexmk reruns XeLaTeX until the \label/\ref numbering behind \pubcite settles.

SRC      := resume.tex
OUT      := cv.pdf
BUILDDIR := build
PDF      := $(BUILDDIR)/$(SRC:.tex=.pdf)

# Pinned to 2025 to match the local Homebrew TeX Live; `latest` is TeX Live 2026
# and renders this document slightly differently.
DOCKER_IMAGE ?= texlive/texlive:TL2025-historic

LATEXMK := latexmk -xelatex -interaction=nonstopmode -halt-on-error \
           -file-line-error -outdir=$(BUILDDIR)

.PHONY: all watch docker clean install-fonts check

all: $(OUT) check

$(OUT): $(SRC)
	$(LATEXMK) $(SRC)
	@cp $(PDF) $(OUT)
	@echo "==> $(OUT)"

# Resume parsers keyword-match the PDF's text layer, and XeTeX emits f-ligatures
# as U+FB00.. which they do not decompose -- so "efficient" silently stops
# matching. Wrap any word listed here with \nolig (see resume.tex) and rebuild.
check:
	@command -v gs >/dev/null || { echo "check skipped (ghostscript not installed)"; exit 0; }
	@gs -q -dNOPAUSE -dBATCH -sDEVICE=txtwrite -sOutputFile=- $(OUT) 2>/dev/null \
	  | LC_ALL=en_US.UTF-8 grep -oE "[^[:space:]]*(ﬀ|ﬁ|ﬂ|ﬃ|ﬄ)[^[:space:]]*" \
	  | sort -u > $(BUILDDIR)/ligatures.txt || true
	@if [ -s $(BUILDDIR)/ligatures.txt ]; then \
	  echo "WARNING: unsearchable in the text layer -- wrap these with nolig:"; \
	  sed 's/^/    /' $(BUILDDIR)/ligatures.txt; \
	else \
	  echo "==> text layer is parser-clean"; \
	fi
	@printf '==> %s pages\n' "$$(gs -q -dNOPAUSE -dBATCH -sDEVICE=bbox $(OUT) 2>&1 | grep -c HiResBoundingBox)"

watch:
	$(LATEXMK) -pvc $(SRC)

docker:
	docker run --rm -v "$(CURDIR)":/work -w /work -u $$(id -u):$$(id -g) \
	  $(DOCKER_IMAGE) $(LATEXMK) $(SRC)
	@cp $(PDF) $(OUT)
	@echo "==> $(OUT) (container)"

install-fonts:
	@mkdir -p $$HOME/Library/Fonts
	@cp "$$(kpsewhich FontAwesome.otf)" $$HOME/Library/Fonts/
	@cp "$$(kpsewhich academicons.ttf)" $$HOME/Library/Fonts/
	@echo "==> installed FontAwesome.otf and academicons.ttf to ~/Library/Fonts"

clean:
	rm -rf $(BUILDDIR)
