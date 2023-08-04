import unittest
import shlex
from datetime import datetime
from remove_old_backups import *

file_names = ('some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip', 'some_backup_02_15_2012.zip', 'some_backup_07_24_2015.zip.7z', 'some_backup_12_01_2007.tar.gz')
bad_filenames = ('backup test name.tar.gz', 'backup 10 12 2021.gz')

copies_to_keep = 4

def test_beginning(self):
    logging.info('Running test: {} '.format(unittest.TestCase.id(self)))

class test_dates(unittest.TestCase):

    def test_bad_dates(self):
        '''
        Verify the program handles invalid dates properly.
        '''
        test_beginning(self)
        rel_files = ('some_backup_22_16_2023.zip', 'some_backup_10_34_2023.tar', 'some_backup_10_34_3000.tar', 'some_backup_24_34_4567.tar.gz')
        with self.assertRaises(SystemExit):
            dates, file_and_date = extract_date(rel_files)
        # self.assertTrue(len(dates) == 0 and len(file_and_date) == 0)
        self.assertLogs(level='ERROR')
        logging.info("\n")


    def test_valid_dates(self):
        '''
        Verify the program handles valid dates properly.
        '''
        test_beginning(self)
        rel_files = ('some_backup_03_22_2023.zip', 'some_backup_10_01_2025.tar', 'some_backup_07_03_2010.zip', 'some_backup_08_01_2006.tar.gz', 'some_backup_02_15_2012.zip', 'some_backup_07_24_2015.zip.7z', 'some_backup_12_01_2007.tar.gz')
        dates, file_and_date = extract_date(rel_files)
        self.assertNotEqual(len(dates), 0)
        self.assertNotEqual(len(file_and_date), 0)
        self.assertEqual(len(dates), len(file_and_date))
        self.assertEqual(len(dates), len(rel_files))
        logging.info("\n")


class test_backup_discovery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        empty_directory = subprocess.run("mkdir /tmp/empty_dir", shell=True, capture_output=True)
        empty_directory = empty_directory.returncode

        directory_to_fill = subprocess.run("mkdir /tmp/dir_to_fill", shell=True, capture_output=True)
        directory_to_fill_success = directory_to_fill.returncode

        if directory_to_fill_success == 0:
            # files_to_create = ('some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip', 'backup test name.tar.gz')
            files_to_create = file_names
            for file in files_to_create:
                absolute_path = "/tmp/dir_to_fill/" + file
                command = "touch {}".format(shlex.quote(absolute_path))
                created_file = subprocess.run(command, shell=True)

        else:
            print("An error occurred creating the directories needed for the backup discovery tests. Skipping......")
            raise unittest.SkipTest()

    @classmethod
    def tearDownClass(cls):
        created_dirs = ("/tmp/dir_to_fill", "/tmp/empty_dir")
        # created_files = ('backup test name.tar.gz','some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip')
        created_files = file_names
        
        for file in created_files:
            # command = "rm /tmp/dir_to_fill/" + file
            command = "rm /tmp/dir_to_fill/{}".format(shlex.quote(file))
            remove_file = subprocess.run(command, shell=True, capture_output=True)
            if remove_file.returncode == 0:
                logging.info("Successfully removed: /tmp/dir_to_fill/{}".format(file))

        for dir in created_dirs:
            command = "rm -r {}".format(shlex.quote(dir))
            removed_dir = subprocess.run(command, shell=True, capture_output=True)
            if remove_file.returncode == 0:
               logging.info("Successfully removed: {}".format(dir))
        logging.info("\n")


    def test_working_command(self):
        '''
        Verify the program successfully discovers backup files when given a valid command.
        '''
        test_beginning(self)
        rel_files = find_backups("ls /tmp/dir_to_fill")
        self.assertTrue(rel_files)
        self.assertEqual(len(rel_files), copies_to_keep)
        logging.info("\n")


    def test_broken_command(self):
        '''
        Verify the program properly handles backup file discovery when given an non-functional.
        '''
        test_beginning(self)
        rel_files = find_backups("qwerqwerqwer /qewrqewr/dir_to_fill")
        self.assertFalse(rel_files)
        logging.info("\n")


    def test_inaccessible_dir(self):
        '''
        Verify the program properly handles backup file discovery when the command 
        lists an inaccessible dir.
        '''
        test_beginning(self)
        rel_files = find_backups("ls /root")
        self.assertFalse(rel_files)
        logging.info("\n")

    
    def test_non_existent_dir(self):
        '''
        Verify the program properly handles backup file discovery when the command lists a 
        directory that doesn't exist.
        '''
        test_beginning(self)
        rel_files = find_backups("ls /erhjngiowhbeokinhhwiok")
        self.assertFalse(rel_files)
        logging.info("\n")


    def test_identify_old_backups_success(self):
        '''
        Verify the program successfully discovers backups.
        '''
        test_beginning(self)
        rel_files = find_backups('ls /tmp/dir_to_fill')
        if rel_files:
            dates, file_and_date = extract_date(rel_files, copies_to_keep=copies_to_keep)
        if dates:
            files_to_keep = identify_old_backups(dates, file_and_date, copies_to_keep=copies_to_keep)
            self.assertEqual(len(files_to_keep), copies_to_keep)
            logging.info("\n")
        
        # else:
        #     logging.warning("Insufficient backups are being maintained")
        #     self.assertFalse(dates)
        #     logging.info("\n")
    
    def test_identify_old_backups_fail(self):
        '''
        Verify the program properly handles backup file discovery when the command lists an
        empty directory.
        '''
        test_beginning(self)
        rel_files = find_backups('ls /tmp/empty_dir')
        self.assertFalse(rel_files)


    def test_remove_old_backups_fail_retention_policy(self):
        '''
        Verify the program properly handles when the backup retention policy is set higher
        than the number of existing backups.
        '''
        test_beginning(self)
        remove_old_backups('ls /tmp/dir_to_fill', "test", copies_to_keep=10, local_dir='/tmp/dir_to_fill/')
        self.assertLogs(level="ERROR")
        logging.info("\n")
    

    def test_remove_old_backups_fail_bad_backup_dir(self):
        '''
        Verify the program properly handles when the local_dir variable is set to a non-existent
        directory.
        '''
        test_beginning(self)
        with self.assertRaises(SystemExit):
            remove_old_backups('ls /tmp/dir_to_fill', "test", copies_to_keep=copies_to_keep, local_dir='/tmp/qwerpiwqer0930402/')
        self.assertLogs(level="ERROR")
        logging.info("\n")


    def test_remove_old_backups_success(self):
        '''
        Verify the program successfully removes old backups from the local filesystem.
        '''
        test_beginning(self)
        list_command = 'ls /tmp/dir_to_fill'
        remove_old_backups(list_command, "test", copies_to_keep=copies_to_keep, local_dir='/tmp/dir_to_fill/')
        self.assertLogs(level="INFO")

        rel_files = find_backups(list_command)
        self.assertEqual(len(rel_files), copies_to_keep)
        logging.info("\n")


    # def test_remove_old_backups_sucess_command(self):
    #     test_beggining(self)
    #     remove_old_backups('rclone lsf /tmp/dir_to_fill', "test", copies_to_keep=copies_to_keep, local_dir= '/tmp/dir_to_fill/', delete_command='rclone deletefile ')
    #     self.assertLogs(level="INFO")
    #     logging.info("\n")
        # '/usr/bin/rclone deletefile -n /tmp/dir_to_fill/'

class test_backup_on_filesystem_command_deletion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        empty_directory = subprocess.run("mkdir /tmp/empty_dir", shell=True, capture_output=True)
        empty_directory = empty_directory.returncode

        directory_to_fill = subprocess.run("mkdir /tmp/dir_to_fill/", shell=True, capture_output=True)
        directory_to_fill_success = directory_to_fill.returncode

        if directory_to_fill_success == 0:
            # files_to_create = ('some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip', 'backup test name.tar.gz')
            files_to_create = file_names
            for file in files_to_create:
                absolute_path = "/tmp/dir_to_fill/" + file
                command = "touch {}".format(shlex.quote(absolute_path))
                created_file = subprocess.run(command, shell=True)

        else:
            print("An error occurred creating the directories needed for the backup discovery tests. Skipping......")
            raise unittest.SkipTest()


    @classmethod
    def tearDownClass(cls):
        created_dirs = ("/tmp/dir_to_fill", "/tmp/empty_dir", )
        # created_files = ('backup test name.tar.gz','some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip')
    
        
        for file in file_names:
            # command = "rm /tmp/dir_to_fill/" + file
            command = "rm /tmp/dir_to_fill/{}".format(shlex.quote(file))
            remove_file = subprocess.run(command, shell=True, capture_output=True)
            if remove_file.returncode == 0:
                logging.info("Successfully removed: /tmp/dir_to_fill/{}".format(file))

        for dir in created_dirs:
            command = "rm -r {}".format(shlex.quote(dir))
            removed_dir = subprocess.run(command, shell=True, capture_output=True)
            if removed_dir.returncode == 0:
               logging.info("Successfully removed: {}".format(dir))
        logging.info("\n")

    
    def test_remove_old_backups_success_command(self):
        '''
        Verify the program successfully removes old backups from the local filesystem using a 
        specific delete command.
        '''
        test_beginning(self)
        list_command = 'rclone lsf /tmp/dir_to_fill'
        remove_old_backups(list_command, "test", copies_to_keep=copies_to_keep, local_dir= '/tmp/dir_to_fill/', delete_command='rclone deletefile ')
        self.assertLogs(level="INFO")
        
        rel_files = find_backups(list_command)
        self.assertEqual(len(rel_files), copies_to_keep)
        logging.info("\n")


class test_backup_command_deletion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        empty_directory = subprocess.run("mkdir /tmp/empty_dir", shell=True, capture_output=True)
        empty_directory = empty_directory.returncode

        directory_to_fill = subprocess.run("mkdir /tmp/dir_to_fill/", shell=True, capture_output=True)
        directory_to_fill_success = directory_to_fill.returncode

        if directory_to_fill_success == 0:
            # files_to_create = ('some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip', 'backup test name.tar.gz')
            files_to_create = file_names
            for file in files_to_create:
                absolute_path = "/tmp/dir_to_fill/" + file
                command = "touch {}".format(shlex.quote(absolute_path))
                created_file = subprocess.run(command, shell=True)

        else:
            print("An error occurred creating the directories needed for the backup discovery tests. Skipping......")
            raise unittest.SkipTest()


    @classmethod
    def tearDownClass(cls):
        created_dirs = ("/tmp/dir_to_fill", "/tmp/empty_dir", )
        # created_files = ('backup test name.tar.gz','some_backup_03_22_2017.zip', 'some_backup_10_01_2022.tar', 'some_backup_07_03_2010.zip')
    
        
        for file in file_names:
            # command = "rm /tmp/dir_to_fill/" + file
            command = "rm /tmp/dir_to_fill/{}".format(shlex.quote(file))
            remove_file = subprocess.run(command, shell=True, capture_output=True)
            if remove_file.returncode == 0:
                logging.info("Successfully removed: /tmp/dir_to_fill/{}".format(file))

        for dir in created_dirs:
            command = "rm -r {}".format(shlex.quote(dir))
            removed_dir = subprocess.run(command, shell=True, capture_output=True)
            if removed_dir.returncode == 0:
               logging.info("Successfully removed: {}".format(dir))
        logging.info("\n")

    
    def test_remove_old_backups_success_command(self):
        '''
        Verify the program successfully removes old backups using only a delete command.
        '''
        test_beginning(self)
        list_command = 'ls /tmp/dir_to_fill'
        remove_old_backups(list_command, "test", copies_to_keep=copies_to_keep, delete_command='rm /tmp/dir_to_fill/')
        self.assertLogs(level="INFO")
        
        rel_files = find_backups(list_command)
        self.assertEqual(len(rel_files), copies_to_keep)
        logging.info("\n")


if __name__ == '__main__':
    logging.basicConfig(filename="test.log",format="%(asctime)s:%(levelname)s:%(message)s", level=logging.DEBUG)
    logging.info('')
    logging.info('')
    logging.info("Starting test at {}".format(datetime.now()))
    logging.info('')
    unittest.main()

