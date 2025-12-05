#!/bin/bash
# ⚠️  DEPRECATED: This script uses the template-based auto-responder which
#    produces low-quality, generic content. Do NOT use for production blogs.
#
#    For quality blog generation, use BLOGINATOR_LLM_MOCK=assistant mode
#    with an AI assistant providing responses. See docs/QUICK_START_GUIDE.md.

set -e

# Emit deprecation warning
echo ""
echo "⚠️  WARNING: generate-batch-blogs.sh is DEPRECATED and produces low-quality content."
echo "   This script uses hardcoded template responses, not actual AI generation."
echo ""
echo "   For quality blogs, use the manual workflow with BLOGINATOR_LLM_MOCK=assistant."
echo "   See docs/QUICK_START_GUIDE.md for the recommended workflow."
echo ""
read -p "Press Enter to continue anyway (Ctrl+C to abort)..."

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load common functions and configuration
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_env_config

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "venv311" ]; then
    source venv311/bin/activate
else
    echo "Error: No virtual environment found at venv/ or venv311/"
    exit 1
fi

# Set up directories from config
GENERATED_DIR="${BLOGINATOR_OUTPUT_DIR}/generated"
INDEX_DIR="${BLOGINATOR_CHROMA_DIR}"
LLM_REQUESTS_DIR="${BLOGINATOR_DATA_DIR}/llm_requests"
LLM_RESPONSES_DIR="${BLOGINATOR_DATA_DIR}/llm_responses"
mkdir -p "$GENERATED_DIR"
AUTO_RESPOND_PY="${PROJECT_ROOT}/scripts/respond-to-llm-requests.py"

# Blog 2: Sprint Planning
echo "=== Generating Blog 2: Sprint Planning ==="
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator outline --index "$INDEX_DIR" \
  --keywords "sprint,planning,agile,scrum,estimation,story,points,capacity,commitment" \
  --title "Sprint Planning: Setting Teams Up for Success" \
  --thesis "Effective sprint planning balances team capacity with realistic commitments and clear objectives" \
  -o "$GENERATED_DIR/blog2-planning-outline.json" &
OUTLINE_PID=$!

sleep 3
python3 "$AUTO_RESPOND_PY"
wait $OUTLINE_PID

echo "Blog 2 outline complete, starting draft..."
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator draft --index "$INDEX_DIR" \
  --outline "$GENERATED_DIR/blog2-planning-outline.json" \
  -o "$GENERATED_DIR/blog2-sprint-planning.md" > /tmp/blog2.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 "$AUTO_RESPOND_PY" 2>&1 | grep "✓" || true
  sleep 1
  if [ -f "$GENERATED_DIR/blog2-sprint-planning.md" ] && [ $(wc -w < "$GENERATED_DIR/blog2-sprint-planning.md") -gt 1000 ]; then
    echo "Blog 2 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w "$GENERATED_DIR/blog2-sprint-planning.md"

# Blog 3: Sprint Grooming
echo "=== Generating Blog 3: Sprint Grooming ==="
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator outline --index "$INDEX_DIR" \
  --keywords "backlog,refinement,grooming,scrum,agile,stories,acceptance,criteria,estimation" \
  --title "Sprint Grooming: The Art of Backlog Refinement" \
  --thesis "Effective backlog refinement reduces planning time and increases sprint predictability" \
  -o "$GENERATED_DIR/blog3-grooming-outline.json" &
OUTLINE_PID=$!

sleep 3
python3 "$AUTO_RESPOND_PY"
wait $OUTLINE_PID

echo "Blog 3 outline complete, starting draft..."
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator draft --index "$INDEX_DIR" \
  --outline "$GENERATED_DIR/blog3-grooming-outline.json" \
  -o "$GENERATED_DIR/blog3-sprint-grooming.md" > /tmp/blog3.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 "$AUTO_RESPOND_PY" 2>&1 | grep "✓" || true
  sleep 1
  if [ -f "$GENERATED_DIR/blog3-sprint-grooming.md" ] && [ $(wc -w < "$GENERATED_DIR/blog3-sprint-grooming.md") -gt 1000 ]; then
    echo "Blog 3 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w "$GENERATED_DIR/blog3-sprint-grooming.md"

# Blog 4: Retrospectives
echo "=== Generating Blog 4: Retrospectives ==="
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator outline --index "$INDEX_DIR" \
  --keywords "retrospective,agile,scrum,improvement,feedback,team,process,kaizen" \
  --title "Sprint Retrospectives: Continuous Improvement in Action" \
  --thesis "Effective retrospectives turn team insights into actionable process improvements" \
  -o "$GENERATED_DIR/blog4-retro-outline.json" &
OUTLINE_PID=$!

sleep 3
python3 "$AUTO_RESPOND_PY"
wait $OUTLINE_PID

echo "Blog 4 outline complete, starting draft..."
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

bloginator draft --index "$INDEX_DIR" \
  --outline "$GENERATED_DIR/blog4-retro-outline.json" \
  -o "$GENERATED_DIR/blog4-sprint-retrospectives.md" > /tmp/blog4.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 "$AUTO_RESPOND_PY" 2>&1 | grep "✓" || true
  sleep 1
  if [ -f "$GENERATED_DIR/blog4-sprint-retrospectives.md" ] && [ $(wc -w < "$GENERATED_DIR/blog4-sprint-retrospectives.md") -gt 1000 ]; then
    echo "Blog 4 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w "$GENERATED_DIR/blog4-sprint-retrospectives.md"

echo "=== ALL BLOGS COMPLETE ==="
ls -lh "$GENERATED_DIR"/blog*.md | grep -v outline
