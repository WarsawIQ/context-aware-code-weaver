#!/usr/bin/env bash
# Minimalne asercje dla testow w bashu.
FAILED=0

assert_contains() {
  local file="$1" needle="$2" desc="$3"
  if grep -qF -- "$needle" "$file"; then
    echo "  ok: $desc"
  else
    echo "  FAIL: $desc — brak '$needle' w $file"
    FAILED=1
  fi
}

assert_not_contains() {
  local file="$1" needle="$2" desc="$3"
  if grep -qF -- "$needle" "$file"; then
    echo "  FAIL: $desc — nieoczekiwane '$needle' w $file"
    FAILED=1
  else
    echo "  ok: $desc"
  fi
}

assert_eq() {
  local actual="$1" expected="$2" desc="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  ok: $desc"
  else
    echo "  FAIL: $desc — jest '$actual', oczekiwano '$expected'"
    FAILED=1
  fi
}

finish() {
  if [[ "$FAILED" -eq 0 ]]; then
    echo "WSZYSTKO OK"
    exit 0
  fi
  echo "SA BLEDY"
  exit 1
}
