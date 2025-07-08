# ConsensusNet GitHub Pages Documentation

This folder contains the GitHub Pages configuration for multi-language documentation.

## Structure

```
docs/
├── _config.yml          # Jekyll configuration
├── index.md             # Landing page with language selection
├── en/
│   └── index.md         # English documentation
├── pl/
│   └── index.md         # Polish documentation
└── README.md            # This file
```

## Setup Instructions

### 1. Enable GitHub Pages

1. Go to your repository settings: `https://github.com/hretheum/consensus.net/settings`
2. Scroll down to "Pages" section
3. Set source to "Deploy from a branch"
4. Select branch: `main` (or your default branch)
5. Select folder: `/docs`
6. Click "Save"

### 2. Access Documentation

After GitHub Pages is enabled, your documentation will be available at:

- **Main page**: https://hretheum.github.io/consensus.net/
- **English docs**: https://hretheum.github.io/consensus.net/en/
- **Polish docs**: https://hretheum.github.io/consensus.net/pl/

### 3. Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file in the `/docs` folder with your domain
2. Configure DNS records to point to `hretheum.github.io`

## Languages Supported

- 🇺🇸 **English** - Complete user documentation
- 🇵🇱 **Polski** - Comprehensive user documentation in Polish

## Features

- **Responsive design** with GitHub's Minima theme
- **Language switching** between English and Polish
- **Comprehensive API documentation** with examples
- **Interactive code samples** in multiple languages
- **Troubleshooting guides** and FAQ sections
- **SEO optimized** with proper meta tags

## Local Development

To test the documentation locally:

```bash
# Install Jekyll
gem install jekyll bundler

# Navigate to docs folder
cd docs

# Create Gemfile
echo 'source "https://rubygems.org"' > Gemfile
echo 'gem "github-pages", group: :jekyll_plugins' >> Gemfile

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Access at http://localhost:4000/consensus.net/
```

## Contributing

When updating documentation:

1. Update both language versions (`en/index.md` and `pl/index.md`)
2. Maintain consistent structure across languages
3. Update version numbers and timestamps
4. Test locally before committing

## Technical Details

- **Theme**: GitHub Pages Minima theme
- **Markdown processor**: Kramdown
- **Syntax highlighting**: Rouge
- **Plugins**: jekyll-feed, jekyll-sitemap, jekyll-seo-tag

## Automatic Deployment

GitHub Pages automatically rebuilds the site when changes are pushed to the main branch. No manual deployment is required.