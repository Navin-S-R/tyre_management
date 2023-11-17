import json
import frappe
import requests
from tyre_management.python.frontend_api import get_smart_tyre_data_bulk
import datetime
from itertools import groupby

def send_preventive_maintenance_alert():
	vehicle_list=[]
	time_change=datetime.timedelta(days=20)
	start_datetime=(datetime.datetime.now()-time_change)
	maintenance_alert_list = frappe.get_all("Tyre Maintenance",
								{
									"maintenance_type":"Preventive Maintenance",
									"time_stamp":[">=",start_datetime],
									"alert_details":["not in",["Preventive Maintenance"]],
									"docstatus":1
								},
								["name","customer","vehicle_no","serial_no"])
	if maintenance_alert_list:
		sorted_data = sorted(maintenance_alert_list, key=lambda x: x['vehicle_no'])
		grouped_data = {key: list(group) for key, group in groupby(sorted_data, key=lambda x: x['vehicle_no'])}
		for key, value in grouped_data.items():
			no_of_wheels = frappe.get.get_value("Vehicle Registration Certificate",{"name":key},"wheels")
			if no_of_wheels and no_of_wheels >= len(value):
				vehicle_list.append(key)
	if vehicle_list:
		res = get_smart_tyre_data_bulk(Vehicle_list=vehicle_list)
		if res and res.get('status') =='success' and res.get('res'):
			for key, value in res.get('res'):
				vehicle_details=frappe.db.get_value("Vehicle Registration Certificate",{"name":key},['customer'],as_dict=True)
				if vehicle_details:
					party_details=frappe.db.get_value("Customer",{"name":vehicle_details.get('customer')},['mail_to_receive_alert','whatsapp_number','name'],as_dict=True)
					alert_type = frappe.get_all("Alert Type Multselect", {
							"parent": vehicle_details.get('customer'),
							"parentfield": "alert_type",
							"parenttype": "Customer"
						}, pluck="alert_type") or []
					tyre_msg=""
					if alert_type:
						party_details["alert_type"] = alert_type
						if "WHATSAPP" in party_details["alert_type"] and party_details.get('whatsapp_number'):
							for row_value in value:
								pass