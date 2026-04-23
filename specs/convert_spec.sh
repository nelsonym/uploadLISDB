#!/usr/bin/env bash
set -euo pipefail

DOCX_FILE="${1:-SpecsUploadingLISDatav1.02.docx}"
OUTPUT_MD="${2:-SpecsUploadingLISDatav1.02.clean.md}"
BUILD_DIR="${3:-build}"

mkdir -p "$BUILD_DIR"

AST_JSON="$BUILD_DIR/spec.ast.json"
VALIDATION_JSON="$BUILD_DIR/spec.validation.json"
VALIDATION_MD="$BUILD_DIR/spec.validation.md"

generate_markdown() {
  pandoc "$DOCX_FILE" \
    --from=docx \
    --to=json \
    --output="$AST_JSON"

  pandoc "$AST_JSON" \
    --from=json \
    --to=gfm+pipe_tables \
    --lua-filter="normalize_styles.lua" \
    --lua-filter="clean_toc.lua" \
    --lua-filter="clean_lists.lua" \
    --lua-filter="table_layout.lua" \
    --lua-filter="numbering.lua" \
    --toc \
    --wrap=none \
    --columns=120 \
    --output="$OUTPUT_MD"

  python3 "postprocess_markdown.py" "$OUTPUT_MD" "$DOCX_FILE"
}

run_validation() {
  python3 "validate_spec_output.py" \
    "$DOCX_FILE" \
    "$OUTPUT_MD" \
    "$VALIDATION_JSON" \
    "$VALIDATION_MD"
}

generate_markdown

if ! run_validation; then
  echo "Validation failed on first pass. Re-running post-processing and validation once more..."
  python3 "postprocess_markdown.py" "$OUTPUT_MD" "$DOCX_FILE"
  if ! run_validation; then
    echo "Validation still failing. Review: $VALIDATION_MD"
    exit 1
  fi
fi

echo "Generated: $OUTPUT_MD"
echo "Validation report: $VALIDATION_MD"
