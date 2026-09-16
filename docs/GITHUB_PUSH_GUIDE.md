# Step-by-Step Guide: Push the Project to GitHub

This guide walks you through creating a GitHub repository, setting it up locally,
and pushing all the code files. Follow each step in order.

---

## Step 1 - Create a GitHub account (skip if you already have one)

1. Go to https://github.com
2. Click "Sign up" and create an account using your email address.
3. Verify your email address.

---

## Step 2 - Create a new repository on GitHub

1. Log in to https://github.com
2. Click the "+" icon in the top-right corner.
3. Select "New repository".
4. Fill in the form:
   - Repository name: `mia-credit-scoring`
   - Description: `Membership inference attack evaluation on credit scoring models with differential privacy defenses`
   - Visibility: Public (required if you want a free Zenodo DOI later)
   - Do NOT check "Add a README file" (you already have one)
   - Do NOT check "Add .gitignore" (you already have one)
   - Do NOT choose a license template (you already have MIT in the README)
5. Click "Create repository".
6. GitHub will show you a page with setup commands. Keep this page open.

---

## Step 3 - Install Git on your computer (skip if already installed)

To check if Git is installed, open a terminal (Command Prompt or PowerShell on Windows,
Terminal on Mac or Linux) and type:

```
git --version
```

If it prints a version number, Git is installed. If not:

- Windows: download from https://git-scm.com/download/win and install.
- Mac: run `xcode-select --install` in Terminal, or download from https://git-scm.com
- Linux (Ubuntu/Debian): run `sudo apt-get install git`

---

## Step 4 - Configure Git with your identity (one-time setup)

In your terminal, run these two commands. Replace the name and email with yours.

```
git config --global user.name "Bibek Maharjan"
git config --global user.email "bbkmhj06@gmail.com"
```

---

## Step 5 - Copy the project files to your computer

You need to have the following files on your computer in a single folder.
If you downloaded the manuscript (manuscript_v1.docx) and saved the code files
from Claude, gather them into one folder named `mia-credit-scoring`.

The folder should contain:

```
mia-credit-scoring/
  README.md
  requirements.txt
  .gitignore
  package.json
  run_experiments_v2.py
  run_dp_only.py
  driver_analysis.py
  build_paper.js
  results/
    mia_results_v2.json
  data/
    README_DATA.md
  docs/
    DIFFPRIVLIB_PATCH.md
    GITHUB_PUSH_GUIDE.md
```

Do NOT copy the CSV dataset files into the repo folder.
Do NOT copy manuscript_v1.docx into the repo folder.
The .gitignore will block them but it is cleaner to leave them out entirely.

---

## Step 6 - Initialize the Git repository

Open your terminal, navigate to the `mia-credit-scoring` folder, and run:

```
cd path/to/mia-credit-scoring
git init
git add .
git status
```

The `git status` command will show a list of files staged for commit.
Check the list. You should NOT see any .csv files or .docx files.
If you do, stop and check your .gitignore file.

---

## Step 7 - Make the first commit

```
git commit -m "Initial commit: MIA credit scoring experiments and manuscript builder"
```

You will see output listing the files that were committed.

---

## Step 8 - Connect to your GitHub repository

On the GitHub page you kept open after Step 2, copy the repository URL.
It will look like:

```
https://github.com/YOUR-USERNAME/mia-credit-scoring.git
```

Now run:

```
git remote add origin https://github.com/YOUR-USERNAME/mia-credit-scoring.git
git branch -M main
```

---

## Step 9 - Push to GitHub

```
git push -u origin main
```

Git will ask for your GitHub username and password. Note that since 2021,
GitHub no longer accepts your account password for command-line pushes.
You need to use a Personal Access Token instead.

### Creating a Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" and select "Generate new token (classic)".
3. Give it a name like "mia-credit-scoring push".
4. Set an expiration (90 days is fine).
5. Check the box next to "repo" (full control of private repositories).
6. Click "Generate token".
7. Copy the token immediately. GitHub will not show it again.

When Git asks for your password during `git push`, paste the token instead of
your account password.

---

## Step 10 - Verify the push

1. Go to https://github.com/YOUR-USERNAME/mia-credit-scoring in your browser.
2. You should see all your files listed, with the README.md rendered on the page.
3. Click on `results/mia_results_v2.json` to confirm the results file is there.
4. Click on `data/README_DATA.md` to confirm dataset download instructions are visible.

---

## Step 11 - Get a Zenodo DOI (for the paper citation)

Zenodo mints a permanent DOI for your GitHub repository, which you can cite in the paper.

1. Go to https://zenodo.org
2. Click "Log in" and choose "Log in with GitHub".
3. Authorize Zenodo to access your GitHub account.
4. Go to https://zenodo.org/account/settings/github/
5. You will see a list of your GitHub repositories.
6. Find `mia-credit-scoring` and toggle the switch to ON.
7. Now go back to your GitHub repository at
   https://github.com/YOUR-USERNAME/mia-credit-scoring
8. Create a release:
   - Click "Releases" on the right side of the page.
   - Click "Create a new release".
   - In the "Tag version" field, type `v1.0.0`
   - In "Release title", write `v1.0.0 - Initial release for paper submission`
   - In the description, write something like:
     "Code and results for: Membership Inference Attacks on Credit Scoring Models.
     Submitted to Computers and Security (Elsevier)."
   - Click "Publish release".
9. Within a few minutes, Zenodo will automatically archive the release and mint a DOI.
10. Go to https://zenodo.org/account/settings/github/ and click on your repository.
    You will see the DOI badge. The DOI will look like:
    `10.5281/zenodo.XXXXXXX`

---

## Step 12 - Update the paper with the DOI

Open `build_paper.js` and find the Code Availability section. Change this line:

```
All experimental code will be made available at a public repository upon acceptance.
```

To something like:

```
All experimental code is available at https://github.com/YOUR-USERNAME/mia-credit-scoring
(DOI: https://doi.org/10.5281/zenodo.XXXXXXX). The main pipeline uses Python 3.11 with
fixed random seeds. The diffprivlib compatibility patch is documented in
docs/DIFFPRIVLIB_PATCH.md.
```

Then rebuild the manuscript: `node build_paper.js`

---

## Step 13 - Add the Zenodo DOI badge to your README (optional but nice)

GitHub and Zenodo both support a clickable badge at the top of the README.
Zenodo gives you a badge markdown snippet. Copy it and add it near the top of
your README.md, then commit and push again:

```
git add README.md build_paper.js
git commit -m "Add Zenodo DOI and GitHub repository URL to code availability section"
git push
```

---

## Summary of commands (all in one block for reference)

```
cd path/to/mia-credit-scoring
git init
git add .
git status
git commit -m "Initial commit: MIA credit scoring experiments and manuscript builder"
git remote add origin https://github.com/YOUR-USERNAME/mia-credit-scoring.git
git branch -M main
git push -u origin main
```

After Zenodo DOI is ready:

```
git add README.md build_paper.js
git commit -m "Add Zenodo DOI to code availability section"
git push
```

---

## Common problems

**Problem:** `git push` fails with "Authentication failed"
**Fix:** Use a Personal Access Token instead of your account password. See Step 9.

**Problem:** `git push` fails with "rejected - Updates were rejected"
**Fix:** Run `git pull origin main --rebase` then `git push` again.

**Problem:** A .csv file appears in `git status`
**Fix:** Check your .gitignore is in the repo root and is named exactly `.gitignore`
(no .txt extension). Run `git rm --cached data/*.csv` to untrack any accidentally staged files.

**Problem:** The results JSON is too large for GitHub
**Fix:** Files up to 100 MB are accepted by GitHub without special tools.
`mia_results_v2.json` is well under 1 MB so this should not be an issue.
