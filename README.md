# Disclaimer
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

This program is used to remove backup files that no longer need to be maintained. I recommend making sure you understand it's usage before running it. The program has a 'dry run' switch `-n` which will show the target backup files that will be removed **without** deleting them.

# Assumptions
This program makes the below assumptions. These assumptions should be true for the script to behave as expected:
1. All backups are in the specified local directory or can be listed with the passed command.
2. The backup file name includes a date in the **MM_DD_YYYY** format. This is used to determine the age of the backup.
   1. There is only one date (in the format above) present in the file name.
3. The files in the specified local directory or listed with the passed command are all backup files for the same thing.

# Usage
```
usage: remove_old_backups.py [-h] [-k COPIES_TO_KEEP] [-l LOCAL_DIR]
                             [-c DELETE_COMMAND] [-n]
                             list_command backup_name

positional arguments:
  list_command       Command to list backup files.
  backup_name        What the backups are of/for.

options:
  -h, --help         show this help message and exit
  -k COPIES_TO_KEEP  Number of backups to retain.
  -l LOCAL_DIR       Local filesystem directory where the backup files are
                     stored.
  -c DELETE_COMMAND  Specific command to run to delete old backup files.
                     Useful for removing backups from cloud storage with a
                     program like rclone.
  -n                 Perform a dry run. Don't remove backups, only print
                     backups to be removed
```

## Examples
Removing backups from local file system (dry run): `python3 remove_old_backups.py "ls /mnt/external_drive/my_backups" "desktop backup" -l "/mnt/external_drive/my_backups" -n`

Removing backups from local file system (dry run): `python3 remove_old_backups.py "ls /mnt/big_drive/backups" "server backup" -l "/mnt/big_drive/backups"`

Removing backups from rclone remote: `python3 remove_old_backups.py "rclone lsf my_remote:backups" "rclone cloud backup" -c "rclone deletefile my_remote:backups/" -n`