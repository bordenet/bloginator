#!/bin/bash
set -e

source venv311/bin/activate

# Blog 2: Sprint Planning
echo "=== Generating Blog 2: Sprint Planning ==="
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator outline --index output/index \
  --keywords "sprint,planning,agile,scrum,estimation,story,points,capacity,commitment" \
  --title "Sprint Planning: Setting Teams Up for Success" \
  --thesis "Effective sprint planning balances team capacity with realistic commitments and clear objectives" \
  -o blog2-planning-outline.json &
OUTLINE_PID=$!

sleep 3
python3 auto_respond.py
wait $OUTLINE_PID

echo "Blog 2 outline complete, starting draft..."
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator draft --index output/index \
  --outline blog2-planning-outline.json \
  -o blog2-sprint-planning.md > /tmp/blog2.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 auto_respond.py 2>&1 | grep "✓" || true
  sleep 1
  if [ -f blog2-sprint-planning.md ] && [ $(wc -w < blog2-sprint-planning.md) -gt 1000 ]; then
    echo "Blog 2 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w blog2-sprint-planning.md

# Blog 3: Sprint Grooming
echo "=== Generating Blog 3: Sprint Grooming ==="
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator outline --index output/index \
  --keywords "backlog,refinement,grooming,scrum,agile,stories,acceptance,criteria,estimation" \
  --title "Sprint Grooming: The Art of Backlog Refinement" \
  --thesis "Effective backlog refinement reduces planning time and increases sprint predictability" \
  -o blog3-grooming-outline.json &
OUTLINE_PID=$!

sleep 3
python3 auto_respond.py
wait $OUTLINE_PID

echo "Blog 3 outline complete, starting draft..."
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator draft --index output/index \
  --outline blog3-grooming-outline.json \
  -o blog3-sprint-grooming.md > /tmp/blog3.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 auto_respond.py 2>&1 | grep "✓" || true
  sleep 1
  if [ -f blog3-sprint-grooming.md ] && [ $(wc -w < blog3-sprint-grooming.md) -gt 1000 ]; then
    echo "Blog 3 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w blog3-sprint-grooming.md

# Blog 4: Retrospectives
echo "=== Generating Blog 4: Retrospectives ==="
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator outline --index output/index \
  --keywords "retrospective,agile,scrum,improvement,feedback,team,process,kaizen" \
  --title "Sprint Retrospectives: Continuous Improvement in Action" \
  --thesis "Effective retrospectives turn team insights into actionable process improvements" \
  -o blog4-retro-outline.json &
OUTLINE_PID=$!

sleep 3
python3 auto_respond.py
wait $OUTLINE_PID

echo "Blog 4 outline complete, starting draft..."
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

bloginator draft --index output/index \
  --outline blog4-retro-outline.json \
  -o blog4-sprint-retrospectives.md > /tmp/blog4.log 2>&1 &
DRAFT_PID=$!

for i in {1..300}; do
  python3 auto_respond.py 2>&1 | grep "✓" || true
  sleep 1
  if [ -f blog4-sprint-retrospectives.md ] && [ $(wc -w < blog4-sprint-retrospectives.md) -gt 1000 ]; then
    echo "Blog 4 complete!"
    break
  fi
done

wait $DRAFT_PID
wc -w blog4-sprint-retrospectives.md

echo "=== ALL BLOGS COMPLETE ==="
ls -lh blog*.md | grep -v outline
