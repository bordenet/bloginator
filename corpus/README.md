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

### Option A: Quick Setup (Recommended for Multiple Sources)

**1. Create corpus.yaml configuration:**

```bash
# Copy example config
cp corpus.sample.yaml corpus.yaml

# Edit with your sources
nano corpus.yaml
```

**2. Configure your sources in corpus.yaml:**

```yaml
sources:
  # OneDrive archive
  - name: "onedrive-blog-archive"
    path: "/Users/you/OneDrive/Blog Archive"
    quality: "preferred"  # High-quality authentic voice
    voice_notes: "Original blog posts from 2019-2021"
    tags: ["archive", "authentic-voice"]
    enabled: true

  # Recent sanitized posts
  - name: "recent-blog-posts"
    path: "../../blogs/"  # Relative paths supported!
    quality: "reference"  # Usable but sanitized
    voice_notes: "Recent posts - voice reads too AI, use sparingly"
    tags: ["recent", "ai-edited"]
    enabled: true

  # Symlinked film blog
  - name: "films-not-made"
    path: "../films-not-made/blog"  # Symlinks work!
    quality: "preferred"
    tags: ["film", "criticism"]
    enabled: true
```

**3. Extract and index:**

```bash
# Extract from all enabled sources
bloginator extract -o output/extracted --config corpus.yaml

# Index into ChromaDB
bloginator index output/extracted -o .bloginator/chroma
```

### Option B: Manual Setup (Legacy, Single Source)

**1. Add Your Writing:**

You can either copy files or use symbolic links (recommended to avoid duplicating data):

```bash
# Option A: Create symbolic links (recommended - no data duplication)
ln -s ~/my-blog/posts corpus/my_blog
ln -s ../films-not-made/blog corpus/films_blog

# Option B: Copy files
cp ~/my-blog/posts/*.md corpus/

# Option C: Mix of both
ln -s ../large-blog-archive corpus/archive
cp important-post.md corpus/
```

**Symbolic links are fully supported!** The extraction tool follows symlinks automatically, so you can link to directories anywhere on your system without copying data.

**2. Extract and index:**

```bash
# Extract from directory
bloginator extract corpus/ -o output/extracted --quality preferred

# Index into ChromaDB
bloginator index output/extracted -o .bloginator/chroma
```

## Supported Path Types

corpus.yaml supports all these path formats:

- **Relative paths**: `../../blogs/` (relative to corpus.yaml location)
- **Absolute paths**: `/Users/you/OneDrive/Blog Archive`
- **Windows paths**: `C:\Users\you\Documents\Blogs`
- **UNC paths**: `\\server\share\blogs`
- **Symlinks**: Full support, no data copying needed!
- **URLs**: `https://example.com/posts.zip` (future - not yet implemented)

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
