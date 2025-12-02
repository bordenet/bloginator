#!/bin/bash
set -e

source venv311/bin/activate

# Ensure blogs directory structure exists
mkdir -p blogs/final blogs/outlines

# Start continuous auto-responder
while true; do
    python3 scripts/auto_respond.py 2>&1 | grep "✓" || true
    sleep 0.5
done &
RESPONDER_PID=$!

trap "kill $RESPONDER_PID 2>/dev/null || true" EXIT

echo "=== Generating Sprint Planning blog ==="
rm -f blogs/outlines/sprint-planning.json blogs/final/sprint-planning.md
bloginator outline --index .bloginator/index \
    --keywords "sprint,planning,agile,scrum,estimation,story,points,capacity,commitment,velocity" \
    --title "Sprint Planning: Setting Teams Up for Success" \
    --thesis "Effective sprint planning balances team capacity with realistic commitments and clear objectives" \
    -o blogs/outlines/sprint-planning.json

bloginator draft --index .bloginator/index \
    --outline blogs/outlines/sprint-planning.json \
    -o blogs/final/sprint-planning.md

echo "=== Generating Sprint Grooming blog ==="
rm -f blogs/outlines/sprint-grooming.json blogs/final/sprint-grooming.md
bloginator outline --index .bloginator/index \
    --keywords "backlog,refinement,grooming,user,stories,acceptance,criteria,estimation" \
    --title "Sprint Grooming: The Art of Backlog Refinement" \
    --thesis "Effective backlog refinement prevents sprint planning chaos and enables predictable delivery" \
    -o blogs/outlines/sprint-grooming.json

bloginator draft --index .bloginator/index \
    --outline blogs/outlines/sprint-grooming.json \
    -o blogs/final/sprint-grooming.md

echo "=== Generating Sprint Retrospectives blog ==="
rm -f blogs/outlines/sprint-retros.json blogs/final/sprint-retros.md
bloginator outline --index .bloginator/index \
    --keywords "retrospective,continuous,improvement,team,feedback,action,items" \
    --title "Sprint Retrospectives: Continuous Improvement in Action" \
    --thesis "Regular retrospectives turn team experiences into actionable improvements" \
    -o blogs/outlines/sprint-retros.json

bloginator draft --index .bloginator/index \
    --outline blogs/outlines/sprint-retros.json \
    -o blogs/final/sprint-retros.md

kill $RESPONDER_PID 2>/dev/null || true

echo "=== All 3 blogs generated ==="
wc -w blogs/final/sprint-planning.md blogs/final/sprint-grooming.md blogs/final/sprint-retros.md
