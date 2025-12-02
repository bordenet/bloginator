#!/bin/bash
set -e

source venv311/bin/activate

# Start continuous auto-responder
while true; do
    python3 scripts/auto_respond.py 2>&1 | grep "✓" || true
    sleep 0.5
done &
RESPONDER_PID=$!

trap "kill $RESPONDER_PID 2>/dev/null || true" EXIT

echo "=== Generating Sprint Planning blog ==="
rm -f blog2-sprint-planning-outline.json blog2-sprint-planning.md
bloginator outline --index output/index \
    --keywords "sprint,planning,agile,scrum,estimation,story,points,capacity,commitment,velocity" \
    --title "Sprint Planning: Setting Teams Up for Success" \
    --thesis "Effective sprint planning balances team capacity with realistic commitments and clear objectives" \
    -o blog2-sprint-planning-outline.json

bloginator draft --index output/index \
    --outline blog2-sprint-planning-outline.json \
    -o blog2-sprint-planning.md

echo "=== Generating Sprint Grooming blog ==="
rm -f blog3-sprint-grooming-outline.json blog3-sprint-grooming.md
bloginator outline --index output/index \
    --keywords "backlog,refinement,grooming,user,stories,acceptance,criteria,estimation" \
    --title "Sprint Grooming: The Art of Backlog Refinement" \
    --thesis "Effective backlog refinement prevents sprint planning chaos and enables predictable delivery" \
    -o blog3-sprint-grooming-outline.json

bloginator draft --index output/index \
    --outline blog3-sprint-grooming-outline.json \
    -o blog3-sprint-grooming.md

echo "=== Generating Sprint Retrospectives blog ==="
rm -f blog4-sprint-retros-outline.json blog4-sprint-retros.md
bloginator outline --index output/index \
    --keywords "retrospective,continuous,improvement,team,feedback,action,items" \
    --title "Sprint Retrospectives: Continuous Improvement in Action" \
    --thesis "Regular retrospectives turn team experiences into actionable improvements" \
    -o blog4-sprint-retros-outline.json

bloginator draft --index output/index \
    --outline blog4-sprint-retros-outline.json \
    -o blog4-sprint-retros.md

kill $RESPONDER_PID 2>/dev/null || true

echo "=== All 3 blogs generated ==="
wc -w blog2-sprint-planning.md blog3-sprint-grooming.md blog4-sprint-retros.md
