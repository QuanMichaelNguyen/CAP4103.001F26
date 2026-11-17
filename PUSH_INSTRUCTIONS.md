# Push this project to a separate GitHub branch

Repository: https://github.com/QuanMichaelNguyen/CAP4103.001F26

**GitHub integration write calls returned HTTP 403 (`Resource not accessible by integration`).** No remote feature branch has been created by ChatGPT. The repository was empty when checked.

## Git Bash / Windows PowerShell

1. Extract this package to a convenient working folder and open a terminal inside `CAP4103_ExamAuth`.
2. Because the remote repository was empty at last check, the following initializes `main` and then creates the feature branch. **Check the GitHub repository first; if someone has added commits, clone/pull instead of reinitializing.**

```bash
git init
git branch -M main
git remote add origin https://github.com/QuanMichaelNguyen/CAP4103.001F26.git
echo "# CAP4103 course repository" > INITIAL_README.md
git add INITIAL_README.md
git commit -m "Initialize course repository"
git push -u origin main
git switch -c feature/multimodal-exam-authentication
git add .
git commit -m "Add multimodal biometric research project and draft deliverables"
git push -u origin feature/multimodal-exam-authentication
```

For the intended submission, only merge after team review. If you already have a local checkout with a populated `main`, instead copy these project files into that checkout, `git switch -c feature/multimodal-exam-authentication`, then add/commit/push.

Note: `results/demo/` is synthetic software-verification output. It is NOT real research data, and must not be presented as an experiment result.
