# GitHub Actions Workflows

## deploy.yml

Automatically deploys the web application to GitHub Pages whenever changes are pushed to the `main` branch.

### How it works

1. Triggers on push to `main` branch or manual workflow dispatch
2. Uploads the contents of the `web/` directory as a Pages artifact
3. Deploys to GitHub Pages using the official GitHub Actions

### Setup Requirements

**One-time setup in your GitHub repository:**

1. Go to repository **Settings** → **Pages**
2. Under "Build and deployment":
   - Source: **GitHub Actions**
   - (Not "Deploy from a branch")
3. Save

That's it! The workflow will automatically deploy on every push to main.

### Accessing the deployed site

After the first successful deployment, your site will be available at:
```
https://pzfreo.github.io/wormgearcalc/
```

### Manual deployment

You can also trigger a deployment manually:
1. Go to **Actions** tab in GitHub
2. Select "Deploy to GitHub Pages" workflow
3. Click "Run workflow"

### Monitoring deployments

- View workflow runs in the **Actions** tab
- Each deployment creates a new environment deployment visible in the **Environments** section
- Failed deployments will show errors in the workflow logs
