#!/usr/bin/env python3
# tophost-ddns script by Cavv

import requests
import bs4
import json
import os
import sys

CONFIG_FILE = "config.json"

CP_DNS_URL = "https://cp.tophost.it/dns"
DNS_UPDATE_URL = "https://cp.tophost.it/x-dns-mod"
LOGIN_URL = "https://cp.tophost.it/x-login"

KNOWN_ARGUMENTS = ["-h", "-u", "-p", "-n", "-v", "-f", "-U"]

# Prints help message
def print_help():
	print("""
tophost-ddns script by Cavv
	
-h		Show this message
-u <username>	Set control panel username
-p <password>	Set control panel password
-n <name>	Set name of DNS record to update (use one argument per name E.g. -n @ -n www)
-v <value>	Set update value (will use public ip by default)
-f		Force update
-U <user_agent>	Set custom user agent""")

# Loads config from json file
def load_config():
	if not os.path.exists(CONFIG_FILE):
		return {}
	
	config = {}
	with open(CONFIG_FILE, "rb") as f:
		config = json.load(f)
	return config

# Loads arguments values in given config
def load_args(config):
	i = 1
	for arg in sys.argv[1:]: # Start from argument 1
		# Bad syntax if argument uses next as value but next is known or there is none
		if arg in ["-u", "-p", "-n", "-v", "-U"]:
			if len(sys.argv) <= i+1 or sys.argv[i+1] in KNOWN_ARGUMENTS:
				print("[ERROR] Bad arguments syntax")
				return None
		
		if arg == "-h":
			print_help()
			sys.exit(0)
		
		if arg == "-u":
			config["username"] = sys.argv[i+1]
		
		if arg == "-p":
			config["password"] = sys.argv[i+1]
		
		if arg == "-n":
			# Remove already present names and append the argument ones
			if config.get("names", []) or not "names" in config:
				config["names"] = []
			config["names"].append(sys.argv[i+1])
		
		if arg == "-v":
			config["update_value"] = sys.argv[i+1]
		
		if arg == "-f":
			config["force_update"] = True
		
		if arg == "-U":
			config["user_agent"] = sys.argv[i+1]
		
		i+=1
	
	return config

# Returns requests session with logged in user
def get_login_session(username, password, user_agent):
	s = requests.Session()
	r = s.post(LOGIN_URL, data = {"user": username, "pass": password}, headers = {"User-Agent": user_agent})
	
	if not r.ok:
		if r.status_code == 403:
			print("[ERROR] Exceeded login rate limit")
		else:
			print("[ERROR] Failed to log in")
		return None
		
	r_json = r.json()
	if "error" in r_json:
		print("[ERROR] " + r_json["error"])
		return None
		
	return s

# Returns update value from site response
def get_update_value(update_value_url, user_agent):
	r = requests.get(update_value_url, headers = {"User-Agent": user_agent})
	if not r.ok:
		return None
	return r.text

# Returns current DNS records in control panel
def scrape_records(html):
	records = []
	
	soup = bs4.BeautifulSoup(html, "html.parser")
	
	table = soup.find("table", id="dns-norm")
	if not table:
		return None
	
	rows = table.find("tbody").find_all("tr")
	if not rows:
		return None
		
	for row in rows:
		row_id = row.get("id", "").replace("tr-", "", 1)

		value_input = row.find("input", id=f"valueo-{row_id}")
		priority_input = row.find("input", id=f"priorityo-{row_id}")
		name_td = row.find("td", id=f"name-{row_id}")
		type_td = row.find("td", id=f"type-{row_id}")
		
		if not all([row_id, value_input, priority_input, name_td, type_td]):
			return None
			
		record = {
			"id": row_id,
			"name": name_td.text.strip(),
			"type": type_td.text.strip(),
			"value": value_input.get("value", ""),
			"priority": priority_input.get("value", "")
		}
		
		records.append(record)

	return records

# Updates DNS records
def update(names, value, s, force_update, user_agent):
	r = s.get(CP_DNS_URL, headers = {"User-Agent": user_agent})
	if not r.ok:
		print("[ERROR] Failed to access control panel")
		return
		
	records = scrape_records(r.text)
	if not records:
		print("[ERROR] Failed to scrape current DNS records")
		return
	
	for name in names:
		# Find the name in current ones and set post data
		post_data = {}
		for record in records:
			if record["name"] == name:
				if record["type"] == "A":
					post_data["record"] = record["id"]
					post_data["value"] = value
					post_data["valueo"] = record["value"]
					post_data["priority"] = ""
					post_data["priorityo"] = ""
					break
		if not post_data:
			print("[ERROR] Missing DNS record (" + name + ")")
			continue
		
		# Update DNS if given value is different or force update is on
		if post_data["valueo"] != value or force_update:
			r = s.post(DNS_UPDATE_URL, data = post_data, headers = {"User-Agent": user_agent})
			if not r.ok:
				print("[ERROR] Failed to update DNS record (" + name + ")")

			r_json = r.json()
			if "error" in r_json:
				print("[ERROR] " + r_json["error"] + " (" + name + ")")
				continue
				
			print("[INFO] Updated DNS record (" + name + ")")
		else:
			print("[INFO] DNS record unchanged (" + name + ")")

if __name__ == "__main__":
	os.chdir(sys.path[0]) # Change working directory to script location
	
	config = load_config()
	config = load_args(config)
	
	if not config:
		print("[ERROR] Failed to load config")
		sys.exit(1)
	
	username = config.get("username", None)
	password = config.get("password", None)
	if not all([username, password]):
		print("[ERROR] Missing credentials")
		sys.exit(1)
	
	names = config.get("names", [])
	update_value = config.get("update_value", None)
	update_value_url = config.get("update_value_url", "https://ipinfo.io/ip")
	force_update = config.get("force_update", False)
	user_agent = config.get("user_agent", "")
	
	login_session = get_login_session(username, password, user_agent)
	if not login_session:
		print("[ERROR] Failed to log in")
		sys.exit(1)
	
	if not update_value:
		update_value = get_update_value(update_value_url, user_agent)
		if not update_value:
			print("[ERROR] Failed to get update value")
			sys.exit(1)
	
	update(names, update_value, login_session, force_update, user_agent)
