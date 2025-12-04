#!/bin/bash
# Pre-commit hook to enforce repository root cleanliness
# Blocks temporary scripts and generated files from being committed to root

set -e

# Get list of staged files in repository root (not in subdirectories)
STAGED_ROOT_FILES=$(git diff --cached --name-only --diff-filter=A | grep -E "^[^/]+$" || true)

if [ -z "$STAGED_ROOT_FILES" ]; then
    exit 0
fi

# Allowed files in root
ALLOWED_ROOT_FILES=(
    "README.md"
    "CLAUDE.md"
    "LICENSE"
    "CONTRIBUTING.md"
    "SECURITY.md"
    ".gitignore"
    ".gitattributes"
    ".pre-commit-config.yaml"
    "pyproject.toml"
    "setup.py"
    "setup.cfg"
    "requirements.txt"
    ".env.example"
    "Makefile"
    "Dockerfile"
    ".dockerignore"
    "validate-monorepo.sh"
)

# Check for violations
VIOLATIONS=()

for file in $STAGED_ROOT_FILES; do
    # Skip if file is in allowed list
    if [[ " ${ALLOWED_ROOT_FILES[@]} " =~ " ${file} " ]]; then
        continue
    fi

    # Check for shell scripts (temp scripts should be in tmp/)
    if [[ "$file" == *.sh ]]; then
        VIOLATIONS+=("❌ Shell script in root: $file (should be in tmp/)")
    fi

    # Check for markdown files (docs should be in docs/)
    if [[ "$file" == *.md ]]; then
        VIOLATIONS+=("❌ Markdown file in root: $file (documentation should be in docs/)")
    fi

    # Check for blog files
    if [[ "$file" == blog*.md ]] || [[ "$file" == blog*.json ]] || [[ "$file" == *_blog.md ]]; then
        VIOLATIONS+=("❌ Blog file in root: $file (should be in blogs/)")
    fi

    # Check for outline files
    if [[ "$file" == *_outline.* ]] || [[ "$file" == outline*.* ]]; then
        VIOLATIONS+=("❌ Outline file in root: $file (should be in blogs/outlines/)")
    fi

    # Check for prompt optimization directories
    if [[ "$file" == prompt_optimization* ]]; then
        VIOLATIONS+=("❌ Prompt optimization in root: $file (should be in prompts/experimentation/)")
    fi
done

# Report violations
if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    echo ""
    echo "🚫 REPOSITORY ROOT CLEANLINESS VIOLATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    for violation in "${VIOLATIONS[@]}"; do
        echo "$violation"
    done
    echo ""
    echo "📝 Repository Root Policy:"
    echo "  • Temporary scripts → tmp/ (git-ignored)"
    echo "  • Blog outputs → blogs/ (git-ignored)"
    echo "  • Prompt experiments → prompts/experimentation/ (git-ignored)"
    echo "  • Documentation → docs/ or specific docs like CLAUDE.md"
    echo ""
    echo "See CLAUDE.md for full repository cleanliness policy."
    echo ""
    exit 1
fi

# Verify critical directories are git-ignored
if ! grep -q "^tmp/" .gitignore; then
    echo "⚠️  WARNING: tmp/ is not in .gitignore"
    exit 1
fi

if ! grep -q "^blogs/" .gitignore; then
    echo "⚠️  WARNING: blogs/ is not in .gitignore"
    exit 1
fi

if ! grep -q "prompts/experimentation/\*" .gitignore; then
    echo "⚠️  WARNING: prompts/experimentation/* is not in .gitignore"
    exit 1
fi

exit 0
