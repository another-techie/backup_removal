#!/usr/bin/python3

from datetime import datetime
import subprocess
import shlex
import sys
import logging
import re
import os
import argparse

def validate_backup_retention(rel_files, copies_to_keep):
    '''
    Verify that the number of backups to retain complies with the retention policy.
    '''
    filenames = len(rel_files)
    if filenames >= copies_to_keep:
        return True

    else:
        logging.info("Number of backups isn't above the minimum retention level of {}.".format(copies_to_keep))
        return False


def extract_date(rel_files, copies_to_keep=4):
    '''
    Attempt to extract the date of the backup from the filename using a regular 
    expression. If a properly formatted date isn't found in one or more filenames,
    log an error and exit.
    '''

    # Parse the dates in the file names and convert them to datetime objects.
    file_and_date = {}
    dates = []
    date_format = "%m_%d_%Y"
    date_re = r"\d{2}_\d{2}_\d{4}"

    logging.info("Identifying date of each backup using filename.")
    for file in rel_files:
    
        # Attempt to find the date in the filename
        date = re.search(date_re, file)
        try:
            
            date_index = date.span()
            date = file[date_index[0]:date_index[1]]

            try:
                # Convert the date to a datetime object
                datetime_version = datetime.strptime(date, date_format)
                file_and_date[datetime_version] = file
                dates.append(datetime_version)
            
            except ValueError as e:
                logging.error("Improperly formatted date for {} {}".format(file, e))
                exit(1)

        except AttributeError:
            logging.error("Missing properly formatted date in {}".format(file))
            exit(1)
    
    logging.info("Identified {} dates / {} backups".format(len(dates), len(rel_files)))
    
    # Order the dates with the most recent stored first.
    meeting_retention_policy = validate_backup_retention(dates, copies_to_keep)
    if meeting_retention_policy:
        dates.sort(reverse=True)
        return dates, file_and_date
    else:
        return False, False



def identify_old_backups(dates, file_and_date, copies_to_keep):
    '''
    Identify the most recent backup files to retain. The number of backups to retain is 
    determined by the value stored in the copies to keep variable.
    '''
    files_to_keep = []
    index = 0
    logging.info("Identifying most recent {} backups to keep.".format(copies_to_keep))
    while copies_to_keep > 0:
        key = dates[index]
        file = file_and_date[key]
        files_to_keep.append(file)
        index += 1
        copies_to_keep -= 1

    logging.info("Backups to keep: {}".format(files_to_keep))
    return files_to_keep


def find_backups(command):
    # Find backups using the specified command
    logging.info("Finding backups using command: {}.".format(command))
    rel_files = subprocess.run(command, shell=True, capture_output=True)

    # Parse the command output and identify the filenames.
    command_output = rel_files.stdout
    command_output = command_output.decode("UTF-8")
    # print(command_output)
    rel_files = command_output.split("\n")
    
    # Remove the extra line from the list of relevant files.
    del rel_files[-1]

    if len(rel_files) > 0:
        logging.info("Found {} backups.".format(len(rel_files)))

        return rel_files
    
    else:
        logging.warning("No backups found")
        return False


def delete_old_backups(rel_files, files_to_keep, backup_name, local_dir=False, delete_command=False, dry_run=False):
# Delete any backup files that are not the recent backup files selected for retention.
    if dry_run:
        print("This is a dry run. Not removing any backups.")
        logging.info("This is a dry run. Not removing any backups.")
        for file in rel_files:
            if file not in files_to_keep:
                print("Backup to be removed: {}".format(file))
                logging.info("Backup to be removed: {}".format(file))
        
    else:
        for file in rel_files:
            if file not in files_to_keep:

                try:
                    # If backups are to be removed from the local filesystem using a specific command
                    if local_dir and delete_command:
                        full_path = local_dir + file

                        # Escape the path with quotes to prevent issues with file paths containing spaces
                        full_path = shlex.quote(full_path)

                        # Add the absolute path for the backup to delete to the delete command
                        command = delete_command + full_path
                        exit_code = subprocess.run(command, shell=True, capture_output=True)

                        if exit_code.returncode != 0:
                            logging.error("{}: an error occurred when attempting to delete {}".format(backup_name, file))
                        
                        else:
                            logging.info("Successfully removed backup: {}".format(file))

                    # If backups are to be removed from the local filesystem
                    if local_dir and not delete_command:
                        full_path = local_dir + file
                        full_path = shlex.quote(full_path)
                        # print("Backup to remove: {}".format(full_path))
                        os.remove(full_path)
                        logging.info("Successfully removed backup: {}".format(file))


                    # If backups are removed exclusively with a delete command.
                    if delete_command and not local_dir:
                        command = delete_command + file
                        exit_code = subprocess.run(command, shell=True, capture_output=True)

                        if exit_code.returncode != 0:
                            logging.error("{}: an error occurred when attempting to delete {}".format(backup_name, file))
                        
                        else:
                            logging.info("Successfully removed backup: {}".format(file))



                
                except FileNotFoundError:
                    logging.error("There is a problem with the delete command. {} wasn't found")
                    exit(1)



def remove_old_backups(backup_list_command, backup_name, copies_to_keep=4, local_dir=False, delete_command=False, dry_run=False):

    # Ensure a minimum number of backups are retained.
    
    if not copies_to_keep >= 3:
        sys.exit("Must retain a minimum of 3 backups!")
        

    rel_files = find_backups(backup_list_command)
    

    # If backups were found
    if rel_files:
        dates, file_and_date = extract_date(rel_files, copies_to_keep=copies_to_keep)

        # Ensure a minimum number of backups are retained.
        if dates:

            files_to_keep = identify_old_backups(dates, file_and_date, copies_to_keep)
            
            delete_old_backups(rel_files, files_to_keep, backup_name, local_dir, delete_command, dry_run)
            logging.info("\n")

        else:
            logging.warning("Insufficient backups are being maintained")




if __name__ == "__main__":
    logging.basicConfig(filename="remove_old_backups.log",format="%(asctime)s:%(levelname)s:%(message)s", level=logging.DEBUG)

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("list_command", help="Command to list backup files.", type=str)
    parser.add_argument("backup_name", help="What the backups are of/for.", type=str)
    parser.add_argument('-k', dest='copies_to_keep', help='Number of backups to retain.', type=int, default=4)
    parser.add_argument('-l', dest='local_dir', help='Local filesystem directory where the backup files are stored.', default=False)
    parser.add_argument('-c', dest='delete_command', help='Specific command to run to delete old backup files. Useful for removing backups from cloud storage with a program like rclone.', default=False)
    parser.add_argument('-n', action='store_true', dest='dry_run', help='Perform a dry run. Don\'t remove backups, only print backups to be removed', default=False)
    args = parser.parse_args()
    
    remove_old_backups(args.list_command, args.backup_name, copies_to_keep=args.copies_to_keep, local_dir=args.local_dir, delete_command=args.delete_command, dry_run=args.dry_run)

