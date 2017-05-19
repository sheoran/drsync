# DRSYNC
Directory Sync (drsync) helps you keep two directories separated by network in sync. 
 * Very thin wrapper around rsync
 * Built to keep a portable development environment in mind and is greatly inspired by tools like ```git```, ```mercurial```
 * Two way on demand sync
 * Supports one way live stream of changes
 * Support sync target alias to send/recieve data from mulitple locations


# Use Case Solved
 1. Sync directory between two systems for developer working over VPN/low bandwidth network
 1. Keep a close to real time/ on demand backup of a directory somewhere remote
 1. Send data to multiple location
 1. Get data from multiple location
 
# Install
    pip install drsync

# How to Use
 1. Go to desired directory and run ```drsync -r```. 
 1. It will register the directory and copy configs to path printed on console.
 1. Review ```rsyncfilter``` file and make changes as needed.
 1. To override default filter template
    1. copy files from you pip install site_packages. 
    ```
    example:
     cp ../python2.7/site-packages/dsync/dsync/data/*.txt ~/.drsync/
    ```

# Caution
   1. Use liveSync feature only if you are sure you won't update anything on remote end, to avoid any kind of data loss. 
    1. Kill live sync when you need to perform changes on remote site, pull those changes and resume livesync.
    1. Other choice is update dsync_conf and remove `--delete` from rsync opts
   2. If not using liveSync and you have made changes on remote end, do a pull before doing anything else.
   3. ```Always review payload after config change using "test" option``` 
   
# Tested
   1. With python 2.7