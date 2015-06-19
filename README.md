# BlackHole

### What is BlackHole and what it can do?

![BlackHole - terminal](https://raw.githubusercontent.com/aenima-x/BlackHole/gh-pages/images/terminal.png)
It's a security tool to keep tracking and monitor all the ssh and sql sessions on your servers.
You will know who is connected to where and see what they are doing in real time.
Identify and keep track of anonymous connections that share a single user.
Use the session logs to do forensics of problems generated after an implementation or deployment done by a user.
Give users access to your platform without handover of any password.
It replaces the shell of the user (in the BlackHole server) giving the user only a menu that offers targets based on his profile.

BlackHole is gonna be the only entry point for all your hosts and databases.

![BlackHole - Diagram](https://raw.githubusercontent.com/aenima-x/BlackHole/gh-pages/images/blackhole-diagram.png)

You can also kill any session ongoing that you don't allow

### Keeping track.

![BlackHole - sessions](https://raw.githubusercontent.com/aenima-x/BlackHole/gh-pages/images/sessions.png)
BlackHole gives you a web interface so you can in real time know who is connected to where.
With the possibility of download the log file of that connection so you can see what the user is doing in it.
Also it stores in a database all the information about all the connections established with the targets.
Including:
- User
- Source IP
- Target destination
- User used to authenticate
- Login date
- Logout date
    
### See it in action

Here you can see it in action

[![BlackHole - Review](https://i1.ytimg.com/vi/NSPyeQ6UXgs/hqdefault.jpg)](http://www.youtube.com/watch?v=NSPyeQ6UXgs)

### Installation

Create the group

```Bash
group add backhole
```

Copy to the destination folder, for this example is /opt

```Bash
mv BlackHole /opt
```

Set the permissions

```Bash
chown -r root:blackhole /opt/BlackHole
```

Install the requirements

```Bash
pip install -r requirements.txt
```

If you want to connect to databases, you must install the command line clients

Create the database and set the configuration file

```Bash
mv /opt/BlackHole/blackhole/settings_dev.py /opt/BlackHole/blackhole/settings.py
```

```Bash
vi /opt/BlackHole/blackhole/settings.py
```

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'DATABASE_NAME',
        'USER': 'USER',
        'PASSWORD': 'PASSWORD'
     }}
```

Define the path for the logs and set it to the "log_path" variable

Create the database

```Bash
/opt/BlackHole/manage.py syncdb
```


To run the admin site you can use the django integrated web server, but it's not recommended for production (you must set DEBUG in settings.py to True, remember set it to False in production).

```Bash
/opt/BlackHole/manage.py runserver
```

**IMPORTANT:** Don't forget to have a redis instance running (you can set the ip or hostname un the settings.py file variable called "redis_server")

**IMPORTANT:** The user who runs the admin site mast have permissions to access to the logs but also to kill the processes (basically must be root)

You can use nginx + gunicorn or apache, use the gunicorn and nginx example files

You are now ready to create users and start using it.

```Bash
useradd -s /opt/BlackHole/launcher.py -g blackhole -d /home/XXXX USER
```

You must set **/opt/BlackHole/launcher.py** as the shell of the users, and don't forget to set "blackhole" as their main group.

It's recommended to disable SCP and SFTP en the server to avoid any access that its not done using BlackHole.
Also Disable port forwarding in the sshd configuration

### Setup
Here you can see how to setup BlackHole
[![BlackHole - Setup](https://i1.ytimg.com/vi/trjYvbQE1vY/hqdefault.jpg)](http://www.youtube.com/watch?v=trjYvbQE1vY)

### Requirements

Software:
- Linux
- Python (tested on 2.6 and 2.7)
- A database engine, in the examples I use MySQL
- Redis (for store information about the active connections)
    
Python Modules:
- Django (Tested with 1.6)
- django-bootstrap3
- django-selectable
- django-widget-tweaks
- paramiko
- urwid
- redis
- pytz
- (The databse engine module of your choice)
    
 