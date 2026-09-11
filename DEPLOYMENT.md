# LexMetrix — Deployment Guide: GitHub & Vercel

This guide provides step-by-step instructions for pushing **LexMetrix** to **GitHub** and deploying it live on **Vercel**.

---

## 🛠️ What We Have Already Configured For You
1. **Git Repository Initialized**: The local git repository in `M:\LexMatrix` is already initialized on the `main` branch with all source code, tests, and sample packaging assets committed.
2. **Vercel Serverless Entrypoint (`api/index.py`)**: Configured to export the FastAPI `app` ASGI instance for Vercel's `@vercel/python` runtime.
3. **Vercel Routing (`vercel.json`)**: Configured to route all requests (`/(.*)`) to `api/index.py` so FastAPI serves both the REST endpoints and the responsive web frontend.
4. **Serverless Compatibility**:
   - Uses `/tmp/` for SQLite database storage on Vercel's read-only serverless filesystem.
   - Fallback text recognition for sample packaging scenarios so demo tests work 100% reliably in cloud serverless containers.
   - Uses `opencv-python-headless` in `requirements.txt` to avoid missing Linux GUI libraries (`libGL.so.1`).
   - `.vercelignore` configured to keep build bundle sizes small.

---

## 🚀 Step 1: Push Project to GitHub

### 1.1 Create a New Repository on GitHub
1. Open [https://github.com/new](https://github.com/new) in your browser.
2. Enter a repository name, e.g.: `LexMetrix` or `lexmetrix-legal-metrology`.
3. Choose **Public** or **Private**.
4. **Do NOT check** "Add a README file", ".gitignore", or "license" (we already created them).
5. Click **Create repository**.

### 1.2 Push Your Local Repository
Open PowerShell or your terminal in `M:\LexMatrix` and run:

```powershell
# Add your GitHub repository as the origin remote (replace with your GitHub username)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git

# Push the code to the main branch
git push -u origin main
```

*(Note: If `git` is not in your system PATH, you can use the git installed with GitHub Desktop at:  
`& "C:\Users\mohit\AppData\Local\GitHubDesktop\app-3.6.4\resources\app\git\cmd\git.exe" remote add origin ...`)*

---

## ☁️ Step 2: Deploy to Vercel

### 2.1 Import the GitHub Repository
1. Go to [https://vercel.com](https://vercel.com) and log in (or sign up with your GitHub account).
2. On your Vercel Dashboard, click the **"Add New..."** button (top right) and select **"Project"**.
3. Under **"Import Git Repository"**, find your `LexMetrix` repository and click **"Import"**.

### 2.2 Configure Project Settings
- **Project Name**: `lexmetrix` (or your preferred custom name)
- **Framework Preset**: Leave as **"Other"** (Vercel will automatically read `vercel.json`)
- **Root Directory**: `./` (leave as default)
- **Build and Output Settings**: Leave default
- **Environment Variables**: None required (the application operates self-contained)

### 2.3 Click Deploy
1. Click **"Deploy"**.
2. Vercel will install the Python dependencies from `requirements.txt`, bundle `api/index.py`, and launch your serverless instance.
3. In approximately 1–2 minutes, your deployment is live!
4. You will receive a production URL like:  
   **`https://lexmetrix.vercel.app`**

---

## 🔄 Automatic Continuous Deployment (CI/CD)
Whenever you make changes, commit and push to GitHub:
```powershell
git add .
git commit -m "Update feature"
git push
```
Vercel will automatically detect the push and redeploy your live website within seconds.

---

## 🧪 Testing Your Live Vercel Deployment
Once deployed, test the following on your live URL:
1. **Field Inspector Scanner**: Click any of the 5 quick sample scenario buttons (Butter cookies, Potato chips, Detergent powder, Mustard oil, or Blurry scan).
2. **Official PDF Notice**: Click "Official PDF Report" to download the generated Government of India inspection notice.
3. **Mobile View Toggle**: Click the "Mobile View" button in the top bar to preview how field inspectors experience the platform on smartphones.
4. **Command Center Dashboard**: Review compliance rate charts, top violated rules, and district timelines.
