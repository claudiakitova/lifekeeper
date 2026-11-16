# Backup

An archive kept in one place can be lost to a stolen laptop, a failed drive or a spilled coffee. Keep at least two copies outside your computer, one of them away from home, and check that you can restore from them.

## The setup

- A cloud copy, encrypted before it leaves your computer. [rclone](https://rclone.org) works with Google Drive, OneDrive, Dropbox, S3 and dozens more. Its `crypt` layer encrypts file contents and names, so the cloud provider can't read either.
- Old versions are kept. Each night's changes and deletions move to a dated folder that is kept for 30 days, so a mistake you notice a week later can still be undone.
- A drive at home, for a second copy you can reach without the internet.
- The backup runs every night by itself.

## Steps

1. Install rclone from rclone.org.
2. Connect your cloud: `rclone config` → new remote → your provider. For Google Drive, create your own OAuth client ID in the Google Cloud console and give it to rclone. rclone's shared client is slow and limited.
3. Add encryption: `rclone config` → new remote → type `crypt` → point it at a folder on the remote from step 2 (say `gdrive:life-archive`) → standard filename encryption → let rclone generate two strong passwords.
4. Write both passwords down, in a password manager and on paper. Without them nobody, including you, can read the backup.
5. Edit the folder list at the top of [`toolkit/backup/backup.ps1`](../toolkit/backup/backup.ps1) (Windows) or [`toolkit/backup/backup.sh`](../toolkit/backup/backup.sh) (Mac, Linux), then run it once by hand.
6. Schedule it: Windows Task Scheduler (daily, "run as soon as possible after a missed start"), or `cron` / `launchd` on a Mac.
7. Test a restore (below).

## What to leave out

The scripts already skip caches and temporary files. Also leave out anything holding secrets (API keys, tokens, the rclone config itself) unless you encrypt it separately.

## Test a restore

Do this once after setting up, and again every few months:

1. `rclone cryptcheck <your folder> <crypt remote>:current/<part>` checks that every file in the cloud matches its original.
2. Restore a few files to a new folder: `rclone copy <crypt remote>:current/<part>/<some file> restored/`.
3. Open them and compare them with the originals.

Write down how to restore, in plain steps, and keep the instructions with the passwords. The person who needs them might not be you.
