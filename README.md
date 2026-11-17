# site_book.kallah.in

## Branches and hosting

- `Dev_v01`: develop and test application changes.
- `Publish`: reviewed files used by MilesWeb hosting. Do **not** develop directly in this branch.
- Hosting URL: `https://book.kallah.in`
- MilesWeb application root: `/home/dnatechy/book.kallah.in`
- Python: `3.10.22`; Passenger startup file: `passenger_wsgi.py`; WSGI entry point: `application`.

## Common GitHub SSH access from MilesWeb

**Important: the common, account-level SSH key already exists on the MilesWeb server. Do not create a new SSH/deploy key for each repository.**

The server's `~/.ssh/config` includes this reusable host alias:

```sshconfig
Host github-milesweb
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github_common
    IdentitiesOnly yes
```

- SSH alias: `github-milesweb`
- Account-level public key is registered under the GitHub user `mani-baskar` at https://github.com/settings/keys
- This account key works for repositories that the GitHub account is authorized to access, including newly created repositories. A separate repository deploy key is not required.
- Never print, copy to the repository, or commit the **private** key.

Check the existing connection:

```bash
ssh -T git@github-milesweb
```

Expected authenticated account greeting: `Hi mani-baskar!` (GitHub's “does not provide shell access” message is normal).

### Connect this existing Book hosting directory

This hosting folder was initialized with Git already. Its tested remote is:

```bash
cd /home/dnatechy/book.kallah.in
git remote set-url origin git@github-milesweb:dnatechy/site_book.kallah.in.git
git fetch origin
git branch -a
git status -sb
```

The local hosting branch is `Publish`, tracking `origin/Publish`. For future updates, after confirming the working tree is safe:

```bash
cd /home/dnatechy/book.kallah.in
git switch Publish
git pull --ff-only origin Publish
```

### Connect a **future** GitHub repository using the same SSH key

Replace `REPO_NAME` and the local path as appropriate. No new SSH key is needed.

For an **empty/new local folder**, clone its Publish branch:

```bash
git clone --branch Publish git@github-milesweb:dnatechy/REPO_NAME.git
```

For an **existing hosting folder** that is not yet a Git repository (and may contain cPanel/Passenger files):

```bash
cd /home/dnatechy/REPO_NAME
git init
git remote add origin git@github-milesweb:dnatechy/REPO_NAME.git
git fetch origin
git switch -c Publish --track origin/Publish
git status -sb
```

If `origin` already exists, use `git remote set-url origin ...` instead of `git remote add origin ...`. If `Publish` is already checked out, do **not** recreate it. Existing untracked files may block checkout; inspect/backup them first. Never use `git reset --hard`, `git clean -fd`, or force checkout to bypass a conflict.

### Deployment and security notes

1. Make application changes on `Dev_v01`; move only approved files to `Publish`.
2. The MilesWeb hosting directory pulls only `Publish` (and restarts Passenger only when application changes require it).
3. Keep runtime `.env`, logs, `tmp/`, virtual environments, credentials, and SSH keys outside Git.
4. SSH authentication does not push files automatically: changes reach GitHub only after an explicit commit and `git push`.
5. Account-level SSH access is broad: protect the MilesWeb account and remove/revoke the GitHub key if the server is compromised.
