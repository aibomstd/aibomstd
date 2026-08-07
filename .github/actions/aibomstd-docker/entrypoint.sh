#!/bin/bash
set -e

# Exit on any error, but allow functions to handle their own errors gracefully

echo "🔍 aibomstd Scanner (GitHub Actions Docker)"
echo "==========================================="

# Inputs
SCAN_PATH="${SCAN_PATH:-.}"
CONFIG_FILE="${CONFIG_FILE:-aibomstd.yml}"
POLICY_MODE="${POLICY_MODE:-warn}"
UPLOAD_ARTIFACT="${UPLOAD_ARTIFACT:-true}"
COMMENT_ON_PR="${COMMENT_ON_PR:-true}"
DATA_RESIDENCY_DECLARE="${DATA_RESIDENCY_DECLARE:-}"

# Outputs
AIBOM_FILE="aibom.json"
VIOLATIONS_FILE="/tmp/violations.json"
PR_COMMENT_FILE="/tmp/pr-comment.md"

echo "📋 Configuration:"
echo "  Scan path: $SCAN_PATH"
echo "  Config file: $CONFIG_FILE"
echo "  Policy mode: $POLICY_MODE"
echo "  Upload artifact: $UPLOAD_ARTIFACT"
echo "  Comment on PR: $COMMENT_ON_PR"
echo ""

# Step 1: Run aibomstd scan
echo "📍 Step 1: Scanning repository..."
cd "$SCAN_PATH"

SCAN_ARGS="scan . --output $AIBOM_FILE --format json"

# Add data residency declarations if provided
if [ -n "$DATA_RESIDENCY_DECLARE" ]; then
  IFS=',' read -ra DECLARES <<< "$DATA_RESIDENCY_DECLARE"
  for decl in "${DECLARES[@]}"; do
    SCAN_ARGS="$SCAN_ARGS --declare $decl"
  done
  echo "  Data residency declarations: $DATA_RESIDENCY_DECLARE"
fi

# Check if config file exists and include it
if [ -f "$CONFIG_FILE" ]; then
  SCAN_ARGS="$SCAN_ARGS --config $CONFIG_FILE"
  echo "  Using config: $CONFIG_FILE"
fi

echo "  Running: aibomstd $SCAN_ARGS"
aibomstd $SCAN_ARGS

if [ ! -f "$AIBOM_FILE" ]; then
  echo "❌ Scan failed: AIBOM not generated"
  exit 1
fi

echo "✅ AIBOM generated: $AIBOM_FILE"
echo ""

# Step 2: Run policy validation
echo "📍 Step 2: Validating policies..."

python3 /scripts/ci_runner.py \
  --aibom "$AIBOM_FILE" \
  --config "$CONFIG_FILE" \
  --output-violations "$VIOLATIONS_FILE" \
  --policy-mode "$POLICY_MODE"

VIOLATIONS_COUNT=0
RISK_SCORE=0

if [ -f "$VIOLATIONS_FILE" ]; then
  VIOLATIONS_COUNT=$(jq '.violations | length' "$VIOLATIONS_FILE" 2>/dev/null || echo 0)
  RISK_SCORE=$(jq '.risk_score' "$VIOLATIONS_FILE" 2>/dev/null || echo 0)
  echo "  Violations found: $VIOLATIONS_COUNT"
  echo "  Risk score: $RISK_SCORE/100"
else
  echo "  No violations found ✅"
fi

echo ""

# Step 3: Format GitHub output
echo "📍 Step 3: Formatting GitHub output..."

python3 /scripts/format_github.py \
  --aibom "$AIBOM_FILE" \
  --violations "$VIOLATIONS_FILE" \
  --output-comment "$PR_COMMENT_FILE" \
  --risk-score "$RISK_SCORE" \
  --violations-count "$VIOLATIONS_COUNT"

echo ""

# Step 4: Upload AIBOM as artifact
if [ "$UPLOAD_ARTIFACT" = "true" ]; then
  echo "📍 Step 4: Uploading AIBOM as artifact..."
  
  # Create artifact directory
  mkdir -p /tmp/aibomstd-artifacts
  cp "$AIBOM_FILE" /tmp/aibomstd-artifacts/aibom.json
  
  if [ -f "$VIOLATIONS_FILE" ]; then
    cp "$VIOLATIONS_FILE" /tmp/aibomstd-artifacts/violations.json
  fi
  
  # Set GitHub output for artifact path
  echo "aibom-json=/tmp/aibomstd-artifacts/aibom.json" >> $GITHUB_OUTPUT
  echo "✅ Artifacts prepared"
else
  echo "⏭️  Skipping artifact upload (disabled)"
fi

echo ""

# Step 5: Comment on PR
if [ "$COMMENT_ON_PR" = "true" ] && [ -n "$GITHUB_PR_NUMBER" ]; then
  echo "📍 Step 5: Commenting on PR #$GITHUB_PR_NUMBER..."
  
  # Read comment content
  if [ -f "$PR_COMMENT_FILE" ]; then
    COMMENT_BODY=$(cat "$PR_COMMENT_FILE")
    
    # Use GitHub API to post comment
    curl -X POST \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/$GITHUB_REPO/issues/$GITHUB_PR_NUMBER/comments" \
      -d "{\"body\":$(echo "$COMMENT_BODY" | jq -Rs .)}" \
      -s -o /dev/null
    
    echo "✅ Comment posted"
  fi
else
  echo "⏭️  Skipping PR comment (PR not detected or disabled)"
fi

echo ""

# Step 6: Set GitHub outputs
echo "📍 Step 6: Setting GitHub outputs..."
echo "violations-count=$VIOLATIONS_COUNT" >> $GITHUB_OUTPUT
echo "risk-score=$RISK_SCORE" >> $GITHUB_OUTPUT

echo ""
echo "==========================================="
echo "✅ aibomstd scan complete"
echo ""
echo "Summary:"
echo "  AIBOM: $AIBOM_FILE"
echo "  Violations: $VIOLATIONS_COUNT"
echo "  Risk score: $RISK_SCORE/100"

# Exit with error if policy mode is "fail" and violations found
if [ "$POLICY_MODE" = "fail" ] && [ "$VIOLATIONS_COUNT" -gt 0 ]; then
  echo ""
  echo "❌ Policy enforcement: CI will FAIL due to $VIOLATIONS_COUNT violation(s)"
  exit 1
fi

echo "✅ All checks passed"
exit 0
