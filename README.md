# tophost-ddns
 Dynamic DNS update script for TopHost domains

## Setup
- Clone repository
```
git clone https://github.com/cavv4/tophost-ddns.git
```
- Change directory
```
cd tophost-ddns
```
- Install requirements
```
python3 -m pip install -r requirements.txt
```
## Usage
```
python3 tophost-ddns.py <arguments>
```
Edit the `config.json` file with your configuration and/or use the arguments below
### Arguments
| Option            | Parameter      | Use                                                                                 |
|-------------------|----------------|-------------------------------------------------------------------------------------|
| `-h` (help)       |                | Show help message                                                                   |
| `-u` (username)   | `<username>`   | Set control panel username                                                          |
| `-p` (password)   | `<password>`   | Set control panel password                                                          |
| `-n` (name)       | `<name>`       | Set name of DNS record to update (use one argument per name E.g. `-n @ -n www)`     |
| `-v` (value)      | `<value>`      | Set update value (will use public ip by default)                                    |
| `-f` (force)      |                | Force update                                                                        |
| `-U` (User agent) | `<user_agent>` | Set custom user agent                                                               |
