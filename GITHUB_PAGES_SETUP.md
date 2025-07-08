# GitHub Pages Setup Instructions

This guide will help you set up GitHub Pages for the ConsensusNet documentation with both English and Polish versions.

## 📋 Quick Setup

### 1. Push Documentation Files

All documentation files are already created. Push them to your repository:

```bash
# Add all documentation files
git add docs/
git add USER_DOCUMENTATION.md
git add DOKUMENTACJA_UZYTKOWNIKA.md
git add GITHUB_PAGES_SETUP.md

# Commit the changes
git commit -m "Add multi-language user documentation and GitHub Pages setup

- English documentation in docs/en/index.md
- Polish documentation in docs/pl/index.md  
- GitHub Pages configuration in docs/_config.yml
- Landing page with language selection
- Complete setup instructions"

# Push to GitHub
git push origin main
```

### 2. Enable GitHub Pages

1. **Go to Repository Settings**
   - Navigate to: https://github.com/hretheum/consensus.net/settings
   - Scroll down to the "Pages" section

2. **Configure Pages Source**
   - Under "Source", select "Deploy from a branch"
   - Choose branch: `main` (or your default branch)
   - Choose folder: `/docs` 
   - Click "Save"

3. **Wait for Deployment** 
   - GitHub will automatically build and deploy your site
   - This usually takes 1-5 minutes
   - You'll see a green checkmark when it's ready

### 3. Access Your Documentation

After GitHub Pages is enabled, your documentation will be available at:

- **🏠 Main Landing Page**: https://hretheum.github.io/consensus.net/
- **🇺🇸 English Documentation**: https://hretheum.github.io/consensus.net/en/
- **🇵🇱 Polish Documentation**: https://hretheum.github.io/consensus.net/pl/

## 📚 What's Included

### Documentation Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── index.md                 # Landing page with language selector
├── en/index.md              # Complete English documentation
├── pl/index.md              # Complete Polish documentation  
├── Gemfile                  # Jekyll dependencies
└── README.md                # Setup instructions
```

### Language Versions

#### 🇺🇸 English Documentation (`/en/`)
- Complete user guide with installation, configuration, and usage
- All 4 verification types (basic, enhanced, multi-agent, adversarial)
- Python, JavaScript, and bash code examples
- Troubleshooting guide and FAQ
- System monitoring and advanced features

#### 🇵🇱 Polish Documentation (`/pl/`)
- Comprehensive user guide in Polish
- Same structure and content as English version
- Polish examples and terminology
- Full troubleshooting and FAQ sections

### Key Features

- **🌐 Multi-language Support**: Seamless switching between English and Polish
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🔍 SEO Optimized**: Proper meta tags and site structure
- **🎨 GitHub Theme**: Clean, professional appearance with Minima theme
- **⚡ Fast Loading**: Optimized for performance
- **🔗 Navigation**: Easy language switching and home navigation

## 🛠️ Local Development

To test the documentation locally before publishing:

```bash
# Install Jekyll (one-time setup)
gem install jekyll bundler

# Navigate to docs folder
cd docs

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Access at: http://localhost:4000/consensus.net/
```

## 🔧 Customization Options

### Custom Domain (Optional)

To use your own domain instead of `hretheum.github.io`:

1. **Add CNAME file:**
   ```bash
   echo "docs.consensus.net" > docs/CNAME
   git add docs/CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. **Configure DNS:**
   - Create CNAME record pointing to `hretheum.github.io`
   - Wait for DNS propagation (can take up to 24 hours)

### Analytics (Optional)

To add Google Analytics:

1. Edit `docs/_config.yml`
2. Uncomment and add your tracking ID:
   ```yaml
   google_analytics: G-XXXXXXXXXX
   ```

### Theme Customization

To customize the appearance:

1. Create `docs/_sass/minima/custom-styles.scss`
2. Add your custom CSS
3. Jekyll will automatically include it

## 📊 Monitoring and Maintenance

### Automatic Updates

- GitHub Pages automatically rebuilds when you push changes
- No manual deployment needed
- Changes appear within 1-5 minutes

### Updating Documentation

When making changes:

1. **Update both language versions** (`en/index.md` and `pl/index.md`)
2. **Maintain consistent structure** across languages
3. **Update version numbers** and timestamps
4. **Test locally** before committing

### Version Control

Keep documentation versions synchronized:

```bash
# Example update workflow
git checkout -b update-docs
# Edit docs/en/index.md and docs/pl/index.md
git add docs/
git commit -m "Update documentation: add new feature examples"
git push origin update-docs
# Create pull request and merge
```

## 🚀 Benefits of This Setup

### For Users
- **Easy access** to documentation in their preferred language
- **Professional appearance** with consistent branding
- **Mobile-friendly** design for all devices
- **Fast loading** and reliable hosting

### For Developers
- **Version controlled** documentation alongside code
- **Automatic deployment** on every change
- **Markdown-based** editing (no HTML required)
- **Free hosting** through GitHub Pages

### For Project Growth
- **SEO benefits** for better discoverability
- **Professional image** for potential contributors
- **Multi-language support** for international adoption
- **Easy maintenance** and updates

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] GitHub Pages is enabled in repository settings
- [ ] Main page loads: https://hretheum.github.io/consensus.net/
- [ ] English docs load: https://hretheum.github.io/consensus.net/en/
- [ ] Polish docs load: https://hretheum.github.io/consensus.net/pl/
- [ ] Language switching works correctly
- [ ] All code examples display properly
- [ ] Links to GitHub repository work
- [ ] Mobile view is responsive

## 🆘 Troubleshooting

### Common Issues

**Site not loading after 10 minutes:**
- Check that GitHub Pages is enabled with `/docs` folder selected
- Ensure branch name is correct (usually `main`)
- Look for errors in repository Actions tab

**404 errors on subpages:**
- Verify file structure matches expected paths
- Check that index.md files exist in each language folder
- Ensure _config.yml has correct baseurl

**Styling looks broken:**
- Confirm Jekyll theme is properly configured
- Check that Gemfile includes github-pages gem
- Verify _config.yml syntax is valid YAML

### Getting Help

If you encounter issues:
1. Check the [GitHub Pages documentation](https://docs.github.com/en/pages)
2. Review Jekyll build logs in the Actions tab
3. Create an issue in the repository with error details

---

🎉 **Congratulations!** Your multi-language documentation is now live and accessible to users worldwide!