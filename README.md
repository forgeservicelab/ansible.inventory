# Repository with Ansible inventory plugins

This is a repository with experimental Ansible inventory plugins. With Ansible, you can use static and dynamic inventory, and you can combine these two.

## Installation

Clone this repo to your home, and then set

```
hostfile = ~/inventory/sources
```

in ansible.cfg


## ssh_config.py

This plugin allows you to use host aliases from your .ssh/config file.

If you have in your .ssh/config

```
Host git
HostName git.domain.org
User YOURUSERNAME
IdentityFile /home/YOURUSERNAME/keys/thekey
```

you can do

```
$ ansible git -m ping
```

## nova.py

This plugin allows you to use names of virtual machines in OpenStack.

If you have

```
$ nova list
+-------+--------------+--------+----------+
| ID    | Name         | Status | Networks |
+-------+--------------+--------+----------+
| [...] | ldaptest     | ACTIVE | [...]    |
| [...] | openldaptest | ACTIVE | [...]    |
+-------+--------------+--------+----------+
```

you can do

```
$ ansible ldaptest -m ping
```

At the moment, the plugin will not handle well instances with the same names.

## localhost

This is a simple static inventory, which only maps alias "localhost". With this in place, one can use " - hosts: localhost" in playbooks which should be run locally.
