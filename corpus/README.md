# Blog Corpus Directory

This directory contains your historical blog posts and writing samples that Bloginator will use to learn your voice and writing style.

## Supported File Formats

- **Markdown** (`.md`, `.markdown`) - Recommended format
- **PDF** (`.pdf`) - Text will be extracted
- **Word Documents** (`.docx`) - Text will be extracted
- **RTF** (`.rtf`) - Rich Text Format
- **Plain Text** (`.txt`)

## Directory Structure

You can organize your files however you like:

```
corpus/
├── 2023/
│   ├── blog-post-1.md
│   ├── blog-post-2.md
│   └── essay.pdf
├── 2024/
│   ├── article-1.md
│   └── article-2.md
└── drafts/
    └── unfinished.md
```

Or keep them flat:

```
corpus/
├── post-1.md
├── post-2.md
├── post-3.md
└── essay.pdf
```

Bloginator will recursively scan this directory and index all supported files.

## Getting Started

### 1. Add Your Writing

Copy your blog posts and writing samples into this directory:

```bash
# Example: Copy from another directory
cp ~/my-blog/posts/*.md corpus/

# Example: Copy from films-not-made or another project
cp ../films-not-made/blog/*.md corpus/
```

### 2. Index Your Corpus

Once you've added files, index them into ChromaDB:

```bash
# From project root
bloginator index corpus/

# Or specify custom output directory
bloginator index corpus/ --chroma-dir .bloginator/chroma
```

### 3. Search to Verify

Test that indexing worked by searching:

```bash
bloginator search "topic you've written about"
```

### 4. Generate Content

Once indexed, you can generate new content:

```bash
# Generate an outline
bloginator outline "Your blog post topic"

# Generate a full draft
bloginator draft "Your blog post topic"
```

## File Requirements

- **Minimum**: At least 5-10 blog posts for good voice preservation
- **Recommended**: 20+ posts for best results
- **Size**: No individual file size limits
- **Encoding**: UTF-8 encoding recommended

## Troubleshooting

### Files Not Being Indexed

Check that:
1. Files are in a supported format (see list above)
2. Files are UTF-8 encoded
3. Files contain actual text content

### Poor Generation Quality

If generated content doesn't match your voice:
1. Add more writing samples (20+ posts recommended)
2. Ensure samples are representative of your actual writing
3. Try adjusting the temperature in your `.env` file

## Configuration

See `.env.example` in the project root for corpus directory configuration:

```bash
# Change corpus location
BLOGINATOR_CORPUS_DIR=corpus

# Change ChromaDB storage location
BLOGINATOR_CHROMA_DIR=.bloginator/chroma
```

## Privacy & Security

- This directory is in `.gitignore` by default
- Your writing stays local (unless using cloud LLM providers)
- ChromaDB vector store also stays local by default
- Never commit sensitive or private content to version control
